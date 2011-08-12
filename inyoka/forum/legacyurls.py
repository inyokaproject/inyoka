# -*- coding: utf-8 -*-
"""
    inyoka.forum.legacyurls
    ~~~~~~~~~~~~~~~~~~~~~~~

    Forum legacy URL support.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.forum.models import Forum, Topic
from inyoka.forum.constants import POSTS_PER_PAGE
from inyoka.utils.urls import href
from inyoka.utils.legacyurls import LegacyDispatcher
from inyoka.portal.user import User


legacy = LegacyDispatcher()
test_legacy_url = legacy.tester

FOLDER_MAPPING = {
    'inbox': 'inbox',
    'sentbox': 'sent',
    'outbox': 'sent',
    'savebox': 'archive',
}


@legacy.url(r'^/viewforum\.php/?$')
@legacy.url(r'^/forum/(\d+)(?:/(\d+))?/?$')
@legacy.url(r'^/category/(\d+)/?$')
def get_old_forum_url(args, match, forum_id=None, offset=None):
    if forum_id is None:
        try:
            forum_id = args['f']
        except KeyError:
            return
    try:
        forum_id = int(forum_id)
    except ValueError:
        return
    forum = Forum.objects.get(forum_id)
    if not forum:
        return
    if offset is None:
        page = 1
    else:
        try:
            offset = int(offset)
        except ValueError:
            return
        page = (offset / POSTS_PER_PAGE) + 1
    if forum.parent_id is None:
        if page <= 1:
            return href('forum', 'category', forum.slug)
        return href('forum', 'category', forum.slug, page)
    if page <= 1:
        return href('forum', 'forum', forum.slug)
    return href('forum', 'forum', forum.slug, page)


@legacy.url(r'^/viewtopic\.php/?$')
@legacy.url(r'^/topic/([0-9]+)(?:/([0-9]+))?(?:/print)?/?$')
def get_old_topic_url(args, match, topic_id=None, offset=None):
    if topic_id is None:
        try:
            topic_id = int(args['t'])
        except (KeyError, ValueError):
            try:
                post_id = int(args['p'])
            except (KeyError, ValueError):
                return
            return href('forum', 'post', post_id)
    topic = Topic.objects.get(id=topic_id)
    if not topic:
        return
    if offset is None:
        try:
            page = int(args['start'])
        except KeyError:
            page = 1
        except ValueError:
            return
    else:
        page = (int(offset) / POSTS_PER_PAGE) + 1
    kwargs = {}
    if 'vote' in args and args['vote'] == 'viewresult':
        kwargs['action'] = 'vote_results'
    if page <= 1:
        return href('forum', 'topic', topic.slug, **kwargs)
    else:
        return href('forum', 'topic', topic.slug, page, **kwargs)


@legacy.url(r'^/index(\.php)?/?$')
def index(args, *other):
    return href('forum')


@legacy.url(r'^/forum/(\d+)/(newtopic|watch|unwatch|mark_read)/?$')
def forum_actions(args, match, forum_id, action):
    forum = Forum.objects.get(int(forum_id))
    if not forum:
        return

    ACTIONS = {
        'watch': 'subscribe',
        'unwatch': 'unsubscribe',
        'mark_read': 'markread',
    }
    try:
        action = ACTIONS[action]
    except KeyError:
        pass # if not in ACTIONS: new action == old action
    return href('forum', 'forum', forum.slug, action)


@legacy.url(r'^/topic/(\d+)/(report|reply|watch|unwatch|solved|unsolved|'
            r'next|previous)/?$')
def topic_actions(args, match, topic_id, action):
    topic = Topic.objects.get(id=topic_id)
    if not topic:
        return
    ACTIONS = {
        'watch': 'subscribe',
        'unwatch': 'unsubscribe',
        'solved': 'solve',
        'unsolved': 'unsolve',
    }
    try:
        action = ACTIONS[action]
    except KeyError:
        pass # if not in ACTIONS: new action == old action
    return href('forum', 'topic', topic.slug, action)


@legacy.url(r'^/topic/\d+/quote/(\d+)/?$')
def quote(args, match, post_id):
    try:
        return href('forum', 'post', int(post_id), 'quote')
    except ValueError:
        return


@legacy.url(r'^/go(:?to)?(:?\.php)?/?$')
def goto(args, match, *_):
    if 'post' in args and args['post'].isdigit():
        return href('forum', 'post', args['post'])
    if 'wikipage' in args:
        return href('wiki', args['wikipage'])


@legacy.url(r'^/groups(:?/(.+))/?$')
def groups(args, match, group=None):
    return href('portal', 'group', group)


@legacy.url(r'^/viewonline/?$')
def whoisonline(args, match):
    return href('portal', 'whoisonline')


@legacy.url(r'^/privmsg\.php/?$')
def privmsg(args, match):
    if 'mode' in args and args['mode'] == 'post':
        try:
            user = User.objects.get(id=args['u'])
            if user is None:
                return
            return href('portal', 'privmsg', 'new', user.username)
        except KeyError:
            return
    elif 'folder' in args:
        return href('portal', 'privmsg', FOLDER_MAPPING[args['folder']])
    else:
        return href('portal', 'privmsg')


@legacy.url(r'^/privmsg/new/?$')
def privmsg_new(args, match):
    if 'u' in args:
        try:
            user = User.objects.get(id=args['u'])
            if user is None:
                return
            return href('portal', 'privmsg', 'new', user.username)
        except KeyError:
            return
    else:
        return href('portal', 'privmsg', 'new')


@legacy.url(r'^/privmsg/folder/([^/]+)/view/(\d+)/?$')
def privmsg_folder(args, match, folder, privmsg_id=None):

    try:
        if 'mode' in args and args['mode'] == 'read':
            return href('portal', 'privmsg', FOLDER_MAPPING[folder], int(args['p']))
        else:
            return href('portal', 'privmsg', FOLDER_MAPPING[folder], privmsg_id)
    except (KeyError, ValueError):
        return


@legacy.url('^/privmsg/(:?reply|quote)/(\d+)/?$')
def privmsg_reply(args, match, privmsg_id):
    try:
        return href('portal', 'privmsg', 'new', reply_to=int(privmsg_id))
    except ValueError:
        return


@legacy.url('^/profile/?$')
def profile(args, match):
    if 'mode' not in args:
        return href('portal', 'usercp')
    elif args['mode'] == 'sendpassword':
        return href('portal', 'lost_password')
    elif args['mode'] == 'viewprofile':
        try:
            user = User.objects.get(id=int(args['u']))
            if user is None:
                return
            return href('portal', 'user', user.username)
        except (KeyError, ValueError):
            return
    elif args['mode'] == 'email':
        try:
            user = User.objects.get(id=int(args['u']))
            if user is None:
                return
            return href('portal', 'user', user.username)
        except (KeyError, ValueError):
            return


@legacy.url('^/register/?$')
def register(args, match):
    return href('portal', 'register')


@legacy.url('^/login/?$')
def login(args, match):
    return href('portal', 'login')


@legacy.url('^/logout/?$')
def logout(args, match):
    return href('portal', 'logout')

@legacy.url('^/memberlist/?$')
def memberlist(args, match):
    return href('portal', 'users')

@legacy.url('^/profile\.php/?$')
def activation(args, match):
    if 'mode' in args and args['mode'] == 'activate' and 'u' in args:
        try:
            user = User.objects.get(id=int(args['u']))
        except User.DoesNotExist:
            return
        return href('portal', 'register', 'resend', user.username, legacy=True)

@legacy.url(r'^/search/(unfixed|newposts|egowatchnotified|egowatch|'
            r'egosearch|unanswered|last\d+)/')
def specialsearches(args, match, search_id):
    if search_id == 'egowatch':
        return href('portal', 'usercp', 'subscriptions')
    if search_id == 'egowatchnotified':
        return href('portal', 'usercp', 'subscriptions', 'notified')
    if search_id == 'unfixed':
        search_id = 'unsolved'
    return href('forum', search_id)
