#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.make_bdd_testadata
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Benjamin Wiegand.
    :copyright: (c) 2011-2017 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import division, print_function

import math
import os
import time
from datetime import datetime
from itertools import izip
from random import choice, randint

import django
from django.conf import settings
from jinja2.constants import LOREM_IPSUM_WORDS

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'development_settings'

from inyoka.forum.models import Forum, Post, Topic
from inyoka.ikhaya.models import Article, Category, Comment
from inyoka.planet.models import Blog
from inyoka.planet.tasks import sync
from inyoka.portal.user import Group, User
from inyoka.utils.captcha import generate_word
from inyoka.utils.terminal import ProgressBar, percentize, show
from inyoka.utils.text import increment_string
from inyoka.wiki.models import Page

settings.DEBUG = settings.DATABASE_DEBUG = False

MARKS = ('.', ';', '!', '?')
WORDS = LOREM_IPSUM_WORDS.split(' ')
NAME_WORDS = [w for w in WORDS if '\n' not in w]

groups = []
users = []
page_names = []
forums = []

GROUPS_COUNT = 3
FORUMS_COUNT = 2
MAX_TOPIC_COUNT = 10
MAX_TOPIC_POST_COUNT = 2
IKHAYA_CATEGORY_COUNT = 5
WIKI_PAGES_COUNT = 20
MAX_WIKI_REVISIONS = 5

BLOGS = {
}


def generate_names(count, func=lambda: choice(NAME_WORDS)):
    """Yields a bunch of unique names"""
    used = []
    for _ in range(count + 1):
        name = func()
        if name in used:
            name = '%s%s%d' % (generate_word(), name, randint(1, 100))
        if name in used:
            name = increment_string(name)
        used.append(name)
        yield name


def create_word(markup=True):
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


def generate_words(min_length=4, max_length=20, markup=True):
    words = []
    for i in range(randint(min_length, max_length)):
        word = create_word(markup)
        if i == 0:
            word = word.capitalize()
        words.append(word)
    return '%s%s' % (' '.join(words), choice(MARKS))


def sentences(min_length=5, max_length=35, markup=True):
    s_list = []
    nls = ['\n\n', '\n\n\n\n', '\n', '']
    for i in range(randint(min_length, max_length)):
        s_list.append(generate_words(markup) + choice(nls))
    return ' '.join(s_list)


def title():
    return u''.join(word for word in generate_words(2, 3, markup=False) if '\n' not in word)


def intro(markup=True):
    return sentences(min_length=3, max_length=10, markup=markup)


def random_time():
    return datetime.fromtimestamp(randint(0, math.floor(time.time())))


def make_groups():
    print('Creating groups')
    pb = ProgressBar(40)
    for percent, name in izip(percentize(GROUPS_COUNT), generate_names(GROUPS_COUNT)):
        groups.append(Group(name=name))
        groups[-1].save()
        pb.update(percent)
    show('\n')


def make_users():
    print('Creating users')
    pb = ProgressBar(40)
    registered_group = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
    username_list = ('bdd_user', 'banned', 'inactive', 'deleted')
    for percent, name in izip(percentize(len(username_list) - 1), username_list):
        u = User.objects.register_user(
            name, '%s@ubuntuusers.local' % name, 'test', False)
        u.date_joined = random_time()
        u.last_login = random_time()
        u.jabber = '%s@%s.local' % (create_word(markup=False), create_word(markup=False))
        u.icq = create_word(markup=False)[:16]
        u.msn = create_word(markup=False)
        u.aim = create_word(markup=False)
        u.signature = generate_words()
        u.occupation = create_word(markup=False)
        u.interests = create_word(markup=False)
        u.website = u'http://%s.de' % create_word(markup=False)

        if u.username == "banned":
            u.status = User.STATUS_BANNED
        if u.username == "bdd_user":
            u.status = User.STATUS_ACTIVE
        if u.username == 'inactive':
            u.status = User.STATUS_INACTIVE
        if u.username == 'deleted':
            u.status = User.STATUS_DELETED

        u.save()
        if u.status == 1:
            u.groups.add(registered_group)
        users.append(u)
        pb.update(percent)
    show('\n')


def make_forum():
    print('Creating forum test data')
    pb = ProgressBar(40)
    for percent, name in izip(percentize(FORUMS_COUNT), generate_names(FORUMS_COUNT, title)):
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
                p = Post(topic=t,
                         text=sentences(min_length=1, max_length=10),
                         author_id=author.id,
                         pub_date=random_time(),
                         position=0)
                p.save()
                t.first_post_id = p.pk
                t.save()
                for i in range(randint(1, MAX_TOPIC_POST_COUNT)):
                    p = Post(topic=t,
                             text=sentences(min_length=1, max_length=10),
                             position=i + 1,
                             author_id=choice(users).id,
                             pub_date=random_time())
                    p.save()
        pb.update(percent)

    # all about the wiki - forum (and discussions sub-forum)
    f = Forum(name=u'Rund ums Wiki', parent=None)
    f.save()
    forums.append(f)
    d = Forum(name=u'Diskussionen', slug=settings.WIKI_DISCUSSION_FORUM, parent=f)
    d.save()
    forums.append(d)
    show('\n')


def make_ikhaya():
    print('Creating ikhaya test data')
    pb = ProgressBar(40)
    for percent, name in izip(percentize(IKHAYA_CATEGORY_COUNT), generate_names(IKHAYA_CATEGORY_COUNT, title)):
        c = Category(name=name)
        c.save()
        for subject in generate_names(6, title):
            dt = random_time()
            a = Article(
                pub_date=dt.date(),
                pub_time=dt.time(),
                author_id=choice(users).id,
                subject=subject,
                category_id=c.pk,
                intro=intro(),
                text=sentences(),
                public=True,
                is_xhtml=False
            )
            a.save()
            for i in range(randint(0, 5)):
                text = sentences(min_length=1, max_length=5)
                if i > 0 and randint(0, 1) == 0:
                    text = '@%d: %s' % (randint(1, i), text)
                Comment(
                    article_id=a.id,
                    text=text,
                    author_id=choice(users).id,
                    pub_date=random_time()
                ).save()
        pb.update(percent)
    show('\n')


def make_wiki():
    print('Creating wiki pages')
    pb = ProgressBar(40)
    for percent, name in izip(percentize(len(page_names) - 1), page_names):
        p = Page.objects.create(name, sentences(min_length=10, max_length=20), choice(users), note=title())
        for i in range(randint(0, MAX_WIKI_REVISIONS)):
            text = sentences(min_length=10, max_length=20, markup=False)
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
    for percent, (name, (blogurl, feedurl)) in izip(percentize(len(BLOGS) - 1),
                                                    BLOGS.iteritems()):
        Blog(name=name, blog_url=blogurl, feed_url=feedurl, description=sentences(min_length=3, max_length=10)).save()
        pb.update(percent)

    sync()
    show('\n')


if __name__ == '__main__':
    django.setup()
    page_names = ['Startseite', 'Welcome'] + list(generate_names(WIKI_PAGES_COUNT))
    make_groups()
    make_users()
    make_wiki()
    make_ikhaya()
    make_forum()
    make_planet()
    print("created test data")
