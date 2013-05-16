# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.views
    ~~~~~~~~~~~~~~~~~~~

    Views for Ikhaya.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import pytz
from datetime import datetime, date, time as dt_time

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils.dates import MONTHS
from django.utils.http import urlencode
from django.utils.text import Truncator
from django.utils.translation import ugettext as _
from django.utils.html import escape

from inyoka.utils import ctype
from inyoka.utils.urls import href, url_for, is_safe_domain
from inyoka.utils.http import templated, AccessDeniedResponse, \
    does_not_exist_is_404
from inyoka.utils.feeds import atom_feed, AtomFeed
from inyoka.utils.pagination import Pagination
from inyoka.utils import generic
from inyoka.utils.dates import get_user_timezone, date_time_to_datetime
from inyoka.utils.notification import send_notification
from inyoka.markup import parse, RenderContext
from inyoka.utils.templating import render_template
from inyoka.utils.flash_confirmation import confirm_action
from inyoka.utils.sortable import Sortable
from inyoka.utils.storage import storage
from inyoka.portal.utils import check_login, require_permission
from inyoka.portal.user import User
from inyoka.portal.models import PrivateMessage, PrivateMessageEntry, \
    Subscription
from inyoka.ikhaya.forms import SuggestArticleForm, EditCommentForm, \
    EditArticleForm, EditPublicArticleForm, EditCategoryForm, \
    EditEventForm, NewEventForm
from inyoka.ikhaya.models import Event, Category, Article, Suggestion, \
    Comment, Report
from inyoka.ikhaya.notifications import send_comment_notifications, \
    send_new_suggestion_notifications


def context_modifier(request, context):
    """
    This function adds two things to the context of all ikhaya pages:
    `archive`
        A list of the latest months with ikhaya articles.
    `categories`
        A list of all ikhaya categories.
    """
    key = 'ikhaya/archive'
    data = cache.get(key)
    if data is None:
        archive = list(Article.published.dates('pub_date', 'month', order='DESC'))
        if len(archive) > 5:
            archive = archive[:5]
            short_archive = True
        else:
            short_archive = False
        data = {
            'archive': archive,
            'short_archive': short_archive
        }
        cache.set(key, data)

    categories = cache.get('ikhaya/categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('ikhaya/categories', categories)

    context.update(
        MONTHS=MONTHS,
        categories=categories,
        ikhaya_description=storage['ikhaya_description'],
        **data
    )


event_delete = generic.DeleteView.as_view(model=Event,
    template_name='ikhaya/event_delete.html',
    redirect_url=href('ikhaya', 'events'),
    required_permission='event_edit')


@templated('ikhaya/index.html', modifier=context_modifier)
def index(request, year=None, month=None, category_slug=None, page=1, full=False):
    """Shows a few articles by different criteria"""
    def _generate_link(page, params):
        if page == 1:
            url = link
        else:
            url = u'%s%d/' % (link, page)
        return url + (full and 'full/' or '') + (params and u'?' + urlencode(params) or u'')

    category = None
    can_read = request.user.can('article_read')
    articles = Article.published if not can_read else Article.objects

    if year and month:
        articles = articles.filter(pub_date__year=year, pub_date__month=month)
        link = (year, month)
    elif category_slug:
        category = Category.objects.get(slug=category_slug)
        articles = articles.filter(category=category)
        link = ('category', category_slug)
    else:
        link = tuple()

    link = href('ikhaya', *link)
    articles = articles.order_by('public', '-updated').only('pub_date', 'slug')
    pagination = Pagination(request, articles, page, 15, _generate_link)
    articles = Article.objects.get_cached([(a.pub_date, a.slug) for a in
        pagination.get_queryset()])

    subscription_ids = []
    if not request.user.is_anonymous:
        subscription_ids = Subscription.objects.values_list('object_id', flat=True) \
            .filter(user=request.user, content_type=ctype(Article))

    return {
        'articles': articles,
        'pagination': pagination,
        'category': category,
        'subscription_ids': subscription_ids,
        'full': full,
        'show_full_choice': True,
    }


@templated('ikhaya/detail.html', modifier=context_modifier)
def detail(request, year, month, day, slug):
    """Shows a single article."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise Http404()
    preview = None
    if article.hidden or article.pub_datetime > datetime.utcnow():
        if not request.user.can('article_read'):
            return AccessDeniedResponse()
        messages.info(request, _(u'This article is not visible for regular users.'))

    if request.method == 'POST' and (not article.comments_enabled or not request.user.is_authenticated()):
        return AccessDeniedResponse()

    # clear notification status
    subscribed = Subscription.objects.user_subscribed(request.user, article, clear_notified=True)

    if article.comments_enabled and request.method == 'POST':
        form = EditCommentForm(request.POST)
        if 'preview' in request.POST:
            ctx = RenderContext(request)
            preview = parse(request.POST.get('text', '')).render(ctx, 'html')
        elif form.is_valid():
            send_subscribe = False
            data = form.cleaned_data
            if data.get('comment_id') and request.user.can('comment_edit'):
                c = Comment.objects.get(id=data['comment_id'])
                c.text = data['text']
                messages.success(request, _(u'The comment was edited successfully.'))
            else:
                send_subscribe = True
                c = Comment(text=data['text'])
                c.article = article
                c.author = request.user
                c.pub_date = datetime.utcnow()
                messages.success(request, _(u'Your comment was created.'))
            c.save()
            if send_subscribe:
                # Send a message to users who subscribed to the article
                send_comment_notifications(request.user, c, article)

            return HttpResponseRedirect(url_for(c))
    elif request.GET.get('moderate'):
        comment = Comment.objects.get(id=int(request.GET.get('moderate')))
        form = EditCommentForm(initial={
            'comment_id': comment.id,
            'text': comment.text,
        })
    else:
        form = EditCommentForm()
    return {
        'article': article,
        'comments': article.comment_set.select_related('author'),
        'form': form,
        'preview': preview,
        'can_post_comment': request.user.is_authenticated(),
        'can_subscribe': request.user.is_authenticated(),
        'can_admin_comment': request.user.can('comment_edit'),
        'can_edit_article': request.user.can('article_edit'),
        'is_subscribed': subscribed
    }


@require_permission('article_edit')
def article_delete(request, year, month, day, slug):
    try:
        """
        do not access cached object!
        This would lead to inconsistent form content
        """
        article = Article.objects.get(pub_date=date(int(year), int(month),
            int(day)), slug=slug)
    except IndexError:
        raise Http404()
    if request.method == 'POST':
        if 'unpublish' in request.POST:
            article.public = False
            article.save()
            messages.info(request,
                _(u'The publication of the article '
                  u'“<a href="%(link)s">%(title)s</a>” has been revoked.')
                % {'link': escape(url_for(article, 'show')),
                     'title': escape(article.subject)})
        elif 'cancel' in request.POST:
            messages.info(request,
                _(u'Deletion of the article “<a href="%(link)s">%(title)s</a>” was canceled.')
                % {'link': escape(url_for(article, 'show')),
                     'title': escape(article.subject)})
        else:
            article.delete()
            messages.success(request,
                _(u'The article “%(title)s” was deleted.')
                % {'title': escape(article.subject)})
    else:
        messages.info(request,
            render_template('ikhaya/article_delete.html',
            {'article': article}))
    return HttpResponseRedirect(href('ikhaya'))


@require_permission('article_edit')
@templated('ikhaya/article_edit.html', modifier=context_modifier)
def article_edit(request, year=None, month=None, day=None, slug=None, suggestion_id=None):
    """
    Display an interface to let the user create or edit an article.
    If `suggestion_id` is given, the new ikhaya article is based on a special
    article suggestion made by a user. After saving it, the suggestion will be
    deleted automatically.
    """
    preview = None
    initial = {'author': request.user}

    if year and month and day and slug:
        try:
            """
            do not access cached object!
            This would lead to inconsistent form content
            """
            article = Article.objects.get(pub_date=date(int(year), int(month),
                int(day)), slug=slug)
        except IndexError:
            raise Http404()
        locked = article.lock(request)
        if locked:
            messages.error(request,
                _(u'This article is currently being edited by “%(user)s”!')
                % {'user': locked})
    else:
        article = None

    if request.method == 'POST':
        if article and article.public:
            form = EditPublicArticleForm(request.POST, instance=article,
                                         initial=initial)
        else:
            form = EditArticleForm(request.POST, instance=article,
                                   initial=initial)
        if 'send' in request.POST:
            if form.is_valid():
                new = article is None
                article = form.save()
                article.unlock()
                if suggestion_id:
                    Suggestion.objects.delete([suggestion_id])
                if new:
                    messages.success(request,
                        _(u'The article “%(title)s” was created.')
                        % {'title': escape(article.subject)})
                    return HttpResponseRedirect(url_for(article, 'edit'))
                else:
                    messages.success(request,
                        _(u'The article “%(title)s” was saved.')
                        % {'title': escape(article.subject)})
                    cache.delete('ikhaya/article/%s/%s' %
                                 (article.pub_date, article.slug))
                    keys = ['ikhaya/latest_articles',
                            'ikhaya/latest_articles/%s' % article.category.slug,
                            'ikhaya/article/%s/%s' % (article.pub_date, article.slug)]
                    cache.delete_many(keys)
                    return HttpResponseRedirect(url_for(article))
        elif 'preview' in request.POST:
            ctx = RenderContext(request)
            preview = parse('%s\n\n%s' % (request.POST.get('intro', ''),
                            request.POST.get('text'))).render(ctx, 'html')
    else:
        if slug:
            if article.public:
                form = EditPublicArticleForm(instance=article, initial=initial)
            else:
                form = EditArticleForm(instance=article, initial=initial)
        elif suggestion_id:
            suggestion = Suggestion.objects.get(id=suggestion_id)
            form = EditArticleForm(initial={
                'subject': suggestion.title,
                'text': suggestion.text,
                'intro': suggestion.intro,
                'author': suggestion.author,
            })
        else:
            form = EditArticleForm(initial=initial)

    return {
        'form': form,
        'article': article,
        'preview': preview,
    }


@check_login(message=_(u'You need to be logged in to subscribe to comments.'))
def article_subscribe(request, year, month, day, slug):
    """Subscribe to article's comments."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise Http404()
    if article.hidden or article.pub_datetime > datetime.utcnow():
        if not request.user.can('article_read'):
            return AccessDeniedResponse()
    try:
        Subscription.objects.get_for_user(request.user, article)
    except Subscription.DoesNotExist:
        Subscription(user=request.user, content_object=article).save()
        messages.info(request,
            _(u'Notifications on new comments to this article will be sent '
              u'to you.'))
    redirect = is_safe_domain(request.GET.get('next', '')) and \
               request.GET['next'] or url_for(article)
    return HttpResponseRedirect(redirect)


@check_login(message=_(u'You need to be logged in to unsubscribe from '
                       'comments.'))
def article_unsubscribe(request, year, month, day, slug):
    """Unsubscribe from article."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise Http404()
    try:
        subscription = Subscription.objects.get_for_user(request.user, article)
    except Subscription.DoesNotExist:
        pass
    else:
        subscription.delete()
        messages.info(request,
            _(u'You will no longer be notified of new comments for this '
              u'article.'))
    redirect = is_safe_domain(request.GET.get('next', '')) and \
               request.GET['next'] or url_for(article)
    return HttpResponseRedirect(redirect)


@check_login()
@templated('ikhaya/report_new.html', modifier=context_modifier)
def report_new(request, year, month, day, slug):
    """Report a mistake in an article."""
    preview = None
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise Http404()

    if request.method == 'POST':
        form = EditCommentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if 'preview' in request.POST:
                ctx = RenderContext(request)
                preview = parse(data['text']).render(ctx, 'html')
            elif 'send' in request.POST:
                report = Report(text=data['text'])
                report.article = article
                report.author = request.user
                report.pub_date = datetime.utcnow()
                report.save()
                cache.delete('ikhaya/reported_article_count')
                messages.success(request, _(u'Thanks for your report.'))
                return HttpResponseRedirect(url_for(report))
    else:
        form = EditCommentForm()
    return {
        'article': article,
        'form': form,
        'preview': preview
    }


@require_permission('article_edit')
def _change_report_status(request, report_id, action, msg):
    report = Report.objects.get(id=report_id)
    if action == 'hide':
        report.deleted = True
    elif action == 'restore':
        report.deleted = False
    elif action == 'solve':
        report.solved = True
    elif action == 'unsolve':
        report.solved = False
    report.save()
    cache.delete('ikhaya/reported_article_count')
    messages.success(request, msg)
    return HttpResponseRedirect(url_for(report))


@confirm_action(_(u'Do you want to hide this report?'),
                confirm=_(u'Hide'), cancel=_(u'Cancel'))
def report_hide(request, report_id):
    return _change_report_status(request, report_id, 'hide',
                _(u'The report was hidden.'))


@confirm_action(_(u'Do you want to restore this report?'),
                confirm=_(u'Restore'), cancel=_(u'Cancel'))
def report_restore(request, report_id):
    return _change_report_status(request, report_id, 'restore',
                _(u'The report was restored.'))


@confirm_action(_(u'Do you want to mark this report as solved?'),
                confirm=_(u'Mark as solved'), cancel=_(u'Cancel'))
def report_solve(request, report_id):
    return _change_report_status(request, report_id, 'solve',
                _(u'The report was marked as solved.'))


@confirm_action(_(u'Do you want to mark this report as unsolved?'),
                confirm=_(u'Mark as unsolved'), cancel=_(u'Cancel'))
def report_unsolve(request, report_id):
    return _change_report_status(request, report_id, 'unsolve',
                _(u'The report was marked as unsolved.'))


@templated('ikhaya/reports.html', modifier=context_modifier)
def reports(request, year, month, day, slug):
    """Shows a list of suggested improved versions of the article."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise Http404()
    return {
        'article': article,
        'reports': article.report_set.select_related(),
        'can_edit': request.user.can('article_edit')
    }


@require_permission('article_edit')
@templated('ikhaya/reportlist.html', modifier=context_modifier)
def reportlist(request):
    """Get a list of all unsolved article reports."""
    reports = Report.objects.filter(solved=False).filter(deleted=False)
    return {
        'reports': reports
    }


@templated('ikhaya/comment_edit.html', modifier=context_modifier)
def comment_edit(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    if not request.user.can('comment_edit') and request.user == comment.author:
        messages.error(request, _(u'Sorry, editing comments is disabled for now.'))
        return HttpResponseRedirect(url_for(comment.article))
    if request.user.can('comment_edit'):
        if request.method == 'POST':
            form = EditCommentForm(request.POST)
            if form.is_valid():
                comment.text = form.cleaned_data['text']
                comment.save()
                messages.success(request, _(u'The comment was saved.'))
                return HttpResponseRedirect(comment.get_absolute_url())
        else:
            form = EditCommentForm(initial={'text': comment.text})
        return {
            'comment': comment,
            'form': form,
        }
    return AccessDeniedResponse()


@require_permission('comment_edit')
def _change_comment_status(request, comment_id, hide, msg):
    c = Comment.objects.get(id=comment_id)
    c.deleted = hide
    c.save()
    messages.success(request, msg)
    return HttpResponseRedirect(url_for(c.article))


@confirm_action(_(u'Do you want to hide this comment?'),
                confirm=_(u'Hide'), cancel=_(u'Cancel'))
def comment_hide(request, comment_id):
    return _change_comment_status(request, comment_id, True,
                _(u'The comment was hidden.'))


@confirm_action(_(u'Do you want to restore this comment?'),
                confirm=_(u'Restore'), cancel=_(u'Cancel'))
def comment_restore(request, comment_id):
    return _change_comment_status(request, comment_id, False,
                _(u'The comment was restored.'))


@templated('ikhaya/archive.html', modifier=context_modifier)
def archive(request):
    """Shows the archive index."""
    months = Article.published.dates('pub_date', 'month')
    return {
        'months': months
    }


def suggest_assign_to(request, suggestion, username):
    try:
        suggestion = Suggestion.objects.get(id=suggestion)
    except Suggestion.DoesNotExist:
        messages.error(request,
            _(u'The suggestion “%(title)s” does not exist.')
            % {'title': suggestion})
        return HttpResponseRedirect(href('ikhaya', 'suggestions'))
    if username == '-':
        suggestion.owner = None
        suggestion.save()
        messages.success(request,
            _(u'The suggestion was assigned to nobody.'))
    else:
        try:
            suggestion.owner = User.objects.get(username)
        except User.DoesNotExist:
            raise Http404
        suggestion.save()
        messages.ssuccess(request, _(u'The suggestion was assigned to “%(user)s”.')
                                    % {'user': username})
    return HttpResponseRedirect(href('ikhaya', 'suggestions'))


@require_permission('article_edit')
def suggest_delete(request, suggestion):
    if request.method == 'POST':
        if not 'cancel' in request.POST:
            try:
                s = Suggestion.objects.get(id=suggestion)
            except Suggestion.DoesNotExist:
                messages.error(request, (_(u'This suggestion does not exist.')))
                return HttpResponseRedirect(href('ikhaya', 'suggestions'))
            if request.POST.get('note'):
                args = {'title': s.title,
                        'username': request.user.username,
                        'note': request.POST['note']}
                send_notification(s.author, u'suggestion_rejected',
                    _(u'Article suggestion deleted'), args)

                # Send the user a private message
                msg = PrivateMessage()
                msg.author = request.user
                msg.subject = _(u'Article suggestion deleted')
                msg.text = render_template('mails/suggestion_rejected.txt', args)
                msg.pub_date = datetime.utcnow()
                recipients = [s.author]
                msg.send(recipients)
                # send notification
                for recipient in recipients:
                    entry = PrivateMessageEntry.objects \
                        .filter(message=msg, user=recipient)[0]
                    if 'pm_new' in recipient.settings.get('notifications',
                                                          ('pm_new',)):
                        title = _(u'New private message from %(user)s: '
                                  '%(subject)s') % {
                                      'user': request.user.username,
                                      'subject': msg.subject,
                                  }
                        send_notification(recipient, 'new_pm', title, {
                                          'user': recipient,
                                              'sender': request.user,
                                              'subject': msg.subject,
                                              'entry': entry,
                                          })

            cache.delete('ikhaya/suggestion_count')
            s.delete()
            messages.success(request, _(u'The suggestion was deleted.'))
        else:
            messages.info(request, _(u'The suggestion was not deleted.'))
        return HttpResponseRedirect(href('ikhaya', 'suggestions'))
    else:
        try:
            s = Suggestion.objects.get(id=suggestion)
        except Suggestion.DoesNotExist:
            messages.error(request, _(u'This suggestion does not exist.'))
            return HttpResponseRedirect(href('ikhaya', 'suggestions'))
        messages.info(request,
            render_template('ikhaya/suggest_delete.html', {'s': s}))
        return HttpResponseRedirect(href('ikhaya', 'suggestions'))


@check_login(message=_(u'Please login to suggest an article.'))
@templated('ikhaya/suggest_new.html', modifier=context_modifier)
def suggest_edit(request):
    """A Page to suggest a new article.

    It just sends an email to the administrators.

    """
    preview = None
    if request.method == 'POST':
        form = SuggestArticleForm(request.POST)
        if 'preview' in request.POST:
            ctx = RenderContext(request)
            preview = parse(request.POST.get('text', '')).render(ctx, 'html')
        elif form.is_valid():
            suggestion = form.save(request.user)
            cache.delete('ikhaya/suggestion_count')
            messages.success(request,
                _(u'Thank you, your article suggestion was submitted. A team '
                  u'member will contact you shortly.'))

            # Send a notification message
            send_new_suggestion_notifications(request.user, suggestion)
            return HttpResponseRedirect(href('ikhaya'))
    else:
        form = SuggestArticleForm()
    return {
        'form': form,
        'preview': preview
    }


@require_permission('article_edit')
@templated('ikhaya/suggestions.html', modifier=context_modifier)
def suggestions(request):
    """Get a list of all article suggestions"""
    # clear notification status
    subscribed = Subscription.objects.user_subscribed(request.user,
                 None, ['ikhaya', 'suggestion'], clear_notified=True)
    suggestions = Suggestion.objects.all()
    return {
        'suggestions': list(suggestions),
        'is_subscribed': subscribed,
    }


category_edit = generic.CreateUpdateView(
                        model=Category, form_class=EditCategoryForm,
                        template_name='ikhaya/category_edit.html',
                        context_object_name='category',
                        urlgroup_name='category_slug',
                        required_permission='category_edit')


@require_permission('event_edit')
@templated('ikhaya/events.html', modifier=context_modifier)
def events(request, show_all=False, invisible=False):
    if show_all:
        objects = Event.objects.filter(visible=True).all()
    elif invisible:
        objects = Event.objects.filter(visible=False).all()
    else:
        objects = Event.objects.filter(date__gt=date.today(), visible=True)
    sortable = Sortable(objects, request.GET, '-date',
        columns=['name', 'date'])
    return {
        'table': sortable,
        'events': sortable.get_queryset(),
        'show_all': show_all,
        'invisible': invisible,
    }


@require_permission('article_edit')
def suggestions_subscribe(request):
    """Subscribe to new suggestions."""
    ct_query = ['ikhaya', 'suggestion']
    try:
        Subscription.objects.get_for_user(request.user, None, ct_query)
    except Subscription.DoesNotExist:
        ct = ContentType.objects.get_by_natural_key(*ct_query)
        Subscription(user=request.user, content_type=ct).save()
        messages.info(request, _(u'Notifications on new suggestions will be sent to you.'))
    redirect = is_safe_domain(request.GET.get('next', '')) and \
               request.GET['next'] or href('ikhaya', 'suggestions')
    return HttpResponseRedirect(redirect)


@require_permission('article_edit')
def suggestions_unsubscribe(request):
    """Unsubscribe from new suggestions."""
    try:
        subscription = Subscription.objects.get_for_user(request.user,
                       None, ['ikhaya', 'suggestion'])
    except Subscription.DoesNotExist:
        pass
    else:
        subscription.delete()
        messages.info(request, _(u'No notifications on suggestions will be sent to you any more.'))
    redirect = is_safe_domain(request.GET.get('next', '')) and \
               request.GET['next'] or href('ikhaya', 'suggestions')
    return HttpResponseRedirect(redirect)


@require_permission('event_edit')
@templated('ikhaya/event_edit.html', modifier=context_modifier)
def event_edit(request, pk=None):
    new = not pk
    event = Event.objects.get(id=pk) if not new else None

    if request.GET.get('copy_from', None):
        if not event:
            event = Event()
        try:
            base_event = Event.objects.get(pk=int(request.GET['copy_from']))
        except Event.DoesNotExist:
            messages.error(request,
                _(u'The event with the id %(id)s could not be used as draft '
                  u'for a new event because it does not exist.')
                % {'id': request.GET['copy_from']})
        else:
            fields = ('name', 'changed', 'created', 'date', 'time',
                      'enddate', 'endtime', 'description', 'author_id',
                      'location', 'location_town', 'location_lat',
                      'location_long')
            for key in fields:
                setattr(event, key, getattr(base_event, key))
            event.visible = False

    if request.method == 'POST':
        form = EditEventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(request.user)
            messages.success(request, _(u'The event was saved.'))
            if new:
                cache.delete('ikhaya/event_count')
            return HttpResponseRedirect(url_for(event))
    else:
        form = EditEventForm(instance=event)

    return {
        'form': form,
        'mode': 'new' if new else 'edit',
        'event': event,
    }


@templated('ikhaya/event_suggest.html', modifier=context_modifier)
def event_suggest(request):
    """
    User form which creates to suggest new events for the calendar.
    """
    if request.method == 'POST':
        form = NewEventForm(request.POST)
        if form.is_valid():
            event = Event()
            convert = (lambda v: get_user_timezone().localize(v)
                                .astimezone(pytz.utc).replace(tzinfo=None))
            data = form.cleaned_data
            event.name = data['name']
            if data['date'] and data['time']:
                d = convert(date_time_to_datetime(
                    data['date'],
                    data['time'] or dt_time(0)
                ))
                event.date = d.date()
                event.time = d.time()
            else:
                event.date = data['date']
                event.time = None
            if data['endtime']:
                d = convert(date_time_to_datetime(
                    data['enddate'] or event.date,
                    data['endtime']
                ))
                event.enddate = d.date()
                event.endtime = event.time and d.time()
            else:
                event.enddate = data['enddate'] or None
                event.endtime = None
            event.description = data['description']
            event.author = request.user
            event.location = data['location']
            event.location_town = data['location_town']
            if data['location_lat'] and data['location_long']:
                event.location_lat = data['location_lat']
                event.location_long = data['location_long']
            event.save()
            cache.delete('ikhaya/event_count')
            messages.success(request,
                _(u'The event has been saved. A team member will review it '
                  u'soon.'))
            event = Event.objects.get(id=event.id)  # get truncated slug
            return HttpResponseRedirect(url_for(event))
    else:
        form = NewEventForm()

    return {
        'form': form,
    }


@atom_feed(name='ikhaya_feed_article')
def feed_article(request, slug=None, mode='short', count=10):
    """
    Shows the ikhaya entries that match the given criteria in an atom feed.
    """
    if slug:
        title = u'%s Ikhaya – %s' % (settings.BASE_DOMAIN_NAME, slug)
        url = href('ikhaya', 'category', slug)
    else:
        title = u'%s Ikhaya' % settings.BASE_DOMAIN_NAME
        url = href('ikhaya')

    articles = Article.objects.get_latest_articles(slug, count)

    feed = AtomFeed(title, feed_url=request.build_absolute_uri(),
                    url=url, rights=href('portal', 'lizenz'), id=url,
                    icon=href('static', 'img', 'favicon.ico'),
                    subtitle=storage['ikhaya_description'])

    for article in articles:
        kwargs = {}
        if mode == 'full':
            kwargs['content'] = u'%s\n%s' % (article.rendered_intro,
                                             article.rendered_text)
            kwargs['content_type'] = 'xhtml'
        if mode == 'short':
            kwargs['summary'] = article.rendered_intro
            kwargs['summary_type'] = 'xhtml'

        feed.add(
            title=article.subject,
            url=url_for(article),
            updated=article.updated,
            published=article.pub_datetime,
            author={
                'name': article.author.username,
                'uri': url_for(article.author)
            },
            **kwargs
        )
    return feed


@atom_feed(name='ikhaya_feed_comment')
@does_not_exist_is_404
def feed_comment(request, id=None, mode='short', count=10):
    """
    Shows the ikhaya comments that match the given criteria in an atom feed.
    """
    article = None
    if id:
        article = Article.published.get(id=id)
        title = _(u'%(domain)s Ikhaya comments – %(title)s') % {
                    'domain': settings.BASE_DOMAIN_NAME,
                    'title': article.subject}
        url = url_for(article)
    else:
        title = _(u'%(domain)s Ikhaya comments') % {
                    'domain': settings.BASE_DOMAIN_NAME}
        url = href('ikhaya')

    comments = Comment.objects.get_latest_comments(article.id if article else None, count)

    feed = AtomFeed(title, feed_url=request.build_absolute_uri(),
                    subtitle=storage['ikhaya_description'],
                    rights=href('portal', 'lizenz'),
                    id=url, url=url, icon=href('static', 'img', 'favicon.ico'),)

    for comment in comments[:count]:
        kwargs = {}
        if mode == 'full':
            kwargs['content'] = comment.rendered_text
            kwargs['content_type'] = 'xhtml'
        if mode == 'short':
            kwargs['summary'] = Truncator(comment.rendered_text).words(100, html=True)
            kwargs['summary_type'] = 'xhtml'

        if article is None:
            article = comment.article

        feed.add(
            title=u'Re: %s' % article.subject,
            url=url_for(comment),
            updated=comment.pub_date,
            published=comment.pub_date,
            author={
                'name': comment.author.username,
                'uri': url_for(comment.author)
            },
            **kwargs
        )
    return feed
