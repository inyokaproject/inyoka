#-*- coding: utf-8 -*-
"""
    inyoka.utils.user
    ~~~~~~~~~~~~~~~~~

    Serveral utilities to work with users.

    Some parts are ported from the django auth-module.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from hashlib import md5, sha1
from django.conf import settings


_username_re = re.compile(ur'^[@\-\.a-z0-9 öäüß]{1,30}$', re.I | re.U)
_username_url_re = re.compile(ur'^[@\-\._a-z0-9 öäüß]{1,30}$', re.I | re.U)
_username_split_re = re.compile(ur'[\s_]+')


def is_valid_username(name):
    """Check if the username entered is a valid one."""
    return _username_re.search(name) is not None


def normalize_username(name):
    """Normalize the username."""
    if _username_url_re.search(name) is not None:
        rv = ' '.join(p for p in _username_split_re.split(name) if p)
        if rv:
            return rv
    raise ValueError('invalid username')


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
    return sha1(('%d%s%s%s' % (
        user.id, user.username,
        settings.SECRET_KEY,
        user.email,
    )).encode('utf8')).digest()[:9].encode('base64') \
        .strip('\n=').replace('/', '_').replace('+', '-')


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


def get_hexdigest(salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the sha1 algorithm.
    """
    if isinstance(raw_password, unicode):
        raw_password = raw_password.encode('utf-8')
    return sha1(str(salt) + raw_password).hexdigest()


def check_password(raw_password, enc_password, convert_user=None):
    """
    Returns a boolean of whether the raw_password was correct.  Handles
    encryption formats behind the scenes.
    """
    if isinstance(raw_password, unicode):
        raw_password = raw_password.encode('utf-8')
    salt, hsh = enc_password.split('$')
    # compatibility with old md5 passwords
    if salt == 'md5':
        result = hsh == md5(raw_password).hexdigest()
        if result and convert_user and convert_user.is_authenticated:
            convert_user.set_password(raw_password)
            convert_user.save()
        return result
    return hsh == get_hexdigest(salt, raw_password)
