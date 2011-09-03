# -*- coding: utf-8 -*-
"""
    inyoka.wiki.views
    ~~~~~~~~~~~~~~~~~

    The views for the wiki.  Unlike the other applications the wiki doesn't
    really use the views but `actions`.  This is the case because we only
    have one kind of page which is a wiki page.  Non existing pages render
    a replacement message to create one, so not much to dispatch.

    Some internal functions such as the image serving are implemented as
    views too because they do not necessarily work on page objects.


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
from hashlib import sha1
from urlparse import urljoin
from django.conf import settings
from django.utils.encoding import force_unicode
from inyoka.utils.html import escape
from inyoka.utils.urls import href, is_safe_domain, url_for
from inyoka.utils.text import join_pagename, normalize_pagename
from inyoka.utils.http import templated, PageNotFound, HttpResponseRedirect, \
    AccessDeniedResponse
from inyoka.utils.dates import format_datetime
from inyoka.utils.feeds import atom_feed, AtomFeed
from inyoka.utils.flashing import flash
from inyoka.utils.imaging import get_thumbnail
from inyoka.wiki.models import Page, Revision
from inyoka.wiki.actions import PAGE_ACTIONS
from inyoka.wiki.acl import has_privilege


def index(request):
    """Wiki index is a redirect to the `settings.WIKI_MAIN_PAGE`."""
    return HttpResponseRedirect(
        href('wiki', settings.WIKI_MAIN_PAGE) +
        (request.GET and '?' + request.GET.urlencode() or '')
    )


def show_page(request, name):
    """Dispatch action calls."""
    normalized_name = normalize_pagename(name)
    if not normalized_name:
        return missing_resource(request)
    action = request.GET.get('action')
    if normalized_name != name or action == 'show':
        args = request.GET.copy()
        if action == 'show':
            del args['action']
        url = href('wiki', normalized_name)
        if args:
            url += '?' + args.urlencode()
        return HttpResponseRedirect(url)
    if action and action not in PAGE_ACTIONS:
        return missing_resource(request)
    return PAGE_ACTIONS[action or 'show'](request, normalized_name)


def redirect_new_page(request):
    """Helper for the `NewPage` macro."""
    template = request.GET.get('template')
    base = request.GET.get('base', '')
    page = request.GET.get('page', '')
    options = {'action': 'edit'}
    backref = request.META.get('HTTP_REFERER')
    if not backref or not is_safe_domain(backref):
        backref = href('wiki', settings.WIKI_MAIN_PAGE)

    if not page:
        flash(u'Die Seite konnte nicht erstellt werden, da kein Seitenname '
              'angegeben wurde.', success=False)
        return HttpResponseRedirect(backref)
    if base:
        page = join_pagename(base, "./" + page)
    try:
        page = Page.objects.get(name__exact=page)
    except Page.DoesNotExist:
        if template:
            options['template'] = join_pagename(settings.WIKI_TEMPLATE_BASE,
                                                template)
        return HttpResponseRedirect(href('wiki', page, **options))
    flash(u'Eine Seite mit dem Namen <a href="%s">%s</a> existiert '
          u'bereits.' % (url_for(page), escape(page.title)), success=False)
    return HttpResponseRedirect(backref)


@templated('wiki/missing_resource.html', status=404)
def missing_resource(request):
    """
    Called if the templated decorator catches a `ObjectDoesNotExist`
    exception on the wiki.  This does not affect missing pages
    because the show view checks for that.

    **Template**
        ``'wiki/missing_resource.html'``

    **Context**
        none

    Not having a context doesn't mean that a template cannot render
    something.  The default context objects also exists for this one.
    """


def get_attachment(request):
    """
    Get an attachment directly and do privilege check.
    """
    target = request.GET.get('target')
    if not target:
        raise PageNotFound()

    target = normalize_pagename(target)
    if not has_privilege(request.user, target, 'read'):
        return AccessDeniedResponse()

    target = Page.objects.attachment_for_page(target)
    target = href('media', target)
    if not target:
        raise PageNotFound()
    return HttpResponseRedirect(target)


def get_image_resource(request):
    """
    Deliver the attachment  as image.  This is used by the `Picture` macro
    mainly.  The idea is that we can still check privileges
    and that the image URL does not change if a new revision is uploaded.
    """
    try:
        width = int(request.GET['width'])
    except (KeyError, ValueError):
        width = None
    try:
        height = int(request.GET['height'])
    except (KeyError, ValueError):
        height = None
    target = request.GET.get('target')
    if not target:
        raise PageNotFound()

    target = normalize_pagename(target)
    if not has_privilege(request.user, target, 'read'):
        return AccessDeniedResponse()

    if height or width:
        page_filename = Page.objects.attachment_for_page(target)
        if page_filename is None:
            raise PageNotFound()

        page_filename = force_unicode(page_filename).encode('utf-8')
        partial_hash = sha1(page_filename).hexdigest()

        force = request.GET.get('force') == 'yes'
        dimension = '%sx%s%s' % (width or '',
                                 height or '',
                                 force and '!' or '')
        hash = '%s%s%s' % (partial_hash, 'i',
                           dimension.replace('!', 'f'))
        base_filename = os.path.join('wiki', 'thumbnails', hash[:1],
                                     hash[:2], hash)
        thumbnail = get_thumbnail(page_filename, base_filename, width, height, force)

        target = urljoin(settings.MEDIA_URL, thumbnail)
    else:
        target = Page.objects.attachment_for_page(target)
        if not target:
            raise PageNotFound()
        target = href('media', target)
    if not target:
        raise PageNotFound()
    return HttpResponseRedirect(target)


@atom_feed(name='wiki_feed', supports_modes=False)
def feed(request, page_name=None, count=10):
    """
    Shows the wiki pages or all revisions of one page that match
    the given criteria in an atom feed.
    """
    if page_name:
        feed = AtomFeed(title=u'ubuntuusers Wiki – %s' % page_name,
                        url=href('wiki', page_name),
                        feed_url=request.build_absolute_uri(),
                        id=href('wiki', page_name),
                        rights=href('portal', 'lizenz'),
                        icon=href('static', 'img', 'favicon.ico'))
    else:
        feed = AtomFeed(u'ubuntuusers Wiki – Letzte Änderungen',
                        url=href('wiki', u'Letzte_Änderungen'),
                        feed_url=request.build_absolute_uri(),
                        id=href('wiki', u'Letzte_Änderungen'),
                        rights=href('portal', 'lizenz'),
                        icon=href('static', 'img', 'favicon.ico'))

    revisions = Revision.objects.get_latest_revisions(page_name, count)

    for rev in revisions:
        kwargs = {}
        text = (u'%s hat am %s den Wikiartikel „%s“ %s.%s' % (
                rev.user or u'Ein anonymer Benutzer', rev.change_date,
                rev.page.title, rev.deleted and u'gelöscht' or u'geändert',
                rev.note and (u' Zusammenfassung: \n%s' % rev.note) or ''))

        kwargs['summary'] = text
        kwargs['summary_type'] = None
        author = rev.user \
            and {'name': rev.user.username, 'uri': url_for(rev.user)} \
            or u'Anonymous'
        feed.add(
            title=u'%s (%s)' % (
                rev.user or 'Anonymous',
                format_datetime(rev.change_date),
            ),
            url=url_for(rev),
            author=author,
            published=rev.change_date,
            updated=rev.change_date,
            **kwargs
        )

    return feed
