#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.wiki.management.commands.generate_static_wiki
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a snapshot of all wiki pages in HTML format. Requires
    BeautifulSoup4 to be installed.

    :copyright: (c) 2007-2019 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import print_function

import datetime
from functools import partial
from hashlib import sha1
from itertools import izip
from os import chmod, mkdir, path, unlink, walk
from re import compile, escape, sub
from shutil import copy, copytree, rmtree

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.defaultfilters import date
from django.utils.encoding import force_unicode
from django.utils.translation import activate
from werkzeug import url_unquote

from inyoka.portal.user import User
from inyoka.portal.models import StaticPage
from inyoka.utils.http import templated
from inyoka.utils.storage import storage
from inyoka.utils.terminal import ProgressBar, percentize
from inyoka.utils.text import normalize_pagename
from inyoka.utils.urls import href
from inyoka.wiki.acl import has_privilege
from inyoka.wiki.models import Page
from inyoka.wiki.exceptions import CaseSensitiveException

FOLDER = 'static_wiki'
INCLUDE_IMAGES = False

UU_DE_DOMAIN = 'ubuntuusers.de'
UU_DE = 'http://%s' + UU_DE_DOMAIN + '/'
UU_PORTAL = UU_DE % ''
UU_FORUM = UU_DE % 'forum.'
UU_WIKI = UU_DE % 'wiki.'
UU_IKHAYA = UU_DE % 'ikhaya.'
UU_PLANET = UU_DE % 'planet.'
UU_COMMUNITY = UU_WIKI + 'Mitmachen'
URL = href('wiki')
NON_WIKI_RE = compile('|'.join(escape(href(u)) for u in
                      ['forum', 'ikhaya', 'pastebin', 'planet', 'portal']))
WIKI_BEGIN_RE = compile("^%s" % escape(href('wiki')))
WIKI_CENTER_RE = compile("^%s$" % escape(href('wiki')))
PORTAL_RE = compile(escape(href('portal')))
DONE_SRCS = {}
UPDATED_SRCS = set()

SNAPSHOT_MESSAGE = u'<div class="message staticwikinote"><strong>Hinweis:'\
                   u'</strong> Dies ist ein statischer Snapshot unseres '\
                   u'Wikis vom %s und kann daher nicht bearbeitet werden. '\
                   u'Der aktuelle Artikel ist unter <a '\
                   u'href="%s">wiki.ubuntuusers.de</a> zu finden.</div>'
SNAPSHOT_DATE = None

REDIRECT_MESSAGE = u'<p>Diese Seite ist eine Weiterleitung. Daher wirst '\
                   u'du in 5 Sekunden automatisch nach <a '\
                   u'href="%s.html">%s</a> weitergeleitet.</p>'

CREATED_MESSAGE = u'<li class="poweredby">Erstellt mit <a '\
                  u'href="http://inyokaproject.org/">Inyoka</a></li>'

EXCLUDE_PAGES = [u'Benutzer/', u'Anwendertreffen/', u'Baustelle/',
                 u'LocoTeam/', u'Wiki/Vorlagen', u'Vorlage/', u'Verwaltung/',
                 u'Galerie', 'Trash/', u'Messen/', u'UWN-Team/', u'Mitmachen/',
                 u'ubuntuusers/']
# we're case insensitive
EXCLUDE_PAGES = [x.lower() for x in EXCLUDE_PAGES]

_iterables = (tuple, list, set, frozenset)
verbosity = 0

BeautifulSoup = partial(BeautifulSoup, features='lxml')


class Command(BaseCommand):
    help = "Creates a snapshot of all wiki pages in HTML format. Requires BeautifulSoup4 to be installed."

    def __init__(self):
        BaseCommand.__init__(self)
        self.license_file = '_lizenz.html'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path',
            action='store',
            dest='path',
            help='Define where to store the static wiki')

        parser.add_argument('--images', action='store_true',
            help='If given, images will be included in the static wiki.')

    def handle(self, *args, **options):
        global verbosity
        verbosity = int(options['verbosity'])
        path = options['path']
        if path is not None:
            global FOLDER
            FOLDER = path

        global INCLUDE_IMAGES
        if options['images']:
            INCLUDE_IMAGES = True

        if verbosity >= 1:
            print("Starting Export")

        global SNAPSHOT_DATE, SNAPSHOT_MESSAGE
        activate(settings.LANGUAGE_CODE)
        SNAPSHOT_DATE = date(datetime.date.today(), settings.DATE_FORMAT)
        SNAPSHOT_MESSAGE = SNAPSHOT_MESSAGE % (SNAPSHOT_DATE, '%s')
        self.create_snapshot()

        if verbosity >= 1:
            print("Export complete")

    @templated('wiki/action_show.html')
    def fetch_page(self, page, **kwargs):
        settings.DEBUG = False
        return {
            'page': page,
            'USER': kwargs.get('user', None),
            'SETTINGS': settings
        }

    @templated('portal/static_page.html')
    def _static_page(self, page, **kwargs):
        """Renders static pages"""
        settings.DEBUG = False

        q = StaticPage.objects.get(key=page)
        return {
            'title': q.title,
            'content': q.content_rendered,
            'key': q.key,
            'page': q,
            'USER': kwargs.get('user', None),
            'SETTINGS': settings
        }

    def _write_file(self, pth, content):
        with open(pth, 'w+') as fobj:
            fobj.write(content.encode('utf-8'))

    def save_file(self, url, is_main_page=False, is_static=False):
        if not INCLUDE_IMAGES and not is_static and not is_main_page:
            return ""

        if url.startswith(settings.STATIC_URL):
            base = settings.STATIC_ROOT
            rel_path = url[len(settings.STATIC_URL):]
        elif url.startswith(settings.MEDIA_URL):
            base = settings.MEDIA_ROOT
            rel_path = url[len(settings.MEDIA_URL):]
        else:
            return ""

        rel_path = url_unquote(rel_path)
        rel_path = sub('\?v=v[\d\.]*', '', rel_path)
        if rel_path:
            abs_path = path.join(base, rel_path)
            hash_code = sha1(force_unicode(rel_path).encode('utf-8')).hexdigest()
            if hash_code not in DONE_SRCS:
                ext = path.splitext(rel_path)[1]
                fname = '%s%s' % (hash_code, ext)
                dst = path.join(FOLDER, 'files', '_', fname)
                copy(abs_path, dst)
                DONE_SRCS[hash_code] = fname
                chmod(dst, 0o644)
            return path.join('_', DONE_SRCS[hash_code])

        return ""

    def fix_path(self, pth, pre=''):
        if isinstance(pth, unicode):
            pth.encode('utf-8')
        return pre + normalize_pagename(url_unquote(pth), False).lower()

    def _pre(self, parts):
        return parts and u''.join('../' for _ in xrange(parts)) or './'

    def handle_removals(self, soup, pre, is_main_page, page_name):
        remove = (('script',),
                  ('ul', 'navi_global'),
                  ('div', 'navi_tabbar navigation'))
        for args in remove:
            for x in soup.find_all(*args):
                x.extract()

    def handle_pathbar(self, soup, pre, is_main_page, page_name):
        pathbar = soup.find('div', 'pathbar')
        pathbar.find('form').decompose()
        children = list(pathbar.children)
        if len(children) > 4:
            # 4 because, the form and div leave a \n behind
            # remove the ubuntuusers.de link
            children = children[5:]
            pathbar.clear()
            for child in children:
                pathbar.append(child)
        else:
            pathbar.decompose()

    def handle_meta_link(self, soup, pre, is_main_page, page_name):

        def _handle_style(tag):
            if tag['href'].startswith(href('portal', 'markup.css')):
                hash_code = sha1(force_unicode('dyn.css').encode('utf-8')).hexdigest()
                rel_path = path.join('_', '%s.css' % hash_code)
                abs_path = path.join(FOLDER, 'files', rel_path)
                if not path.isfile(abs_path):
                    with open(abs_path, 'w+') as fobj:
                        fobj.write(storage['markup_styles'].encode('utf-8'))
                tag['href'] = u'%s%s' % (pre, rel_path)
                return

            rel_path = self.save_file(tag['href'], is_main_page, True)
            if not rel_path:
                tag.extract()
            else:
                tag['href'] = u'%s%s' % (pre, rel_path)
                if rel_path not in UPDATED_SRCS:
                    abs_path = path.join(FOLDER, 'files', rel_path)
                    if path.isfile(abs_path):
                        content = ''
                        with open(abs_path, 'r') as f:
                            content = f.read()

                        _re = compile(r'\?[0-9a-f]{32}')
                        content = _re.sub('', content)
                        with open(abs_path, 'w') as f:
                            f.write(content)
                            UPDATED_SRCS.add(rel_path)

        def _handle_favicon(self, tag):
            rel_path = self.save_file(tag['href'], is_main_page, True)
            if not rel_path:
                tag.extract()
            else:
                tag['href'] = u'%s%s' % (pre, rel_path)

        sub = {'stylesheet': _handle_style,
               'shortcut icon': _handle_favicon}

        for link in soup.find('head').find_all('link'):
            op = sub.get(link['rel'][0], lambda tag: tag.extract())
            op(link)

    def handle_title(self, soup, pre, is_main_page, page_name):
        soup.find('title').string = page_name + u' › ubuntuusers statisches Wiki'

    def handle_logo(self, soup, pre, is_main_page, page_name):
        tag = soup.find('div', 'header').find('h1').find('a')
        tag['href'] = UU_PORTAL
        tag.find('span').string = u'ubuntuusers.de'

    def handle_tabbar(self, soup, pre, is_main_page, page_name):
        sub = {
            'portal': UU_PORTAL,
            'forum': UU_FORUM,
            'wiki': UU_WIKI,
            'ikhaya': UU_IKHAYA,
            'planet': UU_PLANET,
            'community': UU_COMMUNITY,
        }
        for li in soup.find('ul', 'tabbar').find_all('li'):
            key = li['class'][0]
            li.find('a')['href'] = sub[key]

    def handle_link(self, soup, pre, is_main_page, page_name):
        length = len(href('wiki'))
        for a in soup.find_all('a', href=WIKI_BEGIN_RE):
            link = a['href'][length:]
            if link.startswith('_attachment?'):
                a['href'] = UU_WIKI + link
            else:
                if '?' in link:
                    rel_path = self.fix_path(page_name, pre)
                    a['href'] = u'%s.html' % rel_path
                elif '#' in link:
                    target, anchor = link.split(u'#', 1)
                    rel_path = self.fix_path(target, pre)
                    a['href'] = u'%s.html#%s' % (rel_path, anchor)
                else:
                    rel_path = self.fix_path(link, pre)
                    a['href'] = u'%s.html' % rel_path

    def handle_img(self, soup, pre, is_main_page, page_name):
        def _remove_link(tag):
            if tag.parent.name == 'a':
                tag.parent.unwrap()

        if not INCLUDE_IMAGES:
            for img in soup.find_all('img'):
                img['src'] = u'%s%s' % (pre, path.join('img', '1px.png'))
                _remove_link(img)
        else:
            for img in soup.find_all('img'):
                try:
                    rel_path = self.save_file(img['src'], is_main_page,
                                         img['src'].startswith(href('static')))
                    if not rel_path:
                        img['src'] = u'%s%s' % (pre, path.join('img', '1px.png'))
                    else:
                        img['src'] = u'%s%s' % (pre, rel_path)
                    _remove_link(img)
                except KeyError:
                    img.extract()

    def handle_startpage(self, soup, pre, is_main_page, page_name):
        for a in soup.find_all('a', href=WIKI_CENTER_RE):
            a['href'] = u'%s%s.html' % (pre, settings.WIKI_MAIN_PAGE.lower())

    def handle_footer(self, soup, pre, is_main_page, page_name):
        for li in soup.find('div', 'footer').find_all('li'):
            key = li['class'][0]
            if key == 'license':
                li.find('a', 'flavour_switch').extract()
                li.find('br').extract()
                for a in li.find_all('a', href=PORTAL_RE):
                    if a['href'].endswith('lizenz/'):
                        a['href'] = path.join(pre, self.license_file)
                    else:
                        a['href'] = '%s%s' % (UU_PORTAL,
                                          a['href'][len(href('portal')):])
            elif key == 'poweredby':
                tag = BeautifulSoup(CREATED_MESSAGE)
                li.clear()
                li.append(tag.find('li'))

    def handle_non_wiki_link(self, soup, pre, is_main_page, page_name):
        for a in soup.find_all('a', href=NON_WIKI_RE):
            a['href'] = str.replace(a['href'], settings.BASE_DOMAIN_NAME, UU_DE_DOMAIN, 1)

    def handle_snapshot_message(self, soup, pre, is_main_page, page_name):
        tag = BeautifulSoup(SNAPSHOT_MESSAGE % path.join(UU_WIKI, page_name))
        soup.find('div', 'appheader').insert_after(tag.find('div'))

    def handle_redirect_page(self, soup, pre, target):
        page = soup.find('div', id='page')
        page.clear()
        t1 = BeautifulSoup(REDIRECT_MESSAGE % (self.fix_path(target, pre), target))
        page.append(t1.find('p'))
        page.find('head')
        t2 = BeautifulSoup('<meta http-equiv="refresh" content="5;url=%s.html">' %
                           self.fix_path(target, pre))
        page.append(t2.find('meta'))

    HANDLERS = [handle_removals,
                handle_pathbar,
                handle_meta_link,
                handle_title,
                handle_logo,
                handle_tabbar,
                handle_startpage,
                handle_link,
                handle_img,
                handle_footer,
                handle_non_wiki_link,
                handle_snapshot_message]

    def create_snapshot(self):
        user = User.objects.get_anonymous_user()

        # create the folder structure
        if not path.exists(FOLDER):
            mkdir(FOLDER)
        else:
            for root, dirs, files in walk(FOLDER):
                for f in files:
                    unlink(path.join(root, f))
                for d in dirs:
                    rmtree(path.join(root, d))
        mkdir(path.join(FOLDER, 'files'))

        img = partial(path.join, settings.STATIC_ROOT, 'img')
        static_paths = ((img('icons'), 'icons'),
                        (img('wiki'), 'wiki'),
                        (img('interwiki'), 'interwiki'),
                        img('logo.png'),
                        img('favicon.ico'),
                        img('float-left.jpg'),
                        img('float-right.jpg'),
                        img('float-top.jpg'),
                        img('head.jpg'),
                        img('head-right.png'),
                        img('anchor.png'),
                        img('1px.png'),
                        img('main-sprite.png'),
                        img('bullet.gif'))

        for pth in static_paths:
            _pth = pth[0] if isinstance(pth, _iterables) else pth
            if path.isdir(_pth):
                copytree(_pth, path.join(FOLDER, 'files', 'img', pth[1]))
            else:
                copy(_pth, path.join(FOLDER, 'files', 'img'))
        attachment_folder = path.join(FOLDER, 'files', '_')
        mkdir(attachment_folder)

        license_content = self._static_page('lizenz', user=user, settings=settings).content.decode('utf8')
        license_soup = BeautifulSoup(license_content)
        # Apply the handlers from above to modify the page content
        for handler in self.HANDLERS:
            handler(self, license_soup, self._pre(0), is_main_page=False, page_name='Lizenz')
        license_content = unicode(license_soup)
        self._write_file(path.join(FOLDER, 'files', self.license_file), license_content)

        if verbosity >= 1:
            pb = ProgressBar(40)

        unsorted = Page.objects.get_page_list(existing_only=True)
        todo = set()
        num_excluded = 0
        # sort out excluded pages
        for page in unsorted:
            page = page.lower()
            do_add = True
            for exclude in EXCLUDE_PAGES:
                if page.startswith(exclude):
                    do_add = False
                    num_excluded += 1
                    break
            if do_add:
                todo.add(page)

        def _fetch_and_write(name):
            parts = 0
            is_main_page = False

            if not has_privilege(user, name, 'read'):
                return

            try:
                page = Page.objects.get_by_name(name, False, True)
            except CaseSensitiveException as e:
                page = e.page
            except Page.DoesNotExist:
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
                    pth = path.join(FOLDER, 'files', *self.fix_path(part).split('/'))
                    if not path.exists(pth):
                        mkdir(pth)
                    parts += 1

            content = self.fetch_page(page, user=user, settings=settings).content
            if content is None:
                return
            content = content.decode('utf8')
            soup = BeautifulSoup(content)

            # Apply the handlers from above to modify the page content
            for handler in self.HANDLERS:
                handler(self, soup, self._pre(parts), is_main_page, page.name)

            # If a page is a redirect page, add a forward link
            redirect = page.metadata.get('X-Redirect')
            if redirect:
                self.handle_redirect_page(soup, self._pre(parts), redirect)

            content = unicode(soup)

            self._write_file(path.join(FOLDER, 'files', '%s.html' %
                                                   self.fix_path(page.name)), content)

            if is_main_page:
                content = compile(r'(src|href)="\./([^"]+)"') \
                    .sub(lambda m: '%s="./files/%s"' %
                                   (m.groups()[0], m.groups()[1]), content)
                self._write_file(path.join(FOLDER, 'index.html'), content)

        if len(todo) is 0:
            percents = []
        else:
            percents = list(percentize(len(todo)))
        for percent, name in izip(percents, todo):
            _fetch_and_write(name)
            if verbosity >= 1:
                pb.update(percent)

        if verbosity >= 1:
            print(("\nCreated Wikisnapshot with %s pages; excluded %s pages"
                % (len(todo), num_excluded)))
