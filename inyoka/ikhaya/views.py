# -*- coding: utf-8 -*-
"""
    inyoka.ikhaya.views
    ~~~~~~~~~~~~~~~~~~~

    Views for Ikhaya.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import pytz
from datetime import datetime, date, time as dt_time

from django.core.cache import cache
from django.utils.http import urlencode
from django.utils.text import truncate_html_words
from django.contrib.contenttypes.models import ContentType

from inyoka.utils import ctype
from inyoka.utils.urls import href, url_for, global_not_found, is_safe_domain
from inyoka.utils.http import templated, AccessDeniedResponse, \
     HttpResponseRedirect, PageNotFound, does_not_exist_is_404
from inyoka.utils.feeds import atom_feed, AtomFeed
from inyoka.utils.flashing import flash
from inyoka.utils.pagination import Pagination
from inyoka.utils import generic
from inyoka.utils.dates import MONTHS, get_user_timezone, date_time_to_datetime
from inyoka.utils.sortable import Sortable
from inyoka.utils.templating import render_template
from inyoka.utils.notification import send_notification
from inyoka.utils.html import escape
from inyoka.portal.utils import check_login, require_permission
from inyoka.portal.user import User
from inyoka.portal.models import PrivateMessage, PrivateMessageEntry, \
     Subscription
from inyoka.ikhaya.forms import SuggestArticleForm, EditCommentForm, \
     EditArticleForm, EditPublicArticleForm, EditCategoryForm, \
     EditEventForm, NewEventForm
from inyoka.ikhaya.models import Event, Category, Article, Suggestion, \
     Comment, Report
from inyoka.wiki.parser import parse, RenderContext
from inyoka.ikhaya.notifications import send_comment_notifications, \
    send_new_suggestion_notifications


IKHAYA_DESCRIPTION = u'Ikhaya ist der Nachrichtenblog der ubuntuusers-' \
    u'Community. Hier werden Nachrichten und Berichte rund um Ubuntu, Linux' \
    u' und OpenSource-Software veröffentlicht.'


def not_found(request, err_message=None):
    """
    This is called if no URL matches or a view returned a `PageNotFound`.
    """
    from inyoka.ikhaya.legacyurls import test_legacy_url
    response = test_legacy_url(request)
    if response is not None:
        return response
    return global_not_found(request, 'ikhaya', err_message)


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
            'archive':       archive,
            'short_archive': short_archive
        }
        cache.set(key, data)

    categories = cache.get('ikhaya/categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('ikhaya/categories', categories)

    context.update(
        MONTHS=dict(enumerate([''] + MONTHS)),
        categories=categories,
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
        raise PageNotFound()
    preview = None
    if article.hidden or article.pub_datetime > datetime.utcnow():
        if not request.user.can('article_read'):
            return AccessDeniedResponse()
        flash(u'Dieser Artikel ist für reguläre Benutzer nicht sichtbar.')

    if request.method == 'POST' and not article.comments_enabled or not request.user.is_authenticated:
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
                flash(u'Der Kommentar wurde erfolgreich bearbeitet.', True)
            else:
                send_subscribe = True
                c = Comment(text=data['text'])
                c.article = article
                c.author = request.user
                c.pub_date = datetime.utcnow()
                flash(u'Dein Kommentar wurde erstellt.', True)
            c.save()
            if send_subscribe:
                # Send a message to users who subscribed to the article
                send_comment_notifications(request.user, c, article)

            return HttpResponseRedirect(url_for(c))
    elif request.GET.get('moderate'):
        comment = Comment.objects.get(id=int(request.GET.get('moderate')))
        form = EditCommentForm(initial={
            'comment_id':   comment.id,
            'text':         comment.text,
        })
    else:
        form = EditCommentForm()
    return {
        'article':  article,
        'comments': article.comment_set.select_related('author'),
        'form': form,
        'preview': preview,
        'can_post_comment': request.user.is_authenticated,
        'can_subscribe': request.user.is_authenticated,
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
        raise PageNotFound()
    if request.method == 'POST':
        if 'unpublish' in request.POST:
            article.public = False
            article.save()
            flash(u'Die Veröffentlichung des Artikels „<a href="%s">%s</a>“'
                  ' wurde aufgehoben.'
                  % (escape(url_for(article, 'show')), escape(article.subject)))
        elif 'cancel' in request.POST:
            flash(u'Löschen des Artikels „<a href="%s">%s</a>“ wurde abgebrochen.'
                  % (escape(url_for(article, 'show')), escape(article.subject)))
        else:
            article.delete()
            flash(u'Der Artikel „%s“ wurde erfolgreich gelöscht.'
                  % escape(article.subject), True)
    else:
        flash(render_template('ikhaya/article_delete.html',
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
            raise PageNotFound()
        locked = article.lock(request)
        if locked:
            flash(u'Dieser Artikel wird bereits von „%s” bearbeitet!' % locked, False)
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
                    flash(u'Der Artikel „%s“ wurde erstellt.'
                          % escape(article.subject), True)
                    return HttpResponseRedirect(url_for(article, 'edit'))
                else:
                    flash(u'Der Artikel „%s“ wurde gespeichert.'
                          % escape(article.subject), True)
                    cache.delete('ikhaya/article/%s/%s' %
                                 (article.pub_date, article.slug))
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
                'text':    suggestion.text,
                'intro':   suggestion.intro,
                'author':  suggestion.author,
            })
        else:
            form = EditArticleForm(initial=initial)

    return {
        'form': form,
        'article': article,
        'preview': preview,
    }


@check_login(message=u'Du musst angemeldet sein um Kommentare abonnieren '
                     u'zu können')
def article_subscribe(request, year, month, day, slug):
    """Subscribe to article's comments."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise PageNotFound()
    if article.hidden or article.pub_datetime > datetime.utcnow():
        if not request.user.can('article_read'):
            return AccessDeniedResponse()
    try:
        Subscription.objects.get_for_user(request.user, article)
    except Subscription.DoesNotExist:
        Subscription(user=request.user, content_object=article).save()
        flash(u'Du wirst ab nun über neue Kommentare zu diesem Artikel '
              u'benachrichtigt.')
    redirect = is_safe_domain(request.GET.get('next', '')) and \
               request.GET['next'] or url_for(article)
    return HttpResponseRedirect(redirect)


@check_login(message=u'Du musst angemeldet sein um Kommentare abonnieren '
                     u'zu können')
def article_unsubscribe(request, year, month, day, slug):
    """Unsubscribe from article."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise PageNotFound()
    try:
        subscription = Subscription.objects.get_for_user(request.user, article)
    except Subscription.DoesNotExist:
        pass
    else:
        subscription.delete()
        flash(u'Du wirst nun nicht mehr über neue Kommentare zu diesem '
              u'Artikel benachrichtigt.')
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
        raise PageNotFound()

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
                flash(u'Vielen Dank für deine Meldung.', True)
                return HttpResponseRedirect(url_for(report))
    else:
        form = EditCommentForm()
    return {
        'article': article,
        'form': form,
        'preview': preview
    }


def report_update(action, text):
    @require_permission('article_edit')
    def do(request, report_id):
        report = Report.objects.get(id=report_id)
        if request.method == 'POST':
            if 'cancel' in request.POST:
                return HttpResponseRedirect(url_for(report))
            if action == 'hide':
                report.deleted = True
            elif action == 'restore':
                report.deleted = False
            elif action == 'solve':
                report.solved = True
            elif action == 'unsolve':
                report.solved = False
            report.save()
            flash(text, True)
        else:
            flash(render_template('ikhaya/report_update.html',
                {'report': report, 'action': action}))
        return HttpResponseRedirect(url_for(report))
    return do

report_hide = report_update('hide', u'Die Meldung wurde verborgen.')
report_restore = report_update('restore', u'Die Meldung wurde wiederhergestellt.')
report_solve = report_update('solve', u'Die Meldung wurde als erledigt markiert.')
report_unsolve = report_update('unsolve', u'Die Meldung wurde als nicht erledigt markiert.')

@templated('ikhaya/reports.html', modifier=context_modifier)
def reports(request, year, month, day, slug):
    """Shows a list of suggested improved versions of the article."""
    try:
        article = Article.objects.get_cached([(date(int(year), int(month),
            int(day)), slug)])[0]
    except IndexError:
        raise PageNotFound()
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
    user = request.user
    if user.can('comment_edit') or user.id == comment.author.id:
        if request.method == 'POST':
            form = EditCommentForm(request.POST)
            if form.is_valid():
                comment.text = form.cleaned_data['text']
                comment.save()
                flash('Der Kommentar wurde gespeichert', True)
                return HttpResponseRedirect(comment.get_absolute_url())
        else:
            form = EditCommentForm(initial={'text': comment.text})
        return {
            'comment':  comment,
            'form':     form,
        }
    return AccessDeniedResponse()


def comment_update(boolean, text):
    @require_permission('comment_edit')
    def do(request, comment_id):
        c = Comment.objects.get(id=comment_id)
        if request.method == 'POST':
            c.deleted = boolean
            c.save()
            flash(text, True)
        else:
            flash(render_template('ikhaya/comment_update.html',
                 {'comment': c, 'action': 'hide' if boolean else 'restore'}))
        return HttpResponseRedirect(url_for(c.article))
    return do


comment_hide = comment_update(True, u'Der Kommentar wurde verborgen.')
comment_restore = comment_update(False, u'Der Kommentar wurde wiederhergestellt.')


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
        flash(u'Der Vorschlag „%s” existiert nicht.' % suggestion)
        return HttpResponseRedirect(href('ikhaya', 'suggestions'))
    if username == '-':
        suggestion.owner = None
        suggestion.save()
        flash(u'Der Vorschlag wurde niemand zugewiesen.', True)
    else:
        try:
            suggestion.owner = User.objects.get(username)
        except User.DoesNotExist:
            raise PageNotFound
        suggestion.save()
        flash(u'Der Vorschlag wurde %s zugewiesen.' % username, True)
    return HttpResponseRedirect(href('ikhaya', 'suggestions'))


@require_permission('article_edit')
def suggest_delete(request, suggestion):
    if request.method == 'POST':
        if not 'cancel' in request.POST:
            try:
                s = Suggestion.objects.get(id=suggestion)
            except Suggestion.DoesNotExist:
                flash('Diesen Vorschlag gibt es nicht.', False)
                return HttpResponseRedirect(href('ikhaya', 'suggestions'))
            if request.POST.get('note'):
                args = {'title':    s.title,
                        'username': request.user.username,
                        'note':     request.POST['note']}
                send_notification(s.author, u'suggestion_rejected',
                    u'Ikhaya-Vorschlag gelöscht', args)

                # Send the user a private message
                msg = PrivateMessage()
                msg.author = request.user
                msg.subject = u'Ikhaya-Vorschlag gelöscht'
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
                        send_notification(recipient, 'new_pm', u'Neue private '
                                          u'Nachricht von %s: %s' %
                                          (request.user.username, msg.subject), {
                                              'user':     recipient,
                                              'sender':   request.user,
                                              'subject':  msg.subject,
                                              'entry':    entry,
                                          })

            cache.delete('ikhaya/suggestion_count')
            s.delete()
            flash(u'Der Vorschlag wurde gelöscht.', True)
        else:
            flash(u'Der Vorschlag wurde nicht gelöscht.')
        return HttpResponseRedirect(href('ikhaya', 'suggestions'))
    else:
        try:
            s = Suggestion.objects.get(id=suggestion)
        except Suggestion.DoesNotExist:
            flash('Diesen Vorschlag gibt es nicht.', False)
            return HttpResponseRedirect(href('ikhaya', 'suggestions'))
        flash(render_template('ikhaya/suggest_delete.html',
              {'s': s}))
        return HttpResponseRedirect(href('ikhaya', 'suggestions'))


@check_login(message=u'Bitte melde dich an, um einen Ikhaya-Artikel '
                     u'vorzuschlagen.')
@templated('ikhaya/suggest_new.html', modifier=context_modifier)
def suggest_edit(request):
    """
    A Page to suggest a new ikhaya article.  It just sends an email to the
    ikhaya administrators.
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
            flash(u'Dein Artikelvorschlag wurde versendet, das Ikhayateam '
                  u'wird sich sobald wie möglich darum kümmern.',
                  success=True)

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
        flash(u'Du wirst ab nun über neue Artikelvorschläge '
              u'benachrichtigt.')
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
        flash(u'Du wirst nun nicht mehr über neue Artikelvorschläge '
              u'benachrichtigt.')
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
            flash(u'Die Veranstaltung mit der ID %s existiert nicht und kann '
                  u'daher nicht als Basis des Kopiervorgangs benutzt werden.' %
                      request.GET['copy_from'],
                  False)
        else:
            for key in ('name', 'changed', 'created', 'date', 'time', 'enddate',
                'endtime', 'description', 'author_id', 'location',
                'location_town', 'location_lat', 'location_long'):
                setattr(event, key, getattr(base_event, key))
            event.visible = False

    if request.method == 'POST':
        form = EditEventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(request.user)
            flash(u'Die Veranstaltung wurde gespeichert.', True)
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
            convert = (lambda v: get_user_timezone().localize(v) \
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
                d = convert (date_time_to_datetime(
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
            flash(u'Die Veranstaltung wurde gespeichert. Sie wird demnächst '
                  u'von einem Moderator freigeschaltet.', True)
            event = Event.objects.get(id=event.id) # get truncated slug
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
        title = u'ubuntuusers Ikhaya – %s' % slug
        url = href('ikhaya', 'category', slug)
    else:
        title = u'ubuntuusers Ikhaya'
        url = href('ikhaya')

    articles = Article.objects.get_latest_articles(slug, count)

    feed = AtomFeed(title, feed_url=request.build_absolute_uri(),
                    url=url, rights=href('portal', 'lizenz'), id=url,
                    icon=href('static', 'img', 'favicon.ico'),
                    subtitle=IKHAYA_DESCRIPTION)

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
                'uri':  url_for(article.author)
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
        title = u'ubuntuusers Ikhaya-Kommentare – %s' % article.subject
        url = url_for(article)
    else:
        title = u'ubuntuusers Ikhaya-Kommentare'
        url = href('ikhaya')

    comments = Comment.objects.get_latest_comments(article.id if article else None, count)

    feed = AtomFeed(title, feed_url=request.build_absolute_uri(),
                    subtitle=IKHAYA_DESCRIPTION, rights=href('portal', 'lizenz'),
                    id=url, url=url, icon=href('static', 'img', 'favicon.ico'),)

    for comment in comments[:count]:
        kwargs = {}
        if mode == 'full':
            kwargs['content'] = comment.rendered_text
            kwargs['content_type'] = 'xhtml'
        if mode == 'short':
            kwargs['summary'] = truncate_html_words(comment.rendered_text, 100)
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
                'uri':  url_for(comment.author)
            },
            **kwargs
        )
    return feed
