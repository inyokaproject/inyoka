# -*- coding: utf-8 -*-
"""
    inyoka.utils.text
    ~~~~~~~~~~~~~~~~~

    Various text realated tools.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import posixpath
import re
from string import ascii_lowercase, digits
from unicodedata import normalize

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import apnumber
from django.utils.translation import ugettext as _
from django.utils.translation import get_language, pgettext

_str_num_re = re.compile(r'(?:[^\d]*(\d+)[^\d]*)+')
_path_crop = re.compile(r'^(\.\.?/)+')
_unsupported_re = re.compile(r'[\x00-\x19#%?]+')
_slugify_replacement_table = {
    '\xdf': 'ss',
    '\xe4': 'ae',
    '\xe6': 'ae',
    '\xf0': 'dh',
    '\xf6': 'oe',
    '\xfc': 'ue',
    '\xfe': 'th',
}
_slugify_word_re = re.compile(r'[^a-zA-Z0-9%s]+' %
    ''.join(re.escape(c) for c in list(_slugify_replacement_table.keys())))
_wiki_slug_allowed_chars = set(ascii_lowercase + digits + '_+-/.()')
_wiki_slug_replace_chars = {
    '¹': '1',
    '²': '2',
    '³': '3',
    ' ': '_'
}


def increment_string(s):
    """Increment a number in a string or add a number."""
    m = _str_num_re.search(s)
    if m:
        next = str(int(m.group(1)) + 1)
        start, end = m.span(1)
        if start or end:
            return '{0}-{1}{2}'.format(
                s[:max(end - len(next), start)],
                next,
                s[end:])
    return s + '-2'


def slugify(string, convert_lowercase=True):
    """Slugify a string."""
    if isinstance(string, bytes):
        string = string.decode(settings.DEFAULT_CHARSET)
    result = []
    if convert_lowercase:
        string = string.lower()
    for word in _slugify_word_re.split(string.strip()):
        if word:
            for search, replace in _slugify_replacement_table.items():
                word = word.replace(search, replace)
            word = normalize('NFKD', word)
            result.append(word)
    return '-'.join(result) or '-'


def join_pagename(name1, name2):
    """
    Join a page with another one.  This works similar to a normal filesystem
    path join but with different rules.  Here some examples:

    >>> join_pagename('Foo', 'Bar')
    'Foo/Bar'
    >>> join_pagename('Foo', '/Bar')
    'Bar'
    >>> join_pagename('Foo', 'Bar/Baz')
    'Bar/Baz'
    >>> join_pagename('Foo', './Bar/Baz')
    'Foo/Bar/Baz'
    """
    if name1 is None or name2 is None:
        return name1 or name2 or ''
    if not isinstance(name1, str):
        name1 = name1.name
    if not isinstance(name2, str):
        name2 = name2.name
    if '/' in name2 and not _path_crop.match(name2):
        name2 = '/' + name2
    path = posixpath.join(name1, name2).lstrip('/')
    return _path_crop.sub('', posixpath.normpath(path))


def normalize_pagename(name, strip_location_markers=True):
    """
    Normalize a pagename.  Strip unsupported characters.  You have to call
    this function whenever you get a pagename from user input.  The models
    itself never check for normalized names and passing unnormalized page
    names to the models can cause serious breakage.

    If the second parameter is set to `False` the leading slashes or slash
    like path location markers are not removed.  That way the pagename is
    left unnormalized to a part but will be fully normalized after a
    `join_pagename` call.
    """
    name = '_'.join(_unsupported_re.sub('', name).split()).rstrip('/')
    if not strip_location_markers:
        return name
    name = name.lstrip('/')
    return _path_crop.sub('', name)


def wiki_slugify(name):
    """
    A special variant of slugify() used in our wiki. It tries to generate
    an internal representation of a wiki pagename, helpful if someone
    links a wiki pages with little differences like accents.
    """
    if isinstance(name, bytes):
        name = name.decode(settings.DEFAULT_CHARSET)
    name = name.lower()
    for rchar, replacement in _wiki_slug_replace_chars.items():
        name = name.replace(rchar, replacement)
    name = str(normalize('NFD', name))
    existing_chars = set(name)
    disallowed_chars = existing_chars - _wiki_slug_allowed_chars
    for char in disallowed_chars:
        name = name.replace(char, '')
    return name


def get_pagetitle(name, full=True):
    """
    Get the title for a page by name.  Per default it just returns the title
    for the full page, not just the last part.  If you just want the part
    after the last slash set `full` to `False`.
    """
    name = normalize_pagename(name)
    if not full:
        name = name.rsplit('/', 1)[-1]
    return ' '.join(x for x in name.split('_') if x)


def human_number(value, gender=None):
    if value == 10:
        return _("ten")
    if value == 11:
        return _("eleven")
    if value == 12:
        return _("twelve")
    lang = get_language()
    if value == 1 and gender and 'en' not in lang.lower():
        return {
            'masculine': pgettext('masculine', 'one'),
            'feminine': pgettext('feminine', 'one'),
            'neuter': pgettext('neuter', 'one')}.get(gender, _('one'))
    return apnumber(value)
