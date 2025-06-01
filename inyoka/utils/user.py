"""
    inyoka.utils.user
    ~~~~~~~~~~~~~~~~~

    Several utilities to work with users.

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
from datetime import timedelta

from django.conf import settings
from django.core import signing

_username_re = re.compile(r'^[@_\-\.a-z0-9äöüß]{1,30}$', re.I | re.U)


def is_valid_username(name):
    """Check if the username entered is a valid one."""
    return _username_re.search(name) is not None


def gen_activation_key(user):
    """
    Using django's signer, the activation key is calculated with user id and the username.

    :Parameters:
        user
            The user object the activation key is generated for.
    """
    key = signing.dumps({'user_id': user.id, 'username': user.username}, salt='inyoka.activate', compress=True)
    return key


def check_activation_key(user, key) -> bool:
    """
    Check if an activation key is valid for the given user.

    :Parameters:
        user
            The user object for checking purposes.
        key
            The key that needs to be checked for the *user*.
    """

    try:
        user_details = signing.loads(key, salt='inyoka.activate', max_age=timedelta(hours=settings.ACTIVATION_HOURS))
    except signing.BadSignature:
        return False

    return user_details['user_id'] == user.id and user_details['username'] == user.username
