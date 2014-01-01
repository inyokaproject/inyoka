#-*- coding: utf-8 -*-
"""
    inyoka.forum.search
    ~~~~~~~~~~~~~~~~~~~

    Search interfaces for the forum.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.utils.translation import ugettext_lazy

from inyoka.forum.acl import get_privileges, check_privilege
from inyoka.utils.urls import href, url_for
from inyoka.utils.search import search, SearchAdapter
from inyoka.forum.models import Post, Forum
from inyoka.utils.decorators import deferred


class ForumSearchAuthDecider(object):
    """Decides whether a user can display a search result or not."""

    def __init__(self, user):
        self.user = user

    @deferred
    def privs(self):
        # the privileges are set on first call and not on init because this
        # would create one useless query if the user e.g. just searched the
        # wiki.
        privs = get_privileges(self.user, Forum.objects.get_cached())
        return {id: check_privilege(priv, 'read')
                for id, priv in privs.iteritems()}

    def __call__(self, auth):
        return self.privs.get(auth[0], False)


class ForumSearchAdapter(SearchAdapter):
    type_id = 'f'
    auth_decider = ForumSearchAuthDecider
    support_multi = True

    def get_objects(self, docids):
        return Post.objects.select_related('topic', 'author') \
                           .filter(id__in=docids).all()

    def store_object(self, post, connection=None):
        forum = post.topic.cached_forum()
        search.store(connection,
            component='f',
            uid=post.id,
            title=post.topic.title,
            user=post.author_id,
            date=post.pub_date,
            collapse=post.topic.id,
            category=[p.slug for p in forum.parents] + \
                [forum.slug],
            auth=[post.topic.forum_id, post.topic.hidden],
            text=post.text,
            solved='1' if post.topic.solved else '0',
            version=post.topic.get_version_info(default=None),
        )

    def extract_data(self, post):
        return {'title': post.topic.title,
                'user': post.author.username,
                'date': post.pub_date,
                'url': href('forum', 'post', post.id),
                'component': ugettext_lazy(u'Forum'),
                'group': post.topic.cached_forum().name,
                'group_url': url_for(post.topic.cached_forum()),
                'highlight': True,
                'text': post.get_text(),
                'solved': post.topic.solved,
                'version': post.topic.get_version_info(False),
                'hidden': post.hidden or post.topic.hidden,
                'last_post_url': url_for(post.topic.last_post),
                'user_url': url_for(post.author)}

    def recv(self, post_id):
        try:
            query = Post.objects.select_related('topic', 'author')
            post = query.get(id=post_id)
        except Post.DoesNotExist:
            return
        return self.extract_data(post)

    def recv_multi(self, post_ids):
        posts = Post.objects.select_related('topic', 'author') \
                            .filter(id__in=post_ids).all()
        return [self.extract_data(post) for post in posts]

    def get_doc_ids(self):
        pids = Post.objects.values_list('id', flat=True)
        for pid in pids:
            yield pid


search.register(ForumSearchAdapter())
