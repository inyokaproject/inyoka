# -*- coding: utf-8 -*-
"""
    inyoka.wiki.utils
    ~~~~~~~~~~~~~~~~~

    Contains various helper functions for the wiki.  Most of them are only used
    for the wiki application itself, but there are use cases for some of them
    outside of the wiki too.  Any example for that is the diff renderer which
    might be useful for the pastebin too.


    :copyright: (c) 2007-2017 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.shortcuts import redirect
from django.utils.html import smart_urlquote

from inyoka.utils.urls import href, url_for
from inyoka.wiki.models import Page
from inyoka.wiki.storage import storage


class CaseSensitiveException(Exception):
    """
    Raised when a specific page is requested which does not exist, but an
    wiki page exist with another case.
    """
    def __init__(self, page, *args, **kwargs):
        self.page = page
        super(CaseSensitiveException, self).__init__(*args, **kwargs)


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


class CircularRedirectException(Exception):
    """
    Raised when a sequence of redirects becomes circular.
    """


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
