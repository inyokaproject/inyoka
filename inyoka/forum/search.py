#-*- coding: utf-8 -*-
from pyes import TermsFilter
from inyoka.utils.search import search, Index, DocumentType
from inyoka.forum.acl import get_privileges, check_privilege
from inyoka.forum.models import Post, Forum
from inyoka.utils.urls import url_for, href



class PostDocumentType(DocumentType):
    name = 'post'
    model = Post

    mapping = {'properties': {
        'pk': {'type': 'integer', 'store': 'yes'},
        'title': {'type': 'string', 'store': 'yes'},
        'author': {'type': 'string', 'store': 'yes'},
        'author_url': {'type': 'string', 'store': 'yes'},
        'date': {'type': 'date', 'store': 'yes'},
        'category': {'type': 'string', 'store': 'yes'},
        'hidden': {'type': 'boolean', 'store': 'yes'},
        'text': {'type': 'string', 'store': 'yes'},
        'solved': {'type': 'boolean', 'store': 'yes'},
        'version': {'type': 'string', 'store': 'yes'},
        'url': {'type': 'string', 'store': 'yes'},
        'forum': {'type': 'string', 'store': 'yes'},
        'forum_pk': {'type': 'integer', 'store': 'yes'},
        'last_post_url': {'type': 'string', 'store': 'yes'}
    }}

    def get_filter(self, user):
        privs = get_privileges(user, Forum.objects.get_cached())
        forums = [id for id, priv in privs.iteritems()
                                  if check_privilege(priv, 'read')]
        return TermsFilter('forum_pk', forums)

    @classmethod
    def serialize(cls, post):
        forum = post.topic.cached_forum()
        categories = [f.slug for f in forum.parents] + [forum.slug]
        return {'pk': post.pk,
                'title': post.topic.title,
                'author': post.author.username,
                'author_url': url_for(post.author),
                'date': post.pub_date,
                'category': categories,
                'hidden': post.hidden or post.topic.hidden,
                'text': post.get_text(),
                'solved': post.topic.solved,
                'version': post.topic.get_version_info(default=None),
                'url': href('forum', 'post', post.pk),
                'forum': forum.name,
                'forum_pk': forum.pk,
                'last_post_url': url_for(post.topic.last_post)}


class ForumIndex(Index):
    name = 'forum'
    types = [PostDocumentType]


search.register(ForumIndex)
