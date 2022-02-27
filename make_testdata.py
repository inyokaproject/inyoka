#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.make_testadata
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Benjamin Wiegand.
    :copyright: (c) 2011-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


import math
import os
import time
from datetime import datetime

from random import choice, randint

import django
from django.conf import settings
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'development_settings'

django.setup()

from jinja2.constants import LOREM_IPSUM_WORDS

from inyoka.forum.models import Forum, Post, Topic
from inyoka.ikhaya.models import Article, Category, Comment
from inyoka.planet.models import Blog
from inyoka.planet.tasks import sync
from inyoka.portal.user import Group, User
from inyoka.utils.captcha import generate_word
from inyoka.utils.terminal import ProgressBar, percentize, show
from inyoka.utils.text import increment_string
from inyoka.wiki.models import Page

settings.DEBUG = settings.DATABASE_DEBUG = False  # for nice progressbar output ;)


MARKS = ('.', ';', '!', '?')
WORDS = LOREM_IPSUM_WORDS.split(' ')
NAME_WORDS = [w for w in WORDS if '\n' not in w]

groups = []
users = []
page_names = []
forums = []

GROUPS_COUNT = 3
USERS_COUNT = 15
FORUMS_COUNT = 2
MAX_TOPIC_COUNT = 10
MAX_TOPIC_POST_COUNT = 2
IKHAYA_CATEGORY_COUNT = 5
WIKI_PAGES_COUNT = 20
MAX_WIKI_REVISIONS = 5

BLOGS = {
    '[ENC]BladeXPs Blog': ('http://blog.stefan-betz.net/',
                           'http://blog.stefan-betz.net/categories/ubuntu/feed.atom'),
    'Martin Gräßlin': ('http://blog.martin-graesslin.com/blog/',
                       'http://blog.martin-graesslin.com/blog/?cat=6&feed=rss2'),
    'serenitys blog': ('http://beyondserenity.wordpress.com/',
                       'http://beyondserenity.wordpress.com/category/kde-oss-it/feed'),
    'Ikhaya': ('http://ubuntuusers.ikhaya.de',
               'http://ikhaya.ubuntuusers.de/feeds/full/10/')
}


def create_names(count, func=lambda: choice(NAME_WORDS)):
    """Yields a bunch of unique names"""
    used = []
    for _ in range(count + 1):
        name = func()
        if name in used:
            # use some random...
            name = '%s%s%d' % (generate_word(), name, randint(1, 100))
        if name in used:
            # now we need to increment that thingy...
            name = increment_string(name)
        used.append(name)
        yield name


def word(markup=True):
    word = choice(WORDS)
    modifiers = [
        lambda t: '[:%s:%s]' % (choice(page_names), t),
        "'''%s'''", "''%s''", '__%s__', '[http://ubuntuusers.de %s]']
    if markup:
        for modifier in modifiers:
            if randint(1, 50) == 1:
                if hasattr(modifier, '__call__'):
                    word = modifier(word)
                else:
                    word = modifier % word
                break
    return word


def words(min=4, max=20, markup=True):
    ws = []
    for i in range(randint(min, max)):
        w = word(markup)
        if i == 0:
            w = w.capitalize()
        ws.append(w)
    return '%s%s' % (' '.join(ws), choice(MARKS))


def sentences(min=5, max=35, markup=True):
    s_list = []
    nls = ['\n\n', '\n\n\n\n', '\n', '']
    for i in range(randint(min, max)):
        s_list.append(words(markup) + choice(nls))
    return ' '.join(s_list)


def title():
    return ''.join(w for w in words(2, 3, markup=False) if '\n' not in w)


def intro(markup=True):
    return sentences(min=3, max=10, markup=markup)


def randtime():
    return datetime.fromtimestamp(randint(0, math.floor(time.time())))


def make_groups():
    print('Creating groups')
    pb = ProgressBar(40)
    for percent, name in zip(percentize(GROUPS_COUNT), create_names(GROUPS_COUNT)):
        groups.append(Group(name=name))
        groups[-1].save()
        pb.update(percent)
    show('\n')


def make_users():
    print('Creating users')
    pb = ProgressBar(40)
    registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
    for percent, name in zip(percentize(USERS_COUNT), create_names(USERS_COUNT)):
        u = User.objects.register_user(
            name, '%s@ubuntuusers.local' % name, name, False)
        u.date_joined = randtime()
        u.last_login = randtime()
        u.groups.set(list(set(choice(groups) for _ in range(randint(0, 5)))))
        u.jabber = '%s@%s.local' % (word(markup=False), word(markup=False))
        u.icq = word(markup=False)[:16]
        u.msn = word(markup=False)
        u.aim = word(markup=False)
        u.signature = words()
        u.occupation = word(markup=False)
        u.interests = word(markup=False)
        u.website = 'http://%s.de' % word(markup=False)
        if not randint(0, 3):
            u.status = 0
        u.save()
        if u.status == 1:
            u.groups.add(registered_group)
        users.append(u)
        pb.update(percent)
    show('\n')


def make_forum():
    print('Creating forum test data')
    pb = ProgressBar(40)
    for percent, name in zip(percentize(FORUMS_COUNT), create_names(FORUMS_COUNT, title)):
        parent = None
        if randint(1, 6) != 6:
            try:
                parent = choice(forums)
            except IndexError:
                pass
        f = Forum(name=name, parent=parent)
        f.save()
        forums.append(f)
        if parent:
            for _ in range(randint(1, MAX_TOPIC_COUNT)):
                author = choice(users)
                t = Topic(title=title()[:100], author_id=author.id, forum=f)
                t.save()
                p = Post(topic=t, text=sentences(min=1, max=10), author_id=author.id, pub_date=randtime(), position=0)
                p.save()
                t.first_post_id = p.id
                t.save()
                for i in range(randint(1, MAX_TOPIC_POST_COUNT)):
                    p = Post(topic=t, text=sentences(min=1, max=10), position=i + 1, author_id=choice(users).id,
                             pub_date=randtime())
                    p.save()
        pb.update(percent)
    # all about the wiki - forum (and diskussions subforum)
    f = Forum(name='Rund ums Wiki', parent=None)
    f.save()
    forums.append(f)
    d = Forum(name='Diskussionen', slug=settings.WIKI_DISCUSSION_FORUM, parent=f)
    d.save()
    forums.append(d)
    show('\n')


def make_ikhaya():
    print('Creating ikhaya test data')
    pb = ProgressBar(40)
    for percent, name in zip(percentize(IKHAYA_CATEGORY_COUNT), create_names(IKHAYA_CATEGORY_COUNT, title)):
        c = Category(name=name)
        c.save()
        for subject in create_names(6, title):
            dt = randtime()
            a = Article(
                pub_date=dt.date(),
                pub_time=dt.time(),
                author_id=choice(users).id,
                subject=subject,
                category_id=c.id,
                intro=intro(),
                text=sentences(),
                public=True,
                is_xhtml=False
            )
            a.save()
            for i in range(randint(0, 5)):
                text = sentences(min=1, max=5)
                if i > 0 and randint(0, 1) == 0:
                    text = '@%d: %s' % (randint(1, i), text)
                Comment(
                    article_id=a.id,
                    text=text,
                    author_id=choice(users).id,
                    pub_date=randtime()
                ).save()
        pb.update(percent)
    show('\n')


def make_wiki():
    print('Creating wiki pages')
    pb = ProgressBar(40)
    for percent, name in zip(percentize(len(page_names) - 1), page_names):
        p = Page.objects.create(name, sentences(min=10, max=20), choice(users), note=title())
        for i in range(randint(0, MAX_WIKI_REVISIONS)):
            text = sentences(min=10, max=20, markup=False)
            user = choice(users)
            note = title()
            deleted = True if randint(0, 50) == 42 else False
            p.edit(text=text, user=user, note=note, deleted=deleted)
            p.save()
        pb.update(percent)
    show('\n')


def make_planet():
    print("Creating planet test data")
    pb = ProgressBar(40)
    for percent, (name, (blogurl, feedurl)) in zip(percentize(len(BLOGS) - 1),
                                                    iter(BLOGS.items())):
        Blog(name=name, blog_url=blogurl, feed_url=feedurl, description=sentences(min=3, max=10)).save()
        pb.update(percent)
    # Syncing once
    sync()
    show('\n')


if __name__ == '__main__':
    page_names = ['Startseite', 'Welcome'] + list(create_names(WIKI_PAGES_COUNT))
    make_groups()
    make_users()
    make_wiki()
    make_ikhaya()
    make_forum()
    make_planet()
    print("created test data")
