"""
    inyoka.wiki.macros
    ~~~~~~~~~~~~~~~~~~

    Macros for the wiki.

    :copyright: (c) 2012-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import itertools
import operator

from django.conf import settings
from django.db.models import FilteredRelation, Q
from django.utils.translation import gettext as _

from inyoka.markup import macros, nodes
from inyoka.markup.templates import expand_page_template
from inyoka.markup.utils import simple_filter
from inyoka.utils.imaging import parse_dimensions
from inyoka.utils.text import get_pagetitle, join_pagename, normalize_pagename
from inyoka.utils.urls import href, is_safe_domain, urlencode
from inyoka.wiki.models import Page, is_privileged_wiki_page
from inyoka.wiki.signals import build_picture_node
from inyoka.wiki.views import fetch_real_target


class PageCount(macros.Macro):
    """
    Return the number of existing pages.
    """
    names = ('PageCount', 'Seitenzahl')
    allowed_context = ['wiki']

    def build_node(self, context, format):
        return nodes.Text(str(Page.objects.get_page_count()))


class PageList(macros.Macro):
    """
    Return a list of pages.
    """
    names = ('PageList', 'Seitenliste')
    is_block_tag = True
    arguments = (
        ('pattern', str, ''),
        ('case_sensitive', bool, True),
        ('shorten_title', bool, False)
    )
    allowed_context = ['wiki']

    def __init__(self, pattern, case_sensitive, shorten_title):
        self.pattern = normalize_pagename(pattern)
        self.case_sensitive = case_sensitive
        self.shorten_title = shorten_title

    def build_node(self, context, format):
        result = nodes.List('unordered')
        pagelist = Page.objects.get_page_list(exclude_privileged=True)
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
        ('page', str, ''),
        ('shorten_title', bool, False)
    )
    allowed_context = ['wiki']

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
    names = ('OrphanedPages', 'VerwaisteSeiten')
    is_block_tag = True
    allowed_context = ['wiki']

    def build_node(self, context, format):
        result = nodes.List('unordered')
        for page in Page.objects.get_orphans():
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class RedirectPages(macros.Macro):
    """
    Return a list of pages that redirect to somewhere.
    """
    names = ('RedirectPages', 'Weiterleitungen')
    is_block_tag = True
    allowed_context = ['wiki']

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
            result.children.append(nodes.ListItem([link, nodes.Text(' \u2794 '),
                                                   target]))
        return result


class SimilarPages(macros.Macro):
    """
    Show a list of pages similar to the page name given or the
    page from the render context.
    """
    names = ('SimilarPages', 'ÄhnlicheSeiten')
    is_block_tag = True
    arguments = (
        ('page', str, ''),
    )
    allowed_context = ['wiki']

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
            msg = _('You must apply a page name because the macro is being '
                    'called outside the wiki context.')
            return nodes.error_box(_('Invalid arguments'), msg)
        result = nodes.List('unordered')
        for page in Page.objects.get_similar(name):
            if page == ignore:
                continue
            title = [nodes.Text(get_pagetitle(page, True))]
            link = nodes.InternalLink(page, title,
                                      force_existing=True)
            result.children.append(nodes.ListItem([link]))
        return result


class TagList(macros.Macro):
    """
    Show a taglist.
    """
    names = ('TagList', 'TagListe')
    is_block_tag = True
    arguments = (
        ('tag', str, ''),
    )
    allowed_context = ['wiki']

    def __init__(self, active_tag):
        self.active_tag = active_tag

    def build_node(self, context, format):
        active_tag = self.active_tag
        if not active_tag and context.request:
            active_tag = context.request.GET.get('tag')
        result = nodes.List('unordered', class_='taglist')
        if active_tag:
            pages = Page.objects.find_by_tag(active_tag)
            for page in sorted(pages, key=str.lower):
                item = nodes.ListItem([nodes.InternalLink(page)])
                result.children.append(item)
        else:
            for tag in Page.objects.get_taglist(100):
                link = nodes.Link('?' + urlencode({
                    'tag': tag['name']
                    }), [nodes.Text(tag['name'])],
                    style='font-size: %s%%' % tag['size']
                )
                result.children.append(nodes.ListItem([link]))
        head = nodes.Headline(2, children=[
            nodes.Text(_('Pages with tag “%(name)s”') % {
                'name': self.active_tag
            })
        ], class_='head')
        container = nodes.Layer(children=[head, result])
        return container


class FilterByMetaData(macros.Macro):
    """Filter pages by their metadata.

    One filter has the form `key: value`.
    Multiple filters can be combined with a `;` in the sense of a `and`.
    Value can contain multiple values seperated by `,` in the sense of `or`.

    ``NOT`` at the start of a value negates the filter.
    It can be used (multiple times) only at the start of a filter.
    Additionally, only one value can be used with ``NOT``.

    Examples:

        `[[FilterByMetaData("tag: baz")]]` lists pages that have the tag baz
        `[[FilterByMetaData("X-Link: foo,bar")]]` lists pages that have a link to `foo` _or_ `bar`
        `[[FilterByMetaData("X-Link: foo; X-Link: bar")]]` lists pages that have a link to `foo` _and_ `bar`
        `[[FilterByMetaData("X-Link: NOT gras")]]` lists pages that not contain a link to gras
    """

    names = ('FilterByMetaData', 'MetaFilter')
    is_block_tag = True
    arguments = (
        ('filters', str, ''),
    )
    allowed_context = ['wiki']

    def __init__(self, filters):
        self.filters = [x.strip() for x in filters.split(';')]

    def _is_allowed_key(self, key: str) -> bool:
        """
        Returns True, if this is an allowed metadata key.

        Via this method the queryable metadata keys can be restricted.
        Disallowed is for example the key `X-Behave`.
        """
        return key in {'tags', 'tag', 'X-Redirect', 'X-Link', 'X-Attach', 'getestet'}

    def build_node(self, context, format):
        pages = Page.objects.all()

        for part in self.filters:
            if part.count(":") != 1:
                return nodes.error_box(_('No result'),
                    _('Invalid filter syntax. Query: %(query)s') % {
                    'query': '; '.join(self.filters)})

            key, values = part.split(":")

            values = [v.strip() for v in values.split(",")]
            if values[0].startswith("NOT") and len(values) > 1:
                return nodes.error_box(_('No result'),
                    _('Invalid filter syntax. Query: %(query)s') % {
                    'query': '; '.join(self.filters)})

            key = key.strip()
            if not self._is_allowed_key(key):
                return nodes.error_box(_('No result'),
                    _('Invalid filter key %(key)s. Query: %(query)s') % {
                        'key': key,
                        'query': '; '.join(self.filters)})

            if values[0].startswith("NOT"):
                exclude_value = values[0].removeprefix("NOT ")

                normalized_key = key.lower().replace("-", "")
                pages = pages.annotate(**{
                    f'filtered_{normalized_key}': FilteredRelation(
                        'metadata',
                        condition=Q(metadata__key=key),
                    )}
                ).exclude(**{f'filtered_{normalized_key}__value': exclude_value})
            else:
                includes = set(values)
                pages = pages.filter(metadata__key=key, metadata__value__in=includes)

        # exclude privileged pages
        for prefix in settings.WIKI_PRIVILEGED_PAGES:
            pages = pages.exclude(name__startswith=prefix)

        pages = pages.distinct()
        page_names = pages.values_list('name', flat=True)

        if not page_names:
            return nodes.error_box(_('No result'),
                _('The metadata filter has found no results. Query: %(query)s') % {
                    'query': '; '.join(self.filters)})

        # build the node
        result = nodes.List('unordered')
        for p in page_names:
            title = [nodes.Text(get_pagetitle(p))]
            link = nodes.InternalLink(p, title, force_existing=True)
            result.children.append(nodes.ListItem([link]))

        return result


class PageName(macros.Macro):
    """
    Return the name of the current page if the render context
    knows about that.  This is only useful when rendered from
    a wiki page.
    """
    names = ('PageName', 'Seitenname')
    allowed_context = ['wiki']

    def build_node(self, context, format):
        wiki_page = context.kwargs.get('wiki_page', None)
        if wiki_page:
            return nodes.Text(wiki_page.title)
        return nodes.Text(_('Unknown page'))


class Template(macros.Macro):
    """
    Include a page as template and expand it.
    """
    names = ('Template', 'Vorlage')
    has_argument_parser = True
    is_static = True
    allowed_context = ['forum', 'ikhaya', 'wiki']

    def __init__(self, args, kwargs):
        if not args:
            self.template = None
            self.context = []
            return

        items = list(kwargs.items())
        for idx, arg in enumerate(args[1:]):
            items.append(('arguments.%d' % idx, arg))
        # TODO: kill WIKI_ prefix here
        self.template = join_pagename(settings.WIKI_TEMPLATE_BASE,
                                      normalize_pagename(args[0], False))
        if is_privileged_wiki_page(self.template):
            self.template = None
        self.context = items

    def build_node(self):
        return expand_page_template(self.template, self.context, True)


class Attachment(macros.Macro):
    """
    This macro displays a download link for an attachment.
    """
    names = ('Attachment', 'Anhang')
    arguments = (
        ('attachment', str, ''),
        ('text', str, ''),
    )
    allowed_context = ['wiki']

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
            source = href('wiki', '_attachment', target=target)
            return nodes.Link(source, self.children)


class Picture(macros.Macro):
    """
    This macro can display external images and attachments as images.  It
    also takes care about thumbnail generation. For any internal (attachment)
    image included that way an ``X-Attach`` metadata is emitted.

    Like for any link only absolute targets are allowed. This might be
    surprising behavior if you're used to the MoinMoin syntax but caused
    by the fact that the parser does not know at parse time on which page
    it is operating.
    """
    names = ('Picture', 'Bild')
    arguments = (
        ('picture', str, ''),
        ('size', str, ''),
        ('align', str, ''),
        ('alt', str, None),
        ('title', str, None)
    )
    allowed_context = ['ikhaya', 'wiki']

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
        ret_ = build_picture_node.send(sender=self,
                                       context=context,
                                       format=format)
        ret = [_f for _f in itertools.chain(
            list(map(operator.itemgetter(1), ret_))
        ) if _f]

        if ret:
            assert len(ret) == 1, "There must not be more than one node tree per context"
            return ret[0]

        # TODO: refactor using signals on rendering
        #      to get proper application independence
        if context.application == 'wiki':
            target = normalize_pagename(self.target, True)
        else:
            target = self.target

        wiki_page = context.kwargs.get('wiki_page', None)

        if wiki_page:
            target = join_pagename(wiki_page.name, target)

        source = fetch_real_target(target, width=self.width, height=self.height)

        img = nodes.Image(source, self.alt, class_='image-' +
                          (self.align or 'default'), title=self.title)
        if (self.width or self.height) and wiki_page is not None:
            return nodes.Link(fetch_real_target(target), [img])
        return img


macros.register(PageCount)
macros.register(PageList)
macros.register(AttachmentList)
macros.register(OrphanedPages)
macros.register(RedirectPages)
macros.register(SimilarPages)
macros.register(TagList)
macros.register(FilterByMetaData)
macros.register(PageName)
macros.register(Template)
macros.register(Attachment)
macros.register(Picture)
