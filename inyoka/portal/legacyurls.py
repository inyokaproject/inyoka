# -*- coding: utf-8 -*-
"""
    inyoka.portal.legacyurls
    ~~~~~~~~~~~~~~~~~~~~~~~

    Portal legacy URL support (including old legacy urls from UUv1).

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.utils.urls import href, url_for
from inyoka.utils.flashing import flash
from inyoka.utils.legacyurls import LegacyDispatcher
from inyoka.ikhaya.models import Article


legacy = LegacyDispatcher()
test_legacy_url = legacy.tester


@legacy.url(r'^/ikhaya/(\d+)/?')
def ikhaya_article(args, match, article_id):
    # we cannot do that on the ikhaya subdomain,
    # because there /\d+/ is for the pagination.
    try:
        article = Article.objects.get(id=int(article_id))
    except (Article.DoesNotExist, ValueError):
        return
    return url_for(article)

@legacy.url(r'^/ikhaya/([^\d].*)/?$')
def ikhaya(args, match, url):
    # further redirects are done in ikhaya.legacyurls
    return href('ikhaya', url, **args)

@legacy.url(r'^/paste/(\d+)/?$')
def paste(args, match, id):
    return href('pastebin', id)

@legacy.url(r'^/rss/')
def feeds(args, match):
    # users shall select a new feed themselves
    return href('static', 'feeds_update.xml')


@legacy.url(r'^/users/(.+)/?')
def user_profile(args, match, username):
    return href('portal', 'user', username)

@legacy.url(r'^/downloads/?$')
def downloads(args, match):
    return href('wiki', 'Downloads')
    # until we have a new downloads page

@legacy.url(r'^/bookmarks(?:/[^/]+/(?:\d+)?)?/?$')
def bookmarks(args, match):
    flash(u'Seit der Einführung von Inyoka auf ubuntuusers.de gibt es '
          u'keine Lesezeichen mehr.<br/>Als Ersatz kannst du die '
          u'<a href="http://de.wikipedia.org/wiki/Bookmark">Lesezeichen-Funktion'
          u'</a> moderner Web-Browser nutzen.', False)
    return href('portal')


# Very old legacy URLs from UUv1, copied from UUv2.portal.redirect

@legacy.url(r'^/portal\.php')
def v1_portal(args, match):
    return href()

@legacy.url(r'^/index\.php')
def v1_forum_index(args, match):
    return href('forum')

@legacy.url(r'^/viewtopic\.php')
def v1_forum_topic(args, match):
    if 't' in args:
        return href('forum', 'topic', args['t'])
    elif 'p' in args:
        return href('forum', 'post', args['p'])
    else:
        return href('forum')

@legacy.url(r'^/viewforum\.php')
def v1_forum_forum(args, match):
    if 'f' in args:
        return href('forum', 'forum', args['f'], args.get('start'))
    else:
        return href('forum')

@legacy.url(r'^/login\.php')
def v1_login(args, match):
    return href('portal', 'login')

@legacy.url(r'^/map\.php')
def v1_map(args, match):
    return href('portal', 'map')

@legacy.url(r'^/profile\.php')
def v1_profile(args, match):
    return href('portal', 'usercp')

@legacy.url(r'^/wiki/(.+)$')
def v1_wiki(args, match, page):
    return href('wiki', page)
