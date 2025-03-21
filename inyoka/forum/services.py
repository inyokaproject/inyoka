"""
    inyoka.forum.services
    ~~~~~~~~~~~~~~~~~~~~~

    Forum specific services.


    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from urllib.parse import unquote

from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.http import require_GET, require_POST

from inyoka.forum.models import Post
from inyoka.portal.utils import get_ubuntu_versions
from inyoka.utils.services import SimpleDispatcher, never_cache

dispatcher = SimpleDispatcher()


@dispatcher.register()
def get_post(request):
    try:
        post_id = int(request.GET['post_id'])
        post = Post.objects.select_related('topic', 'author').get(id=post_id)
    except (KeyError, ValueError, Post.DoesNotexist):
        return None
    if not request.user.has_perm('forum.view_forum', post.topic.forum) or (not request.user.has_perm('forum.moderate_forum', post.topic.forum) and post.topic.hidden or post.hidden):
        return None
    return {
        'id': post.id,
        'author': post.author.username,
        'text': post.text
    }


@dispatcher.register()
def toggle_categories(request):
    if request.user.is_anonymous:
        return False
    hidden_categories = set()
    for id in request.GET.getlist('hidden[]'):
        try:
            hidden_categories.add(int(id))
        except ValueError:
            pass
    if not hidden_categories:
        request.user.settings.pop('hidden_forum_categories', None)
    else:
        request.user.settings['hidden_forum_categories'] = tuple(hidden_categories)
    request.user.save(update_fields=('settings',))
    return True


@dispatcher.register()
def toggle_category(request):
    if request.user.is_anonymous:
        return False

    try:
        category_id = int(request.GET.get('id'))
    except TypeError:
        return False

    hidden_categories = request.user.settings.get('hidden_forum_categories', [])
    state = request.GET.get('state')

    if state == 'hide':
        hidden_categories.append(category_id)
    elif state == 'show':
        try:
            hidden_categories.remove(category_id)
        except ValueError:
            return False
    else:
        return False

    request.user.settings['hidden_forum_categories'] = tuple(set(hidden_categories))
    request.user.save()
    return True


@dispatcher.register()
def get_version_details(request):
    try:
        version = request.GET['version']
        obj = [x for x in get_ubuntu_versions() if x.number == version][0]
    except (IndexError, KeyError, MultiValueDictKeyError):
        return {}

    return {
        'number': obj.number,
        'name': obj.name,
        'lts': obj.lts,
        'active': obj.active,
        'current': obj.current,
        'dev': obj.dev,
        'link': obj.link,
    }


@require_POST
@dispatcher.register()
def get_new_latest_posts(request):
    try:
        post_id = int(request.POST.get('post'))
    except (TypeError, ValueError):
        return HttpResponseBadRequest()

    post = Post.objects.get(id=post_id)

    if not request.user.has_perm('forum.view_forum', post.topic.forum) or (not request.user.has_perm('forum.moderate_forum', post.topic.forum) and post.topic.hidden or post.hidden):
        return None

    posts = Post.objects.filter(id__gt=post.id, topic__id=post.topic.id) \
                        .order_by('-position').all()

    return render(request, 'forum/_edit_latestpost_row.html', {
        '__main__': True,
        'posts': posts,
    })


@never_cache
@require_GET
@dispatcher.register()
def mark_topic_split_point(request):
    post_id = request.GET.get('post', None)
    topic = request.GET.get('topic', None)
    from_here = request.GET.get('from_here', False)
    post_ids = request.session.get('_split_post_ids', {})
    unchecked = False

    if topic and post_id:
        topic = unquote(topic)  # To replace quotes. e.g. the colon
        post_ids = post_ids if topic in post_ids else {topic: []}

        post_id_marked = '!%s' % post_id

        if post_id in post_ids[topic]:
            post_ids[topic].remove(post_id)
            unchecked = True

        if post_id_marked in post_ids[topic]:
            post_ids[topic].remove(post_id_marked)

        if from_here:
            post_ids = {topic: [post_id_marked]}
        elif not from_here and not unchecked:
            post_ids[topic].append(post_id)
            for pid in post_ids[topic]:
                if pid.startswith('!'):
                    post_ids[topic].remove(pid)

        if post_id in post_ids[topic] and post_id_marked in post_ids[topic]:
            post_ids[topic].remove(post_id)

        request.session['_split_post_ids'] = post_ids
