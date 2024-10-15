"""
    inyoka.forum.views
    ~~~~~~~~~~~~~~~~~~

    The views for the forum.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from operator import attrgetter

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import F, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from guardian.mixins import PermissionRequiredMixin as GuardianPermissionRequiredMixin

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
    mark_all_forums_read,
)
from inyoka.forum.notifications import (
    notify_reported_topic_subscribers,
    send_deletion_notification,
    send_discussion_notification,
    send_edit_notifications,
    send_newtopic_notifications,
    send_notification_for_topics,
)
from inyoka.markup.base import RenderContext, parse
from inyoka.markup.parsertools import flatten_iterator
from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.portal.utils import abort_access_denied
from inyoka.utils.database import get_simplified_queryset
from inyoka.utils.dates import _localtime, format_datetime
from inyoka.utils.feeds import InyokaAtomFeed
from inyoka.utils.flash_confirmation import confirm_action
from inyoka.utils.forms import clear_surge_protection
from inyoka.utils.generic import PermissionRequiredMixin
from inyoka.utils.http import (
    AccessDeniedResponse,
    does_not_exist_is_404,
    templated,
)
from inyoka.utils.notification import send_notification
from inyoka.utils.pagination import Pagination
from inyoka.utils.storage import storage
from inyoka.utils.templating import flash_message
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
    all_categories = Forum.objects.get_categories()

    if category:
        categories = [x for x in all_categories if x.slug == category]
        if not categories:
            raise Http404()
        category = categories[0]
        unread_forum = category.find_welcome(request.user)
        if unread_forum is not None:
            return redirect(url_for(unread_forum, 'welcome'))
    else:
        categories = tuple(forum for forum in forums if forum in all_categories)

    hidden_categories = []
    if request.user.is_authenticated:
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
    if not forum or forum.is_category:
        raise Http404()

    if not request.user.has_perm('forum.view_forum', forum):
        return abort_access_denied(request)

    unread_forum = forum.find_welcome(request.user)
    if unread_forum is not None:
        return redirect(url_for(unread_forum, 'welcome'))

    topic_ids = Topic.objects.filter(forum=forum)\
                             .values_list('id', flat=True)\
                             .order_by('-sticky', '-last_post')
    pagination = Pagination(request, topic_ids, page, TOPICS_PER_PAGE,
                            url_for(forum), total=forum.topic_count.value())

    subforums = [children for children in forum.children if request.user.has_perm('forum.view_forum', children)]
    last_post_ids = [f.last_post_id for f in subforums]
    last_post_map = Post.objects.last_post_map(last_post_ids)

    topics = Topic.objects.prepare_for_overview(list(pagination.get_queryset()))

    if not request.user.has_perm('forum.moderate_forum', forum):
        topics = [topic for topic in topics if not topic.hidden]

    for topic in topics:
        topic.forum = forum

    context = {
        'forum': forum,
        'subforums': subforums,
        'last_posts': last_post_map,
        'is_subscribed': Subscription.objects.user_subscribed(request.user, forum),
        'can_moderate': request.user.has_perm('forum.moderate_forum', forum),
        'can_create': request.user.has_perm('forum.add_topic_forum', forum),
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

    if not request.user.has_perm('forum.view_forum', topic.forum):
        return abort_access_denied(request)

    if topic.hidden:
        if request.user.has_perm('forum.moderate_forum', topic.forum):
            messages.info(request, _('This topic is not visible for regular users.'))
        elif request.user == topic.author and not Post.objects.filter(topic=topic).exclude(author=request.user).exists():
            # A user can see a topic if all posts of this topic are from this user https://github.com/inyokaproject/inyoka/pull/1191
            # This is useful if the topic was hidden automatically by the spam filter
            messages.info(request, _('This topic is hidden. Either it needs to be activated by moderators or it has been hidden explicitly by moderators.'))
        else:
            return abort_access_denied(request)

    unread_forum = topic.cached_forum().find_welcome(request.user)
    if unread_forum is not None:
        return redirect(url_for(unread_forum, 'welcome'))

    topic.touch()

    polls = None
    if topic.has_poll:
        polls = Poll.objects.filter(topic=topic).all()

        if request.method == 'POST' and 'vote' in request.POST:
            if not request.user.has_perm('forum.vote_forum', topic.forum):
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
                        messages.error(request, _('The poll already ended.'))
                        continue
                    poll.votings.add(PollVote(voter=request.user), bulk=False)
                    poll.options.filter(id__in=votes) \
                                .update(votes=F('votes') + 1)

    post_ids = Post.objects.filter(topic=topic) \
                           .values_list('id', flat=True)
    pagination = Pagination(request, post_ids, 1 if page == 'last' else page,
                            POSTS_PER_PAGE, url_for(topic),
                            total=topic.post_count.value(), rownum_column='position')
    if page == 'last':
        return HttpResponseRedirect(pagination.last)

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
    if request.user.is_authenticated:
        topic.mark_read(request.user)

    subscribed = Subscription.objects.user_subscribed(request.user, topic,
        ('forum', 'topic'), clear_notified=True)

    team_icon = storage['team_icon'] or None

    if team_icon:
        team_icon = href('media', team_icon)

    can_mod = request.user.has_perm('forum.moderate_forum', topic.forum)
    can_reply = request.user.has_perm('forum.add_reply_forum', topic.forum)
    can_vote = request.user.has_perm('forum.vote_forum', topic.forum)

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
        messages.success(request, _('The poll “%(poll)s” was added.') % {'poll': poll.question})
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
                _('The poll “%(poll)s” was removed.') % {'poll': poll.question}
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
                messages.error(request, _('The attachment “%(attachment)s” does already exist.')
                               % {'attachment': att_name})
            else:
                attachments.append(attachment)
                att_ids.append(attachment.id)
                messages.success(request, _('The attachment “%(attachment)s” was added '
                                 'successfully.') % {'attachment': att_name})

    elif 'delete_attachment' in request.POST:
        id = int(request.POST['delete_attachment'])
        matching_attachments = [a for a in attachments if a.id == id]
        if not matching_attachments:
            messages.info(request, _('The attachment with the ID “%(id)d” does not exist.')
                          % {'id': id}, False)
        else:
            attachment = matching_attachments[0]
            attachment.delete()
            attachments.remove(attachment)
            if attachment.id in att_ids:
                att_ids.remove(attachment.id)
            messages.info(request, _('The attachment “%(attachment)s” was deleted.')
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
            messages.error(request, _('The article “%(article)s” does not exist. However, you '
                           'can create it now.') % {'article': norm_page_name})
            return HttpResponseRedirect(href('wiki', norm_page_name))
        forum_slug = settings.WIKI_DISCUSSION_FORUM
        messages.info(
            request, _(
                'No discussion is linked yet to the article “%(article)s”. '
                'You can create a discussion now or <a href="%(link)s">link '
                'an existing topic</a> to the article.'
            ) % {
                'article': page_name,
                'link': url_for(page, 'discussion')
            }
        )
    if topic_slug:
        topic = Topic.objects.get(slug=topic_slug)
        forum = topic.forum
    elif forum_slug:
        forum = Forum.objects.get_cached(slug=forum_slug)
        if not forum or forum.is_category:
            raise Http404()
        newtopic = firstpost = True
    elif post_id:
        post = Post.objects.get(id=int(post_id))
        locked = post.lock(request)
        if locked:
            messages.error(request,
                _('This post is currently being edited by “%(user)s”!')
                % {'user': locked})
        topic = post.topic
        forum = topic.forum
        firstpost = post.id == topic.first_post_id
    elif quote_id:
        quote = Post.objects.select_related('topic', 'author') \
                            .get(id=int(quote_id))
        topic = quote.topic
        forum = topic.forum

    # We don't need Spam Checks for these Types of Users or Forums:
    # - Hidden Forums
    # - Users with post_count >= INYOKA_SPAM_DETECT_LIMIT
    # - Users with forum.moderate_forum Permission
    needs_spam_check = True
    if request.user.post_count.value(default=0) >= settings.INYOKA_SPAM_DETECT_LIMIT:
        needs_spam_check = False
    elif request.user.has_perm('forum.moderate_forum', forum) or post and post.pk:
        needs_spam_check = False
    else:
        if not User.objects.get_anonymous_user().has_perm('forum.view_forum', forum):
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

    if request.method == 'POST' and (request.user.has_perm('forum.moderate_forum', forum) or not needs_spam_check):
        # Moderators, trusted users and all users in non-public forums are exempt from the surge protection
        # https://github.com/inyokaproject/inyoka/issues/1203
        form.surge_protection_timeout = None

    # check privileges
    if post:
        if topic.locked or topic.hidden or post.hidden:
            if not request.user.has_perm('forum.moderate_forum', forum):
                messages.error(request, _('You cannot edit this post.'))
                post.unlock()
                return HttpResponseRedirect(href('forum', 'topic', post.topic.slug,
                                            post.page))
            elif topic.locked:
                messages.error(request,
                               _('You are editing a post on a locked topic. '
                                 'Please note that this may be considered as impolite!'))
        if not (request.user.has_perm('forum.moderate_forum', forum) or
                (post.author.id == request.user.id and
                 request.user.has_perm('forum.add_reply_forum', forum) and
                 post.check_ownpost_limit('edit'))):
            messages.error(request, _('You cannot edit this post.'))
            post.unlock()
            return HttpResponseRedirect(href('forum', 'topic', post.topic.slug,
                                             post.page))
    elif topic:
        if topic.hidden:
            if not request.user.has_perm('forum.moderate_forum', forum):
                messages.error(request,
                    _('You cannot reply in this topic because it is '
                      'hidden.'))
                return HttpResponseRedirect(url_for(topic))
        elif topic.locked:
            if not request.user.has_perm('forum.moderate_forum', forum):
                messages.error(request,
                    _('You cannot reply to this topic because '
                      'it was locked.'))
                return HttpResponseRedirect(url_for(topic))
            else:
                messages.error(request,
                    _('You are replying to a locked topic. '
                      'Please note that this may be considered as impolite!'))
        elif quote and quote.hidden:
            if not request.user.has_perm('forum.moderate_forum', forum):
                return abort_access_denied(request)
        else:
            if not request.user.has_perm('forum.add_reply_forum', forum):
                return abort_access_denied(request)
    else:
        if not request.user.has_perm('forum.add_topic_forum', forum):
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
        elif quote_id:
            url = href('forum', 'post', quote_id)
        return HttpResponseRedirect(url)

    # Clear surge protection to avoid multi-form hickups.
    clear_surge_protection(request, form)

    # Handle polls
    poll_ids = list(map(int, list(filter(bool, request.POST.get('polls', '').split(',')))))
    poll_form = poll_options = polls = None
    if (newtopic or firstpost) and request.user.has_perm('forum.poll_forum', forum):
        poll_form, poll_options, polls = handle_polls(request, topic, poll_ids)

    # handle attachments
    att_ids = list(map(int, list(filter(bool,
        request.POST.get('attachments', '').split(',')
    ))))
    if request.user.has_perm('forum.upload_forum', forum):
        attach_form, attachments = handle_attachments(request, post, att_ids)

    # the user submitted a valid form
    if 'send' in request.POST and form.is_valid():
        d = form.cleaned_data

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
                    _('This topic was already created. Please think about '
                      'editing your topic before creating a new one.'))
                return HttpResponseRedirect(url_for(doublepost.topic))

        if not topic and newtopic or firstpost:
            if not topic and newtopic:
                topic = Topic(forum=forum, author=request.user)
            topic.title = d['title']
            if topic.ubuntu_distro != d.get('ubuntu_distro')\
               or topic.ubuntu_version != d.get('ubuntu_version'):
                topic.ubuntu_distro = d.get('ubuntu_distro')
                topic.ubuntu_version = d.get('ubuntu_version')
            if request.user.has_perm('forum.sticky_forum', forum):
                topic.sticky = d.get('sticky', False)
            elif d.get('sticky', False):
                messages.error(request, _('You are not allowed to mark this '
                                            'topic as "important".'))

            topic.save()
            topic.forum.invalidate_topic_cache()

            if request.user.has_perm('forum.poll_forum', forum):
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

        if form._spam:
            post.mark_spam(report=True, update_akismet=False)

        if not form._spam:
            if newtopic:
                send_newtopic_notifications(request.user, post, topic, forum)
            elif not post_id:
                send_edit_notifications(request.user, post, topic, forum)
        if page:
            # the topic is a wiki discussion, bind it to the wiki
            # page and send notifications.
            page.topic = topic
            page.save()
            if not form._spam:
                send_discussion_notification(request.user, page)

        if not form._spam and not post_id:
            Subscription.create_auto_subscription(request.user, topic)

        messages.success(request, _('The post was saved successfully.'))
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
        'can_attach': request.user.has_perm('forum.upload_forum', forum),
        'can_create_poll': request.user.has_perm('forum.poll_forum', forum),
        'can_moderate': request.user.has_perm('forum.moderate_forum', forum),
        'can_sticky': request.user.has_perm('forum.sticky_forum', forum),
        'attach_form': attach_form,
        'attachments': list(attachments),
        'posts': posts,
        'storage': storage,
        'discussions': discussions,
    }


@confirm_action(message=gettext_lazy('Do you want to (un)lock the topic?'),
                confirm=gettext_lazy('(Un)lock'),
                cancel=gettext_lazy('Cancel'))
@login_required
def lock_topic(request, topic_slug, locked, page=1):
    """Lock/unlock a topic and redirect to it"""
    topic = Topic.objects.get(slug=topic_slug)
    if not request.user.has_perm('forum.moderate_forum', topic.forum):
        return abort_access_denied(request)

    topic.locked = locked
    topic.save()
    if locked:
        msg = _('The topic was locked.')
    else:
        msg = _('The topic was unlocked.')
    messages.success(request, msg)
    topic.forum.invalidate_topic_cache()

    return HttpResponseRedirect(href('forum', 'topic', topic_slug, page))


@login_required
def solve_topic(request, topic_slug, solved, page=1):
    """Solve/unsolve a topic and redirect to it"""
    topic = Topic.objects.get(slug=topic_slug)
    if not request.user.has_perm('forum.view_forum', topic.forum):
        return abort_access_denied(request)
    if topic.locked and not request.user.has_perm('forum.moderate_forum', topic.forum):
        return abort_access_denied(request)

    topic.solved = solved
    topic.save()
    if solved:
        msg = _('The topic was marked as solved.')
    else:
        msg = _('The topic was marked as unsolved.')
    messages.success(request, msg)
    topic.forum.invalidate_topic_cache()

    return HttpResponseRedirect(href('forum', 'topic', topic_slug, page))


def _generate_subscriber(cls, obj_slug, subscriptionkw, flasher):
    """
    Generates a subscriber-function to deal with objects of type `obj`
    which have the slug `slug` and are registered in the subscription by
    `subscriptionkw` and have the flashing-test `flasher`
    """
    @login_required
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
                _('There is no “%(slug)s” anymore.') % {'slug': slug})
            return HttpResponseRedirect(href('forum'))

        if isinstance(obj, Topic):
            forum = obj.forum
        else:
            forum = obj
        if not request.user.has_perm('forum.view_forum', forum):
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


def _generate_unsubscriber(cls, obj_slug, subscriptionkw, flasher, page=1):
    """
    Generates an unsubscriber-function to deal with objects of type `obj`
    which have the slug `slug` and are registered in the subscription by
    `subscriptionkw` and have the flashing-test `flasher`
    """
    @login_required
    def unsubscriber(request, **kwargs):
        """ If the user has already subscribed to this %s, this view removes it.
        """ % obj_slug
        slug = kwargs[obj_slug]
        try:
            obj = cls.objects.get(slug=slug)
        except ObjectDoesNotExist:
            messages.error(
                request,
                _('There is no “%(slug)s” anymore.') % {'slug': slug}
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
            if obj_slug == 'topic':
                return HttpResponseRedirect(href('forum', 'topic',
                                                 'topic_slug', page))
            else:
                return HttpResponseRedirect(url_for(obj))
    return unsubscriber


subscribe_forum = _generate_subscriber(Forum,
    'slug', 'forum',
    (gettext_lazy('Notifications on new topics within this forum will be sent to you.')))


unsubscribe_forum = _generate_unsubscriber(Forum,
    'slug', 'forum',
    (gettext_lazy('No notifications on new topics within this forum will be sent to you '
       'any more.')))

subscribe_topic = _generate_subscriber(Topic,
    'topic_slug', 'topic',
    (gettext_lazy('Notifications on new posts in this topic will be sent to you.')))

unsubscribe_topic = _generate_unsubscriber(Topic,
    'topic_slug', 'topic',
    (gettext_lazy('No notifications on new posts in this topic will be sent to you any '
       'more')))


@login_required
@templated('forum/report.html')
def report(request, topic_slug, page=1):
    """Change the report_status of a topic and redirect to it"""
    topic = Topic.objects.get(slug=topic_slug)
    if not request.user.has_perm('forum.view_forum', topic.forum):
        return abort_access_denied(request)
    if topic.reported:
        messages.info(request, _('This topic was already reported.'))
        return HttpResponseRedirect(url_for(topic))

    if request.method == 'POST':
        form = ReportTopicForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            topic.reported = data['text']
            topic.reporter_id = request.user.id
            topic.save()

            notify_reported_topic_subscribers(
                _('Reported topic: “%(topic)s”') % {'topic': topic.title},
                {'topic': topic, 'text': data['text']})

            cache.delete('forum/reported_topic_count')
            messages.success(request, _('The topic was reported.'))
            return HttpResponseRedirect(href('forum', 'topic', topic_slug,
                                             page))
    else:
        form = ReportTopicForm()
    return {
        'topic': topic,
        'form': form
    }


@login_required
@permission_required('forum.manage_reported_topic', raise_exception=True)
@templated('forum/reportlist.html')
def reportlist(request):
    """Get a list of all reported topics"""
    def _add_field_choices():
        """Add dynamic field choices to the reported topic formular"""
        form.fields['selected'].choices = [(topic.id, '') for topic in topics]

    if 'topic' in request.GET:
        topic = Topic.objects.get(slug=request.GET['topic'])
        if 'assign' in request.GET:
            # check that user can only assign himself if he has moderation rights
            if request.user.has_perm('forum.moderate_forum', topic.forum):
                if topic.report_claimed_by_id:
                    messages.info(request, _('This report has already been claimed.'))
                else:
                    topic.report_claimed_by_id = request.user.id
            else:
                messages.info(request, _('You don\'t have moderation rights for the seleted topic.'))
        elif 'unassign' in request.GET and request.GET.get('unassign') == request.user.username:
            topic.report_claimed_by_id = None
        topic.save()
        return HttpResponseRedirect(href('forum', 'reported_topics'))

    topics = Topic.objects.filter(reported__isnull=False).order_by('-report_claimed_by','slug').all()
    if request.method == 'POST':
        form = ReportListForm(request.POST)
        _add_field_choices()
        if form.is_valid():
            data = form.cleaned_data
            if not data['selected']:
                messages.error(request, _('No topics selected.'))
            else:
                # We select all topics that have been selected and also
                # select the regarding forum, 'cause we will check for the
                # moderation privilege.
                topics_selected = topics.filter(id__in=data['selected']).select_related('forum')

                topic_ids_modrights = set()
                # Check for the moderate privilege of the forums of selected
                # reported topics and take only the topic IDs where the
                # requesting user can moderate the forum.
                for forum, selected_topics in groupby(topics_selected, attrgetter('forum')):
                    if request.user.has_perm('forum.moderate_forum', forum):
                        topic_ids_modrights.update(list(map(attrgetter('id'), selected_topics)))
                for topic in topics_selected:
                    if topic.report_claimed_by_id == request.user.id:
                        topic_ids_modrights.add(topic.id)

                # Update the reported state.
                Topic.objects.filter(id__in=topic_ids_modrights).update(
                    reported=None, reporter=None, report_claimed_by=None)
                cache.delete('forum/reported_topic_count')
                topics = [t for t in topics if t.id not in topic_ids_modrights]
                if len(topics_selected) == len(topic_ids_modrights):
                    messages.success(request, _('The selected tickets have been closed.'))
                else:
                    messages.success(request, _('Only a subset of selected tickets has been '
                        'closed, considering your moderation privileges '
                        'for the regarding forums.'))
    else:
        form = ReportListForm()
        _add_field_choices()

    subscribers = storage['reported_topics_subscribers'] or ''
    subscribed = str(request.user.id) in subscribers.split(',')

    return {
        'topics': topics,
        'form': form,
        'subscribed': subscribed,
    }


def reported_topics_subscription(request, mode):
    subscribers = storage['reported_topics_subscribers'] or ''
    users = {int(i) for i in subscribers.split(',') if i}

    if mode == 'subscribe':
        if not request.user.has_perm('forum.manage_reported_topic'):
            return AccessDeniedResponse()
        users.add(request.user.id)
        messages.success(request, _('A notification will be sent when a topic is reported.'))
    elif mode == 'unsubscribe':
        try:
            users.remove(request.user.id)
        except KeyError:
            pass
        messages.success(request, _('You will not be notified anymore when a topic is reported.'))

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
    if not request.user.has_perm('forum.moderate_forum', topic.forum):
        return abort_access_denied(request)

    form = partial(MoveTopicForm, current_forum=topic.forum, user=request.user)

    if request.method == 'POST':
        form = form(request.POST)
        if form.is_valid():
            new_forum = form.cleaned_data['forum']
            old_forum_name = topic.forum.name
            topic.move(new_forum)

            # send a notification to the topic author to inform him about
            # the new forum.
            nargs = {'username': topic.author.username,
                     'topic': topic,
                     'mod': request.user.username,
                     'forum_name': new_forum.name,
                     'old_forum_name': old_forum_name}

            user_notifications = topic.author.settings.get('notifications', ('topic_move',))
            if 'topic_move' in user_notifications and topic.author.username != request.user.username:
                send_notification(topic.author, 'topic_moved',
                    _('Your topic “%(topic)s” was moved.')
                    % {'topic': topic.title}, nargs)

            send_notification_for_topics(request.user.id,
                                         template='topic_moved',
                                         template_args=nargs,
                                         subject=_('The topic “%(topic)s” was moved.') % {'topic': topic.title},
                                         topic_ids=[topic.id],
                                         include_forums=True,
                                         forum_ids=[topic.forum.id]
                                         )

            if form.cleaned_data['edit_post']:
                return HttpResponseRedirect(url_for(topic.first_post, action='edit'))
            else:
                return HttpResponseRedirect(url_for(topic))
    else:
        form = form(initial={'forum': topic.forum.id})
    return {
        'form': form,
        'topic': topic
    }


@templated('forum/splittopic.html')
def splittopic(request, topic_slug, page=1):
    old_topic = Topic.objects.get(slug=topic_slug)
    old_posts = old_topic.posts.all()

    if not request.user.has_perm('forum.moderate_forum', old_topic.forum):
        return abort_access_denied(request)

    post_ids = request.session.get('_split_post_ids', {})
    if not post_ids.get(topic_slug, None):
        messages.info(request, _('No post selected.'))
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

    form = partial(SplitTopicForm, user=request.user)

    if request.method == 'POST':
        form = form(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            # Sanity check to not circulary split topics to the same topic
            # (they get erased in that case)
            if data['action'] != 'new' and data['topic_to_move'].slug == old_topic.slug:
                messages.error(request, _('You cannot set this topic as target.'))
                return HttpResponseRedirect(request.path)

            posts = list(posts)

            if data['action'] == 'new':
                if posts[0].hidden:
                    messages.error(request,
                       _('The First post of the new topic must not be '
                          'hidden.'))
                    return HttpResponseRedirect(request.path)
                new_topic = Topic.objects.create(
                    title=data['new_title'],
                    forum=data['forum'],
                    slug=None,
                    author_id=posts[0].author_id,
                    ubuntu_version=data['ubuntu_version'],
                    ubuntu_distro=data['ubuntu_distro'])
                new_topic.forum.topic_count.incr()

                Post.split(posts, old_topic, new_topic)
            else:
                new_topic = data['topic_to_move']
                Post.split(posts, old_topic, new_topic)

            del request.session['_split_post_ids']

            send_notification_for_topics(request.user.id,
                                         template='topic_split',
                                         template_args={'new_topic': new_topic, 'old_topic': old_topic,
                                                        'mod': request.user.username},
                                         subject=_('The topic “%(topic)s” was split.') % {'topic': old_topic.title},
                                         topic_ids=[old_topic.id, new_topic.id],
                                         include_forums=data['action'] == 'new',
                                         forum_ids=[new_topic.forum.id]
                                         )

            if data['edit_post']:
                return HttpResponseRedirect(url_for(posts[0], action='edit'))
            else:
                return HttpResponseRedirect(url_for(posts[0]))
    else:
        form = form(initial={
            'forum': old_topic.forum_id,
            'ubuntu_version': old_topic.ubuntu_version,
            'ubuntu_distro': old_topic.ubuntu_distro,
        })

    return {
        'topic': old_topic,
        'forum': old_topic.forum,
        'form': form,
        'posts': posts,
    }


@confirm_action(message=gettext_lazy('Do you want to restore this post?'),
                confirm=gettext_lazy('Restore'),
                cancel=gettext_lazy('Cancel'))
def restore_post(request, post_id):
    """
    This function removes the hidden flag of a post to make it visible for
    normal users again.
    """
    post = Post.objects.select_related('topic', 'topic__forum').get(id=post_id)
    if not request.user.has_perm('forum.moderate_forum', post.topic.forum):
        return abort_access_denied(request)
    post.show(change_post_counter=post.topic.forum.user_count_posts)
    messages.success(request,
        _('The post by “%(user)s” was made visible.')
        % {'user': post.author.username})
    return HttpResponseRedirect(url_for(post))


@confirm_action(message=gettext_lazy('Do you really want to hide / delete this post?'),
                confirm=gettext_lazy('Hide / Delete'),
                cancel=gettext_lazy('Cancel'))
def delete_post(request, post_id, action='hide'):
    """
    Sets the hidden flag of a post to True if action == 'hide'. which has the
    effect that normal users can't see it anymore (moderators still can). If
    action == 'delete' really deletes the post.
    """
    post = Post.objects.select_related('topic', 'topic__forum').get(id=post_id)
    topic = post.topic

    can_hide = (
        request.user.has_perm('forum.moderate_forum', topic.forum) and
        not (post.author_id == request.user.id and post.check_ownpost_limit('delete'))
    )
    can_delete = can_hide and request.user.has_perm('forum.delete_topic_forum', topic.forum)

    if action == 'delete' and not can_delete:
        return abort_access_denied(request)
    if action == 'hide' and not can_hide:
        return abort_access_denied(request)

    if post.id == topic.first_post_id:
        if topic.post_count.value() == 1:
            return HttpResponseRedirect(
                href('forum', 'topic', topic.slug, action))
        if action == 'delete':
            msg = _('The first post of a topic cannot be deleted.')
        else:
            msg = _('The first post of a topic cannot be hidden.')
        messages.error(request, msg)
    else:
        if action == 'hide':
            post.hide(change_post_counter=topic.forum.user_count_posts)
            messages.success(
                request,
                _('The post by “%(user)s” was hidden.') % {'user': post.author.username}
            )
            return HttpResponseRedirect(url_for(post))
        elif action == 'delete':
            position = post.position
            post.delete()
            messages.success(
                request,
                _('The post by “%(user)s” was deleted.') % {'user': post.author.username}
            )
            page = max(0, position) // POSTS_PER_PAGE + 1
            url = href('forum', 'topic', topic.slug, *(page != 1 and (page,) or ()))
            return HttpResponseRedirect(url)
    return HttpResponseRedirect(href('forum', 'topic', topic.slug,
                                     post.page))


@confirm_action(message=gettext_lazy('Do you really want to mark this post as ham / spam?'),
                confirm=gettext_lazy('Mark as ham / spam'),
                cancel=gettext_lazy('Cancel'))
def mark_ham_spam(request, post_id, action='spam'):
    post = Post.objects.select_related('topic__forum').get(id=post_id)
    topic = post.topic

    if not request.user.has_perm('forum.moderate_forum', topic.forum):
        return abort_access_denied(request)

    if action == 'ham':
        post.mark_ham()
        # Authors are not subscribed to own posts if the post is detected as spam
        # subscribe author after marking as ham
        # https://github.com/inyokaproject/inyoka/issues/1119
        Subscription.create_auto_subscription(post.author, topic)

    elif action == 'spam':
        post.mark_spam(report=False, update_akismet=True)
    return HttpResponseRedirect(url_for(post))


@templated('forum/revisions.html')
def revisions(request, post_id):
    post = Post.objects.select_related('topic', 'topic__forum').get(id=post_id)
    topic = post.topic
    forum = topic.forum
    if not request.user.has_perm('forum.moderate_forum', forum):
        return HttpResponseRedirect(post.get_absolute_url())

    revisions = PostRevision.objects.filter(post=post).order_by('-store_date')

    return {
        'post': post,
        'topic': topic,
        'forum': forum,
        'revisions': revisions
    }


@confirm_action(message=gettext_lazy('Do you want to restore the revision of the post?'),
                confirm=gettext_lazy('Restore'),
                cancel=gettext_lazy('Cancel'))
def restore_revision(request, rev_id):
    rev = PostRevision.objects.select_related('post__topic__forum').get(id=rev_id)
    if not request.user.has_perm('forum.moderate_forum', rev.post.topic.forum):
        return abort_access_denied(request)
    rev.restore(request)
    messages.success(request, _('An old revision of the post was restored.'))
    return HttpResponseRedirect(href('forum', 'post', rev.post_id))


@confirm_action(message=gettext_lazy('Do you want to restore the topic?'),
                confirm=gettext_lazy('Restore'),
                cancel=gettext_lazy('Cancel'))
def restore_topic(request, topic_slug):
    """
    This function removes the hidden flag of a topic to make it visible for
    normal users again.
    """
    topic = Topic.objects.get(slug=topic_slug)
    if not request.user.has_perm('forum.moderate_forum', topic.forum):
        return abort_access_denied(request)
    topic.hidden = False
    topic.save()
    messages.success(request,
        _('The topic “%(topic)s” was restored.') % {'topic': topic.title})
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
    can_moderate = request.user.has_perm('forum.moderate_forum', topic.forum)
    can_delete = request.user.has_perm('forum.delete_topic_forum', topic.forum)

    if not can_moderate:
        return abort_access_denied(request)

    if action == 'delete' and not can_delete:
        return abort_access_denied(request)

    if action == 'delete' and not topic.hidden:
        return abort_access_denied(request)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, _('Action canceled.'))
        else:
            if action == 'hide':
                topic.hidden = True
                topic.save()
                redirect = url_for(topic)
                messages.success(
                    request,
                    _('The topic “%(topic)s” was hidden.') % {'topic': topic.title}
                )

            elif action == 'delete':
                send_deletion_notification(request.user, topic, request.POST.get('reason', None))
                topic.delete()
                redirect = url_for(topic.forum)
                messages.success(request,
                    _('The topic “%(topic)s” was deleted successfully.')
                    % {'topic': topic.title})

            topic.forum.invalidate_topic_cache()
            return HttpResponseRedirect(redirect)
    else:
        flash_message(request, 'forum/delete_topic.html', {'topic': topic, 'action': action})

    return HttpResponseRedirect(url_for(topic))


class ForumTopicAtomFeed(InyokaAtomFeed):
    """
    Atom feed with posts of a topic.
    """
    name = 'forum_topic_feed'

    def get_object(self, request, *args, **kwargs):
        topic = get_object_or_404(Topic, slug=kwargs['slug'], hidden=False)

        # We have only one feed, so it's always in the view of ANONYMOUS_USER
        anonymous = User.objects.get_anonymous_user()
        if not anonymous.has_perm('forum.view_forum', topic.cached_forum()):
            raise PermissionDenied

        super().get_object(request, *args, **kwargs)

        return topic

    def title(self, topic):
        return _('%(site)s topic – “%(topic)s”') % {'topic': topic.title, 'site': settings.BASE_DOMAIN_NAME}

    def _subtitle(self, topic):
        return _('Feed contains posts of the topic “%(topic)s”.') % {'topic': topic.title}

    def link(self, topic):
        return url_for(topic)

    def items(self, topic):
        return topic.posts.filter(hidden=False).select_related('author').order_by('-position')[:self.count]

    def item_title(self, post):
        return '%s (%s)' % (
            post.author.username,
            format_datetime(post.pub_date)
        )

    def item_description(self, post):
        if self.mode == 'full':
            return post.get_text()
        if self.mode == 'short':
            return self._shorten_html(post.get_text)

    def item_link(self, post):
        return url_for(post)

    def item_author_name(self, post):
        return post.author.username

    def item_author_link(self, post):
        return url_for(post.author)

    def item_pubdate(self, post):
        return _localtime(post.pub_date)

    def item_updateddate(self, post):
        if post.has_revision:
            update_date = post.revisions.latest('store_date').store_date
        else:
            update_date = post.pub_date

        return _localtime(update_date)


class ForumAtomFeed(InyokaAtomFeed):
    """
    Atom feed with new topics of the whole forum.
    """
    name = 'forum_forum_feed'
    title = _('%(site)s forum') % {'site': settings.BASE_DOMAIN_NAME}
    link = href('forum')

    def _subtitle(self, __):
        return _('Feed contains new topics of the whole forum')

    def items(self, _):
        return Topic.objects.get_latest(count=self.count)

    def item_title(self, topic):
        return topic.title

    def item_categories(self, topic):
        _forum = topic.forum
        categories = [_forum.name]
        categories += [p.name for p in _forum.parents]

        ubuntu_version = topic.get_ubuntu_version()
        if ubuntu_version:
            categories.append(ubuntu_version)

        version_info = topic.get_version_info()
        if version_info:
            categories.append(version_info)

        return categories

    def item_description(self, topic):
        post = topic.first_post
        text = post.get_text()

        if self.mode == 'full':
            return text
        if self.mode == 'short':
            return self._shorten_html(text)

    def item_link(self, topic):
        return url_for(topic)

    def item_author_name(self, topic):
        return topic.author.username

    def item_author_link(self, topic):
        return url_for(topic.author)

    def item_pubdate(self, topic):
        post = topic.first_post
        return _localtime(post.pub_date)

    def item_updateddate(self, topic):
        post = topic.last_post
        return _localtime(post.pub_date)


class OneForumAtomFeed(ForumAtomFeed):
    """
    Atom feed with new topics of one forum.
    """

    def get_object(self, request, *args, **kwargs):
        forum = Forum.objects.get_cached(slug=kwargs['slug'])

        super().get_object(request, *args, **kwargs)

        return forum

    def title(self, forum):
        return _('%(site)s forum – “%(forum)s”') % {'forum': forum.name, 'site': settings.BASE_DOMAIN_NAME}

    def link(self, forum):
        return url_for(forum)

    def _subtitle(self, forum):
        return _('Feed contains new topics of the forum “%(forum)s”.') % {'forum': forum.name}

    def items(self, forum):
        return Topic.objects.get_latest(forum=forum, count=self.count)


def markread(request, slug=None):
    """
    Mark either all or only the given forum as read.
    """
    user = request.user
    if user.is_anonymous:
        messages.info(request, _('Please login to mark posts as read.'))
        return HttpResponseRedirect(href('forum'))
    if slug:
        forum = get_object_or_404(Forum, slug=slug)
        forum.mark_read(user)
        user.save()
        messages.success(request,
            _('The forum “%(forum)s” was marked as read.') %
            {'forum': forum.name})
        return HttpResponseRedirect(url_for(forum))
    else:
        mark_all_forums_read(user)
        messages.success(request, _('All forums were marked as read.'))
    return HttpResponseRedirect(href('forum'))


MAX_PAGES_TOPICLIST = 50


@templated('forum/topiclist.html')
def topiclist(request, page=1, action='newposts', hours=24, user=None, forum=None):
    page = int(page)

    if action != 'author' and page > MAX_PAGES_TOPICLIST:
        messages.info(
            request,
            _('You can only display the last %(n)d pages.') % {'n': MAX_PAGES_TOPICLIST}
        )
        return HttpResponseRedirect(href('forum'))

    topics = Topic.objects.exclude(first_post_id__isnull=True).order_by('-last_post')

    if 'version' in request.GET:
        topics = topics.filter(ubuntu_version=request.GET['version'])

    if action == 'last':
        hours = int(hours)
        if hours > 24:
            raise Http404()
        topics = topics.filter(posts__pub_date__gt=datetime.utcnow() - timedelta(hours=hours))
        topics = topics.distinct()
        title = _('Posts of the last %(n)d hours') % {'n': hours}
        url = href('forum', 'last%d' % hours, forum)
    elif action == 'unanswered':
        topics = topics.filter(first_post=F('last_post'))
        title = _('Unanswered topics')
        url = href('forum', 'unanswered', forum)
    elif action == 'unsolved':
        topics = topics.filter(solved=False)
        title = _('Unsolved topics')
        url = href('forum', 'unsolved', forum)
    elif action == 'topic_author':
        user = User.objects.get(username__iexact=user)
        topics = topics.filter(author=user)
        url = href('forum', 'topic_author', user.username, forum)
        title = _('Topics by “%(user)s”') % {'user': user.username}
    elif action == 'author':
        user = user and User.objects.get(username__iexact=user) or request.user
        if request.user.is_anonymous:
            messages.info(request, _('You need to be logged in to use this function.'))
            return abort_access_denied(request)
        topics = topics.filter(posts__author=user).distinct()

        if user != request.user:
            title = _('Posts by “%(user)s”') % {'user': user.username}
            url = href('forum', 'author', user.username, forum)
        else:
            title = _('Involved topics')
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
        title = _('New posts')

    invisible = [f.id for f in Forum.objects.get_forums_filtered(request.user, reverse=True)]
    if invisible:
        topics = topics.exclude(forum__id__in=invisible)

    forum_obj = None
    if forum:
        forum_obj = Forum.objects.get_cached(forum)
        if forum_obj and forum_obj.id not in invisible:
            topics = topics.filter(forum=forum_obj)

    total_topics = get_simplified_queryset(topics).count()
    topics = topics.values_list('id', flat=True)
    pagination = Pagination(request, topics, page, TOPICS_PER_PAGE, url,
                            total=total_topics, max_pages=MAX_PAGES_TOPICLIST)
    topic_ids = [tid for tid in pagination.get_queryset()]

    # check for moderation permissions
    moderatable_forums = [
        obj.id for obj in
        Forum.objects.get_forums_filtered(request.user, 'forum.moderate_forum', reverse=True)
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
    if request.user.is_anonymous:
        messages.info(request, _('You need to be logged in to use this function.'))
        return abort_access_denied(request)

    posts = Post.objects.filter(author=user).order_by('-pub_date')

    if topic_slug is not None:
        posts = posts.filter(topic__slug=topic_slug)
        pagination_url = href('forum', 'author', user.username, 'topic', topic_slug)
    elif forum_slug is not None:
        posts = posts.filter(topic__forum__slug=forum_slug)
        pagination_url = href('forum', 'author', user.username, 'forum', forum_slug)
    else:
        pagination_url = href('forum', 'author', user.username)

    # hidden forums is much faster than checking for visible forums
    hidden_ids = [f.id for f in Forum.objects.get_forums_filtered(request.user, reverse=True)]
    if hidden_ids:
        posts = posts.exclude(topic__forum__id__in=hidden_ids)

    total_posts = get_simplified_queryset(posts).count()

    # at least with MySQL we need this, as it is the fastest method
    posts = posts.values_list('id', flat=True)

    pagination = Pagination(request, posts, page, TOPICS_PER_PAGE, pagination_url,
        total=total_posts, max_pages=MAX_PAGES_TOPICLIST)
    post_ids = [post_id for post_id in pagination.get_queryset()]

    posts = Post.objects.filter(id__in=post_ids).order_by('-pub_date').select_related('topic', 'topic__forum', 'author')

    # check for moderation permissions
    moderatable_forums = [
        obj.id for obj in
        Forum.objects.get_forums_filtered(request.user, 'forum.moderate_forum')
    ]

    def can_moderate(topic):
        return topic.forum_id in moderatable_forums

    topic = None
    forum = None

    if topic_slug is not None and len(posts):
        topic = posts[0].topic
        title = _('Posts by “{user}” in topic “{topic}”').format(user=user.username, topic=topic.title)
    elif forum_slug is not None and len(posts):
        forum = posts[0].topic.forum
        title = _('Posts by “{user}” in forum “{forum}”').format(user=user.username, forum=forum.name)
    else:
        title = _('Posts by “{user}”').format(user=user.username)

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


class WelcomeMessageView(GuardianPermissionRequiredMixin, DetailView):
    """
    View has shows the welcome message of a forum.

    The user can accept the message with a post request with the key accept
    set to True.
    """
    model = Forum
    template_name = 'forum/welcome.html'
    permission_required = 'forum.view_forum'

    def dispatch(self, *args, **kwargs):
        """
        If the forum does not have a welcome message, then 404 is raised.
        """
        self.object = self.get_object()
        if not self.object.welcome_title:
            raise Http404()
        return super().dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Set the accepted status of the request.user to either accepted or
        rejected and redirects to the main forum page if rejected or to the
        forum if accepted.
        """
        accepted = self.request.POST.get('accept', False)
        self.object.read_welcome(self.request.user, accepted)
        if accepted:
            return HttpResponseRedirect(url_for(self.object))
        return HttpResponseRedirect(href('forum'))


@does_not_exist_is_404
def next_topic(request, topic_slug):
    this = Topic.objects.get(slug=topic_slug)
    next = Topic.objects.filter(forum=this.forum,
                                last_post__gt=this.last_post) \
                        .order_by('last_post').all()
    if not next.exists():
        messages.info(request, _('No recent topics within this forum.'))
        next = [this.forum]
    return HttpResponseRedirect(url_for(next[0]))


@does_not_exist_is_404
def previous_topic(request, topic_slug):
    this = Topic.objects.get(slug=topic_slug)

    previous = Topic.objects.filter(forum=this.forum,
                                    last_post__lt=this.last_post) \
                            .order_by('-last_post').all()
    if not previous.exists():
        messages.info(request, _('No older topics within this forum.'))
        previous = [this.forum]
    return HttpResponseRedirect(url_for(previous[0]))


class ForumEditMixin(PermissionRequiredMixin):
    """
    Mixin for the ForumCreateView and the ForumUpdateView.
    """
    permission_required = 'forum.change_forum'
    model = Forum
    form_class = EditForumForm
    template_name = 'forum/forum_edit.html'

    def form_valid(self, form):
        if self.object and ('welcome_title' in form.changed_data or 'welcome_text' in form.changed_data):
            self.object.clear_welcome()
        return super().form_valid(form)


class ForumCreateView(ForumEditMixin, CreateView):
    """
    View to create a new forum.
    """


class ForumUpdateView(ForumEditMixin, UpdateView):
    """
    View to update an existing forum.
    """
