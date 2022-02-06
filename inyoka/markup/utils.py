#-*- coding: utf-8 -*-
"""
    inyoka.markup.utils
    ~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re


acceptable_css_properties = frozenset((
    'azimuth', 'background-color', 'border-bottom-color',
    'border-collapse', 'border-color', 'border-left-color',
    'border-right-color', 'border-top-color', 'clear', 'color',
    'cursor', 'direction', 'display', 'elevation', 'float', 'font',
    'font-family', 'font-size', 'font-style', 'font-variant',
    'font-weight', 'height', 'letter-spacing', 'line-height', 'overflow',
    'pause', 'pause-after', 'pause-before', 'pitch', 'pitch-range',
    'richness', 'speak', 'speak-header', 'speak-numeral',
    'speak-punctuation', 'speech-rate', 'stress', 'text-align',
    'text-decoration', 'text-indent', 'unicode-bidi', 'vertical-align',
    'voice-family', 'volume', 'white-space', 'width', 'max-width',
))

acceptable_css_keywords = frozenset((
    'auto', 'aqua', 'black', 'block', 'blue', 'bold', 'both', 'bottom',
    'brown', 'center', 'collapse', 'dashed', 'dotted', 'fuchsia',
    'gray', 'green', '!important', 'italic', 'left', 'lime', 'maroon',
    'medium', 'none', 'navy', 'normal', 'nowrap', 'olive', 'pointer',
    'purple', 'red', 'right', 'solid', 'silver', 'teal', 'top',
    'transparent', 'underline', 'white', 'yellow'
))

_css_url_re = re.compile(r'url\s*\(\s*[^\s)]+?\s*\)\s*')
_css_sanity_check_re = re.compile(r'''(?x)
    ^(
        [:,;#%.\sa-zA-Z0-9!]
      |  \w-\w
      | '[\s\w]+'|"[\s\w]+"
      | \([\d,\s]+\)
    )*$
''')
_css_pair_re = re.compile(r'([-\w]+)\s*:\s*([^:;]*)')
_css_unit_re = re.compile(r'''(?x)
    ^(
        #[0-9a-f]+
      | rgb\(\d+%?,\d*%?,?\d*%?\)?
      | \d{0,2}\.?\d{0,2}(cm|em|ex|in|mm|pc|pt|px|%|,|\))?
    )$
''')


def filter_style(css):
    if css is None:
        return None

    css = _css_url_re.sub(' ', css)
    if _css_sanity_check_re.match(css) is None:
        return ''

    clean = []
    for prop, value in _css_pair_re.findall(css):
        if not value:
            continue
        if prop.lower() in acceptable_css_properties:
            clean.append('%s: %s' % (prop, value))
        elif prop.split('-', 1)[0].lower() in \
             ('background', 'border', 'margin', 'padding'):
            for keyword in value.split():
                if not keyword in acceptable_css_keywords and \
                   not _css_unit_re.match(keyword):
                    break
            else:
                clean.append('%s: %s' % (prop, value))
    return '; '.join(clean)


class ArgumentCollector(type):

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
                    if typedef in (int, float, str):
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
            if old_init:
                old_init(self, *result, **orig_kw)

        if old_init:
            new_init.__doc__ = old_init.__doc__
            new_init.__module__ = old_init.__module__
        d['__init__'] = new_init
        return type.__new__(cls, name, bases, d)


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


def join_array(array, delimiter):
    if not isinstance(array.value, (tuple, list)):
        return ''
    result = []
    for key in array.value:
        result.append(str(key))
    return str(delimiter).join(result)


def has_key(mapping, search):
    if not isinstance(mapping.value, dict):
        return False
    return search in mapping.value


def regex_match(pattern, string):
    """
    Match a string against a regex pattern.  Works like `simple_match`.
    """
    return re.match(pattern, string) is not None


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
    return filter(re.compile('^%s$%s' % (
        re.escape(pattern).replace('\\*', '.*?'),
        not case_sensitive and '(?i)' or ''
    )).match, iterable)
