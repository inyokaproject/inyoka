"""
    inyoka.utils.generic
    ~~~~~~~~~~~~~~~~~~~~

    Generic view classes.

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as _PermissionRequiredMixin,
)
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import base, edit, list

from inyoka.utils.database import get_simplified_queryset
from inyoka.utils.pagination import Pagination
from inyoka.utils.sortable import Sortable
from inyoka.utils.templating import flash_message


def trigger_fix_errors_message(request):
    messages.error(request, _('Errors occurred, please fix them.'))


class EditMixin:
    """Provides a flash message and success url"""
    urlgroup_name = ''

    def form_valid(self, form):
        model = self.model or self.queryset.query.model
        response = super().form_valid(form)
        format_args = {'verbose_name': model._meta.verbose_name,
                       'object_name': escape(str(self.object))}
        if self.create:
            message = _('{verbose_name} “{object_name}” was successfully created.')
        else:
            message = _('{verbose_name} “{object_name}” was successfully changed.')

        messages.success(self.request, message.format(**format_args))
        return response

    def get_success_url(self):
        return self.object.get_absolute_url('edit')

    def get_urlgroup_name(self):
        return self.urlgroup_name or self.context_object_name


class FilterMixin:
    filtersets = []

    def render_to_response(self, context, **kwargs):
        req = self.request
        filters = [f(req.GET or None) for f in self.filtersets]
        context['filtersets'] = filters
        return base.TemplateResponseMixin.render_to_response(self, context, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        for f in self.filtersets:
            instance = f(self.request.GET or None, queryset=qs)
            qs = instance.qs
        return qs


class PermissionRequiredMixin(_PermissionRequiredMixin):
    raise_exception = True
    login_required = True

    def handle_no_authentication(self):
        return redirect_to_login(self.request.build_absolute_uri(), self.get_login_url(), self.get_redirect_field_name())

    def dispatch(self, request, *args, **kwargs):
        if self.login_required and not request.user.is_authenticated:
            return self.handle_no_authentication()
        return super().dispatch(request, *args, **kwargs)


class CreateView(PermissionRequiredMixin, base.TemplateResponseMixin, EditMixin,
                 edit.BaseCreateView):
    create = True


class UpdateView(PermissionRequiredMixin, base.TemplateResponseMixin, EditMixin,
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
            raise Http404(_("No %(verbose_name)s found matching the query") %
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
    message = gettext_lazy('{verbose_name} “{object_name}” was deleted successfully!')

    def get_success_url(self):
        self.success_url = self.redirect_url
        return super().get_success_url()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        flash_message(request, self.template_name, {'object': self.object})
        return HttpResponseRedirect(self.redirect_url)

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            messages.info(request, _('Canceled.'))
        else:
            super().post(request, *args, **kwargs)

        return HttpResponseRedirect(self.redirect_url)

    def form_valid(self, form):
        format_args = {
            'verbose_name': self.model._meta.verbose_name,
            'object_name': escape(str(self.object)),
        }
        messages.success(self.request, self.message.format(**format_args))

        return super().form_valid(form)


class DeleteView(PermissionRequiredMixin, BaseDeleteView):
    pass


class BaseListView(base.TemplateResponseMixin, list.MultipleObjectMixin, base.View):
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

    def prepare_context(self, context, queryset):
        context['pagination'] = pagination = self.get_custom_pagination(queryset)
        context['object_list'] = queryset = pagination.get_queryset()
        context['paginate_by'] = self.get_paginate_by(queryset)
        context.update(self.get_context_data(**context))

        context_object_name = self.get_context_object_name(queryset)
        if context_object_name is not None:
            context[context_object_name] = queryset

        return context, queryset


class SortableListView(BaseListView):
    columns = ['id']
    default_column = 'id'

    def get(self, request, *args, **context):
        queryset = self.get_queryset()
        table = Sortable(queryset, request.GET, self.default_column,
                         columns=self.columns)

        queryset = table.get_queryset()
        context['table'] = table
        context, self.object_list = self.prepare_context(context, queryset)

        return self.render_to_response(context)


class OrderedListView(PermissionRequiredMixin, BaseListView):
    order_by = ['id']

    def get(self, request, *args, **context):
        queryset = self.get_queryset().order_by(*self.order_by)
        context, self.object_list = self.prepare_context({}, queryset)

        return self.render_to_response(context)


class ListView(PermissionRequiredMixin, SortableListView):
    pass
