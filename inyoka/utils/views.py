# -*- coding: utf-8 -*-
"""
    inyoka.utils.views
    ~~~~~~~~~~~~~~~~~~

    Some custom mixins for views.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import ImproperlyConfigured
from inyoka.portal.utils import abort_access_denied

from .django_19_auth_mixins import \
    PermissionRequiredMixin as _PermissionRequiredMixin


class PermissionRequiredMixin(_PermissionRequiredMixin):
    """
    Mixin to check the permission of an inyoka user.
    """

    def has_permission(self):
        perms = self.get_permission_required()
        for perm in perms:
            if self.request.user.can(perm):
                return True
        return False

    def handle_no_permission(self):
        return abort_access_denied(self.request)


class FormPreviewMixin(object):
    """Mixin to enable FormViews to display a preview."""

    def get_context_data(self, **kwargs):
        """Inject the preview into the context dict, if it was requested."""
        context = super(FormPreviewMixin, self).get_context_data(**kwargs)
        if 'preview' in self.request.POST:
            context['previews'] = self.render_previews()
        return context

    def render_previews(self):
        """Render the previews."""
        previews = {}

        for field in self.get_preview_fields():
            previews[field] = self.preview_method(self.request.POST.get(field, ''))

        return previews

    def get_preview_fields(self):
        """Return the list of form field names that should be rendered."""
        if hasattr(self, 'preview_fields'):
            return self.preview_fields
        else:
            raise ImproperlyConfigured(
                '{0} is missing the preview_fields attribute. Define {0}.preview_fields '
                'or overwrite {0}.get_preview_fields().'.format(self.__class__.__name__)
            )

    def post(self, request):
        """Process POST requests.

        We need to overwrite this method to make the preview work. If the word 'preview'
        is in the `request.POST` we want to show the form again, so we treat the form as
        invalid.
        """
        form = self.get_form()
        if form.is_valid() and 'preview' not in request.POST:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
