#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.generate_static_wiki
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a snapshot of all wiki pages in HTML format.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
import shutil
from functools import partial
from os import path
from hashlib import md5, sha1
from itertools import izip
from urlparse import urlparse, parse_qs
from werkzeug import url_unquote

from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.utils.encoding import force_unicode

from inyoka.utils.http import templated
from inyoka.utils.imaging import get_thumbnail, parse_dimensions
from inyoka.utils.urls import href
from inyoka.utils.text import normalize_pagename
from inyoka.utils.terminal import ProgressBar, percentize
from inyoka.utils.templating import Breadcrumb
from inyoka.wiki.models import Page
from inyoka.wiki.views import fetch_real_target
from inyoka.wiki.acl import has_privilege
from inyoka.portal.user import User


#FIXME: Don't rely on STATIC_ROOT but use the finders or collect_static.
settings.STATIC_ROOT = settings.STATICFILES_DIRS[0]

FOLDER = 'static_wiki'
UU_DE = 'http://%subuntuusers.de/'
UU_PORTAL = UU_DE % ''
UU_FORUM = UU_DE % 'forum.'
UU_WIKI = UU_DE % 'wiki.'
UU_NEWS = UU_DE % 'ikhaya.'
UU_PLANET = UU_DE % 'planet.'
UU_COMMUNITY = UU_DE % 'community.'
URL = href('wiki')
DONE_SRCS = {}


SRC_RE = re.compile(r'src="([^"]+)"')
STYLE_RE = re.compile(r'(?:rel="stylesheet"\s+type="text/css"\s+)href="([^"]+)"')
FAVICON_RE = re.compile(r'rel="shortcut icon" href="([^"]+)"')
TAB_RE = re.compile(r'(<div class="navi_tabbar navigation">).+?(</div>)', re.DOTALL)
META_RE = re.compile(r'(<p class="meta">).+?(</p>)\s*', re.DOTALL)
NAVI_RE = re.compile(r'(<ul class="navi_global">).+?(</ul>)\s*', re.DOTALL)
IMG_RE = re.compile(r'href="%s\?target=([^"]+)"' % href('wiki', '_image'))
REAL_MEDIA_RE = re.compile(r'href="%s\?target=([^"]+)"' % settings.MEDIA_URL)
REAL_IMG_RE = re.compile(r'href="%s.*?"' % settings.STATIC_URL)
LINK_RE = re.compile(r'href="%s([^"]+)"' % URL)
STARTPAGE_RE = re.compile(r'href="(%s)"' % URL)
ERROR_REPORT_RE = re.compile(r'<a href=".[^"]+" id="user_error_report_link">Fehler melden</a><br/>\s*')
POWERED_BY_RE = re.compile(r'<li class="poweredby">.*?</li>\s*', re.DOTALL)
SEARCH_PATHBAR_RE = re.compile(r'<form .*? class="search">.+?</form>\s*', re.DOTALL)
DROPDOWN_RE = re.compile(r'<div class="dropdown">.+?</div>\s*', re.DOTALL)
PATHBAR_RE = re.compile(r'(<div class="pathbar">).*?(</div>)\s*', re.DOTALL)
JS_LOGIN = re.compile(r'<form.*?id="js_login_form">.+?</form>\s*', re.DOTALL)
LOGO_RE = re.compile(r'<h1><a href=".*?"><span>ubuntuusers.de</span></a></h1>', re.DOTALL)
TABBAR_RE = re.compile(r'<li class="(portal|forum|wiki|ikhaya|planet|community).*?"><a href=".*?">(.*?)</a></li>', re.DOTALL)
OPENSEARCH_RE = re.compile(r'<link rel="search".*? />\s*', re.DOTALL)
FOOTER_RE = re.compile(r'<a href="%s(lizenz|kontakt|datenschutz|impressum)/.*?">(.+?)</a>' % href('portal'), re.DOTALL)
GLOBAL_MESSAGE_RE = re.compile(r'(<div class="message global">).+?(</div>)\s*', re.DOTALL)

SNAPSHOT_MESSAGE = u'''<div class="message staticwikinote">
<strong>Hinweis:</strong> Dies ist nur ein statischer Snapshot unseres Wikis. Dieser kann nicht bearbeitet werden und veraltet sein. Der aktuelle Artikel ist unter <a href="%s">wiki.ubuntuusers.de</a> zu finden.
</div>'''

EXCLUDE_PAGES = [u'Benutzer/', u'Anwendertreffen/', u'Baustelle/', u'LocoTeam/',
                 u'Wiki/Vorlagen', u'Vorlage/', u'Verwaltung/', u'Galerie', 'Trash/',
                 u'Messen/', u'UWN-Team/', u'Mitmachen/', u'ubuntuusers/']
# we're case insensitive
EXCLUDE_PAGES = [x.lower() for x in EXCLUDE_PAGES]


INCLUDE_IMAGES = False

_iterables = (tuple, list, set, frozenset)

@templated('wiki/action_show.html')
def fetch_page(page, **kwargs):
    settings.DEBUG = False
    return {
        'page': page,
        'BREADCRUMB': Breadcrumb(),
        'USER': kwargs.get('user', None),
        'SETTINGS': settings
    }


def save_file(url, is_main_page=False, is_static=False):
    if not INCLUDE_IMAGES and not is_static and not is_main_page:
        return ""
    if url.startswith(settings.STATIC_URL):
        base = settings.STATIC_ROOT
        rel_path = url[len(settings.STATIC_URL)+1:]
    elif url.startswith(URL):
        base = settings.MEDIA_ROOT

        query = parse_qs(urlparse(url).query)
        width = query.get('width', [None])[0]
        height = query.get('height', [None])[0]
        target = query.get('target', [None])[0]
        width, height = parse_dimensions('%sx%s' % (width, height))
        if not target:
            return ""

        target = force_unicode(target)
        target = normalize_pagename(target)

        if height or width:
            page_filename = Page.objects.attachment_for_page(target)
            if page_filename is None:
                return ""

            partial_hash = sha1(force_unicode(page_filename).encode('utf-8')).hexdigest()

            force = query.get('force', [None])[0]
            dimension = '%sx%s%s' % (width or '',
                                     height or '',
                                     force and '!' or '')
            hash = '%s%s%s' % (partial_hash, 'i',
                               dimension.replace('!', 'f'))
            base_filename = os.path.join('wiki', 'thumbnails', hash[:1],
                                         hash[:2], hash)
            rel_path = get_thumbnail(page_filename, base_filename, width, height)
        else:
            rel_path = Page.objects.attachment_for_page(target)
            if not rel_path:
                return ""
        if not rel_path:
            return ""
    else:
        return ""
    try:
        if rel_path:
            abs_path = os.path.join(base, rel_path)
            hash = md5(force_unicode(rel_path).encode('utf-8')).hexdigest()
            if hash not in DONE_SRCS:
                ext = os.path.splitext(rel_path)[1]
                fname = '%s%s' % (hash, ext)
                shutil.copy(abs_path, path.join(FOLDER, 'files', '_', fname))
                DONE_SRCS[hash] = fname
            return os.path.join('_', DONE_SRCS[hash])
    except IOError:
        pass

    return ""


def fix_path(pth):
    if isinstance(pth, unicode):
        pth.encode('utf-8')
    return normalize_pagename(pth, False).lower()


def replacer(func, parts, is_main_page, page_name):
    pre = (parts and u''.join('../' for i in xrange(parts)) or './')
    def replacer(match):
        return func(match, pre, is_main_page, page_name)
    return replacer


def handle_src(match, pre, is_main_page, page_name):
    is_static = 'static' in match.groups()[0]
    return u'src="%s%s"' % (pre, save_file(match.groups()[0], is_main_page, is_static))


def handle_img(match, pre, is_main_page, page_name):
    if not INCLUDE_IMAGES:
        return u'href="%s%s"' % (pre, os.path.join('_', '1px.png'))
    return u'href="%s%s"' % (pre, save_file(fetch_real_target(target=url_unquote(match.groups()[0].encode('utf8'))), is_main_page))


def handle_style(match, pre, is_main_page, page_name):
    ret = u'rel="stylesheet" type="text/css" href="%s%s"' % (pre, save_file(match.groups()[0], is_main_page, True))
    return ret


def handle_favicon(match, pre, is_main_page, page_name):
    ret = u'rel="shortcut icon" href="%s%s"' % (pre, save_file(match.groups()[0], is_main_page, True))
    return ret


def handle_link(match, pre, is_main_page, page_name):
    if not '?' in match.group():
        return u'href="%s%s.html"' % (pre, fix_path(match.groups()[0]))
    return u'href="%s%s.html"' % (pre, fix_path(page_name))


def handle_powered_by(match, pre, is_main_page, page_name):
    return u'<li class="poweredby">Erstellt mit <a href="http://ubuntuusers.de/inyoka">Inyoka</a></li>'

def handle_logo(match, pre, is_main_page, page_name):
    return u'<h1><a href="%s"><span>ubuntuusers.de</span></a></h1>' % UU_PORTAL

def handle_tabbar(match, pre, is_main_page, page_name):
    sub = {
        'portal': ('', UU_PORTAL),
        'forum': ('', UU_FORUM),
        'wiki': (' active', UU_WIKI),
        'ikhaya': ('', UU_NEWS),
        'planet': ('', UU_PLANET),
        'community': ('', UU_COMMUNITY),
    }
    key = match.groups()[0]
    return u'<li class="%s%s"><a href="%s">%s</a></li>' % (key, sub[key][0], sub[key][1], match.groups()[1])

def handle_footer(match, pre, is_main_page, page_name):
    return u'<a href="%s%s">%s</a>' % (UU_PORTAL, match.groups()[0], match.groups()[1])

def handle_startpage(match, pre, is_main_page, page_name):
    return u'href="%s%s.html"' % (pre, settings.WIKI_MAIN_PAGE.lower())

def handle_snapshot_message(match, pre, is_main_page, page_name):
    return SNAPSHOT_MESSAGE % os.path.join(UU_WIKI, page_name)


REPLACERS = (
    (IMG_RE,            handle_img),
    (SRC_RE,            handle_src),
    (STYLE_RE,          handle_style),
    (FAVICON_RE,        handle_favicon),
    (LINK_RE,           handle_link),
    (STARTPAGE_RE,      handle_startpage),
    (POWERED_BY_RE,     handle_powered_by),
    (META_RE,           ''),
    (NAVI_RE,           ''),
    (ERROR_REPORT_RE,   ''),
    (GLOBAL_MESSAGE_RE, ''),
    (SEARCH_PATHBAR_RE, ''),
    (DROPDOWN_RE,       ''),
    (PATHBAR_RE,        ''),
    (JS_LOGIN,          ''),
    (OPENSEARCH_RE,     ''),
    (REAL_IMG_RE,       ''),
    (REAL_MEDIA_RE,     ''),
    (LOGO_RE,           handle_logo),
    (TABBAR_RE,         handle_tabbar),
    (FOOTER_RE,         handle_footer),
    (TAB_RE,            handle_snapshot_message)
)

def create_snapshot():
    # remove the snapshot folder and recreate it
    try:
        shutil.rmtree(FOLDER)
    except OSError:
        pass

    user = User.objects.get_anonymous_user()

    # create the folder structure
    os.mkdir(FOLDER)
    os.mkdir(path.join(FOLDER, 'files'))
    stroot = settings.STATIC_ROOT
    ff = partial(path.join, stroot, 'img')
    static_paths = ((path.join(stroot, 'img', 'icons'), 'icons'),
        ff('logo.png'), ff('favicon.ico'), ff('float-left.jpg'),
        ff('float-right.jpg'), ff('float-top.jpg'), ff('head.jpg'),
        ff('head-right.png'), ff('anchor.png'), ff('header-sprite.png'),
        ff('1px.png'))
    for pth in static_paths:
        _pth = pth[0] if isinstance(pth, _iterables) else pth
        if path.isdir(_pth):
            shutil.copytree(_pth, path.join(FOLDER, 'files', 'img', pth[1]))
        else:
            shutil.copy(_pth, path.join(FOLDER, 'files', 'img'))
    attachment_folder = path.join(FOLDER, 'files', '_')
    os.mkdir(attachment_folder)

    pb = ProgressBar(40)

    unsorted = Page.objects.get_page_list(existing_only=True)
    pages = set()
    excluded_pages = set()
    # sort out excluded pages
    for page in unsorted:
        for exclude in EXCLUDE_PAGES:
            if exclude.lower() in page.lower():
                excluded_pages.add(page)
            else:
                pages.add(page)
    todo = pages - excluded_pages

    def _fetch_and_write(name):
        parts = 0
        is_main_page = False

        if not has_privilege(user, name, 'read'):
            return

        try:
            page = Page.objects.get_by_name(name, False, True)
        except Page.DoesNotExist:
            return

        if page.name in excluded_pages:
            # however these are not filtered before…
            return

        if page.name == settings.WIKI_MAIN_PAGE:
            is_main_page = True

        if page.rev.attachment:
            # page is an attachment
            return
        if len(page.trace) > 1:
            # page is a subpage
            # create subdirectories
            for part in page.trace[:-1]:
                pth = path.join(FOLDER, 'files', *fix_path(part).split('/'))
                if not path.exists(pth):
                    os.mkdir(pth)
                parts += 1

        content = fetch_page(page, user=user, settings=settings).content
        if content is None:
            return
        content = content.decode('utf8')

        for regex, repl in REPLACERS:
            if callable(repl):
                repl = replacer(repl, parts, is_main_page, page.name)
            content = regex.sub(repl, content)

        # Filter out all JavaScript directives
        # TODO: This way all tag-filters/replaces above could work
        #       but for now i'm too lazy...
        soap = BeautifulSoup(content)
        [x.extract() for x in soap.findAll('script')]
        content = unicode(soap)

        def _write_file(pth):
            with open(pth, 'w+') as fobj:
                fobj.write(content.encode('utf-8'))

        _write_file(path.join(FOLDER, 'files', '%s.html' % fix_path(page.name)))

        if is_main_page:
            content = re.compile(r'(src|href)="\./([^"]+)"') \
                    .sub(lambda m: '%s="./files/%s"' % (m.groups()[0], m.groups()[1]), content)
            _write_file(path.join(FOLDER, 'index.html'))

    percents = list(percentize(len(todo)))
    for percent, name in izip(percents, todo):
        _fetch_and_write(name)
        pb.update(percent)
    print
    print ("Created Wikisnapshot with %s pages; excluded %s pages"
           % (len(todo), len(excluded_pages)))


if __name__ == '__main__':
    create_snapshot()
