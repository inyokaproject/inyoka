# -*- coding: utf-8 -*-
"""
    inyoka.utils.generic
    ~~~~~~~~~~~~~~~~~~~~

    Generic view classes.

    :copyright: (c) 2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.views.generic import edit, base, list
from django.utils.translation import ugettext as _

from inyoka.portal.utils import require_permission
from inyoka.utils.database import get_simplified_queryset
from inyoka.utils.flashing import flash
from inyoka.utils.html import escape
from inyoka.utils.http import TemplateResponse, HttpResponseRedirect
from inyoka.utils.pagination import Pagination
from inyoka.utils.sortable import Sortable
from inyoka.utils.templating import render_template
from inyoka.utils.urls import href


class TemplateResponseMixin(base.TemplateResponseMixin):
    """A mixin that can be used to render a template.

    This mixin hooks in our own `Jinja <http://jinja.pocoo.org>`_
    based :class:`TemplateResponse` class.
    """
    response_class = TemplateResponse

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response with a template rendered with the given context.
        """
        template_name = self.get_template_names()[0]
        return self.response_class(template_name=template_name, context=context)


class EditMixin(object):
    """Provides a flash message and success url"""
    urlgroup_name = ''
    message = u'{verbose_name} “{object_name}” wurde erfolgreich {action}!'

    def form_valid(self, form):
        model = self.model or self.queryset.query.model
        response = super(EditMixin, self).form_valid(form)
        format_args = {'verbose_name': model._meta.verbose_name,
                       'object_name': escape(unicode(self.object))}
        format_args['action'] = u'erstellt' if self.create else u'geändert'
        flash(self.message.format(**format_args), True)
        return response

    def get_success_url(self):
        return self.object.get_absolute_url('edit')

    def get_urlgroup_name(self):
        return self.urlgroup_name or self.context_object_name


class PermissionMixin(object):
    """
    Like the `permission_required` decorator, but for generic views.
    The check can be explicitely disabled by setting `required_permission`
    to False
    """
    required_permission = None

    def get(self, *args, **kwargs):
        func = super(PermissionMixin, self).get
        if self.required_permission:
            func = require_permission(self.required_permission)(func)
        return func(*args, **kwargs)

    def post(self, *args, **kwargs):
        func = super(PermissionMixin, self).post
        if self.required_permission:
            func = require_permission(self.required_permission)(func)
        return func(*args, **kwargs)


class LoginMixin(object):
    """
    This mixin forces a redirection to the login page if the requesting user
    is not logged in and if either :py:attr:`required_login` or
    :py:attr:`required_login_METHOD` is `True`, depending on the current
    request method.
    """
    required_login = False
    required_login_get = False
    required_login_post = False
    required_login_delete = False

    def get(self, *args, **kwargs):
        func = super(LoginMixin, self).get
        req = args[0]
        if not self.required_login and not self.required_login_get or \
                req.user.is_authenticated:
            return func(*args, **kwargs)
        args = {'next': 'http://%s%s' % (req.get_host(), req.path)}
        return HttpResponseRedirect(href('portal', 'login', **args))

    def delete(self, *args, **kwargs):
        func = super(LoginMixin, self).delete
        req = args[0]
        if not self.required_login and not self.required_login_delete or \
                req.user.is_authenticated:
            return func(*args, **kwargs)
        args = {'next': 'http://%s%s' % (req.get_host(), req.path)}
        return HttpResponseRedirect(href('portal', 'login', **args))

    def post(self, *args, **kwargs):
        func = super(LoginMixin, self).post
        req = args[0]
        if not self.required_login and self.required_login_post or \
                req.user.is_authenticated:
            return func(*args, **kwargs)
        args = {'next': 'http://%s%s' % (req.get_host(), req.path)}
        return HttpResponseRedirect(href('portal', 'login', **args))


class FilterMixin(object):
    filtersets = []

    def render_to_response(self, context, **kwargs):
        req = self.request
        filters = [filter(req.GET or None) for filter in self.filtersets]
        context['filtersets'] = filters
        return TemplateResponseMixin.render_to_response(self, context, **kwargs)

    def get_queryset(self):
        qs = super(FilterMixin, self).get_queryset()
        for filter in self.filtersets:
            instance = filter(self.request.GET or None, queryset=qs)
            qs = instance.qs
        return qs


class CreateView(LoginMixin, PermissionMixin, TemplateResponseMixin, EditMixin,
                 edit.BaseCreateView):
    create = True


class UpdateView(LoginMixin, PermissionMixin, TemplateResponseMixin, EditMixin,
                 edit.BaseUpdateView):
    create = False

    # c&p from django to allow context_object_name as url_param :(
    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug_field = self.get_slug_field()
        slug = self.kwargs[self.get_urlgroup_name()]
        queryset = queryset.filter(**{slug_field: slug})

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(_(u"No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


def CreateUpdateView(*init_args, **init_kwargs):
    """
    Helper function to combine `UpdateView` and `CreateView`.
    TODO: Make me a class based view...
    """
    def func(request, *args, **kwargs):
        if kwargs.get(init_kwargs.get('urlgroup_name') or
                      init_kwargs.get('context_object_name')):
            view = UpdateView.as_view(*init_args, **init_kwargs)
        else:
            view = CreateView.as_view(*init_args, **init_kwargs)
        return view(request, *args, **kwargs)
    return func


class BaseDeleteView(edit.BaseDeleteView):
    """
    Generic deletion view. Flashes a template message to confirm
    the deletion and issues the redirects.
    """
    redirect_url = None
    template_name = None
    message = u'Die {verbose_name} „{object_name}“ wurde erfolgreich gelöscht!'

    def get_success_url(self):
        self.sucess_url = self.redirect_url
        return super(BaseDeleteView, self).get_success_url()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        flash(render_template(self.template_name, {'object': self.object}))
        return HttpResponseRedirect(self.redirect_url)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            flash(u'Löschen abgebrochen!')
        else:
            super(BaseDeleteView, self).post(request, *args, **kwargs)
            format_args = {
                'verbose_name': self.model._meta.verbose_name,
                'object_name': escape(unicode(self.object)),
            }
            flash(self.message.format(**format_args), True)
        return HttpResponseRedirect(self.redirect_url)


class DeleteView(LoginMixin, PermissionMixin, BaseDeleteView):
    pass


class BaseListView(TemplateResponseMixin, list.MultipleObjectMixin, base.View):
    default_column = 'id'
    columns = ['id']
    paginate_by = 25
    base_link = None

    def get_paginate_by(self, queryset):
        paginate_by = self.kwargs.get('paginate_by') or \
                      self.request.GET.get('paginate_by')
        paginate_by = paginate_by or self.paginate_by
        return int(paginate_by)

    def get_custom_pagination(self, queryset):
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        cqry = get_simplified_queryset(queryset)
        pagination = Pagination(self.request, queryset, page,
                                self.get_paginate_by(queryset),
                                total=cqry.count(),
                                link=self.base_link)
        return pagination

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        return kwargs

    def get(self, request, *args, **context):
        queryset = self.get_queryset()
        table = Sortable(queryset, request.GET, self.default_column,
                         columns=self.columns)

        queryset = table.get_queryset()
        context['table'] = table
        context['pagination'] = pagination = self.get_custom_pagination(queryset)

        if pagination.needs_redirect_to:
            return pagination.needs_redirect_to()

        context['object_list'] = queryset = pagination.get_queryset()
        context['paginate_by'] = self.get_paginate_by(queryset)
        context.update(self.get_context_data(**context))

        context_object_name = self.get_context_object_name(queryset)
        if context_object_name is not None:
            context[context_object_name] = queryset

        self.object_list = pagination.get_queryset()

        return self.render_to_response(context)


class ListView(LoginMixin, PermissionMixin, BaseListView):
    pass
