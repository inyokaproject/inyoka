#-*- coding: utf-8 -*-
"""
    inyoka.portal.auth
    ~~~~~~~~~~~~~~~~~~~~

    Custom authorization functions for Inyoka.

    :copyright: (c) 2007-2016 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group

from inyoka.portal.user import User, UserBanned


class InyokaAuthBackend(ModelBackend):
    """Customized authenticating backend to support Inyoka specific features.

     * user banning
     * Workarounds for case (in)sensitive user names
     * anonymous user Permissions
    """

    def authenticate(self, username, password):
        """
        Authenticate a user with `username` (which can also be the email
        address) and `password`.

        :Raises:
            User.DoesNotExist
                If the user with `username` does not exist
            UserBanned
                If the found user was banned by an admin.
        """
        try:
            user = User.objects.get_by_username_or_email(username)
        except:
            return None

        if user.is_banned:
            # user banned ad infinitum
            if user.banned_until is None:
                raise UserBanned()
            else:
                # user banned for a specific period of time
                if (user.banned_until >= datetime.utcnow()):
                    raise UserBanned()
                else:
                    # period of time gone, reset status
                    user.status = User.STATUS_ACTIVE
                    user.banned_until = None
                    user.save()
                    user.groups.add(Group.objects.get_registered_group())

        if user.check_password(password):
            return user

    def _get_permissions(self, user_obj, obj, from_name):
        """
        Returns the permissions of `user_obj` from `from_name`. `from_name` can
        be either "group" or "user" to return permissions from
        `_get_group_permissions` or `_get_user_permissions` respectively.
        """
        if obj is not None:
            return set()

        perm_cache_name = '_%s_perm_cache' % from_name
        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                perms = getattr(self, '_get_%s_permissions' % from_name)(user_obj)
            perms = perms.values_list('content_type__app_label', 'codename').order_by()
            setattr(user_obj, perm_cache_name, set("%s.%s" % (ct, name) for ct, name in perms))
        return getattr(user_obj, perm_cache_name)

    def get_all_permissions(self, user_obj, obj=None):
        if obj is not None:
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = self.get_user_permissions(user_obj)
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)
