# -*- coding: utf-8 -*-
"""
    inyoka.forum.views
    ~~~~~~~~~~~~~~~~~~

    The views for the forum.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from itertools import groupby
from operator import attrgetter

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q, Count
from django.http import Http404, HttpResponseRedirect
from django.utils.text import Truncator
from django.utils.translation import ugettext as _

from inyoka.forum.acl import (
    CAN_MODERATE,
    CAN_READ,
    check_privilege,
    filter_invisible,
    get_forum_privileges,
    get_privileges,
    have_privilege,
)
from inyoka.forum.constants import POSTS_PER_PAGE, TOPICS_PER_PAGE
from inyoka.forum.forms import (
    AddAttachmentForm,
    AddPollForm,
    EditForumForm,
    EditPostForm,
    MoveTopicForm,
    NewTopicForm,
    ReportListForm,
    ReportTopicForm,
    SplitTopicForm,
)
from inyoka.forum.models import (
    Attachment,
    Forum,
    Poll,
    PollOption,
    PollVote,
    Post,
    PostRevision,
    Topic,
    WelcomeMessage,
    mark_all_forums_read,
)
from inyoka.forum.notifications import (
    send_deletion_notification,
    send_discussion_notification,
    send_edit_notifications,
    send_newtopic_notifications,
)
from inyoka.markup import RenderContext, parse
from inyoka.markup.parsertools import flatten_iterator
from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.portal.utils import (
    abort_access_denied,
    require_permission,
    simple_check_login,
)
from inyoka.utils.database import get_simplified_queryset
from inyoka.utils.dates import format_datetime
from inyoka.utils.feeds import AtomFeed, atom_feed
from inyoka.utils.flash_confirmation import confirm_action
from inyoka.utils.forms import clear_surge_protection
from inyoka.utils.generic import trigger_fix_errors_message
from inyoka.utils.http import (
    AccessDeniedResponse,
    does_not_exist_is_404,
    templated,
)
from inyoka.utils.notification import (
    notify_about_subscription,
    send_notification,
)
from inyoka.utils.pagination import Pagination
from inyoka.utils.storage import storage
from inyoka.utils.templating import render_template
from inyoka.utils.text import normalize_pagename
from inyoka.utils.urls import href, is_safe_domain, url_for
from inyoka.wiki.models import Page
from inyoka.wiki.utils import quote_text


@templated('forum/index.html')
def index(request, category=None):
    """
    Return all forums without parents.
    These forums are treated as categories but not as real forums.
    """

    is_index = category is None
    forums = Forum.objects.get_forums_filtered(request.user, sort=True)

    if category:
        category = Forum.objects.get_cached(category)
        if not category or category.parent is not None:
            raise Http404()
        category = category
        categories = [category]

        wmsg = category.find_welcome(request.user)
        if wmsg is not None:
            return welcome(request, wmsg.slug, request.path)
    else:
        categories = tuple(forum for forum in forums if forum.parent_id is None)

    hidden_categories = []
    if request.user.is_authenticated():
        hidden_categories.extend(request.user.settings.get(
            'hidden_forum_categories', ())
        )

    forum_hierarchy = []
    toplevel_last_post_ids = []
    for obj in categories:
        category_forums = []
        for forum in obj.filter_children(forums):
            category_forums.append((forum, forum.filter_children(forums)))
            toplevel_last_post_ids.append(forum.last_post_id)
        forum_hierarchy.append((obj, category_forums))

    last_post_map = Post.objects.last_post_map(toplevel_last_post_ids)

    return {
        'categories': categories,
        'is_index': is_index,
        'hidden_categories': hidden_categories,
        'forum_hierarchy': forum_hierarchy,
        'forum': category,
        'last_posts': last_post_map,
    }


@templated('forum/forum.html')
def forum(request, slug, page=1):
    """
    Return a single forum to show a topic list.
    """
    forum = Forum.objects.get_cached(slug)
    # if the forum is a category we raise Http404. Categories have
    # their own url at /category.
    if not forum or forum.parent_id is None:
        raise Http404()

    privs = get_privileges(request.user, [forum] + forum.children)
    if not check_privilege(privs[forum.pk], 'read'):
        return abort_access_denied(request)

    fmsg = forum.find_welcome(request.user)
    if fmsg is not None:
        return welcome(request, fmsg.slug, request.path)

    topic_ids = Topic.objects.filter(forum=forum)\
                             .values_list('id', flat=True)\
                             .order_by('-sticky', '-last_post')
    pagination = Pagination(request, topic_ids, page, TOPICS_PER_PAGE,
                            url_for(forum), total=forum.topic_count.value())

    subforums = filter_invisible(request.user, forum.children, perm=privs)
    last_post_ids = map(lambda f: f.last_post_id, subforums)
    last_post_map = Post.objects.last_post_map(last_post_ids)

    qs = Topic.objects.prepare_for_overview(list(pagination.get_queryset()))

    # FIXME: Filter topics with no last_post or first_post
    topics = [topic for topic in qs if topic.first_post and topic.last_post]

    if not check_privilege(privs[forum.pk], 'moderate'):
        topics = [topic for topic in topics if not topic.hidden]

    for topic in topics:
        topic.forum = forum

    context = {
        'forum': forum,
        'subforums': subforums,
        'last_posts': last_post_map,
        'is_subscribed': Subscription.objects.user_subscribed(request.user, forum),
        'can_moderate': check_privilege(privs[forum.pk], 'moderate'),
        'can_create': check_privilege(privs[forum.pk], 'create'),
        'supporters': forum.get_supporters(),
        'topics': topics,
        'pagination': pagination,
    }
    return context


@templated('forum/topic.html')
def viewtopic(request, topic_slug, page=1):
    """
    Shows a topic, the posts are paginated.
    If the topic has a `hidden` flag, the user gets a nice message that the
    topic is deleted and is redirected to the topic's forum.  Moderators can
    see these topics.
    """
    topic = Topic.objects.get(slug=topic_slug)
    privileges = get_forum_privileges(request.user, topic.cached_forum())

    if not check_privilege(privileges, 'read'):
        return abort_access_denied(request)

    if topic.hidden:
        if check_privilege(privileges, 'moderate'):
            messages.info(request, _(u'This topic is not visible for regular users.'))
        else:
            return abort_access_denied(request)

    fmsg = topic.cached_forum().find_welcome(request.user)
    if fmsg is not None:
        return welcome(request, fmsg.slug, request.path)

    topic.touch()

    polls = None
    if topic.has_poll:
        polls = Poll.objects.select_related('options') \
                            .filter(topic=topic).all()

        if request.method == 'POST' and 'vote' in request.POST:
            if not check_privilege(privileges, 'vote'):
                return abort_access_denied(request)
            # the user participated in a poll
            for poll in polls:
                # get the votes for every poll in this topic
                if poll.multiple_votes:
                    votes = request.POST.getlist('poll_%s' % poll.id)
                else:
                    vote = request.POST.get('poll_%s' % poll.id)
                    votes = vote and [vote] or []
                if votes:
                    if poll.participated:
                        continue
                    elif poll.ended:
                        messages.error(request, _(u'The poll already ended.'))
                        continue
                    poll.votings.add(PollVote(voter=request.user))
                    poll.options.filter(id__in=votes) \
                                .update(votes=F('votes') + 1)

    post_ids = Post.objects.filter(topic=topic) \
                           .values_list('id', flat=True)
    pagination = Pagination(request, post_ids, page, POSTS_PER_PAGE, url_for(topic),
                            total=topic.post_count.value(), rownum_column='position')

    post_ids = list(pagination.get_queryset())
    posts = Post.objects.filter(id__in=post_ids) \
                        .order_by('position') \
                        .select_related('author') \
                        .prefetch_related('attachments')

    # assign the current topic to the posts to prevent
    # extra queries in check_ownpost_limit.
    for p in posts:
        p.topic = topic

    # clear read status and subscriptions
    if request.user.is_authenticated():
        topic.mark_read(request.user)

    subscribed = Subscription.objects.user_subscribed(request.user, topic,
        ('forum', 'topic'), clear_notified=True)

    team_icon = storage['team_icon'] or None

    if team_icon:
        team_icon = href('media', team_icon)

    can_mod = check_privilege(privileges, 'moderate')
    can_reply = check_privilege(privileges, 'reply')
    can_vote = check_privilege(privileges, 'vote')

    def can_edit(post):
        return (
            post.author_id == request.user.id and can_reply and
            post.check_ownpost_limit('edit')
        )

    def can_delete(post):
        return (
            can_reply and post.author_id == request.user.id
            and post.check_ownpost_limit('delete')
        )

    voted_all = not (polls and bool([True for p in polls if p.can_vote]))

    marked_split_posts = request.session.get('_split_post_ids', [])
    if marked_split_posts and topic.slug in marked_split_posts:
        marked_split_posts = marked_split_posts[topic.slug]

    return {
        'topic': topic,
        'forum': topic.cached_forum(),
        'posts': posts,
        'is_subscribed': subscribed,
        'pagination': pagination,
        'polls': polls,
        'show_vote_results': request.GET.get('action') == 'vote_results',
        'voted_all': voted_all,
        'can_moderate': can_mod,
        'can_edit': can_edit,
        'can_reply': can_reply,
        'can_vote': can_vote,
        'can_delete': can_delete,
        'team_icon_url': team_icon,
        'discussions': Page.objects.discussions(topic),
        'marked_split_posts': marked_split_posts
    }


def handle_polls(request, topic, poll_ids):
    """Handle creation of polls.

    This function is called from :func:`edit` to handle the creation
    of polls.  It can happen that a poll with no topic_id is created,
    this is a result of the inline-editing feature so that we have no
    chance to properly delete those poll objects once the user
    canceled his action.

    :param request: The current request
    :param topic: The current topic object.  Can be `None`.
    :param poll_ids: A list of integers representing the existing poll ids
                     to bind and show them properly.
    """
    poll_form = AddPollForm(('add_poll' in request.POST or
        'add_option' in request.POST) and request.POST or None)
    poll_options = request.POST.getlist('options') or ['', '']

    if 'add_poll' in request.POST and poll_form.is_valid():
        d = poll_form.cleaned_data
        now = datetime.utcnow()
        end_time = (d['duration'] and now + timedelta(days=d['duration'])
                    or None)
        poll = Poll(topic=topic, question=d['question'],
                    multiple_votes=d['multiple'],
                    start_time=now, end_time=end_time)
        poll.save()
        for name in poll_options:
            option = PollOption(name=name, poll=poll)
            option.save()
        poll_form = AddPollForm()
        poll_options = ['', '']
        messages.success(request, _(u'The poll “%(poll)s” was added.') % {'poll': poll.question})
        poll_ids.append(poll.id)
    elif 'add_option' in request.POST:
        poll_options.append('')

    elif 'delete_poll' in request.POST:
        try:
            poll = Poll.objects.get(id=int(request.POST['delete_poll']),
                                    topic=topic)
        except Poll.DoesNotExist:
            pass
        else:
            messages.info(
                request,
                _(u'The poll “%(poll)s” was removed.') % {'poll': poll.question}
            )
            if topic is not None:
                topic.has_poll = Poll.objects \
                    .filter(Q(topic=topic) & ~Q(id=poll.id)) \
                    .exists()
            poll.delete()
    query = Poll.objects.filter(topic=topic)
    if poll_ids:
        query = query.filter(id__in=poll_ids)
    polls = query.all() if (poll_ids or topic) else []
    return poll_form, poll_options, polls


def handle_attachments(request, post, att_ids):
    """Handle creation of attachments.

    This function is called by :func:`edit` to handle the creation of attachments.

    :param request: current request.
    :param post: The current post that gets edited.  Can be `None`.
    :param att_ids: A list of integers representing existing attachments.
    """
    # check for post = None to be sure that the user can't "hijack"
    # other attachments.
    if att_ids:
        attachments = list(Attachment.objects.filter(id__in=att_ids).all())
    else:
        attachments = []
    if 'attach' in request.POST:
        attach_form = AddAttachmentForm(request.POST, request.FILES)
    else:
        attach_form = AddAttachmentForm()

    if 'attach' in request.POST:
        # the user uploaded a new attachment
        if attach_form.is_valid():
            d = attach_form.cleaned_data
            att_name = d.get('filename') or d['attachment'].name
            attachment = Attachment.create(
                att_name, d['attachment'],
                request.FILES['attachment'].content_type,
                attachments, override=d['override'],
                comment=d['comment']
            )
            if not attachment:
                messages.error(request, _(u'The attachment “%(attachment)s” does already exist.')
                               % {'attachment': att_name})
            else:
                attachments.append(attachment)
                att_ids.append(attachment.id)
                messages.success(request, _(u'The attachment “%(attachment)s” was added '
                                 'successfully.') % {'attachment': att_name})

    elif 'delete_attachment' in request.POST:
        id = int(request.POST['delete_attachment'])
        matching_attachments = filter(lambda a: a.id == id, attachments)
        if not matching_attachments:
            messages.info(request, _(u'The attachment with the ID “%(id)d” does not exist.')
                          % {'id': id}, False)
        else:
            attachment = matching_attachments[0]
            attachment.delete()
            attachments.remove(attachment)
            if attachment.id in att_ids:
                att_ids.remove(attachment.id)
            messages.info(request, _(u'The attachment “%(attachment)s” was deleted.')
                          % {'attachment': attachment.name}, False)
    return attach_form, attachments


@templated('forum/edit.html')
def edit(request, forum_slug=None, topic_slug=None, post_id=None,
         quote_id=None, page_name=None):
    """
    This function allows the user to create a new topic which is created in
    the forum `slug` if `slug` is a string.
    Else a new discussion for the wiki article `article` is created inside a
    special forum that contains wiki discussions only (see the
    WIKI_DISCUSSION_FORUM setting).  It's title is set to the wiki article's
    name.
    When creating a new topic, the user has the choice to upload files bound
    to this topic or to create one or more polls.
    """
    post = topic = forum = quote = posts = discussions = None
    newtopic = firstpost = False
    attach_form = None
    attachments = []
    preview = None
    page = None

    if settings.FORUM_DISABLE_POSTING:
        messages.error(request, _('Post functionality is currently disabled.'))
        return HttpResponseRedirect(href('forum'))

    if page_name:
        norm_page_name = normalize_pagename(page_name)
        try:
            page = Page.objects.get(name=norm_page_name)
        except Page.DoesNotExist:
            messages.error(request, _(u'The article “%(article)s” does not exist. However, you '
                           'can create it now.') % {'article': norm_page_name})
            return HttpResponseRedirect(href('wiki', norm_page_name))
        forum_slug = settings.WIKI_DISCUSSION_FORUM
        messages.info(
            request, _(
                u'No discussion is linked yet to the article “%(article)s”. '
                u'You can create a discussion now or <a href="%(link)s">link '
                u'an existing topic</a> to the article.'
            ) % {
                'article': page_name,
                'link': href('wiki', norm_page_name, 'discussion')
            }
        )
    if topic_slug:
        topic = Topic.objects.get(slug=topic_slug)
        forum = topic.forum
    elif forum_slug:
        forum = Forum.objects.get_cached(slug=forum_slug)
        if not forum or not forum.parent_id:
            raise Http404()
        newtopic = firstpost = True
    elif post_id:
        post = Post.objects.get(id=int(post_id))
        locked = post.lock(request)
        if locked:
            messages.error(request,
                _(u'This post is currently beeing edited by “%(user)s”!')
                % {'user': locked})
        topic = post.topic
        forum = topic.forum
        firstpost = post.id == topic.first_post_id
    elif quote_id:
        quote = Post.objects.select_related('topic', 'author') \
                            .get(id=int(quote_id))
        topic = quote.topic
        forum = topic.forum

    # Get the privileges here, because we need to know if the user requires
    # antispam measures
    privileges = get_forum_privileges(request.user, forum)
    needs_spam_check = True
    if request.user.post_count.value(default=0) >= settings.INYOKA_SPAM_DETECT_LIMIT:
        # Exclude very active users.
        needs_spam_check = False
    elif check_privilege(privileges, 'moderate') or post and post.pk:
        # Exclude moderators for the current forum from spam checks
        # as well as already existing posts
        needs_spam_check = False
    else:
        anonymous_privileges = get_forum_privileges(User.objects.get_anonymous_user(), forum)
        if not check_privilege(anonymous_privileges, 'read'):
            # Don't require spam checks for not publicly readable forums
            needs_spam_check = False

    if newtopic:
        form = NewTopicForm(
            force_version=forum.force_version,
            needs_spam_check=needs_spam_check,
            request=request,
            data=request.POST or None,
            initial={
                'text': forum.newtopic_default_text,
                'title': page and norm_page_name or '',
            },
        )
    elif quote:
        form = EditPostForm(
            is_first_post=firstpost,
            needs_spam_check=needs_spam_check,
            request=request,
            data=request.POST or None,
            initial={
                'text': quote_text(
                    quote.text, quote.author, 'post:%s:' % quote.id
                ) + '\n',
            }
        )
    else:
        form = EditPostForm(
            is_first_post=firstpost,
            needs_spam_check=needs_spam_check,
            request=request,
            data=request.POST or None,
        )

    if request.method == 'POST' and check_privilege(privileges, 'moderate'):
        # Disable surge protection for moderators
        form.surge_protection_timeout = None

    if request.method == 'POST' and check_privilege(privileges, 'moderate'):
        # Disable surge protection for moderators
        form.surge_protection_timeout = None

    # check privileges
    if post:
        if (topic.locked or topic.hidden or post.hidden) and \
           not check_privilege(privileges, 'moderate'):
            messages.error(request, _(u'You cannot edit this post.'))
            post.unlock()
            return HttpResponseRedirect(href('forum', 'topic', post.topic.slug,
                                        post.page))
        if not (check_privilege(privileges, 'moderate') or
                (post.author.id == request.user.id and
                 check_privilege(privileges, 'reply') and
                 post.check_ownpost_limit('edit'))):
            messages.error(request, _(u'You cannot edit this post.'))
            post.unlock()
            return HttpResponseRedirect(href('forum', 'topic', post.topic.slug,
                                             post.page))
    elif topic:
        if topic.hidden:
            if not check_privilege(privileges, 'moderate'):
                messages.error(request,
                    _(u'You cannot reply in this topic because it was '
                      u'deleted by a moderator.'))
                return HttpResponseRedirect(url_for(topic))
        elif topic.locked:
            if not check_privilege(privileges, 'moderate'):
                messages.error(request,
                    _(u'You cannot reply to this topic because '
                      u'it was locked.'))
                return HttpResponseRedirect(url_for(topic))
            else:
                messages.error(request,
                    _(u'You are replying to a locked topic. '
                      u'Please note that this may be considered as impolite!'))
        elif quote and quote.hidden:
            if not check_privilege(privileges, 'moderate'):
                return abort_access_denied(request)
        else:
            if not check_privilege(privileges, 'reply'):
                return abort_access_denied(request)
    else:
        if not check_privilege(privileges, 'create'):
            return abort_access_denied(request)

    # the user has canceled the action
    if request.method == 'POST' and request.POST.get('cancel'):
        url = href('forum')
        if forum_slug:
            url = href('forum', 'forum', forum.slug)
        elif topic_slug:
            url = href('forum', 'topic', topic.slug)
        elif post_id:
            url = href('forum', 'post', post.id)
            post.unlock()
        return HttpResponseRedirect(url)

    # Clear surge protection to avoid multi-form hickups.
    clear_surge_protection(request, form)

    # Handle polls
    poll_ids = map(int, filter(bool, request.POST.get('polls', '').split(',')))
    poll_form = poll_options = polls = None
    if (newtopic or firstpost) and check_privilege(privileges, 'create_poll'):
        poll_form, poll_options, polls = handle_polls(request, topic, poll_ids)

    # handle attachments
    att_ids = map(int, filter(bool,
        request.POST.get('attachments', '').split(',')
    ))
    if check_privilege(privileges, 'upload'):
        attach_form, attachments = handle_attachments(request, post, att_ids)

    # the user submitted a valid form
    if 'send' in request.POST and form.is_valid():
        d = form.cleaned_data

        is_spam_post = form._spam and not form._spam_discard

        if not post:  # not when editing an existing post
            doublepost = Post.objects \
                .filter(author=request.user, text=d['text'],
                        pub_date__gt=(datetime.utcnow() - timedelta(0, 300)))
            if not newtopic:
                doublepost = doublepost.filter(topic=topic)
            try:
                doublepost = doublepost.select_related('topic').all()[0]
            except IndexError:
                pass
            else:
                messages.info(request,
                    _(u'This topic was already created. Please think about '
                      u'editing your topic before creating a new one.'))
                return HttpResponseRedirect(url_for(doublepost.topic))

        if not topic and newtopic or firstpost:
            if not topic and newtopic:
                topic = Topic(forum=forum, author=request.user)
            topic.title = d['title']
            if topic.ubuntu_distro != d.get('ubuntu_distro')\
               or topic.ubuntu_version != d.get('ubuntu_version'):
                topic.ubuntu_distro = d.get('ubuntu_distro')
                topic.ubuntu_version = d.get('ubuntu_version')
            if check_privilege(privileges, 'sticky'):
                topic.sticky = d.get('sticky', False)

            topic.save()
            topic.forum.invalidate_topic_cache()

            if check_privilege(privileges, 'create_poll'):
                for poll in polls:
                    topic.polls.add(poll)
                topic.has_poll = bool(polls)
                topic.save()

        if not post:
            post = Post(topic=topic, author_id=request.user.id)
            # TODO: Move this somehow to model to ease unittesting!
            if newtopic:
                post.position = 0

        # If there are attachments, we need to get a post id before we render
        # the text in order to parse the ``Bild()`` macro during first save. We
        # can set the ``has_attachments`` attribute lazily because the post is
        # finally saved in ``post.edit()``.
        if attachments:
            post.has_attachments = True
            if not post.id:
                post.save()
            Attachment.update_post_ids(att_ids, post)
        else:
            post.has_attachments = False

        post.edit(d['text'])

        if is_spam_post:
            post.mark_spam(report=True, update_akismet=False)

        if not is_spam_post:
            if newtopic:
                send_newtopic_notifications(request.user, post, topic, forum)
            elif not post_id:
                send_edit_notifications(request.user, post, topic, forum)
        if page:
            # the topic is a wiki discussion, bind it to the wiki
            # page and send notifications.
            page.topic = topic
            page.save()
            if not is_spam_post:
                send_discussion_notification(request.user, page)

        if not is_spam_post:
            subscribed = Subscription.objects.user_subscribed(request.user, topic)
            if request.user.settings.get('autosubscribe', True) and not subscribed and not post_id:
                subscription = Subscription(user=request.user, content_object=topic)
                subscription.save()

        messages.success(request, _(u'The post was saved successfully.'))
        if newtopic:
            return HttpResponseRedirect(url_for(post.topic))
        else:
            post.unlock()
            return HttpResponseRedirect(url_for(post))

    # the user wants to see a preview
    elif 'preview' in request.POST:
        ctx = RenderContext(request, forum_post=post)
        tt = request.POST.get('text', '')
        preview = parse(tt).render(ctx, 'html')

    # the user is going to edit an existing post/topic
    elif post:
        form = EditPostForm(
            is_first_post=firstpost,
            needs_spam_check=needs_spam_check,
            request=request,
            data=request.POST or None,
            initial={
                'title': topic.title,
                'ubuntu_distro': topic.ubuntu_distro,
                'ubuntu_version': topic.ubuntu_version,
                'sticky': topic.sticky,
                'text': post.text,
            }
        )
        if not attachments:
            attachments = Attachment.objects.filter(post=post)

    if not newtopic:
        max = topic.post_count.value()
        posts = topic.posts.select_related('author') \
                           .filter(hidden=False, position__gt=max - 15) \
                           .order_by('-position')
        discussions = Page.objects.filter(topic=topic)

    return {
        'form': form,
        'poll_form': poll_form,
        'options': poll_options,
        'polls': polls,
        'post': post,
        'forum': forum,
        'topic': topic,
        'preview': preview,
        'isnewtopic': newtopic,
        'isfirstpost': firstpost,
        'can_attach': check_privilege(privileges, 'upload'),
        'can_create_poll': check_privilege(privileges, 'create_poll'),
        'can_moderate': check_privilege(privileges, 'moderate'),
        'can_sticky': check_privilege(privileges, 'sticky'),
        'attach_form': attach_form,
        'attachments': list(attachments),
        'posts': posts,
        'storage': storage,
        'discussions': discussions,
    }


@confirm_action(message=_(u'Do you want to (un)lock the topic?'),
                confirm=_(u'(Un)lock'), cancel=_(u'Cancel'))
@simple_check_login
def change_lock_status(request, topic_slug, solved=None, locked=None):
    return change_status(request, topic_slug, solved, locked)


@simple_check_login
def change_status(request, topic_slug, solved=None, locked=None):
    """Change the status of a topic and redirect to it"""
    topic = Topic.objects.get(slug=topic_slug)
    if not have_privilege(request.user, topic.forum, CAN_READ):
        abort_access_denied(request)
    if solved is not None:
        topic.solved = solved
        topic.save()
        if solved:
            msg = _(u'The topic was marked as solved.')
        else:
            msg = _(u'The topic was marked as unsolved.')
        messages.success(request, msg)
    if locked is not None:
        if not have_privilege(request.user, topic.forum, CAN_MODERATE):
            return AccessDeniedResponse()
        topic.locked = locked
        topic.save()
        if locked:
            msg = _(u'The topic was locked.')
        else:
            msg = _(u'The topic was unlocked.')
        messages.info(request, msg)
    topic.forum.invalidate_topic_cache()

    return HttpResponseRedirect(url_for(topic))


def _generate_subscriber(cls, obj_slug, subscriptionkw, flasher):
    """
    Generates a subscriber-function to deal with objects of type `obj`
    which have the slug `slug` and are registered in the subscription by
    `subscriptionkw` and have the flashing-test `flasher`
    """
    @simple_check_login
    def subscriber(request, **kwargs):
        """
        If the user has already subscribed to this %s, it just redirects.
        If there isn't such a subscription, a new one is created.
        """ % obj_slug
        slug = kwargs[obj_slug]
        try:
            obj = cls.objects.get(slug=slug)
        except ObjectDoesNotExist:
            messages.error(request,
                _(u'There is no “%(slug)s” anymore.') % {'slug': slug})
            return HttpResponseRedirect(href('forum'))

        if not have_privilege(request.user, obj, CAN_READ):
            return abort_access_denied(request)
        if not Subscription.objects.user_subscribed(request.user, obj):
            # there's no such subscription yet, create a new one
            Subscription(user=request.user, content_object=obj).save()
            messages.info(request, flasher)
        # redirect the user to the page he last watched
        if request.GET.get('next', False) and is_safe_domain(request.GET['next']):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return HttpResponseRedirect(url_for(obj))
    return subscriber


def _generate_unsubscriber(cls, obj_slug, subscriptionkw, flasher):
    """
    Generates an unsubscriber-function to deal with objects of type `obj`
    which have the slug `slug` and are registered in the subscription by
    `subscriptionkw` and have the flashing-test `flasher`
    """
    @simple_check_login
    def unsubscriber(request, **kwargs):
        """ If the user has already subscribed to this %s, this view removes it.
        """ % obj_slug
        slug = kwargs[obj_slug]
        try:
            obj = cls.objects.get(slug=slug)
        except ObjectDoesNotExist:
            messages.error(
                request,
                _(u'There is no “%(slug)s” anymore.') % {'slug': slug}
            )
            return HttpResponseRedirect(href('forum'))

        try:
            subscription = Subscription.objects.get_for_user(request.user, obj)
        except Subscription.DoesNotExist:
            pass
        else:
            # there's already a subscription for this forum, remove it
            subscription.delete()
            messages.info(request, flasher)
        # redirect the user to the page he last watched
        if request.GET.get('next', False) and is_safe_domain(request.GET['next']):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return HttpResponseRedirect(url_for(obj))
    return unsubscriber


subscribe_forum = _generate_subscriber(Forum,
    'slug', 'forum',
    (_(u'Notifications on new topics within this forum will be sent to you.')))


unsubscribe_forum = _generate_unsubscriber(Forum,
    'slug', 'forum',
    (_(u'No notifications on new topics within this forum will be sent to you '
       u'any more.')))

subscribe_topic = _generate_subscriber(Topic,
    'topic_slug', 'topic',
    (_(u'Notifications on new posts in this topic will be sent to you.')))

unsubscribe_topic = _generate_unsubscriber(Topic,
    'topic_slug', 'topic',
    (_(u'No notifications on new posts in this topic will be sent to you any '
       u'more')))


@simple_check_login
@templated('forum/report.html')
def report(request, topic_slug):
    """Change the report_status of a topic and redirect to it"""
    topic = Topic.objects.get(slug=topic_slug)
    if not have_privilege(request.user, topic.forum, CAN_READ):
        return abort_access_denied(request)
    if topic.reported:
        messages.info(request, _(u'This topic was already reported.'))
        return HttpResponseRedirect(url_for(topic))

    if request.method == 'POST':
        form = ReportTopicForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            topic.reported = data['text']
            topic.reporter_id = request.user.id
            topic.save()

            subscribers = storage['reported_topics_subscribers'] or u''
            users = (User.objects.get(id=int(i)) for i in subscribers.split(',') if i)
            for user in users:
                send_notification(user, 'new_reported_topic',
                                  _(u'Reported topic: “%(topic)s”') % {'topic': topic.title},
                                  {'topic': topic, 'text': data['text']})

            cache.delete('forum/reported_topic_count')
            messages.success(request, _(u'The topic was reported.'))
            return HttpResponseRedirect(url_for(topic))
    else:
        form = ReportTopicForm()
    return {
        'topic': topic,
        'form': form
    }


@require_permission('manage_topics')
@templated('forum/reportlist.html')
def reportlist(request):
    """Get a list of all reported topics"""
    def _add_field_choices():
        """Add dynamic field choices to the reported topic formular"""
        form.fields['selected'].choices = [(t.id, u'') for t in topics]

    if 'topic' in request.GET:
        topic = Topic.objects.get(slug=request.GET['topic'])
        if 'assign' in request.GET:
            if topic.report_claimed_by_id:
                messages.info(request, _('This report has already been claimed.'))
            else:
                topic.report_claimed_by_id = request.user.id
        elif 'unassign' in request.GET and request.GET.get('unassign') == request.user.username:
            topic.report_claimed_by_id = None
        topic.save()
        return HttpResponseRedirect(href('forum', 'reported_topics'))

    topics = Topic.objects.filter(reported__isnull=False).all()
    if request.method == 'POST':
        form = ReportListForm(request.POST)
        _add_field_choices()
        if form.is_valid():
            d = form.cleaned_data
            if not d['selected']:
                messages.error(request, _(u'No topics selected.'))
            else:
                # We select all topics that have been selected and also
                # select the regarding forum, 'cause we will check for the
                # moderation privilege.
                topics_selected = topics.filter(id__in=d['selected']).select_related('forum')

                t_ids_mod = []
                # Check for the moderate privilege of the forums of selected
                # reported topics and take only the topic IDs where the
                # requesting user can moderate the forum.
                for f, ts in groupby(topics_selected, attrgetter('forum')):
                    if have_privilege(request.user, f, CAN_MODERATE):
                        t_ids_mod += map(attrgetter('id'), ts)

                # Update the reported state.
                Topic.objects.filter(id__in=t_ids_mod).update(
                    reported=None, reporter=None, report_claimed_by=None)
                cache.delete('forum/reported_topic_count')
                topics = filter(lambda t: t.id not in t_ids_mod, topics)
                if len(topics_selected) == len(t_ids_mod):
                    messages.success(request, _(u'The selected tickets have been closed.'))
                else:
                    messages.success(request, _(u'Only a subset of selected tickets has been '
                        u'closed, considering your moderation privileges '
                        u'for the regarding forums.'))
    else:
        form = ReportListForm()
        _add_field_choices()

    subscribers = storage['reported_topics_subscribers'] or u''
    subscribed = str(request.user.id) in subscribers.split(',')

    return {
        'topics': topics,
        'form': form,
        'subscribed': subscribed,
    }


def reported_topics_subscription(request, mode):
    subscribers = storage['reported_topics_subscribers'] or u''
    users = set(int(i) for i in subscribers.split(',') if i)

    if mode == 'subscribe':
        if not request.user.can('manage_topics'):
            return AccessDeniedResponse()
        users.add(request.user.id)
        messages.success(request, _(u'A notification will be sent when a topic is reported.'))
    elif mode == 'unsubscribe':
        try:
            users.remove(request.user.id)
        except KeyError:
            pass
        messages.success(request, _(u'You will not be notified anymore when a topic is reported.'))

    storage['reported_topics_subscribers'] = ','.join(str(i) for i in users)

    return HttpResponseRedirect(href('forum', 'reported_topics'))


def post(request, post_id):
    """Redirect to the "real" post url (see `PostManager.url_for_post`)"""
    try:
        url = Post.url_for_post(int(post_id),
            paramstr=request.GET and request.GET.urlencode())
    except (Topic.DoesNotExist, Post.DoesNotExist):
        raise Http404()
    return HttpResponseRedirect(url)


def first_unread_post(request, topic_slug):
    """
    Redirect the user to the first unread post in a special topic.
    """
    try:
        unread = Topic.objects.only('id', 'forum__id').get(slug=topic_slug)
    except Topic.DoesNotExist:
        raise Http404()

    data = request.user._readstatus.data.get(unread.forum.id, [None, []])
    query = Post.objects.filter(topic=unread)

    last_pid, ids = data
    if last_pid is not None:
        query = query.filter(id__gt=last_pid)

    if ids:
        # We need a try/catch here, cause the post don't have to exist
        # any longer.
        try:
            post_ids = Post.objects.filter(topic=unread, id__in=ids) \
                                   .values_list('id', flat=True)
            post_id = max(post_ids)
        except ValueError:
            pass
        else:
            query = query.filter(id__gt=post_id)

    try:
        first_unread_post = query.order_by('position')[0]
    except IndexError:
        # No new post, this also means the user called first_unread himself
        # as the icon won't show up in that case, hence we just return to
        # page one of the topic.
        redirect = href('forum', 'topic', topic_slug)
    else:
        redirect = Post.url_for_post(first_unread_post.id)
    return HttpResponseRedirect(redirect)


def last_post(request, topic_slug):
    """
    Redirect to the last post of the given topic.
    """
    try:
        last = Topic.objects.values_list('last_post', flat=True)\
                            .get(slug=topic_slug)
        params = request.GET and request.GET.urlencode()
        url = Post.url_for_post(last, paramstr=params)
        return HttpResponseRedirect(url)
    except (Post.DoesNotExist, Topic.DoesNotExist):
        raise Http404()


@templated('forum/movetopic.html')
def movetopic(request, topic_slug):
    """Move a topic into another forum"""

    topic = Topic.objects.get(slug=topic_slug)
    if not have_privilege(request.user, topic.forum, CAN_MODERATE):
        return abort_access_denied(request)

    forums = [
        forum
        for forum in Forum.objects.get_cached()
        if forum.parent is not None and forum.id != topic.forum.id
    ]
    mapping = {forum.id: forum for forum in filter_invisible(request.user, forums)}

    if not mapping:
        return abort_access_denied(request)

    if request.method == 'POST':
        form = MoveTopicForm(request.POST)
        form.fields['forum'].refresh()
        if form.is_valid():
            data = form.cleaned_data
            forum = mapping.get(int(data['forum']))
            if forum is None:
                return abort_access_denied(request)
            old_forum_name = topic.forum.name
            topic.move(forum)
            # send a notification to the topic author to inform him about
            # the new forum.
            nargs = {'username': topic.author.username,
                     'topic': topic,
                     'mod': request.user.username,
                     'forum_name': forum.name,
                     'old_forum_name': old_forum_name}

            user_notifications = topic.author.settings.get('notifications', ('topic_move',))
            if 'topic_move' in user_notifications and topic.author.username != request.user.username:
                send_notification(topic.author, 'topic_moved',
                    _(u'Your topic “%(topic)s” was moved.')
                    % {'topic': topic.title}, nargs)

            users_done = set([topic.author.id, request.user.id])
            ct = ContentType.objects.get_for_model
            subscriptions = Subscription.objects.filter((Q(content_type=ct(Topic)) &
                                                         Q(object_id=topic.id)) |
                                                        (Q(content_type=ct(Forum)) &
                                                         Q(object_id=topic.forum.id)))
            for subscription in subscriptions:
                if subscription.user.id in users_done:
                    continue
                nargs['username'] = subscription.user.username
                notify_about_subscription(subscription, 'topic_moved',
                    _(u'The topic “%(topic)s” was moved.')
                    % {'topic': topic.title}, nargs)
                users_done.add(subscription.user.id)
            return HttpResponseRedirect(url_for(topic))
    else:
        form = MoveTopicForm()
        form.fields['forum'].refresh()
    return {
        'form': form,
        'topic': topic
    }


@templated('forum/splittopic.html')
def splittopic(request, topic_slug, page=1):
    old_topic = Topic.objects.get(slug=topic_slug)
    old_posts = old_topic.posts.all()

    if not have_privilege(request.user, old_topic.forum, CAN_MODERATE):
        return abort_access_denied(request)

    post_ids = request.session.get('_split_post_ids', {})
    if not post_ids.get(topic_slug, None):
        messages.info(request, _(u'No post selected.'))
        return HttpResponseRedirect(old_topic.get_absolute_url())
    else:
        post_ids = post_ids[topic_slug]

    if str(post_ids[0]).startswith('!'):
        post_id = post_ids[0][1:]
        firstpos = Post.objects.values_list('position', flat=True).get(id=post_id)
        # selected one post to split all following posts
        posts = old_posts.filter(position__gte=firstpos)
    else:
        posts = old_posts.filter(id__in=[int(pid) for pid in post_ids])

    # Order the posts in the same way as they will be attached to the new topic
    posts = posts.order_by('position')

    if request.method == 'POST':
        form = SplitTopicForm(request.POST)
        form.fields['forum'].refresh()

        if form.is_valid():
            data = form.cleaned_data

            # Sanity check to not circulary split topics to the same topic
            # (they get erased in that case)
            if data['action'] != 'new' and data['topic'].slug == old_topic.slug:
                messages.error(request, _(u'You cannot set this topic as target.'))
                return HttpResponseRedirect(request.path)

            posts = list(posts)

            try:
                if data['action'] == 'new':
                    new_topic = Topic.objects.create(
                        title=data['title'],
                        forum=data['forum'],
                        slug=None,
                        author_id=posts[0].author_id,
                        ubuntu_version=data['ubuntu_version'],
                        ubuntu_distro=data['ubuntu_distro'])
                    new_topic.forum.topic_count.incr()

                    Post.split(posts, old_topic, new_topic)
                else:
                    new_topic = data['topic']
                    Post.split(posts, old_topic, new_topic)

                del request.session['_split_post_ids']

            except ValueError:
                messages.error(request,
                    _(u'You cannot move a topic into a category. '
                      u'Please choose a forum.'))
                return HttpResponseRedirect(request.path)

            new_forum = new_topic.forum
            nargs = {'username': None,
                     'new_topic': new_topic,
                     'old_topic': old_topic,
                     'mod': request.user.username}
            users_done = set([request.user.id])
            filter = Q(topic_id=old_topic.id)
            if data['action'] == 'new':
                filter |= Q(forum_id=new_forum.id)
            # TODO: Disable until http://forum.ubuntuusers.de/topic/benachrichtigungen-nach-teilung-einer-diskuss/ is resolved to not spam the users
            # subscriptions = Subscription.objects.select_related('user').filter(filter)
            subscriptions = []

            for subscription in subscriptions:
                # Skip loop for users already notified:
                if subscription.user.id in users_done:
                    continue
                # Added Users to users_done which should not get any
                # notification for splited Topics:
                if 'topic_split' not in subscription.user.settings.get('notifications', ('topic_split',)):
                    users_done.add(subscription.user.id)
                    continue
                nargs['username'] = subscription.user.username
                notify_about_subscription(subscription, 'topic_splited',
                    _(u'The topic “%(topic)s” was split.')
                    % {'topic': old_topic.title}, nargs)
                users_done.add(subscription.user.id)
            return HttpResponseRedirect(url_for(new_topic))
    else:
        form = SplitTopicForm(initial={
            'forum': old_topic.forum_id,
            'ubuntu_version': old_topic.ubuntu_version,
            'ubuntu_distro': old_topic.ubuntu_distro,
        })
        form.fields['forum'].refresh()

    return {
        'topic': old_topic,
        'forum': old_topic.forum,
        'form': form,
        'posts': posts,
    }


@confirm_action(message=_(u'Do you want to restore this post?'),
                confirm=_(u'Restore'), cancel=_(u'Cancel'))
def restore_post(request, post_id):
    """
    This function removes the hidden flag of a post to make it visible for
    normal users again.
    """
    post = Post.objects.get(id=post_id)
    if not have_privilege(request.user, post.topic.forum, CAN_MODERATE):
        return abort_access_denied(request)
    post.show()
    messages.success(request,
        _(u'The post by “%(user)s” was made visible.')
        % {'user': post.author.username})
    return HttpResponseRedirect(url_for(post))


@confirm_action(message=_(u'Do you really want to hide / delete this post?'),
                confirm=_(u'Hide / Delete'), cancel=_(u'Cancel'))
def delete_post(request, post_id, action='hide'):
    """
    Sets the hidden flag of a post to True if action == 'hide'. which has the
    effect that normal users can't see it anymore (moderators still can). If
    action == 'delete' really deletes the post.
    """
    post = Post.objects.get(id=post_id)
    topic = post.topic

    can_hide = (
        have_privilege(request.user, topic.forum, CAN_MODERATE) and
        not (post.author_id == request.user.id and post.check_ownpost_limit('delete'))
    )
    can_delete = can_hide and request.user.can('delete_topic')

    if action == 'delete' and not can_delete:
        return abort_access_denied(request)
    if action == 'hide' and not can_hide:
        return abort_access_denied(request)

    if post.id == topic.first_post_id:
        if topic.post_count.value() == 1:
            return HttpResponseRedirect(href('forum', 'topic',
                                             topic.slug, action))
        if action == 'delete':
            msg = _(u'The first post of a topic cannot be deleted.')
        else:
            msg = _(u'The first post of a topic cannot be hidden.')
        messages.error(request, msg)
    else:
        if action == 'hide':
            post.hide()
            messages.success(
                request,
                _(u'The post by “%(user)s” was hidden.') % {'user': post.author.username}
            )
            return HttpResponseRedirect(url_for(post))
        elif action == 'delete':
            position = post.position
            post.delete()
            messages.success(
                request,
                _(u'The post by “%(user)s” was deleted.') % {'user': post.author.username}
            )
            page = max(0, position) // POSTS_PER_PAGE + 1
            url = href('forum', 'topic', topic.slug, *(page != 1 and (page,) or ()))
            return HttpResponseRedirect(url)
    return HttpResponseRedirect(href('forum', 'topic', topic.slug,
                                     post.page))


@confirm_action(message=_(u'Do you really want to mark this post as ham / spam?'),
                confirm=_(u'Mark as ham / spam'), cancel=_(u'Cancel'))
def mark_ham_spam(request, post_id, action='spam'):
    post = Post.objects.select_related('topic__forum').get(id=post_id)
    topic = post.topic

    if not have_privilege(request.user, topic.forum, CAN_MODERATE):
        return abort_access_denied(request)

    if action == 'ham':
        post.mark_ham()
    elif action == 'spam':
        post.mark_spam(report=False, update_akismet=True)
    return HttpResponseRedirect(url_for(post))


@templated('forum/revisions.html')
def revisions(request, post_id):
    post = Post.objects.select_related('topic', 'topic.forum').get(id=post_id)
    topic = post.topic
    forum = topic.forum
    if not have_privilege(request.user, forum, CAN_MODERATE):
        return abort_access_denied(request)
    revs = PostRevision.objects.filter(post=post).all()
    return {
        'post': post,
        'topic': topic,
        'forum': forum,
        'revisions': reversed(revs)
    }


@confirm_action(message=_(u'Do you want to restore the revision of the post?'),
                confirm=_(u'Restore'), cancel=_(u'Cancel'))
def restore_revision(request, rev_id):
    rev = PostRevision.objects.select_related('post.topic.forum').get(id=rev_id)
    if not have_privilege(request.user, rev.post.topic.forum, CAN_MODERATE):
        return abort_access_denied(request)
    rev.restore(request)
    messages.success(request, _(u'An old revision of the post was restored.'))
    return HttpResponseRedirect(href('forum', 'post', rev.post_id))


@confirm_action(message=_(u'Do you want to restore the topic?'),
                confirm=_(u'Restore'), cancel=_(u'Cancel'))
def restore_topic(request, topic_slug):
    """
    This function removes the hidden flag of a topic to make it visible for
    normal users again.
    """
    topic = Topic.objects.get(slug=topic_slug)
    if not have_privilege(request.user, topic.forum, CAN_MODERATE):
        return abort_access_denied(request)
    topic.hidden = False
    topic.save()
    messages.success(request,
        _(u'The topic “%(topic)s” was restored.') % {'topic': topic.title})
    topic.forum.invalidate_topic_cache()
    return HttpResponseRedirect(url_for(topic))


def delete_topic(request, topic_slug, action='hide'):
    """
    Sets the hidden flag of a topic to True if action=='hide', which has the
    effect that normal users can't see it anymore (moderators still can).
    Completely deletes the topic if action=='delete'.
    """
    assert action in ('hide', 'delete')

    topic = Topic.objects.select_related('forum').get(slug=topic_slug)
    can_moderate = have_privilege(request.user, topic.forum, CAN_MODERATE)
    can_delete = request.user.can('delete_topic')

    if action == 'delete' and not can_delete and not can_moderate:
        return abort_access_denied(request)
    if action == 'hide' and not can_moderate:
        return abort_access_denied(request)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, _(u'Action canceled.'))
        else:
            if action == 'hide':
                topic.hidden = True
                topic.save()
                redirect = url_for(topic)
                messages.success(
                    request,
                    _(u'The topic “%(topic)s” was hidden.') % {'topic': topic.title}
                )

            elif action == 'delete':
                send_deletion_notification(request.user, topic, request.POST.get('reason', None))
                topic.delete()
                redirect = url_for(topic.forum)
                messages.success(request,
                    _(u'The topic “%(topic)s” was deleted successfully.')
                    % {'topic': topic.title})

            topic.forum.invalidate_topic_cache()
            return HttpResponseRedirect(redirect)
    else:
        messages.info(request, render_template('forum/delete_topic.html', {'topic': topic, 'action': action}))

    return HttpResponseRedirect(url_for(topic))


@atom_feed(name='forum_topic_feed')
@does_not_exist_is_404
def topic_feed(request, slug=None, mode='short', count=10):
    # We have one feed, so we use ANONYMOUS_USER to cache the correct feed.
    anonymous = User.objects.get_anonymous_user()

    topic = Topic.objects.get(slug=slug)
    if topic.hidden:
        raise Http404()

    if not have_privilege(anonymous, topic.cached_forum(), CAN_READ):
        return abort_access_denied(request)

    maxposts = max(settings.AVAILABLE_FEED_COUNTS['forum_topic_feed'])
    posts = topic.posts.select_related('author').order_by('-position')[:maxposts]

    feed = AtomFeed(_(u'%(site)s topic – “%(topic)s”')
                    % {'topic': topic.title, 'site': settings.BASE_DOMAIN_NAME},
                    url=url_for(topic),
                    feed_url=request.build_absolute_uri(),
                    rights=href('portal', 'lizenz'),
                    icon=href('static', 'img', 'favicon.ico'))

    for post in posts:
        kwargs = {}
        if mode == 'full':
            kwargs['content'] = post.get_text()
            kwargs['content_type'] = 'xhtml'
        if mode == 'short':
            kwargs['summary'] = Truncator(post.get_text).words(100, html=True)
            kwargs['summary_type'] = 'xhtml'

        feed.add(
            title='%s (%s)' % (
                post.author.username,
                format_datetime(post.pub_date)
            ),
            url=url_for(post),
            author=post.author,
            published=post.pub_date,
            updated=post.pub_date,
            **kwargs
        )
    return feed


@atom_feed(name='forum_forum_feed')
@does_not_exist_is_404
def forum_feed(request, slug=None, mode='short', count=10):
    # We have one feed, so we use ANONYMOUS_USER to cache the correct feed.
    anonymous = User.objects.get_anonymous_user()

    if slug:
        forum = Forum.objects.get_cached(slug=slug)
        if not have_privilege(anonymous, forum, CAN_READ):
            return abort_access_denied(request)

        topics = Topic.objects.get_latest(forum.slug, count=count)
        title = _(u'%(site)s forum – “%(forum)s”') % {'forum': forum.name,
                'site': settings.BASE_DOMAIN_NAME}
        url = url_for(forum)
    else:
        allowed_forums = [f.id for f in filter_invisible(anonymous, Forum.objects.get_cached())]
        if not allowed_forums:
            return abort_access_denied(request)
        topics = Topic.objects.get_latest(allowed_forums=allowed_forums, count=count)
        title = _(u'%(site)s forum') % {'site': settings.BASE_DOMAIN_NAME}
        url = href('forum')

    feed = AtomFeed(title, feed_url=request.build_absolute_uri(),
                    url=url, rights=href('portal', 'lizenz'),
                    icon=href('static', 'img', 'favicon.ico'))

    for topic in topics:
        kwargs = {}
        post = topic.first_post

        text = post.get_text()

        if mode == 'full':
            kwargs['content'] = text
            kwargs['content_type'] = 'xhtml'
        if mode == 'short':
            kwargs['summary'] = Truncator(text).words(100, html=True)
            kwargs['summary_type'] = 'xhtml'

        feed.add(
            title=topic.title,
            url=url_for(topic),
            author={
                'name': topic.author.username,
                'uri': url_for(topic.author),
            },
            published=post.pub_date,
            updated=post.pub_date,
            **kwargs
        )

    return feed


def markread(request, slug=None):
    """
    Mark either all or only the given forum as read.
    """
    user = request.user
    if user.is_anonymous:
        messages.info(request, _(u'Please login to mark posts as read.'))
        return HttpResponseRedirect(href('forum'))
    if slug:
        forum = Forum.objects.get(slug=slug)
        forum.mark_read(user)
        user.save()
        messages.success(request,
            _(u'The forum “%(forum)s” was marked as read.') %
            {'forum': forum.name})
        return HttpResponseRedirect(url_for(forum))
    else:
        mark_all_forums_read(user)
        messages.success(request, _(u'All forums were marked as read.'))
    return HttpResponseRedirect(href('forum'))


MAX_PAGES_TOPICLIST = 50


@templated('forum/topiclist.html')
def topiclist(request, page=1, action='newposts', hours=24, user=None, forum=None):
    page = int(page)

    if action != 'author' and page > MAX_PAGES_TOPICLIST:
        messages.info(
            request,
            _(u'You can only display the last %(n)d pages.') % {'n': MAX_PAGES_TOPICLIST}
        )
        return HttpResponseRedirect(href('forum'))

    topics = Topic.objects.order_by('-last_post')

    if 'version' in request.GET:
        topics = topics.filter(ubuntu_version=request.GET['version'])

    if action == 'last':
        hours = int(hours)
        if hours > 24:
            raise Http404()
        topics = topics.filter(posts__pub_date__gt=datetime.utcnow() - timedelta(hours=hours))
        title = _(u'Posts of the last %(n)d hours') % {'n': hours}
        url = href('forum', 'last%d' % hours, forum)
    elif action == 'unanswered':
        topics = topics.annotate(p_count=Count('posts')).filter(p_count=1)
        title = _(u'Unanswered topics')
        url = href('forum', 'unanswered', forum)
    elif action == 'unsolved':
        topics = topics.filter(solved=False)
        title = _(u'Unsolved topics')
        url = href('forum', 'unsolved', forum)
    elif action == 'topic_author':
        user = User.objects.get(username__iexact=user)
        topics = topics.filter(author=user)
        url = href('forum', 'topic_author', user.username, forum)
        title = _(u'Topics by “%(user)s”') % {'user': user.username}
    elif action == 'author':
        user = user and User.objects.get(username__iexact=user) or request.user
        if user.is_anonymous:
            messages.info(request, _(u'You need to be logged in to use this function.'))
            return abort_access_denied(request)
        topics = topics.filter(posts__author=user).distinct()

        if user != request.user:
            title = _(u'Posts by “%(user)s”') % {'user': user.username}
            url = href('forum', 'author', user.username, forum)
        else:
            title = _(u'My posts')
            url = href('forum', 'egosearch', forum)
    elif action == 'newposts':
        forum_ids = tuple(forum.id for forum in Forum.objects.get_cached())
        # get read status data
        read_status = request.user._readstatus.data
        read_topics = tuple(flatten_iterator(
            read_status.get(id, [None, []])[1] for id in forum_ids
        ))
        if read_topics:
            topics = topics.exclude(last_post__id__in=read_topics)
        url = href('forum', 'newposts', forum)
        title = _(u'New posts')

    invisible = [f.id for f in Forum.objects.get_forums_filtered(request.user, reverse=True)]
    if invisible:
        topics = topics.exclude(forum__id__in=invisible)

    forum_obj = None
    if forum:
        forum_obj = Forum.objects.get_cached(forum)
        if forum_obj and forum_obj.id not in invisible:
            topics = topics.filter(forum=forum_obj)

    topics = topics.distinct()
    total_topics = get_simplified_queryset(topics).count()
    topics = topics.values_list('id', flat=True)
    pagination = Pagination(request, topics, page, TOPICS_PER_PAGE, url,
                            total=total_topics, max_pages=MAX_PAGES_TOPICLIST)
    topic_ids = [tid for tid in pagination.get_queryset()]

    # check for moderation permissions
    moderatable_forums = [
        obj.id for obj in
        Forum.objects.get_forums_filtered(request.user, CAN_MODERATE, reverse=True)
    ]

    def can_moderate(topic):
        return topic.forum_id not in moderatable_forums

    if topic_ids:
        related = ('forum', 'author', 'last_post', 'last_post__author',
                   'first_post')
        topics = Topic.objects.filter(id__in=topic_ids).select_related(*related) \
                              .order_by('-last_post__id')
    else:
        topics = []

    return {
        'topics': topics,
        'pagination': pagination,
        'title': title,
        'can_moderate': can_moderate,
        'hide_sticky': False,
        'forum': forum_obj,
    }


@templated('forum/postlist.html')
def postlist(request, page=1, user=None, topic_slug=None, forum_slug=None):
    page = int(page)
    
    user = user and User.objects.get(username__iexact=user) or request.user
    if user.is_anonymous:
        messages.info(request, _(u'You need to be logged in to use this function.'))
        return abort_access_denied(request)
    
    posts = Post.objects.filter(author=user).order_by('-pub_date').distinct()
    
    additional_title = None
    
    topic = None
    if topic_slug is not None:
        topics = Topic.objects.filter(slug=topic_slug)
        if topics.exists():
            topic = topics[0]
            posts = posts.filter(topic=topic)
            additional_title = _(u'in topic “%(topic)s”') % { 'topic': topic }
        else:
            raise Http404()
    
    forum = None
    if forum_slug is not None:
        forum = Forum.objects.get_cached(forum_slug)
        posts = posts.filter(topic__forum=forum)
        additional_title = _(u'in forum “%(forum)s”') % { 'forum': forum }

    if additional_title is None:
        title = _(u'Posts by “{user}”').format(user=user.username)
    else:
        title = _(u'Posts by “{user}” {additional_title}').format(user=user.username, \
            additional_title=additional_title)
    
    url = href('forum', 'author', user.username, 'topic', topic)
    
    visible = [f.id for f in Forum.objects.get_forums_filtered(request.user)]
    if visible:
        posts = posts.filter(topic__forum__id__in=visible)

    total_posts = get_simplified_queryset(posts).count()
    posts = posts.values_list('id', flat=True)
    pagination = Pagination(request, posts, page, TOPICS_PER_PAGE, url,
                            total=total_posts, max_pages=MAX_PAGES_TOPICLIST)
    post_ids = [tid for tid in pagination.get_queryset()]

    # check for moderation permissions
    moderatable_forums = [
        obj.id for obj in
        Forum.objects.get_forums_filtered(request.user, CAN_MODERATE)
    ]

    def can_moderate(topic):
        return topic.forum_id in moderatable_forums

    if post_ids:
        related = ('topic', 'topic__forum', 'author')
        posts = Post.objects.filter(id__in=post_ids).select_related(*related)
    else:
        posts = []

    return {
        'posts': posts,
        'pagination': pagination,
        'title': title,
        'can_moderate': can_moderate,
        'hide_sticky': False,
        'forum': forum,
        'topic': topic,
        'username': user.username,
    }



@templated('forum/welcome.html')
def welcome(request, slug, path=None):
    """
    Show a welcome message on the first visit to greet the users or
    inform him about special rules.
    """
    forum = Forum.objects.get(slug=slug)
    if not forum.welcome_message:
        raise Http404()
    goto_url = path or url_for(forum)
    if request.method == 'POST':
        accepted = request.POST.get('accept', False)
        forum.read_welcome(request.user, accepted)
        if accepted:
            return HttpResponseRedirect(request.POST.get('goto_url'))
        else:
            return HttpResponseRedirect(href('forum'))
    return {
        'goto_url': goto_url,
        'message': forum.welcome_message,
        'forum': forum
    }


@does_not_exist_is_404
def next_topic(request, topic_slug):
    this = Topic.objects.get(slug=topic_slug)
    next = Topic.objects.filter(forum=this.forum,
                                last_post__gt=this.last_post) \
                        .order_by('last_post').all()
    if not next.exists():
        messages.info(request, _(u'No recent topics within this forum.'))
        next = [this.forum]
    return HttpResponseRedirect(url_for(next[0]))


@does_not_exist_is_404
def previous_topic(request, topic_slug):
    this = Topic.objects.get(slug=topic_slug)

    previous = Topic.objects.filter(forum=this.forum,
                                    last_post__lt=this.last_post) \
                            .order_by('-last_post').all()
    if not previous.exists():
        messages.info(request, _(u'No older topics within this forum.'))
        previous = [this.forum]
    return HttpResponseRedirect(url_for(previous[0]))


@require_permission('forum_edit')
@templated('forum/forum_edit.html')
def forum_edit(request, slug=None, parent=None):
    """
    Display an interface to let the user create or edit an forum.
    If `id` is given, the forum with id `id` will be edited.
    """

    forum = None
    errors = False
    initial = {'parent': parent} if parent else {}

    if slug:
        forum = Forum.objects.get_cached(slug)
        if forum is None:
            raise Http404()

    if request.method == 'POST':
        form = EditForumForm(request.POST, forum=forum)
        form.fields['parent'].refresh(add=[(0, u'-')], remove=[forum])

        if form.is_valid():
            data = form.cleaned_data
            if not slug:
                forum = Forum()
            forum.name = data['name']
            forum.position = data['position']
            old_slug = forum.slug
            forum.slug = data['slug']
            forum.description = data['description']
            if int(data['parent']) > 0:
                forum.parent = Forum.objects.get(id=int(data['parent']))
            else:
                forum.parent = None

            if data['welcome_msg_subject']:
                # subject and text are bound to each other, validation
                # is done in admin.forms
                welcome_msg = WelcomeMessage(
                    title=data['welcome_msg_subject'],
                    text=data['welcome_msg_text']
                )
                welcome_msg.save()
                forum.welcome_message_id = welcome_msg.id

            forum.newtopic_default_text = data.get('newtopic_default_text', None)
            forum.force_version = data['force_version']

            if not form.errors and not errors:
                forum.save()
                keys = ['forum/index'] + ['forum/forums/' + f.slug
                                          for f in Forum.objects.get_cached()]
                if old_slug is not None:
                    keys.append('forum/forums/' + old_slug)
                cache.delete_many(keys)
                cache.delete('forum/slugs')
                if slug:
                    msg = _(u'The forum “%(forum)s” was changed successfully.')
                else:
                    msg = _(u'The forum “%(forum)s” was created successfully.')
                messages.success(request, msg % {'forum': forum.name})
                return HttpResponseRedirect(href('forum'))
        else:
            trigger_fix_errors_message(request)

    else:
        if slug is None:
            form = EditForumForm(initial=initial)
        else:
            welcome_msg = forum.welcome_message

            form = EditForumForm(initial={
                'name': forum.name,
                'slug': forum.slug,
                'description': forum.description,
                'parent': forum.parent_id,
                'position': forum.position,
                'welcome_msg_subject': welcome_msg and welcome_msg.title or u'',
                'welcome_msg_text': welcome_msg and welcome_msg.text or u'',
                'force_version': forum.force_version,
                'count_posts': forum.user_count_posts,
            })
        form.fields['parent'].refresh(add=[(0, u'-')], remove=[forum])
    return {
        'form': form,
        'forum': forum
    }

