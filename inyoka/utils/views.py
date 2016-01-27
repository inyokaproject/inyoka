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
