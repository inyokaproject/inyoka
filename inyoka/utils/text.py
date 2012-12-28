# -*- coding: utf-8 -*-
"""
    inyoka.utils.text
    ~~~~~~~~~~~~~~~~~

    Various text realated tools.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import random
import posixpath
import unicodedata

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import apnumber
from django.utils.translation import get_language
from django.utils.translation import pgettext, ugettext as _


_str_num_re = re.compile(r'(?:[^\d]*(\d+)[^\d]*)+')
_path_crop = re.compile(r'^(\.\.?/)+')
_unsupported_re = re.compile(r'[\x00-\x19#%?]+')
_slugify_replacement_table = {
    u'\xdf': 'ss',
    u'\xe4': 'ae',
    u'\xe6': 'ae',
    u'\xf0': 'dh',
    u'\xf6': 'oe',
    u'\xfc': 'ue',
    u'\xfe': 'th',
}
_slugify_word_re = re.compile(ur'[^a-zA-Z0-9%s]+' %
    u''.join(re.escape(c) for c in _slugify_replacement_table.keys()))


def increment_string(s):
    """Increment a number in a string or add a number."""
    m = _str_num_re.search(s)
    if m:
        next = str(int(m.group(1)) + 1)
        start, end = m.span(1)
        if start or end:
            return u'{0}-{1}{2}'.format(
                s[:max(end - len(next), start)],
                next,
                s[end:])
    return s + u'-2'


def get_random_password():
    """This function returns a pronounceable word."""
    consonants = u'bcdfghjklmnprstvwz'
    vowels = u'aeiou'
    numbers = u'0123456789'
    all = consonants + vowels + numbers
    length = random.randrange(8, 12)
    password = u''.join(
        random.choice(consonants) +
        random.choice(vowels) +
        random.choice(all) for x in xrange(length // 3)
    )[:length]
    return password


def slugify(string, convert_lowercase=True):
    """Slugify a string."""
    if isinstance(string, str):
        string = string.decode(settings.DEFAULT_CHARSET)
    result = []
    if convert_lowercase:
        string = string.lower()
    for word in _slugify_word_re.split(string.strip()):
        if word:
            for search, replace in _slugify_replacement_table.iteritems():
                word = word.replace(search, replace)
            word = unicodedata.normalize('NFKD', word)
            result.append(word.encode('ascii', 'ignore'))
    return u'-'.join(result) or u'-'


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
    if not isinstance(name1, basestring):
        name1 = name1.name
    if not isinstance(name2, basestring):
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
    name = u'_'.join(_unsupported_re.sub('', name).split()).rstrip('/')
    if not strip_location_markers:
        return name
    if name.startswith('./'):
        return name[2:]
    elif name.startswith('../'):
        return name[3:]
    return name.lstrip('/')


def get_pagetitle(name, full=True):
    """
    Get the title for a page by name.  Per default it just returns the title
    for the full page, not just the last part.  If you just want the part
    after the last slash set `full` to `False`.
    """
    name = normalize_pagename(name)
    if not full:
        name = name.rsplit('/', 1)[-1]
    return u' '.join(x for x in name.split('_') if x)


def get_next_increment(values, string, max_length=None, stripdate=False):
    """Return the next usable incremented string."""
    def _stripdate(value):
        parts = value.split('/')
        return parts[:-1], parts[-1]

    def _get_value(value):
        if stripdate:
            stripped = _stripdate(value)
            return u'{0}/{1}'.format(u'/'.join(stripped[0]),
                                     increment_string(stripped[1]))
        return increment_string(value)

    values = list(_stripdate(x)[1] if stripdate else x for x in values)

    if not values:
        return string[:max_length] if max_length is not None else string

    base = None
    for value in values:
        match = _str_num_re.search(value)
        if match is not None and int(match.group(1)) > base:
            base = int(match.group(1))

    gs = (lambda s: s if base is None else s + unicode(base))
    poi = _get_value(gs(string))
    if max_length is None:
        return poi

    if len(poi) > max_length:
        # we need to shorten the string a bit so that we don't break any rules
        strip = max_length - len(poi)
        string = string[:strip]
    return _get_value(gs(string))


def human_number(value, gender=None):
    if value == 10:
        return _("ten")
    if value == 11:
        return _("eleven")
    if value == 12:
        return _("twelve")
    lang = get_language()
    if value == 1 and gender and 'en' not in lang.lower():
        return {'masculine': pgettext('masculine', u'one'),
                'feminine': pgettext('feminine', u'one'),
                'neuter': pgettext('neuter', u'one')
        }.get(gender, _(u'one'))
    return apnumber(value)
