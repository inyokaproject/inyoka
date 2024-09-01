"""
    inyoka.wiki.services
    ~~~~~~~~~~~~~~~~~~~~

    Because of the same-origin policy we do not serve AJAX services as part
    of the normal, subdomain bound request dispatching.  This middleware
    dispatches AJAX requests on every subdomain to the modules that provide
    JSON callbacks.

    What it does is listening for "/?__service__=wiki.something" which
    dispatches to ``inyoka.wiki.services.dispatcher('something')``.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from inyoka.forum.models import Post as ForumPost
from inyoka.markup.base import RenderContext, parse
from inyoka.utils.services import SimpleDispatcher
from inyoka.wiki.exceptions import CaseSensitiveException
from inyoka.wiki.models import Page

dispatcher = SimpleDispatcher()


@require_http_methods(['GET','POST'])
@dispatcher.register()
def render_preview(request):
    """Render some preview text."""
    page = post = None
    simplified = True
    if 'page' in request.POST:
        try:
            page = Page.objects.get_by_name(request.POST['page'])
        except Page.DoesNotExist:
            page = None
        except CaseSensitiveException as e:
            page = e.page
        simplified = False
    if 'post' in request.POST:
        try:
            post = ForumPost.objects.get(pk=request.POST['post'])
        except ForumPost.DoesNotExist:
            post = None

    context = RenderContext(request, simplified=simplified, wiki_page=page, forum_post=post)
    html = parse(request.POST.get('text', '')).render(context, 'html')
    return HttpResponse(html, content_type='text/plain')
