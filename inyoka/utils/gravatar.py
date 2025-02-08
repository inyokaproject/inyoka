"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various application independent utilities.

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
from hashlib import md5
from urllib.parse import urlencode

import requests

BASE_URL = 'https://www.gravatar.com/avatar/'
PROFILE_URL = 'https://www.gravatar.com/'
RATINGS = ('g', 'pg', 'r', 'x')
MAX_SIZE = 512
MIN_SIZE = 1
DEFAULTS = ('404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro')


def email_hash(string):
    string = string.strip().lower().encode()
    return md5(string).hexdigest()


def get_gravatar(email, rating='g', size=80, default='mm'):
    """Generate a link to the users' Gravatar."""
    assert rating.lower() in RATINGS
    assert MIN_SIZE <= size <= MAX_SIZE

    options = {'s': size, 'r': rating, 'd': default}
    return BASE_URL + email_hash(email) + '?' + urlencode(options)


def get_profile(email):
    """Retrieves the profile data of the user.

    :return: A dictionary representing the profile or `None` if nothing found.
    """
    profile = None
    url = '%s%s.json' % (PROFILE_URL, email_hash(email))
    response = requests.get(url)
    if response.status_code == 200:
        profile = json.loads(response.content)['entry'][0]
    return profile
