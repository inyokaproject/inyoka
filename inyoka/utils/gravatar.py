# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various application independent utilities.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import requests
from hashlib import md5
from urllib import urlencode
from django.utils import simplejson as json


BASE_URL = 'http://www.gravatar.com/avatar/'
SECURE_BASE_URL = 'https://secure.gravatar.com/avatar/'
PROFILE_URL = 'http://www.gravatar.com/'
RATINGS = ('g', 'pg', 'r', 'x')
MAX_SIZE = 512
MIN_SIZE = 1
DEFAULTS = ('404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro')


def email_hash(string):
    return md5(string.strip().lower()).hexdigest()


def get_gravatar(email, secure=False, rating='g', size=80, default='mm'):
    """Generate a link to the users' Gravatar."""
    assert rating.lower() in RATINGS
    assert MIN_SIZE <= size <= MAX_SIZE

    url = SECURE_BASE_URL if secure else BASE_URL

    options = {'s': size, 'r': rating, 'd': default}
    url += email_hash(email) + '?' + urlencode(options)
    return url


def get_profile(email):
    """Retrieves the profile data of the user.

    :return: A dictionary representing the profile or `None` if nothing found.
    """
    profile = None
    url = u'%s%s.json' % (PROFILE_URL, email_hash(email))
    response = requests.get(url)
    if response.status_code == 200:
        profile = json.loads(response.content)['entry'][0]
    return profile
