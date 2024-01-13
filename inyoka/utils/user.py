"""
    inyoka.utils.user
    ~~~~~~~~~~~~~~~~~

    Several utilities to work with users.

    Some parts are ported from the django auth-module.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import hashlib
import re

from django.conf import settings
from django.contrib.auth import hashers

_username_re = re.compile(r'^[@_\-\.a-z0-9äöüß]{1,30}$', re.I | re.U)


def is_valid_username(name):
    """Check if the username entered is a valid one."""
    return _username_re.search(name) is not None


def gen_activation_key(user):
    """
    It's calculated using a sha1 hash of the user id, the username,
    the users email and our secret key and shortened to ensure the
    activation link has less then 80 chars.

    :Parameters:
        user
            An user object from the user the key
            will be generated for.
    """
    return hashlib.sha1(('%d%s%s%s' % (
        user.id, user.username,
        settings.SECRET_KEY,
        user.email,
    )).encode('utf8')).hexdigest()


def check_activation_key(user, key):
    """
    Check if an activation key is correct

    :Parameters:
        user
            An user object a new key will be generated for.
            (For checking purposes)
        key
            The key that needs to be checked for the *user*.
    """
    return key == gen_activation_key(user)


class UnsaltedMD5PasswordHasher(hashers.UnsaltedMD5PasswordHasher):
    algorithm = 'md5'
