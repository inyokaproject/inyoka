# -*- coding: utf-8 -*-
"""
    inyoka.wiki.macros
    ~~~~~~~~~~~~~~~~~~

    Macros for the wiki.

    :copyright: (c) 2012-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import random
import string
import operator
import itertools
from datetime import date, datetime, timedelta
from collections import OrderedDict

from django.conf import settings
from django.dispatch import receiver
from django.utils.translation import ugettext as _, ungettext

from inyoka.markup import nodes, macros
from inyoka.markup.parsertools import MultiMap, flatten_iterator
from inyoka.markup.signals import build_picture_node
from inyoka.markup.templates import expand_page_template
from inyoka.markup.utils import simple_filter
from inyoka.utils.cache import cache
from inyoka.utils.dates import format_time, datetime_to_timezone
from inyoka.utils.imaging import parse_dimensions
from inyoka.utils.pagination import Pagination
from inyoka.utils.templating import render_template
from inyoka.utils.text import get_pagetitle, join_pagename, normalize_pagename
from inyoka.utils.urls import href, url_for, urlencode, is_safe_domain
from inyoka.wiki.models import Page, MetaData, Revision
from inyoka.wiki.views import fetch_real_target


def make_int(s, default):
    try:
        return int(s)
    except (ValueError, TypeError):
        return int(default)


class RecentChanges(macros.Macro):
    """
    Show a table of the recent changes.  This macro does only work for HTML
    so far, all other formats just get an empty text back.
    """

    names = (u'RecentChanges', u'LetzteÄnderungen')

    arguments = (
        ('per_page', int, 50),
        ('days', int, 10),
    )
    is_block_tag = True

    def __init__(self, per_page, days):
        self.per_page = per_page
        self.default_days = days

    def build_node(self, context, format):
        wiki_page = context.kwargs.get('wiki_page', None)
        if not context.request or not wiki_page:
            return nodes.Paragraph([
                nodes.Text(_(u'Recent changes cannot be rendered on this page'))
            ])

        max_days = make_int(context.request.GET.get('max_days'), self.default_days)
        page_num = make_int(context.request.GET.get('page'), 1)
        days = []
        days_found = set()

        def link_func(page_num, parameters):
            if page_num == 1:
                parameters.pop('page', None)
            else:
                parameters['page'] = str(page_num)
            rv = href('wiki', wiki_page.name)
            if parameters:
                rv += '?' + urlencode(parameters)
            return rv

        def pagebuffer_sorter(x, y):
            pb = pagebuffer
            return cmp(pb[x][-1].change_date, pb[y][-1].change_date)

        cache_key = 'wiki/recent_changes/%d-%d' % (max_days, page_num)
        data = cache.get(cache_key)
        if data is None:
            revisions = Revision.objects.filter(
                change_date__gt=(datetime.utcnow() - timedelta(days=max_days))
            ).select_related('user', 'page')
            pagination = Pagination(context.request, revisions,
                                    page_num, self.per_page, link_func)

            for revision in pagination.get_queryset():
                d = datetime_to_timezone(revision.change_date)
                key = (d.year, d.month, d.day)
                if key not in days_found:
                    days.append((date(*key), []))
                    days_found.add(key)
                days[-1][1].append(revision)

            table = nodes.Table(class_='recent_changes')

            for day, changes in days:
                table.children.append(nodes.TableRow([
                    nodes.TableHeader([
                        nodes.Text(day)
                    ], colspan=4)
                ]))

                pagebuffer = OrderedDict()
                changes = sorted(changes, key=lambda x: x.change_date)

                for rev in changes:
                    if not rev.page in pagebuffer:
                        pagebuffer[rev.page] = []
                    pagebuffer[rev.page].append(rev)

                _pagebuffer = sorted(pagebuffer, cmp=pagebuffer_sorter, reverse=True)

                for page in _pagebuffer:
                    revs = pagebuffer[page]

                    if len(revs) > 1:
                        stamps = (format_time(revs[0].change_date),
                                  format_time(revs[-1].change_date))
                        stamp = u'%s' % (stamps[0] == stamps[-1] and stamps[0] or
                                u'%s - %s' % stamps)
                    else:
                        stamp = format_time(revs[0].change_date)

                    table.children.append(nodes.TableRow([
                        nodes.TableCell([
                            nodes.Text(stamp)
                        ], class_='timestamp'),
                        nodes.TableCell([
                            nodes.InternalLink(page.name),
                            nodes.Text(u' ('),
                            nodes.Link(href('wiki', page.name, action='log'), [
                                nodes.Text(str(len(revs)) + 'x')
                            ]),
                            nodes.Text(u')')
                        ])]))

                    page_notes = nodes.List('unordered', [], class_='note_list')
                    for rev in revs:
                        if rev.user_id:
                            page_notes.children.append(nodes.ListItem([
                                nodes.Text(rev.note or ''),
                                nodes.Text(u'%svon ' % (rev.note and u' (' or '')),
                                nodes.Link(url_for(rev.user), [
                                    nodes.Text(rev.user.username)]),
                                nodes.Text(rev.note and u')' or '')
                            ]))
                        else:
                            page_notes.children.append(nodes.ListItem([
                                nodes.Text(rev.note),
                                nodes.Text(u'%svon ' % (rev.note and u'(' or '')),
                                nodes.Text(rev.remote_addr),
                                nodes.Text(rev.note and u')' or '')]))
                    table.children[-1].children.extend([
                        nodes.TableCell(
                            page_notes.children and [page_notes] or
                            [nodes.Text(u'')], class_='note')])
            data = {
                'nodes': table,
                'pagination': render_template('pagination.html', {'pagination': pagination})
            }
            cache.set(cache_key, data)

        # if rendering to html we add a pagination, pagination is stupid for
        # other static representations ;)
        if format == 'html':
            return u'<div class="recent_changes">%s%s</div>' % (
                data['nodes'].render(context, format),
                '<div class="pagination">%s<div style="clear: both">'
                '<div></div>' % data['pagination']
            )

        return data['nodes']


class PageCount(macros.Macro):
    """
    Return the number of existing pages.
    """
    names = (u'PageCount', 'Seitenzahl')

    def build_node(self, context, format):
        return nodes.Text(unicode(Page.objects.get_page_count()))


class PageList(macros.Macro):
    """
    Return a list of pages.
    """
    names = ('PageList', 'Seitenliste')
    is_block_tag = True
    arguments = (
        ('pattern', unicode, ''),
        ('case_sensitive', bool, True),
        ('shorten_title', bool, False)
    )

    def __init__(self, pattern, case_sensitive, shorten_title):
        self.pattern = normalize_pagename(pattern)
        self.case_sensitive = case_sensitive
        self.shorten_title = shorten_title

    def build_node(self, context, format):
        result = nodes.List('unordered')
        pagelist = Page.objects.get_page_list()
        if self.pattern:
            pagelist = simple_filter(self.pattern, pagelist,
                                     self.case_sensitive)
        for page in pagelist:
            title = [nodes.Text(get_pagetitle(page, not self.shorten_title))]
            link = nodes.InternalLink(page, title, force_existing=True)
            result.children.append(nodes.ListItem([link]))
            result.children.append(nodes.Text('\n'))
        return result


class AttachmentList(macros.Macro):
    """
    Return a list of attachments or attachments below
    a given page.
    """
    names = ('AttachmentList', 'Anhänge')
    is_block_tag = True
    arguments = (
        ('page', unicode, ''),
        ('shorten_title', bool, False)
    )

    def __init__(self, page, shorten_title):
        self.page = normalize_pagename(page)
        self.shorten_title = shorten_title

    def build_node(self, context, format):
        result = nodes.List('unordered')
        pagelist = Page.objects.get_attachment_list(self.page or None)
        for page in pagelist:
            title = [nodes.Text(get_pagetitle(page, not self.shorten_title))]
            link = nodes.InternalLink(page, title, force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class OrphanedPages(macros.Macro):
    """
    Return a list of orphaned pages.
    """
    names = (u'OrphanedPages', u'VerwaisteSeiten')
    is_block_tag = True

    def build_node(self, context, format):
        result = nodes.List('unordered')
        for page in Page.objects.get_orphans():
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class MissingPages(macros.Macro):
    """
    Return a list of missing pages.
    """
    names = (u'MissingPages', u'FehlendeSeiten')
    is_block_tag = True

    def build_node(self, context, format):
        result = nodes.List('unordered')
        for page, count in Page.objects.get_missing():
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link, nodes.Text(u' (%sx)' % count)]))
        return result


class RedirectPages(macros.Macro):
    """
    Return a list of pages that redirect to somewhere.
    """
    names = (u'RedirectPages', u'Weiterleitungen')
    is_block_tag = True

    def build_node(self, context, format):
        result = nodes.List('unordered')
        # TODO i18n: bloody hell, this is crazy... requires some more thinking
        #           and a migration as well as coordination with the wiki team...
        for page in Page.objects.find_by_metadata('weiterleitung'):
            target = page.metadata.get('weiterleitung')
            link = nodes.InternalLink(page.name, [nodes.Text(page.title)],
                                      force_existing=True)
            title = [nodes.Text(get_pagetitle(target, True))]
            target = nodes.InternalLink(target, title)
            result.children.append(nodes.ListItem([link, nodes.Text(u' \u2794 '),
                                                   target]))
        return result


class NewPage(macros.Macro):
    """
    Show a small form to create a new page below a page or in
    top level and with a given template.
    """
    names = (u'NewPage', u'NeueSeite')
    is_static = True
    arguments = (
        ('base', unicode, ''),
        ('template', unicode, ''),
        ('text', unicode, '')
    )

    def __init__(self, base, template, text):
        self.base = base
        self.template = template
        self.text = text

    def build_node(self):
        return nodes.html_partial('wiki/_new_page_macro.html', True,
            text=self.text,
            base=self.base,
            template=self.template
        )


class SimilarPages(macros.Macro):
    """
    Show a list of pages similar to the page name given or the
    page from the render context.
    """
    names = (u'SimilarPages', u'ÄhnlicheSeiten')
    is_block_tag = True
    arguments = (
        ('page', unicode, ''),
    )

    def __init__(self, page_name):
        self.page_name = page_name

    def build_node(self, context, format):
        wiki_page = context.kwargs.get('wiki_page', None)
        if wiki_page:
            name = wiki_page.name
            ignore = name
        else:
            name = self.page_name
            ignore = None
        if not name:
            msg = _(u'You must apply a page name because the macro is being '
                    u'called outside the wiki context.')
            return nodes.error_box(_(u'Invalid arguments'), msg)
        result = nodes.List('unordered')
        for page in Page.objects.get_similar(name):
            if page == ignore:
                continue
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class TagCloud(macros.Macro):
    """
    Show a tag cloud (or a tag list if the ?tag parameter is defined in
    the URL).
    """
    names = (u'TagCloud', u'TagWolke')
    is_block_tag = True
    arguments = (
        ('max', int, 100),
    )

    def __init__(self, max):
        self.max = max

    def build_node(self, context, format):
        if context.request:
            active_tag = context.request.GET.get('tag')
            if active_tag:
                return TagList(active_tag, _raw=True). \
                    build_node(context, format)

        result = nodes.Layer(class_='tagcloud')
        for tag in Page.objects.get_tagcloud(self.max):
            title = ungettext('one page', '%(count)d pages',
                              tag['count']) % tag
            result.children.extend((
                nodes.Link('?' + urlencode({
                        'tag': tag['name']
                    }), [nodes.Text(tag['name'])],
                    title=title,
                    style='font-size: %s%%' % tag['size']
                ),
                nodes.Text(' ')
            ))

        head = nodes.Headline(2, children=[nodes.Text(_(u'Tags'))],
                              class_='head')
        container = nodes.Layer(children=[head, result])

        return container


class TagList(macros.Macro):
    """
    Show a taglist.
    """
    names = ('TagList', u'TagListe')
    is_block_tag = True
    arguments = (
        ('tag', unicode, ''),
    )

    def __init__(self, active_tag):
        self.active_tag = active_tag

    def build_node(self, context, format):
        active_tag = self.active_tag
        if not active_tag and context.request:
            active_tag = context.request.GET.get('tag')
        result = nodes.List('unordered', class_='taglist')
        if active_tag:
            pages = Page.objects.find_by_tag(active_tag)
            for page in sorted(pages, key=string.lower):
                item = nodes.ListItem([nodes.InternalLink(page)])
                result.children.append(item)
        else:
            for tag in Page.objects.get_tagcloud():
                link = nodes.Link('?' + urlencode({
                        'tag': tag['name']
                    }), [nodes.Text(tag['name'])],
                    style='font-size: %s%%' % tag['size']
                )
                result.children.append(nodes.ListItem([link]))
        head = nodes.Headline(2, children=[
            nodes.Text(_(u'Pages with tag “%(name)s”') % {
                'name': self.active_tag
            })
        ], class_='head')
        container = nodes.Layer(children=[head, result])
        return container


class Include(macros.Macro):
    """
    Include a page.  This macro works dynamically thus the included headlines
    do not appear in the TOC.
    """
    names = (u'Include', u'Einbinden')
    is_block_tag = True
    arguments = (
        ('page', unicode, ''),
        ('silent', bool, False)
    )

    def __init__(self, page, silent):
        self.page = normalize_pagename(page)
        self.silent = silent
        self.context = []
        if self.page:
            self.metadata = [nodes.MetaData('X-Attach', ('/' + self.page,))]

    def build_node(self, context, format):
        try:
            page = Page.objects.get_by_name(self.page)
        except Page.DoesNotExist:
            if self.silent:
                return nodes.Text('')
            msg = _(u'The page “%(name)s” was not found') % {
                'name': self.page}
            return nodes.error_box(_(u'Page not found'), msg)
        context.kwargs.setdefault('included_pages', set())
        if page.name in context.kwargs['included_pages']:
            msg = _(u'Detected a circular include macro call')
            return nodes.error_box(_(u'Circular import'), msg)
        context.kwargs['included_pages'].add(page.name)
        return page.rev.text.render(context=context, format=format)


class RandomPageList(macros.Macro):
    """
    Return random a list of pages.
    """
    names = (u'RandomPageList', u'Zufallsseite')
    is_block_tag = True
    arguments = (
        ('pages', int, 10),
        ('shorten_title', bool, False)
    )

    def __init__(self, pages, shorten_title):
        self.pages = pages
        self.shorten_title = shorten_title

    def build_node(self, context, format):
        result = nodes.List('unordered')
        # TODO i18n: Again this fancy meta data... wheeeey :-)
        #           see RedirectPages for more infos.
        redirect_pages = Page.objects.find_by_metadata('weiterleitung')
        pagelist = filter(lambda p: not p in redirect_pages,
                          Page.objects.get_page_list())

        pages = []
        found = 0
        while found < self.pages and pagelist:
            pagename = random.choice(pagelist)
            pagelist.remove(pagename)
            pages.append(pagename)
            found += 1

        for page in pages:
            title = [nodes.Text(get_pagetitle(page, not self.shorten_title))]
            link = nodes.InternalLink(page, title, force_existing=True)
            result.children.append(nodes.ListItem([link]))

        return result


class RandomKeyValue(macros.Macro):
    names = (u'RandomKeyValue', u'ZufallsZitat', u'ZufälligerServer')
    arguments = (
        ('page', unicode, u''),
        ('key', unicode, u''),
        ('node_type', {
            'text': u'text',
            'link': u'link'
        }, 'text'),
    )

    def __init__(self, page, key, node_type):
        self.page = page
        self.key = key
        self.node_type = node_type

    def build_node(self, context, format):
        try:
            page = Page.objects.get_by_name(self.page)
        except Page.DoesNotExist:
            return nodes.error_box(_(u'Page not found'),
                _(u'The page “%(name)s” was not found') % {
                    'name': self.page
            })

        doc = page.rev.text.parse()
        stack = OrderedDict()
        last_cat = None
        buffer = []
        for i in doc.query.by_type(nodes.Section):
            for node in i.children:
                if isinstance(node, nodes.Headline) and node.level == 1:
                    buffer = []
                    id = node.id
                    stack.setdefault(id, {}).update({
                        'name': u''.join(x.text for x in node.query.children)
                    })
                    last_cat = id
                elif isinstance(node, nodes.List):
                    # values for the key
                    items = random.choice(node.children)
                    desc = u''.join(x.text for x in items.query.children)

                    stack.setdefault(last_cat, {}).update({
                        'desc': desc.strip()
                    })
                elif isinstance(node, nodes.Paragraph):
                    buffer.append(node)

        if self.key:
            if not self.key in stack:
                return nodes.error_box(_(u'Key not defined'),
                    _(u'The key “%(name)s” is not defined') % {
                        'name': self.key
                })
            cat = stack[self.key]
            node_type = self.node_type == 'list' and nodes.Link or nodes.Text
            return node_type(cat['desc'])
        else:
            result = nodes.Container()
            for v in stack.values():
                if not 'desc' in v:
                    continue

                desc = nodes.Strong(children=[nodes.Text(v['name'])])
                value_list = nodes.List('unordered', children=[
                    nodes.Link(v['desc'])
                ])
                result.children.extend([desc, value_list])
            return result


class FilterByMetaData(macros.Macro):
    """
    Filter pages by their metadata
    """

    names = (u'FilterByMetaData', u'MetaFilter')
    is_block_tag = True
    arguments = (
        ('filters', unicode, ''),
    )

    def __init__(self, filters):
        self.filters = [x.strip() for x in filters.split(';')]

    def build_node(self, context, format):
        mapping = []
        for part in self.filters:
            # TODO: Can we do something else instead of skipping?
            if not ':' in part:
                continue
            key = part.split(':')[0].strip()
            values = [x.strip() for x in part.split(':')[1].split(',')]
            mapping.extend(map(lambda x: (key, x), values))
        mapping = MultiMap(mapping)

        pages = set()

        for key in mapping.keys():
            values = list(flatten_iterator(mapping[key]))
            includes = [x for x in values if not x.startswith('NOT ')]
            kwargs = {'key': key, 'value__in': includes}
            q = MetaData.objects.select_related('page').filter(**kwargs)
            res = set(x.page for x in q.all())
            pages = pages.union(res)

        # filter the pages with `AND`
        res = set()
        for key in mapping.keys():
            for page in pages:
                e = [x[4:] for x in mapping[key] if x.startswith('NOT ')]
                i = [x for x in mapping[key] if not x.startswith('NOT ')]
                exclude = False
                for val in set(page.metadata[key]):
                    if val in e:
                        exclude = True
                if not exclude and set(page.metadata[key]) == set(i):
                    res.add(page)

        names = [p.name for p in res]

        if not names:
            return nodes.error_box(_(u'No result'),
                _(u'The metadata filter has found no results. Query: %(query)s') % {
                    'query': u'; '.join(self.filters)})

        # build the node
        result = nodes.List('unordered')
        for page in names:
            title = [nodes.Text(get_pagetitle(page))]
            link = nodes.InternalLink(page, title, force_existing=True)
            result.children.append(nodes.ListItem([link]))

        return result


class PageName(macros.Macro):
    """
    Return the name of the current page if the render context
    knows about that.  This is only useful when rendered from
    a wiki page.
    """
    names = (u'PageName', u'Seitenname')

    def build_node(self, context, format):
        wiki_page = context.kwargs.get('wiki_page', None)
        if wiki_page:
            return nodes.Text(wiki_page.title)
        return nodes.Text(_(u'Unknown page'))


class Template(macros.Macro):
    """
    Include a page as template and expand it.
    """
    names = (u'Template', u'Vorlage')
    has_argument_parser = True
    is_static = True

    def __init__(self, args, kwargs):
        if not args:
            self.template = None
            self.context = []
            return
        items = kwargs.items()
        for idx, arg in enumerate(args[1:]):
            items.append(('arguments.%d' % idx, arg))
        # TODO: kill WIKI_ prefix here
        self.template = join_pagename(settings.WIKI_TEMPLATE_BASE,
                                      normalize_pagename(args[0], False))
        self.context = items

    def build_node(self):
        return expand_page_template(self.template, self.context, True)


class Attachment(macros.Macro):
    """
    This macro displays a download link for an attachment.
    """
    names = (u'Attachment', u'Anhang')
    arguments = (
        ('attachment', unicode, u''),
        ('text', unicode, u''),
    )

    def __init__(self, target, text):
        self.target = target
        self.text = text
        self.is_external = not is_safe_domain(target)
        if not self.is_external:
            self.metadata = [nodes.MetaData('X-Attach', [target])]
            target = normalize_pagename(target, True)
        self.children = [nodes.Text(self.text or self.target)]

    def build_node(self, context, format):
        target = self.target
        if self.is_external:
            return nodes.Link(target, self.children)
        else:
            wiki_page = context.kwargs.get('wiki_page', None)
            if wiki_page:
                target = join_pagename(wiki_page.name, self.target)
            source = href('wiki', '_attachment',
                target=target,
            )
            return nodes.Link(source, self.children)

@receiver(build_picture_node)
def build_wiki_picture_node(sender, context, format, **kwargs):
    if not context.application == 'wiki':
        return


    target, width, height = (sender.target, sender.width, sender.height)
    try:
        wiki_page = context.kwargs.get('wiki_page', None)
        if wiki_page:
            target = join_pagename(wiki_page.name, target)
        source = fetch_real_target(target, width, height)
        img = nodes.Image(source, sender.alt, class_='image-' +
                          (sender.align or 'default'), title=sender.title)
        if (sender.width or sender.height) and wiki_page is not None:
            return nodes.Link(fetch_real_target(target), [img])
        return img
    except StaticFile.DoesNotExist:
        return

macros.register(RecentChanges)
macros.register(PageCount)
macros.register(PageList)
macros.register(AttachmentList)
macros.register(OrphanedPages)
macros.register(MissingPages)
macros.register(RedirectPages)
macros.register(NewPage)
macros.register(SimilarPages)
macros.register(TagCloud)
macros.register(TagList)
macros.register(Include)
macros.register(RandomPageList)
macros.register(RandomKeyValue)
macros.register(FilterByMetaData)
macros.register(PageName)
macros.register(Template)
macros.register(Attachment)
