#-*- coding: utf-8 -*-
from datetime import datetime
from django.contrib.auth.backends import ModelBackend
from inyoka.portal.user import User, UserBanned


class InyokaAuthBackend(ModelBackend):
    """Customized authenticating backend to support Inyoka specific features.

     * user banning
     * Workarounds for case (in)sensitive user names
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
            user = User.objects.get(username)
        except User.DoesNotExist:
            # fallback to email login
            if '@' in username:
                user = User.objects.get(email__iexact=username)
            else:
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
                    user.status = 1
                    user.banned_until = None
                    user.save()

        if user.check_password(password):
            return user
