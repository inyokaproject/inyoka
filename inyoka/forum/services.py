# -*- coding: utf-8 -*-
"""
    inyoka.forum.services
    ~~~~~~~~~~~~~~~~~~~~~

    Forum specific services.


    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from urllib import unquote

from django.db import transaction
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError

from inyoka.forum.models import Topic, Post, Forum
from inyoka.forum.acl import get_forum_privileges, check_privilege, \
    have_privilege
from inyoka.portal.models import Subscription
from inyoka.portal.utils import abort_access_denied, UBUNTU_VERSIONS
from inyoka.utils.services import SimpleDispatcher, permit_methods, never_cache
from inyoka.utils.templating import render_template


def on_get_topic_autocompletion(request):
    query = request.GET.get('q', '')
    topics = Topic.objects.filter(slug__startswith=query)[:11]
    data = [t.slug for t in topics]
    if len(data) > 10:
        data[10] = '...'
    return data


def on_get_post(request):
    try:
        post_id = int(request.GET['post_id'])
        post = Post.objects.select_related('topic', 'author').get(id=post_id)
    except (KeyError, ValueError, Post.DoesNotexist):
        return None
    privs = get_forum_privileges(request.user, post.topic.forum)
    if not check_privilege(privs, 'read') or (not check_privilege(privs,
                       'moderate') and post.topic.hidden or post.hidden):
        return None
    return {
        'id':       post.id,
        'author':   post.author.username,
        'text':     post.text
    }


def on_toggle_categories(request):
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


@never_cache
@permit_methods(('POST',))
@transaction.autocommit
def subscription_action(request, action=None):
    assert action is not None and action in ('subscribe', 'unsubscribe')
    type = request.POST['type']
    slug = request.POST['slug']
    cls = None

    if type == 'forum':
        cls = Forum
    elif type == 'topic':
        cls = Topic

    obj = cls.objects.get(slug=slug)
    if request.user.is_anonymous \
       or not have_privilege(request.user, obj, 'read'):
        return abort_access_denied(request)
    try:
        subscription = Subscription.objects.get_for_user(request.user, obj)
    except Subscription.DoesNotExist:
        if action == 'subscribe':
            Subscription(user=request.user, content_object=obj).save()
    else:
        if action == 'unsubscribe':
            subscription.delete()


@never_cache
@permit_methods(('POST',))
def on_change_status(request, solved=None):
    if not 'slug' in request.POST:
        return
    topic = Topic.objects.get(slug=request.POST['slug'])
    can_read = have_privilege(request.user, topic.forum, 'read')
    if request.user.is_anonymous or not can_read:
        return abort_access_denied(request)
    if solved is not None:
        topic.solved = solved
        topic.save()


def on_get_version_details(request):
    try:
        version = request.GET['version']
        obj = [x for x in UBUNTU_VERSIONS if x.number == version][0]
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


@permit_methods(('POST',))
def on_get_new_latest_posts(request):
    post_id = int(request.POST['post'])
    post = Post.objects.get(id=post_id)

    posts = Post.objects.filter(id__gt=post.id, topic__id=post.topic.id) \
                        .order_by('-position').all()

    code = render_template('forum/_edit_latestpost_row.html', {
        '__main__': True,
        'posts': posts,
    })

    return HttpResponse(code)


@never_cache
@permit_methods(('GET',))
def on_mark_topic_split_point(request):
    post_id = request.GET.get('post', None)
    topic = request.GET.get('topic', None)
    from_here = request.GET.get('from_here', False)
    post_ids = request.session.get('_split_post_ids', {})
    unchecked = False

    if topic and post_id:
        topic = unquote(topic) # To replace quotes. e.g. the colon
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


dispatcher = SimpleDispatcher(
    get_topic_autocompletion=on_get_topic_autocompletion,
    get_post=on_get_post,
    toggle_categories=on_toggle_categories,
    subscribe=lambda r: subscription_action(r, 'subscribe'),
    unsubscribe=lambda r: subscription_action(r, 'unsubscribe'),
    mark_solved=lambda r: on_change_status(r, True),
    mark_unsolved=lambda r: on_change_status(r, False),
    get_version_details=on_get_version_details,
    get_new_latest_posts=on_get_new_latest_posts,
    mark_topic_split_point=on_mark_topic_split_point
)
