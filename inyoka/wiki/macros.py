# -*- coding: utf-8 -*-
"""
    inyoka.wiki.macros
    ~~~~~~~~~~~~~~~~~~

    The module contains the core macros and the logic to find macros.

    The term macro is derived from the MoinMoin wiki engine which refers to
    macros as small pieces of dynamic snippets that are exanded at rendering
    time.  For inyoka macros are pretty much the same just they are always
    expanded at parsing time.  However, for the sake of dynamics macros can
    mark themselves as runtime macros.  In that case during parsing the macro
    is inserted directly into the parsing as as block (or inline, depending on
    the macro settings) node and called once the data is loaded from the
    serialized instructions.

    This leads to the limitation that macros must be pickleable.  So if you
    feel the urge of creating a closure or something similar in your macro
    initializer remember that and move the code into the render method.

    For example macro implementations have a look at this module's sourcecode
    which implements all the builtin macros.


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import random
import string
from datetime import datetime, date, timedelta
from collections import OrderedDict
from django.conf import settings
from django.core.cache import cache
from inyoka.utils.urls import href, urlencode, url_for
from inyoka.portal.models import StaticFile
from inyoka.forum.models import Attachment as ForumAttachment
from inyoka.wiki.parser import nodes
from inyoka.wiki.utils import simple_filter, debug_repr, dump_argstring, \
    ArgumentCollector
from inyoka.wiki.models import Page, Revision, MetaData
from inyoka.wiki.templates import expand_page_template
from inyoka.utils.css import filter_style
from inyoka.utils.urls import is_external_target
from inyoka.utils.text import human_number, join_pagename, normalize_pagename, \
    get_pagetitle
from inyoka.utils.dates import parse_iso8601, format_datetime, format_time, \
    datetime_to_timezone
from inyoka.utils.pagination import Pagination
from inyoka.utils.parsertools import MultiMap, flatten_iterator
from inyoka.utils.imaging import get_thumbnail, parse_dimensions


def get_macro(name, args, kwargs):
    """
    Instanciate a new macro or return `None` if it doesn't exist.  This is
    used by the parser when it encounters a `macro_begin` token.  Usually
    there is no need to call this function from outside the parser.  There
    may however be macros that want to extend the functionallity of an
    already existing macro.
    """
    cls = ALL_MACROS.get(name)
    if cls is None:
        return
    return cls(args, kwargs)


class Macro(object):
    """
    Baseclass for macros.  All macros should extend from that or implement
    the same attributes.  The preferred way however is subclassing.
    """

    __metaclass__ = ArgumentCollector

    #: if a macro is static this has to be true.
    is_static = False

    #: true if this macro returns a block level node in dynamic
    #: rendering. This does not affect static rendering.
    is_block_tag = False

    #: unused in `Macro` but not `TreeMacro`.
    is_tree_processor = False

    #: set this to True if you want to do the argument parsing yourself.
    has_argument_parser = False

    #: if a macro is dynamic it's unable to emit metadata normally. This
    #: slot allows one to store a list of nodes that are sent to the
    #: stream before the macro itself is emited and removed from the
    #: macro right afterwards so that it consumes less storage pickled.
    metadata = None

    #: the arguments this macro expects
    arguments = ()

    __repr__ = debug_repr

    @property
    def macro_name(self):
        """The name of the macro."""
        return REVERSE_MACROS.get(self.__class__)

    @property
    def argument_string(self):
        """The argument string."""
        return dump_argstring(self.argument_def)

    @property
    def wiki_representation(self):
        """The macro in wiki markup."""
        args = self.argument_string
        return u'[[%s%s]]' % (
            self.macro_name,
            args and (u'(%s)' % args) or ''
        )

    def render(self, context, format):
        """Dispatch to the correct render method."""
        rv = self.build_node(context, format)
        if isinstance(rv, basestring):
            return rv
        return rv.render(context, format)

    def build_node(self, context=None, format=None):
        """
        If this is a static macro this method has to return a node.  If it's
        a runtime node a context and format parameter is passed.

        A static macro has to return a node, runtime macros can either have
        a look at the passed format and return a string for that format or
        return a normal node which is then rendered into that format.
        """


class TreeMacro(Macro):
    """
    Special macro that is processed after the whole tree was created.  This
    is useful for a `TableOfContents` macro that has to look for headline
    tags etc.

    If a macro is a tree processor the `build_node` function is passed a
    tree as only argument.  That being said it's impossible to use a tree
    macro as runtime macro.
    """

    is_tree_processor = True
    is_static = True

    #: When the macro should be expanded. Possible values are:
    #:
    #: `final`
    #:      the macro is expanded at the end of the transforming process.
    #:
    #: `initial`
    #:      the macro is expanded at the end of the parsing process, before
    #:      the transformers and other tree macro levels (default).
    #:
    #: `late`
    #:      Like initial, but after initial macros.
    stage = 'initial'

    def render(self, context, format):
        """A tree macro is not a runtime macro.  Never static"""
        raise RuntimeError('tree macro is not allowed to be non static')

    def build_node(self, tree):
        """
        Works like a normal `build_node` function but it's passed a node that
        represents the syntax tree.  It can be queried using the query
        interface attached to nodes.

        The return value must be a node, even if the macro shouldn't output
        anything.  In that situation it's recommended to return just an empty
        `nodes.Text`.
        """


class RecentChanges(Macro):
    """
    Show a table of the recent changes.  This macro does only work for HTML
    so far, all other formats just get an empty text back.
    """

    arguments = (
        ('per_page', int, 50),
        ('days', int, 10),
    )
    is_block_tag = True

    def __init__(self, per_page, days):
        self.per_page = per_page
        self.default_days = days

    def build_node(self, context, format):
        if not context.request or not context.wiki_page:
            return nodes.Paragraph([
                nodes.Text(u'Letzte Änderungen können von hier aus '
                           u'nicht dargestellt werden.')
            ])

        def make_int(s, default):
            try:
                return int(s)
            except (ValueError, TypeError):
                return int(default)

        max_days = make_int(context.request.GET.get('max_days'), self.default_days)
        page_num = make_int(context.request.GET.get('page'), 1)
        days = []
        days_found = set()

        def link_func(page_num, parameters):
            if page_num == 1:
                parameters.pop('page', None)
            else:
                parameters['page'] = str(page_num)
            rv = href('wiki', context.wiki_page.name)
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
                change_date__gt=(datetime.utcnow()-timedelta(days=max_days))
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
                        stamp = u'%s' % (stamps[0]==stamps[-1] and stamps[0] or \
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
                                nodes.Text(str(len(revs))+'x')
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
                            page_notes.children and [page_notes] or \
                            [nodes.Text(u'')], class_='note')])
            data = {
                'nodes':      table,
                'pagination': pagination.generate()
            }
            cache.set(cache_key, data)

        # if rendering to html we add a pagination, pagination is stupid for
        # docbook and other static representations ;)
        if format == 'html':
            return u'<div class="recent_changes">%s%s</div>' % (
                data['nodes'].render(context, format),
                '<div class="pagination">%s<div style="clear: both">'
                '<div></div>' % data['pagination']
            )

        return data['nodes']


class TableOfContents(TreeMacro):
    """
    Show a table of contents.  We do not embedd the TOC in a DIV so far and
    there is also no title on it.
    """
    stage = 'final'
    is_block_tag = True
    arguments = (
        ('max_depth', int, 3),
        ('type', {
            'unordered':    'unordered',
            'arabic0':      'arabiczero',
            'arabic':       'arabic',
            'alphabeth':    'alphalower',
            'ALPHABETH':    'alphaupper',
            'roman':        'romanlower',
            'ROMAN':        'romanupper'
        }, 'arabic')
    )

    def __init__(self, depth, list_type):
        self.depth = depth
        self.list_type = list_type

    def build_node(self, tree):
        result = nodes.List(self.list_type)
        stack = [result]
        normalized_level = 0
        last_level = 0
        for headline in tree.query.by_type(nodes.Headline):
            if not headline.level == last_level:
                if headline.level > normalized_level:
                    normalized_level += 1
                elif headline.level < normalized_level:
                    normalized_level -= 1
            if normalized_level > self.depth:
                continue
            elif normalized_level > len(stack):
                for x in xrange(normalized_level - len(stack)):
                    node = nodes.List(self.list_type)
                    if stack[-1].children:
                        stack[-1].children[-1].children.append(node)
                    else:
                        result.children.append(nodes.ListItem([node]))
                    stack.append(node)
            elif normalized_level < len(stack):
                for x in xrange(len(stack) - normalized_level):
                    stack.pop()
            ml = normalized_level*((45-self.depth-normalized_level)/(normalized_level or 1))
            text = len(headline.text)>ml and headline.text[:ml]+'...' or \
                   headline.text
            caption = [nodes.Text(text)]
            link = nodes.Link('#' + headline.id, caption)
            stack[-1].children.append(nodes.ListItem([link]))
            last_level = headline.level
        head = nodes.Layer(children=[nodes.Text(u'Inhaltsverzeichnis')],
                           class_='head')
        result = nodes.Layer(class_='toc toc-depth-%d' % self.depth,
                             children=[head, result])
        return result


class PageCount(Macro):
    """
    Return the number of existing pages.
    """

    def build_node(self, context, format):
        return nodes.Text(unicode(Page.objects.get_page_count()))


class PageList(Macro):
    """
    Return a list of pages.
    """

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


class AttachmentList(Macro):
    """
    Return a list of attachments or attachments below
    a given page.
    """

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


class OrphanedPages(Macro):
    """
    Return a list of orphaned pages.
    """

    is_block_tag = True

    def build_node(self, context, format):
        result = nodes.List('unordered')
        for page in Page.objects.get_orphans():
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class MissingPages(Macro):
    """
    Return a list of missing pages.
    """

    is_block_tag = True

    def build_node(self, context, format):
        result = nodes.List('unordered')
        for page, count in Page.objects.get_missing():
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link, nodes.Text(u' (%sx)' % count)]))
        return result


class RedirectPages(Macro):
    """
    Return a list of pages that redirect to somewhere.
    """

    is_block_tag = True

    def build_node(self, context, format):
        result = nodes.List('unordered')
        for page in Page.objects.find_by_metadata('weiterleitung'):
            target = page.metadata.get('weiterleitung')
            link = nodes.InternalLink(page.name, [nodes.Text(page.title)],
                                      force_existing=True)
            title = [nodes.Text(get_pagetitle(target, True))]
            target = nodes.InternalLink(target, title)
            result.children.append(nodes.ListItem([link, nodes.Text(u' \u2794 '),
                                                   target]))
        return result


class PageName(Macro):
    """
    Return the name of the current page if the render context
    knows about that.  This is only useful when rendered from
    a wiki page.
    """

    def build_node(self, context, format):
        if context.wiki_page:
            return nodes.Text(context.wiki_page.title)
        return nodes.Text('Unbekannte Seite')


class NewPage(Macro):
    """
    Show a small form to create a new page below a page or in
    top level and with a given template.
    """

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


class SimilarPages(Macro):
    """
    Show a list of pages similar to the page name given or the
    page from the render context.
    """

    is_block_tag = True
    arguments = (
        ('page', unicode, ''),
    )

    def __init__(self, page_name):
        self.page_name = page_name

    def build_node(self, context, format):
        if context.wiki_page:
            name = context.wiki_page.name
            ignore = name
        else:
            name = self.page_name
            ignore = None
        if not name:
            return nodes.error_box('Parameterfehler', u'Du musst eine '
                                   u'Seite angeben, wenn das Makro '
                                   u'außerhalb des Wikis verwendet wird.')
        result = nodes.List('unordered')
        for page in Page.objects.get_similar(name):
            if page == ignore:
                continue
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class TagCloud(Macro):
    """
    Show a tag cloud (or a tag list if the ?tag parameter is defined in
    the URL).
    """

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
            if tag['count'] == 1:
                title = 'eine Seite'
            else:
                title = '%s Seiten' % human_number(tag['count'], 'feminine')
            result.children.extend((
                nodes.Link('?' + urlencode({
                        'tag':  tag['name']
                    }), [nodes.Text(tag['name'])],
                    title=title,
                    style='font-size: %s%%' % tag['size']
                ),
                nodes.Text(' ')
            ))

        head = nodes.Headline(2, children=[nodes.Text(u'Tag-Wolke')],
                              class_='head')
        container = nodes.Layer(children=[head, result])

        return container


class TagList(Macro):
    """
    Show a taglist.
    """

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
                        'tag':  tag['name']
                    }), [nodes.Text(tag['name'])],
                    style='font-size: %s%%' % tag['size']
                )
                result.children.append(nodes.ListItem([link]))
        head = nodes.Headline(2, children=[
            nodes.Text(u'Seiten mit Tag „%s“' % self.active_tag)
        ], class_='head')
        container = nodes.Layer(children=[head, result])
        return container


class Include(Macro):
    """
    Include a page.  This macro works dynamically thus the included headlines
    do not appear in the TOC.
    """

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
            return nodes.error_box(u'Seite nicht gefunden',
                                   u'Die Seite „%s“ wurde nicht '
                                   u'gefunden.' % self.page)
        if page.name in context.included_pages:
            return nodes.error_box(u'Zirkulärer Import',
                                   u'Rekursiver Aufruf des Include-'
                                   u'Makros wurde erkannt.')
        context.included_pages.add(page.name)
        return page.rev.text.render(context=context, format=format)


class Template(Macro):
    """
    Include a page as template and expand it.
    """

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
        self.template = join_pagename(settings.WIKI_TEMPLATE_BASE,
                                      normalize_pagename(args[0], False))
        self.context = items

    def build_node(self):
        return expand_page_template(self.template, self.context, True)


class Attachment(Macro):
    """
    This macro displays a download link for an attachment.
    """

    arguments = (
        ('attachment', unicode, u''),
        ('text', unicode, u''),
    )

    def __init__(self, target, text):
        self.target = target
        self.text = text
        self.is_external = is_external_target(target)
        if not self.is_external:
            self.metadata = [nodes.MetaData('X-Attach', [target])]
            target = normalize_pagename(target, True)
        self.children = [nodes.Text(self.text or self.target)]

    def build_node(self, context, format):
        target = self.target
        if self.is_external:
            return nodes.Link(target, self.children)
        else:
            if context.wiki_page:
                target = join_pagename(context.wiki_page.name, self.target)
            source = href('wiki', '_attachment',
                target=target,
            )
            return nodes.Link(source, self.children)


class Picture(Macro):
    """
    This macro can display external images and attachments as images.  It
    also takes care about thumbnail generation.  For any internal (attachment)
    image included that way an ``X-Attach`` metadata is emitted.

    Like for any link only absolute targets are allowed.  This might be
    surprising behavior if you're used to the MoinMoin syntax but caused
    by the fact that the parser does not know at parse time on which page
    it is operating.
    """

    arguments = (
        ('picture', unicode, u''),
        ('size', unicode, u''),
        ('align', unicode, u''),
        ('alt', unicode, None),
        ('title', unicode, None)
    )

    def __init__(self, target, dimensions, alignment, alt, title):
        self.metadata = [nodes.MetaData('X-Attach', [target])]
        self.width, self.height = parse_dimensions(dimensions)
        self.target = target
        self.alt = alt or target
        self.title = title

        self.align = alignment
        if self.align not in ('left', 'right', 'center'):
            self.align = None

    def build_node(self, context, format):
        if context.application == 'wiki':
            target = normalize_pagename(self.target, True)
        else:
            target = self.target

        if context.wiki_page:
            target = join_pagename(context.wiki_page.name, target)

        source = href('wiki', '_image', target=target,
                      width=self.width, height=self.height)
        file = None

        if context.application == 'ikhaya':
            try:
                file = StaticFile.objects.get(identifier=target)
                if (self.width or self.height) and os.path.exists(file.file.path):
                    tt = target.rsplit('.', 1)
                    dimension = '%sx%s' % (self.width and int(self.width) or '',
                                           self.height and int(self.height) or '')
                    target = '%s%s.%s' % (tt[0], dimension, tt[1])

                    destination = os.path.join(settings.MEDIA_ROOT, 'portal/thumbnails', target)
                    thumb = get_thumbnail(file.file.path, destination, self.width, self.height)
                    if thumb:
                        source = os.path.join(settings.MEDIA_URL, 'portal/thumbnails', thumb.rsplit('/', 1)[1])
                    else:
                        # fallback to the orginal file
                        source = os.path.join(settings.MEDIA_URL, file.file.name)
                else:
                    source = url_for(file)
            except StaticFile.DoesNotExist:
                pass
        if context.application == 'forum':
            try:
                # There are times when two users upload a attachment with the same
                # name, both have post=None, so we cannot .get() here
                # and need to filter for attachments that are session related.
                # THIS IS A HACK and should go away once we found a way
                # to upload attachments directly to bound posts in a sane way...
                if context.request is not None and 'attachments' in context.request.POST:
                    att_ids = map(int, filter(bool,
                        context.request.POST.get('attachments', '').split(',')
                    ))
                    files = ForumAttachment.objects.filter(name=target, post=context.forum_post,
                                                           id__in=att_ids)
                    return nodes.HTML(files[0].html_representation)
                else:
                    file = ForumAttachment.objects.get(name=target, post=context.forum_post)
                    return nodes.HTML(file.html_representation)
            except (ForumAttachment.DoesNotExist, IndexError), exc:
                pass

        img = nodes.Image(source, self.alt, class_='image-' +
                          (self.align or 'default'), title=self.title)
        if (self.width or self.height) and context.wiki_page is not None:
            return nodes.Link(href('wiki', '_image', target=target), [img])
        elif (self.width or self.height) and not context.application == 'wiki' and file is not None:
            return nodes.Link(url_for(file), [img])
        return img

    def __setstate__(self, dict):
        self.__dict__ = dict
        if 'title' not in dict:
            self.title = None


class Date(Macro):
    """
    This macro accepts an `iso8601` string or unix timestamp (the latter in
    UTC) and formats it using the `format_datetime` function.
    """

    arguments = (
        ('date', unicode, None),
    )

    def __init__(self, date):
        if not date:
            self.now = True
        else:
            self.now = False
            try:
                self.date = parse_iso8601(date)
            except ValueError:
                try:
                    self.date = datetime.utcfromtimestamp(int(date))
                except ValueError:
                    self.date = None

    def build_node(self, context, format):
        if self.now:
            date = datetime.utcnow()
        else:
            date = self.date
        if date is None:
            return nodes.Text(u'ungültiges Datum')
        return nodes.Text(format_datetime(date))


class Newline(Macro):
    """
    This macro just forces a new line.
    """

    is_static = True

    def build_node(self):
        return nodes.Newline()


class Anchor(Macro):
    """
    This macro creates an anchor accessible by url.
    """

    is_static = True
    arguments = (
        ('id', unicode, None),
    )

    def __init__(self, id):
        self.id = id

    def build_node(self):
        return nodes.Link(u'#%s' % self.id, id=self.id, class_='anchor',
                          children=[nodes.Text(u'')])


class RandomPageList(Macro):
    """
    Return random a list of pages.
    """

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


class Span(Macro):
    is_static = True
    arguments = (
        ('content', unicode, ''),
        ('class_', unicode, None),
        ('style', unicode, None),
    )

    def __init__(self, content, class_, style):
        self.content = content
        self.class_ = class_
        self.style = filter_style(style) or None

    def build_node(self):
        return nodes.Span(children=[nodes.Text(self.content)],
                        class_=self.class_, style=self.style)


class RandomKeyValue(Macro):
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
            return nodes.error_box(u'Seite nicht gefunden',
                                   u'Die Seite „%s“ wurde nicht '
                                   u'gefunden.' % self.page)

        doc = page.rev.text.parse()
        stack = OrderedDict()
        last_cat = None
        buffer = []
        for _ in doc.query.by_type(nodes.Section):
            for node in _.children:
                if isinstance(node, nodes.Headline) and node.level == 1:
                    buffer = []
                    id = node.id
                    stack.setdefault(id, {}).update({
                        'name':  u''.join(x.text for x in node.query.children)
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
                return nodes.error_box(u'Schlüssel nicht definiert',
                    u'Der Schlüssel „%s” wurde nicht definiert.' % self.key)
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


class FilterByMetaData(Macro):
    """
    Filter pages by their metadata
    """

    is_block_tag = True

    arguments = (
        ('filters', unicode, ''),
    )

    def __init__(self, filters):
        self.filters = [x.strip() for x in filters.split(';')]

    def build_node(self, context, format):
        mapping = []
        for part in self.filters:
            key = part.split(':')[0].strip()
            values = [x.strip() for x in part.split(':')[1].split(',')]
            mapping.extend(map(lambda x: (key, x), values))
        mapping = MultiMap(mapping)

        pages = set([])

        for key in mapping.keys():
            values = list(flatten_iterator(mapping[key]))
            includes = [x for x in values if not x.startswith('NOT ')]
            kwargs = {'key': key, 'value__in': includes}
            q = MetaData.objects.select_related(depth=1).filter(**kwargs)
            res = set(x.page for x in q.all())
            pages = pages.union(res)

        # filter the pages with `AND`
        res = set([])
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
            return nodes.error_box(u'Kein Ergebnis',
                u'Der Metadaten-Filter hat keine Ergebnisse gefunden. Query: %s'
                % u'; '.join(self.filters))

        # build the node
        result = nodes.List('unordered')
        for page in names:
            title = [nodes.Text(get_pagetitle(page))]
            link = nodes.InternalLink(page, title, force_existing=True)
            result.children.append(nodes.ListItem([link]))

        return result

#: this mapping is used by the `get_macro()` function to map public
#: macro names to the classes.
ALL_MACROS = {
    u'Anhänge':             AttachmentList,
    u'Anker':               Anchor,
    u'BR':                  Newline,
    u'Bild':                Picture,
    u'Anhang':              Attachment,
    u'Datum':               Date,
    u'Einbinden':           Include,
    u'FehlendeSeiten':      MissingPages,
    u'Inhaltsverzeichnis':  TableOfContents,
    u'LetzteÄnderungen':    RecentChanges,
    u'NeueSeite':           NewPage,
    u'Seitenliste':         PageList,
    u'Seitenname':          PageName,
    u'Seitenzahl':          PageCount,
    u'TagListe':            TagList,
    u'TagWolke':            TagCloud,
    u'VerwaisteSeiten':     OrphanedPages,
    u'Vorlage':             Template,
    u'Weiterleitungen':     RedirectPages,
    u'Zufallsseite':        RandomPageList,
    u'ÄhnlicheSeiten':      SimilarPages,
    u'SPAN':                Span,
    u'ZufallsZitat':        RandomKeyValue,
    u'ZufälligerServer':    RandomKeyValue,
    u'MetaFilter':          FilterByMetaData,
}


#: automatically updated reverse mapping of macros
REVERSE_MACROS = dict((v, k) for k, v in ALL_MACROS.iteritems())
