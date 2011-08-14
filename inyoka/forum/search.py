#-*- coding: utf-8 -*-
from inyoka.utils.search import search, Index, DocumentType


class TopicType(DocumentType):
    name = 'topic'
    fields = ('title', 'slug', 'solved', 'locked',
              'ubuntu_version', 'ubuntu_distro')



class ForumIndex(Index):
    name = 'forum'
    types = [TopicType]


search.register(ForumIndex)
