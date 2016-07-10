# -*- coding: utf-8 -*-
"""
    inyoka.portal.auth
    ~~~~~~~~~~~~~~~~~~~~

    Custom authorization functions for Inyoka.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib.auth.models import Permission

from inyoka.portal.user import User, UserBanned


class InyokaAuthBackend(object):
    """
    Customized authentication backend to support Inyoka specific features:

    * user banning
    * workaround for case (in)sensitive user names
    * login by username or email
    * anonymous permissions
    """

    def authenticate(self, username=None, password=None, **kwargs):
        """
        Authenticate a user with `username` (which can also be the email
        address) and `password`.

        :Raises:
            UserBanned
                If the found user was banned by an admin.
        """
        try:
            user = User.objects.get_by_username_or_email(username)
        except:
            User().set_password(password)
            return None

        if not user.check_password(password):
            return None

        if user.is_banned:
            if not user.unban():
                raise UserBanned()

        if user.system:
            return None

        return user

    def get_user_permissions(self, user_obj, obj=None):
        """
        Returns present Permissions for user_obj.

        As we don't use user based Permissions in Inyoka we always return an empty
        set to avoid incompatibilities with Django Upstream.
        """
        return set()

    def get_group_permissions(self, user_obj, obj=None):
        """
        Returns the permissions of `user_obj` based on the groups a user is in.
        """
        if obj is not None:
            return set()
        perm_cache_name = '_perm_cache'

        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                perms = Permission.objects.filter(group__user=user_obj)
            perms = perms.values_list('content_type__app_label', 'codename').order_by()
            setattr(user_obj, perm_cache_name, set("%s.%s" % (app, permission) for app, permission in perms))
        return getattr(user_obj, perm_cache_name)

    def get_all_permissions(self, user_obj, obj=None):
        """
        Returns all present Permissions for user_obj.

        In fact we simply return get_group_permissions() because we don't use any
        other Permissions in Inyoka.
        """
        return self.get_group_permissions(user_obj, obj)

    def has_perm(self, user_obj, perm, obj=None):
        """
        Return `True` if `user_obj` has `perm` or `False` in any other case.

        This Backend don't support object based permissions, and will always
        return `False` if requests through this backend if `obj` is given.

        Inactive Users, except anonymous, always get back `False` for security
        reasons.
        """
        if obj is not None:
            return False

        if not (user_obj.is_active or user_obj.is_anonymous()):
            return False

        return perm in self.get_all_permissions(user_obj, obj)

    def has_module_perms(self, user_obj, app_label):
        """
        Returns True if user_obj has any permissions in the given app_label.

        Inactive Users, except anonymous, always get back `False` for security
        reasons.
        """
        if not (user_obj.is_active or user_obj.is_anonymous()):
            return False

        for perm in self.get_all_permissions(user_obj):
            if perm[:perm.index('.')] == app_label:
                return True
        return False

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
