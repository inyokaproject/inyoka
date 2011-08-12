# -*- coding: utf-8 -*-
"""
    inyoka.utils.text
    ~~~~~~~~~~~~~~~~~

    Various text realated tools.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import os
import random
import posixpath
import unicodedata
from django.conf import settings


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
        next = str(int(m.group(1))+1)
        start, end = m.span(1)
        if start or end:
            return u'%s-%s%s' % (s[:max(end - len(next), start)], next, s[end:])
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


def human_number(number, genus=None):
    """Numbers from 1 - 12 are words."""
    if not 0 < number <= 12:
        return str(number)
    if number == 1:
        return {
            'masculine':    u'ein',
            'feminine':     u'eine',
            'neuter':       u'ein'
        }.get(genus, u'eins')
    return (u'zwei', u'drei', u'vier', u'fünf', u'sechs',
            u'sieben', u'acht', u'neun', u'zehn', u'elf', u'zwölf')[number - 2]


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


def shorten_filename(name, length=20, suffix=''):
    """
    Shorten the `name` to the specified `length`.
    If `suffix` is given append it before the extension.

    >>> shorten_filename("FoobarBaz.tar.gz", 15, "-2")
    'Foobar-2.tar.gz'
    >>> shorten_filename("Foobar.tar.gz", 9, "-1")
    Traceback (most recent call last):
      ...
    ValueError: -1.tar.gz is >= 9 chars
    """
    try:
        name, extension = name.split('.', 1)
        dot = '.'
    except ValueError:
        extension = dot = ''
    new_suffix = suffix + dot + extension
    slice_index = length - len(new_suffix)
    if slice_index <= 0:
        raise ValueError("%s is >= %d chars" % (new_suffix, length))
    return name[:length - len(new_suffix)] + new_suffix


def get_new_unique_filename(name, path='', shorten=True, length=20):
    counter = 0
    new_name = shorten_filename(name, length)
    while os.path.exists(os.path.join(path, new_name)):
        counter += 1
        new_name = shorten_filename(name, length, suffix="-" + str(counter))
    return new_name


def get_next_increment(values, string, max_length=None, stripdate=False):
    """Return the next usable incremented string.

    Usage Example::

        >>> get_next_increment(['cat', 'cat10', 'cat2'], u'cat')
        u'cat-11'
        >>> get_next_increment(['cat', 'cat2'], u'cat')
        u'cat-3'
        >>> get_next_increment(['cat', 'cat1'], u'cat')
        u'cat-2'
        >>> get_next_increment([], u'cat')
        u'cat'
        >>> get_next_increment(['cat'], u'cat')
        u'cat-2'
        >>> get_next_increment(['cat', 'cat10', 'cat2'], u'cat', 3)
        u'-11'
        >>> get_next_increment(['cat', 'cat100'], u'cat', 3)
        u'-101'

    """
    def _stripdate(value):
        parts = value.split('/')
        return parts[:-1], parts[-1]

    def _get_value(value):
        if stripdate:
            stripped = _stripdate(value)
            return u'%s/%s' % (u'/'.join(stripped[0]), increment_string(stripped[1]))
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
