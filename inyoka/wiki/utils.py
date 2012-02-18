# -*- coding: utf-8 -*-
"""
    inyoka.wiki.utils
    ~~~~~~~~~~~~~~~~~

    Contains various helper functions for the wiki.  Most of them are only
    usefor for the the wiki application itself, but there are use cases for
    some of them outside of the wiki too.  Any example for that is the diff
    renderer which might be useful for the pastebin too.


    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from itertools import ifilter

from inyoka.wiki.storage import storage
from inyoka.utils.urls import href, smart_urlquote
from inyoka.portal.user import User


def has_conflicts(text):
    """Returns `True` if there are conflict markers in the text."""
    from inyoka.wiki.parser import parse, nodes
    if isinstance(text, basestring):
        text = parse(text)
    return text.query.all.by_type(nodes.ConflictMarker).has_any


def debug_repr(obj):
    """
    A function that does a debug repr for an object.  This is used by all the
    `nodes`, `macros` and `parsers` so that we get a debuggable ast.
    """
    return '%s.%s(%s)' % (
        obj.__class__.__module__.rsplit('.', 1)[-1],
        obj.__class__.__name__,
        ', '.join('%s=%r' % (key, value)
        for key, value in sorted(getattr(obj, '__dict__', {}).items())
        if not key.startswith('_')))


def simple_match(pattern, string, case_sensitive=False):
    """
    Match a string against a pattern.  Works like `simple_filter`.
    """
    return re.compile('^%s$%s' % (
        re.escape(pattern).replace('\\*', '.*?'),
        not case_sensitive and '(?i)' or ''
    )).match(string) is not None


def simple_filter(pattern, iterable, case_sensitive=True):
    """
    Filter an iterable against a pattern.  The pattern is pretty simple, the
    only special thing is that "*" is a wildcard.  The return value is an
    iterator, not a list.
    """
    return ifilter(re.compile('^%s$%s' % (
        re.escape(pattern).replace('\\*', '.*?'),
        not case_sensitive and '(?i)' or ''
    )).match, iterable)


def dump_argstring(argdef, sep=u', '):
    """Create an argument string from an argdef list."""
    result = []
    for is_kwarg, is_default, name, typedef, value in argdef:
        if is_default:
            continue
        if typedef is bool:
            value = value and 'ja' or 'nein'
        result.append((is_kwarg and name + '=' or '') + value)
    return sep.join(result)


def get_smilies(full=False):
    """
    This method returns a list of tuples for all the smilies in the storage.
    Per default for multiple codes only the first one is returend, if you want
    all codes set the full parameter to `True`.
    """
    if full:
        return storage.smilies[:]
    result = []
    images_yielded = set()
    for code, img in storage.smilies:
        if img in images_yielded:
            continue
        result.append((code, img))
        images_yielded.add(img)
    return result


def resolve_interwiki_link(wiki, page):
    """
    Resolve an interwiki link. If no such wiki exists the return value
    will be `None`.
    """
    if wiki == 'user':
        return href('portal', 'user', page)
    if wiki == 'attachment':
        return href('wiki', '_attachment', target=page)
    rule = storage.interwiki.get(wiki)
    if rule is None:
        return
    quoted_page = smart_urlquote(page)
    if '$PAGE' not in rule:
        link = rule + quoted_page
    else:
        link = rule.replace('$PAGE', quoted_page)
    return link


def quote_text(text, author=None, item_url=None):
    """
    Returns the wiki syntax quoted version of `text`.
    If the optional argument `author` (username as string or User object) is
    given, a written-by info is prepended.
    """
    if isinstance(author, User):
        author = author.username

    if item_url:
        by = author and (u'[user:%s:] [%s schrieb]:\n' % (author, item_url)) or u''
    else:
        by = author and (u"[user:%s:] schrieb:\n" % author) or u''
    return text and by + u'\n'.join(
        '>' + (not line.startswith('>') and ' ' or '') + line
        for line in text.split('\n')
    ) or u''


class ArgumentCollector(type):
    """
    Metaclass for classes that accept arguments.
    """

    def __new__(cls, name, bases, d):
        no_parser = d.get('has_argument_parser')
        if not no_parser:
            for base in bases:
                if getattr(base, 'has_argument_parser', False):
                    no_parser = True
        if no_parser:
            return type.__new__(cls, name, bases, d)
        arguments = d.get('arguments', ())
        old_init = d.get('__init__')

        def new_init(self, *args, **orig_kw):
            if orig_kw.pop('_raw', False) and old_init:
                return old_init(self, *args, **orig_kw)
            missing = object()
            result, args, kwargs = args[:-2], args[-2], args[-1]
            result = list(result)
            argdef = []
            for idx, (key, typedef, default) in enumerate(arguments):
                try:
                    value = args[idx]
                    kwarg = False
                except IndexError:
                    value = kwargs.get(key, missing)
                    kwarg = True
                if value is missing:
                    value = default
                    is_default = True
                else:
                    is_default = False
                    if typedef in (int, float, unicode):
                        try:
                            value = typedef(value)
                        except:
                            value = default
                    elif typedef is bool:
                        value = value.lower() in ('ja', 'wahr', 'positiv', '1')
                    elif isinstance(typedef, tuple):
                        if value not in typedef:
                            value = default
                    elif isinstance(typedef, dict):
                        value = typedef.get(value, default)
                    else:
                        assert 0, 'invalid typedef'
                result.append(value)
                argdef.append((kwarg, is_default, key, typedef, value))
            self.argument_def = argdef
            if old_init:
                old_init(self, *result, **orig_kw)

        if old_init:
            new_init.__doc__ = old_init.__doc__
            new_init.__module__ = old_init.__module__
        d['__init__'] = new_init
        return type.__new__(cls, name, bases, d)
