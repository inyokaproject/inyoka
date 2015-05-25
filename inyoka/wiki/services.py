# -*- coding: utf-8 -*-
"""
    inyoka.wiki.services
    ~~~~~~~~~~~~~~~~~~~~

    Because of the same-origin policy we do not serve AJAX services as part
    of the normal, subdomain bound request dispatching.  This middleware
    dispatches AJAX requests on every subdomain to the modules that provide
    JSON callbacks.

    What it does is listening for "/?__service__=wiki.something" which
    dispatches to ``inyoka.wiki.services.dispatcher('something')``.


    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.http import HttpResponse

from inyoka.forum.models import Post as ForumPost
from inyoka.markup import parse, RenderContext
from inyoka.utils.services import permit_methods, SimpleDispatcher
from inyoka.wiki.models import Page
from inyoka.wiki.utils import get_smilies


def on_get_smilies(request):
    """Get a list of smilies"""
    return get_smilies()


@permit_methods(('GET', 'POST'))
def on_render_preview(request):
    """Render some preview text."""
    page = post = None
    simplified = True
    if 'page' in request.REQUEST:
        try:
            page = Page.objects.get_by_name(request.REQUEST['page'])
        except Page.DoesNotExist:
            page = None
        simplified = False
    if 'post' in request.REQUEST:
        try:
            post = ForumPost.objects.get(pk=request.REQUEST['post'])
        except ForumPost.DoesNotExist:
            post = None

    context = RenderContext(request, simplified=simplified, wiki_page=page, forum_post=post)
    html = parse(request.REQUEST.get('text', '')).render(context, 'html')
    # TODO: return json.
    return HttpResponse(html, mimetype='text/plain')


dispatcher = SimpleDispatcher(
    get_smilies=on_get_smilies,
    render_preview=on_render_preview)
