# -*- coding: utf-8 -*-
"""
    inyoka.wiki.utils
    ~~~~~~~~~~~~~~~~~

    Contains various helper functions for the wiki.  Most of them are only used
    for the wiki application itself, but there are use cases for some of them
    outside of the wiki too.  Any example for that is the diff renderer which
    might be useful for the pastebin too.


    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.shortcuts import redirect

from inyoka.utils.urls import url_for
from inyoka.wiki.exceptions import CaseSensitiveException, CircularRedirectException
from inyoka.wiki.models import Page


def case_sensitive_redirect(function):
    """
    Redirect to the right case of a wiki page.
    """
    def wrapper(request, *args, **kwargs):
        try:
            return function(request, *args, **kwargs)
        except CaseSensitiveException as e:
            url = url_for(e.page)
            return redirect(url)
    return wrapper


def has_conflicts(text):
    """Returns `True` if there are conflict markers in the text."""
    from inyoka.markup import parse, nodes
    if isinstance(text, basestring):
        text = parse(text)
    return text.query.all.by_type(nodes.ConflictMarker).has_any


def quote_text(text, author=None, item_url=None):
    """
    Returns the wiki syntax quoted version of `text`.
    If the optional argument `author` (username as string or User object) is
    given, a written-by info is prepended.
    """
    try:  # We use try/catch here to not have to import the User model
        author = author.username
    except AttributeError:
        pass

    if item_url:
        by = author and (u'[user:%s:] [%s schrieb]:\n' % (author, item_url)) or u''
    else:
        by = author and (u"[user:%s:] schrieb:\n" % author) or u''
    return text and by + u'\n'.join(
        '>' + (not line.startswith('>') and ' ' or '') + line
        for line in text.split('\n')
    ) or u''


def get_safe_redirect_target(target=None):
    """ Resolve X-Redirect headers without circular redirects. """
    if target is None:
        # shouldn't happen ;)
        return False

    previous = []

    while target is not None:
        if '#' in target:
            target, anchor = target.rsplit('#', 1)
        else:
            anchor = None

        if target in previous:
            raise CircularRedirectException()
        else:
            previous.append(target)

        try:
            target = Page.objects.get_by_name(target).metadata.get('X-Redirect', None)
        except Page.DoesNotExist:
            # This can happen, if the target of the redirect is a view
            break

    return (previous.pop(), anchor)
