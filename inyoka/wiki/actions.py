"""
    inyoka.wiki.actions
    ~~~~~~~~~~~~~~~~~~~

    This module contains all the actions for the wiki.  Actions are bound
    to a page and change the default display for a page.  Per default the
    action is 'show' and displays the most recent revision or the revision
    provided in the URL.  Other actions are 'edit', 'delete', 'info',
    'diff' etc.

    All actions are passed normalized page names because the view function
    that dispatches action ensures that.  If however actions are called from
    a source that deals with user submitted data all page names *must* be
    normalized.  The database models do not do this on their own!


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.html import escape
from django.utils.translation import gettext as _

from inyoka.markup.base import RenderContext, parse
from inyoka.portal.models import Subscription
from inyoka.utils.http import (
    AccessDeniedResponse,
    TemplateResponse,
    does_not_exist_is_404,
    templated,
)
from inyoka.utils.pagination import Pagination
from inyoka.utils.storage import storage
from inyoka.utils.templating import flash_message
from inyoka.utils.text import get_pagetitle, join_pagename, normalize_pagename
from inyoka.utils.urls import href, is_safe_domain, url_for
from inyoka.wiki.acl import PrivilegeTest, has_privilege, require_privilege
from inyoka.wiki.exceptions import CircularRedirectException
from inyoka.wiki.forms import (
    AddAttachmentForm,
    EditAttachmentForm,
    ManageDiscussionForm,
    MvBaustelleForm,
    NewArticleForm,
    PageEditForm,
)
from inyoka.wiki.models import Page
from inyoka.wiki.notifications import send_edit_notifications
from inyoka.wiki.utils import case_sensitive_redirect, get_safe_redirect_target


def clean_article_name(view):
    """Decorator to clean pagenames as they are passed to the view functions."""
    def decorate(request, *args, **kwargs):
        kwargs['name'] = normalize_pagename(kwargs['name'])
        return view(request, *args, **kwargs)
    return decorate


def context_modifier(request, context):
    """
    If a key called ``'page'`` that points to a page object is part of the
    context this modifier will hook a `PrivilegeTest` for the current user
    and that page into the request (called ``can``).  Then the templates
    can test for privileges this way::

        {% if can.read %}...{% endif %}
    """
    if 'page' in context:
        page_name = getattr(context['page'], 'name', None)
        if page_name:
            context['is_subscribed'] = request.user.is_authenticated and \
                Subscription.objects.user_subscribed(request.user,
                                                     context['page'],
                                                     clear_notified=True)
            context['can'] = PrivilegeTest(request.user, page_name)


@clean_article_name
@require_privilege('read')
@templated('wiki/action_show.html', modifier=context_modifier)
@case_sensitive_redirect
def do_show(request, name, rev=None, allow_redirect=True):
    """
    Show a given revision or the most recent one.  This action requires the
    read privilege.  If a page does not exist yet and no revision was provided
    in the URL it will call `do_missing_page` and return that output.

    Otherwise the page from the database is loaded and displayer.  Because it
    does not catch not found exceptions the `views.show_page` function that
    dispatches the actions automatically renders a missing resource.

    **Template**
        ``'wiki/action_show.html'``

    **Context**
        ``page``
            the bound `Page` object that should be shown.  Because it's bound
            the `rev` attribute points to the requested revision.  Note that
            deleted pages must not be handled in the template because the view
            automatically dispatches to `do_missing_page` if a revision is
            marked as deleted.
    """
    try:
        if rev is None:
            page = Page.objects.get_by_name(name)
        else:
            page = Page.objects.get_by_name_and_rev(name, rev)
    except Page.DoesNotExist:
        return do_missing_page(request, name)

    redirect = page.metadata.get('X-Redirect', None)
    if allow_redirect and redirect is not None:
        try:
            redirect, anchor = get_safe_redirect_target(redirect)
        except CircularRedirectException:
            messages.error(request,
                _('This page contains a redirect that leads to a '
                  'redirect loop!'))
            return HttpResponseRedirect(url_for(page, action='show_no_redirect'))

        messages.info(request,
            _('Redirected from “<a href="%(link)s">%(title)s</a>”.') % {
                'link': escape(url_for(page, action='show_no_redirect')),
                'title': escape(page.title)
            }
        )
        return HttpResponseRedirect(href('wiki', redirect, _anchor=anchor))
    if page.rev.deleted:
        return do_missing_page(request, name, page)

    if page.rev.id != page.last_rev.id:
        messages.info(request, _('You are viewing an old revision of this wiki page.'))

    return {
        'page': page,
        'tags': page.metadata['tag'],
        'deny_robots': rev is not None,
    }


@clean_article_name
@require_privilege('read')
@case_sensitive_redirect
def do_metaexport(request, name):
    """
    Export metadata as raw text.  This exists mainly for debugging reasons but
    it could make sense for external scripts too that want to get a quick list
    of backlinks etc.  Like the `do_show` action this requires read access to
    the page.
    """
    try:
        page = Page.objects.get_by_name(name)
    except Page.DoesNotExist:
        return HttpResponse('', content_type='text/plain; charset=utf-8',
                            status=404)

    metadata = []
    for key, values in page.metadata.items():
        for value in values:
            metadata.append('%s: %s' % (key, value))

    response = HttpResponse('\n'.join(metadata).encode('utf-8'),
                            content_type='text/plain; charset=utf-8')
    response['X-Robots-Tag'] = 'noindex'
    return response


@templated('wiki/missing_page.html', status=404, modifier=context_modifier)
def do_missing_page(request, name, _page=None):
    """
    Called if a page does not exist yet but it was requested by show.

    **Template**
        ``'wiki/missing_page.html'``

    **Context**
        ``page_name``
            The name of the page that does not exist.

        ``title``
            The title of that page.

        ``similar``
            List of pages with a similar name.  The list contains some dicts
            with ``name`` and ``title`` items.

        ``backlinks``
            Like ``similar`` but contains a list of pages that refer to this
            page with links.
    """
    can_create = has_privilege(request.user, name, 'create')
    if can_create:
        create_link = href('wiki', 'wiki', 'create', name)
    else:
        new_name = '%s/%s' % (storage['wiki_newpage_root'], name)
        if has_privilege(request.user, new_name, 'create'):
            create_link = href('wiki', 'wiki', 'create', new_name)
        else:
            create_link = None

    # If there's an info page for the creation of new pages configured
    # we overwrite that create_link to that configuration.
    if create_link is not None:
        create_link = storage['wiki_newpage_infopage'] or create_link

    try:
        not_finished = Page.objects.get_by_name(join_pagename(
            storage['wiki_newpage_root'], name
        ), cached=False)
    except Page.DoesNotExist:
        not_finished = None

    return {
        'page': _page,
        'page_name': name,
        'create_link': create_link,
        'title': get_pagetitle(name),
        'similar': [{
            'name': x,
            'title': get_pagetitle(x)
        } for x in sorted(Page.objects.get_similar(name))],
        'backlinks': [{
            'name': x.name,
            'title': x.title
        } for x in sorted(Page.objects.find_by_metadata('X-Link', name),
                          key=lambda x: x.title.lower())],
        'not_finished': not_finished
    }


@clean_article_name
@require_privilege('manage')
@does_not_exist_is_404
@case_sensitive_redirect
def do_revert(request, name, rev=None):
    """The revert action has no template, it uses a flashed form."""
    try:
        page = Page.objects.get_by_name_and_rev(name, rev)
        url = url_for(page.rev)
    except Page.DoesNotExist:
        raise Http404()
    latest_rev = page.revisions.latest()
    if latest_rev == page.rev:
        messages.error(request,
                       _('Revision is the latest one, revert aborted.'))
    elif request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, _('Revert aborted.'))
        else:
            new_revision = page.rev.revert(request.POST.get('note'),
                                           request.user,
                                           request.META.get('REMOTE_ADDR'))
            page.last_rev = new_revision
            messages.success(request,
                             _('“%(title)s” was reverted successfully') % {
                                 'title': escape(page.rev.title)})
            url = url_for(page)
    else:
        flash_message(request, 'wiki/action_revert.html', {'page': page})

    return HttpResponseRedirect(url)


def _rename(request, page, new_name, force=False, new_text=None):
    """
    Rename all revisions of `page` to `new_name`.

    Return True if renaming was successful, else False
    """
    old_name = page.name
    # check that there are no duplicate attachments existing
    # pointing to the new page name.

    def get_attachment_set_from_pagename(pagename):
        attachment_pages = Page.objects.get_attachment_list(pagename, existing_only=False)
        return {
            attachment_page.split('/')[-1]
            for attachment_page
            in attachment_pages
        }

    new_page_attachments = get_attachment_set_from_pagename(new_name)
    old_page_attachments = get_attachment_set_from_pagename(old_name)
    conflicting = new_page_attachments.intersection(old_page_attachments)

    if conflicting and not force:
        linklist = ', '.join('<a href="%s">%s</a>' %
            (join_pagename(new_name, name), name.split('/')[-1])
            for name in conflicting)
        messages.error(request,
            _('These attachments are already attached to the new page name: %(names)s. '
              'Please make sure that they are not required anymore. '
              '<a href="%(link)s">Force rename and deletion of conflicting attachments</a>,') % {
                  'names': linklist,
                  'link': url_for(page, action='rename', force=True)})
        return False

    elif conflicting and force:
        for attachment in conflicting:
            obj = Page.objects.get_by_name(join_pagename(new_name, attachment))
            models.Model.delete(obj)

    title = page.title
    page.name = new_name

    page.edit(note=_('Renamed from %(old_name)s') % {'old_name': title},
              user=request.user,
              text=new_text,
              clean_cache=False)

    if request.POST.get('add_redirect'):
        old_text = '# X-Redirect: %s\n' % new_name
        Page.objects.create(
            name=old_name, text=old_text, user=request.user,
            note=_('Renamed to %(new_name)s') % {'new_name': page.title},
            remote_addr=request.META.get('REMOTE_ADDR'))

    # move all attachments
    attachment_pages = [
        Page.objects.get_by_name(attachment)
        for attachment
        in Page.objects.get_attachment_list(old_name)
    ]
    old_attachment_page_names = [
        attachmentpage.name
        for attachmentpage
        in attachment_pages
    ]
    new_attachment_page_names = []
    for attachment_page in attachment_pages:
        old_attachment_title = attachment_page.title
        new_attachment_name = normalize_pagename(join_pagename(page.trace[-1],
                                                  attachment_page.short_title))
        attachment_page.name = new_attachment_name
        new_attachment_page_names.append(new_attachment_name)
        attachment_page.edit(note=_('Renamed from %(old_name)s') % {'old_name': old_attachment_title},
                remote_addr=request.META.get('REMOTE_ADDR'),
                clean_cache=False)

    Page.objects.clean_cache([old_name, new_name] + old_attachment_page_names + new_attachment_page_names)
    return True


@clean_article_name
@require_privilege('manage')
@does_not_exist_is_404
@case_sensitive_redirect
@transaction.atomic
def do_rename(request, name, new_name=None, force=False):
    """Rename all revisions."""
    page = Page.objects.get_by_name(name, raise_on_deleted=True)

    if new_name is None:
        new_name = name

    if request.method == 'POST':
        new_name = normalize_pagename(request.POST.get('new_name', ''))
        if not new_name:
            messages.error(request, _('No page name given.'))
        else:
            try:
                Page.objects.get_by_name(new_name)
            except Page.DoesNotExist:
                if _rename(request, page, new_name, force):
                    messages.success(request,
                                     _('Renamed the page successfully.'))
            else:
                messages.error(request,
                               _('A page with this name already exists.'))
                return HttpResponseRedirect(href('wiki', name))

        return HttpResponseRedirect(url_for(page))

    flash_message(request, 'wiki/action_rename.html', {
        'page': page,
        'new_name': new_name,
        'force': force
    })
    return HttpResponseRedirect(url_for(page, 'show'))


def _get_wiki_article_templates():
    """Return a list of template choices for use in NewArticleForm."""
    # TODO: this is a hack, do not have these hardcoded here!
    return [('Vorlage/Artikel_normal', _('Normal (for experienced authors)')),
            ('Vorlage/Artikel_umfangreich', _('Extensive (for beginners)')),
            ('Vorlage/Howto', _('Howto')),
            ('', _('I don\'t want a template'))]


def _get_wiki_reserved_names():
    """Return a list of words that should not be used as article names."""
    return ['wiki', 'a']


@templated('wiki/action_create.html', modifier=context_modifier)
def do_create(request, name=None):
    """Create a new wiki page."""
    template_choices = _get_wiki_article_templates()
    reserved_names = _get_wiki_reserved_names()

    # All authentication and permission checks are done in the form validation.
    if request.method == 'POST':
        form = NewArticleForm(user=request.user,
                              template_choices=template_choices,
                              reserved_names=reserved_names,
                              data=request.POST.copy())
        if form.is_valid():
            name = form.cleaned_data['name']
            template_name = form.cleaned_data['template']

            if template_name is None:
                text = storage.get('wiki_newpage_template', default='')
            else:
                template = Page.objects.get_by_name(name=template_name)
                text = template.rev.text.value

            new_page = Page.objects.create(user=request.user,
                                           name=name,
                                           # TODO: Kick out anonymous editing
                                           remote_addr=request.META.get('REMOTE_ADDR'),
                                           text=text)
            msg = _('The page <a href="{link}">{name}</a> has been created.')
            messages.success(request, msg.format(link=url_for(new_page),
                                                 name=name))
            return HttpResponseRedirect(url_for(new_page, action='edit'))
    else:
        form = NewArticleForm(user=request.user,
                              template_choices=template_choices,
                              reserved_names=reserved_names)
        if name is not None:
            form.initial = {'name': name}

    return {'form': form}


@clean_article_name
@require_privilege('edit')
@templated('wiki/action_edit.html', modifier=context_modifier)
@case_sensitive_redirect
def do_edit(request, name, rev=None):
    """Edit an existing wiki page.

    If the page is an attachment this redirects to a form to update the
    attachment.
    If it's a normal page this just displays a text box for the page text
    and an input field for the change note.

    **Template**
        ``'wiki/action_edit.html'``

    **Context**
        ``name``
            The name of the page that is edited.

        ``page``
            The `Page` object of the page that is edited.  This only exists
            if a page is edited, not if a page is created.

        ``form``
            A `PageEditForm` instance.

        ``preview``
            If we are in preview mode this is a rendered HTML preview.
    """
    try:
        page = Page.objects.get_by_name_and_rev(name=name, rev=rev)
    except Page.DoesNotExist:
        if Page.objects.filter(name=name).exists():
            msg = _('The given revision does not exist for this article, '
                    'using last revision instead.')
            url = href('wiki', name, 'a', 'edit')
        else:
            msg = _('The article „{name}“ does not exist, you can '
                    'try to create it now.').format(name=name)
            url = href('wiki', 'wiki', 'create', name)
        messages.info(request, msg)
        return HttpResponseRedirect(url)
    else:
        if page.rev.deleted and not has_privilege(request.user, name, 'create'):
            return AccessDeniedResponse()

    # attachments have a custom editor
    if page and page.rev.attachment:
        return do_attach_edit(request, name=page.name)

    preview = None
    rev = page.rev.id

    if request.method == 'POST':
        form = PageEditForm(user=request.user,
                            name=name,
                            data=request.POST.copy())
        if 'cancel' in request.POST:
            messages.info(request, _('Editing of this page was canceled.'))
            return HttpResponseRedirect(url_for(page))
        elif 'preview' in request.POST:
            ctx = RenderContext(request, wiki_page=page)
            tt = request.POST.get('text', '')
            preview = parse(tt).render(ctx, 'html')
        elif form.is_valid():
            old_rev = page.rev
            page.edit(user=request.user,
                      text=form.cleaned_data['text'],
                      note=form.cleaned_data['note'],
                      change_date=datetime.utcnow(),
                      deleted=None)
            current_rev = page.rev
            send_edit_notifications(user=request.user,
                                    rev=current_rev,
                                    old_rev=old_rev)
            messages.success(request, _('The page has been edited.'))
            return HttpResponseRedirect(url_for(page))
    else:
        form = PageEditForm(user=request.user,
                            name=name)
        form.initial = {'text': page.rev.text.value,
                        'edit_time': datetime.utcnow(),
                        'revision': page.rev.id}

    return {
        'name': name,
        'title': get_pagetitle(name),
        'page': page,
        'form': form,
        'preview': preview,
        'wiki_edit_note_rendered': storage['wiki_edit_note_rendered'],
        'license_note_rendered': storage['license_note_rendered'],
        'deny_robots': True,
    }


@clean_article_name
@require_privilege('delete')
@does_not_exist_is_404
@case_sensitive_redirect
def do_delete(request, name):
    """Delete the page (deletes the last recent revision)."""
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, 'Canceled.')
        else:
            page.edit(user=request.user, deleted=True,
                      remote_addr=request.META.get('REMOTE_ADDR'),
                      note=request.POST.get('note', '') or 'Page deleted.')
            messages.success(request, 'Page deleted successfully.')
    else:
        flash_message(request,'wiki/action_delete.html', {'page': page})

    return HttpResponseRedirect(url_for(page))


# TODO: This damn function is much too specific as translation would
#      make sense.  We need to figure out how to rewrite this properly.
@clean_article_name
@require_privilege('manage')
@templated('wiki/action_mv_baustelle.html')
@case_sensitive_redirect
@transaction.atomic
def do_mv_baustelle(request, name):
    """
    "Move" the page to an editing area called "Baustelle", ie. do:
     * Rename page `name` to Baustelle/`name`
     * Create copy `name`
     * Create boxes indicating page is worked on or a copy

    Do *not* automatically modify the ACL

    :TODO: Find a better name for this function
    """
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    discontinued = name.startswith('Baustelle/Verlassen')

    if request.method == 'POST':
        form = MvBaustelleForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            text = page.revisions.latest().text.value

            # Rename page (and include box)
            if data['completion_date']:
                date = data['completion_date']
                date = '%i.%i.%i, ' % (date.day, date.month, date.year)
            else:
                date = ''

            # Move from 'Baustelle/Verlassen' to 'Baustelle'
            if text.startswith('[[Vorlage(Verlassen'):
                text = text[text.find('\n') + 1:]
            new_text = '[[Vorlage(Überarbeitung, %s%s, %s)]]\n%s' % (date,
                       name, data['user'], text)
            try:
                Page.objects.get_by_name(data['new_name'])
            except Page.DoesNotExist:
                if not _rename(request, page, data['new_name'],
                               new_text=new_text):
                    messages.error(request,
                        'Beim Verschieben in die Baustelle ist ein Fehler '
                        'aufgereten.')
                    return HttpResponseRedirect(url_for(page))
            else:
                messages.error(request,
                    'In der Baustelle befindet sich bereits eine Seite '
                    'mit dem Namen „%s”.' % data['new_name'])
                return HttpResponseRedirect(url_for(page))

            # Create copy (and include box)
            if not discontinued:
                copy_text = '[[Vorlage(Kopie, %s)]]\n' % name + text
                Page.objects.create(name=name, text=copy_text,
                    user=request.user,
                    note='Kopie; Original in der Baustelle')

            messages.success(request,
                'Seite erfolgreich in die Baustelle verschoben - ggf. '
                '<a href="%(link)s">Zugriffsrechte</a> anpassen' % {
                    'link': escape(href('wiki', 'Wiki/ACL/All-in-One'))
                }
            )
            return HttpResponseRedirect(url_for(page))

    form = MvBaustelleForm()
    if discontinued:
        init_name = name.replace('Baustelle/Verlassen/', 'Baustelle/')
    else:
        init_name = 'Baustelle/%s' % name
    form.initial = {'new_name': init_name, 'user': request.user}
    return {
        'page': page,
        'form': form,
    }


# TODO: This damn function is way too specific as translation would
#      make sense.  We need to figure out how to rewrite this properly.
@clean_article_name
@require_privilege('manage')
@does_not_exist_is_404
@case_sensitive_redirect
@transaction.atomic
def do_mv_discontinued(request, name):
    """Move page from ``Baustelle`` to ``Baustelle/Verlassen``"""
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, 'Verschieben wurde abgebrochen.')
        else:
            new_name = name.replace('Baustelle', 'Baustelle/Verlassen')
            text = page.revisions.latest().text.value
            if text.startswith('[[Vorlage(Baustelle'):
                text = text[text.find('\n') + 1:]
            text = '[[Vorlage(Verlassen)]]\n' + text
            try:
                Page.objects.get_by_name(new_name)
            except Page.DoesNotExist:
                if not _rename(request, page, new_name, new_text=text):
                    messages.error(request,
                        'Beim Verschieben ist ein Fehler aufgereten.')
                    return HttpResponseRedirect(url_for(page))
            else:
                messages.error(request,
                    'Die Seite „%s” existiert bereits.' % new_name)
                return HttpResponseRedirect(url_for(page))
            messages.success(request,
                'Seite wurde erfolgreich verschoben.')
    else:
        flash_message(request, 'wiki/action_mv_discontinued.html', {'page': page})
    return HttpResponseRedirect(url_for(page))


# TODO: This damn function is way too specific as translation would
#      make sense.  We need to figure out how to rewrite this properly.
@clean_article_name
@require_privilege('manage')
@does_not_exist_is_404
@case_sensitive_redirect
@transaction.atomic
def do_mv_back(request, name):
    """
    Move page back from ``Baustelle`` to its origin, move copy (which may exist
    at this origin) to ``Trash/`` and remove box (so revert ``do mv_baustelle``
    """
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, 'Wiederherstellen wurde abgebrochen.')
        else:
            if name.startswith('Baustelle/'):
                new_name = name[10:]  # Remove the leading 'Baustelle/' from the name
            else:
                new_name = name
            # Move copy to Trash
            try:
                copy = Page.objects.get_by_name(new_name)
            except Page.DoesNotExist:
                # no need to move to Trash
                pass
            else:
                copy_text = copy.revisions.latest().text.value
                if copy_text.startswith('[[Vorlage(Kopie'):
                    copy_text = copy_text[copy_text.find('\n') + 1:]
                moved = False
                for id in range(1, 100):
                    trash_name = "Trash/%s-%i" % (new_name, id)
                    try:
                        Page.objects.get_by_name(trash_name)
                    except Page.DoesNotExist:
                        if not _rename(request, copy, trash_name,
                                       new_text=copy_text):
                            continue
                        moved = True
                        break
                if not moved:
                    messages.error(request,
                        'Kopie konnte nicht nach Trash verschoben werden')
                    return HttpResponseRedirect(url_for(page))
            # Remove box
            text = page.revisions.latest().text.value
            while text.startswith('[[Vorlage(Baustelle') or \
                    text.startswith('[[Vorlage(Überarbeitung'):
                text = text[text.find('\n') + 1:]
            # Rename
            if not _rename(request, page, new_name, new_text=text):
                messages.error(request,
                    'Beim Verschieben ist ein Fehler aufgereten.')
                return HttpResponseRedirect(url_for(page))

            messages.success(request,
                'Seite erfolgreich ins Wiki verschoben - ggf. '
                '<a href="%(link)s">Zugriffsrechte</a> anpassen' % {
                    'link': escape(href('wiki', 'Wiki/ACL/All-in-One'))
                }
            )
            return HttpResponseRedirect(url_for(page))
    else:
        flash_message(request, 'wiki/action_mv_back.html', {'page': page})
    return HttpResponseRedirect(url_for(page))


@clean_article_name
@login_required
@require_privilege('read')
@templated('wiki/action_log.html', modifier=context_modifier)
@case_sensitive_redirect
def do_log(request, name, pagination_page=1):
    """
    Show a revision log for this page.

    **Template**
        ``'wiki/action_log.html'``

    **Context**
        ``page``
            The `Page` object this template action renders the revision
            log of.  It's unbound thus the `rev` attribute is `None`.

        ``revisions``
            The list of revisions ordered by date.  The newest revision
            first.
    """
    if request.method == 'POST':
        if 'rev' in request.POST and 'new_rev' in request.POST:
            return HttpResponseRedirect(href('wiki', name, 'a', 'diff',
                                        request.POST.get('rev'),
                                        request.POST.get('new_rev')))

    page = Page.objects.get_by_name(name)
    url = url_for(page, action='log')

    pagination = Pagination(request, page.revisions.all().order_by('-id'), pagination_page,
                            settings.WIKI_REVISIONS_PER_PAGE, url)

    return {
        'page': page,
        'revisions': pagination.get_queryset().select_related('user'),
        'pagination': pagination,
        'deny_robots': True,
    }


@login_required
@clean_article_name
@require_privilege('read')
@templated('wiki/action_diff.html', modifier=context_modifier)
@case_sensitive_redirect
def do_diff(request, name, old_rev=None, new_rev=None, udiff=False):
    """Render a diff between two pages."""
    if old_rev is None:
        old_rev = Page.objects.get_head(name, -1)

    diff = Page.objects.compare(name, old_rev, new_rev)
    if udiff:
        return HttpResponse(diff.udiff, content_type='text/plain; charset=utf-8')

    return {
        'diff': diff,
        'page': diff.page,
        'deny_robots': True,
    }


@login_required
@clean_article_name
@require_privilege('read')
@templated('wiki/action_backlinks.html', modifier=context_modifier)
@case_sensitive_redirect
def do_backlinks(request, name):
    """
    Display a list of backlinks.

    Because this is part of the pathbar that is displayed for deleted pages
    it should not fail for deleted pages!  Additionally it probably makes
    sense to track pages that link to a deleted page.
    """
    page = Page.objects.get_by_name(name)

    return {
        'page': page,
        'deny_robots': True,
    }


@clean_article_name
@require_privilege('read')
@does_not_exist_is_404
@case_sensitive_redirect
def do_export(request, name, format='raw', rev=None):
    """
    Export the given revision or the most recent one to the specified format
    (raw or html).

    =============== ======= ==================================================
    Format          Partial Full    Description
    =============== ======= ==================================================
    ``raw``         yes     no      The raw wiki markup exported.
    ``HTML``        yes     yes     The wiki markup converted to HTML4.
    =============== ======= ==================================================


    **Template**
        Depending on the output format either no template at all or one of
        the following ones:
        -   ``'wiki/export.html'``

    **Context**
        The context is of course only passed if a template is rendered but
        the same for all the templates.

        ``page``
            The bound `Page` object which should be rendered.
    """
    if rev is None or not rev.isdigit():
        page = Page.objects.get_by_name(name, raise_on_deleted=True)
    else:
        page = Page.objects.get_by_name_and_rev(name, rev,
                                                raise_on_deleted=True)
    ctx = {
        'page': page
    }
    if format == 'html':
        response = TemplateResponse('wiki/export.html', ctx,
                                    content_type='text/html; charset=utf-8')
    else:
        response = HttpResponse(page.rev.text.value.encode('utf-8'),
                                content_type='text/plain; charset=utf-8')

    response['X-Robots-Tag'] = 'noindex'
    return response


@clean_article_name
@require_privilege('attach')
@templated('wiki/action_attach.html', modifier=context_modifier)
@case_sensitive_redirect
def do_attach(request, name):
    """
    List all pages with attachments according to the given page and
    allow the user to attach new files.

    **Template**
        ``'wiki/action_attach.html'``

    **Context**
        ``page``
            The `Page` that owns the attachment

        ``attachments``
            A list of `Page` objects that are attachments and below this
            page.  They all have a proper attachment attributes which is
            an `Attachment`.

        ``form``
            An `AddAttachmentForm` instance.
    """
    page = Page.objects.get_by_name(name)
    if page.rev.attachment_id is not None:
        messages.error(request, _('Attachments within attachments are not allowed!'))
        return HttpResponseRedirect(url_for(page))
    attachments = Page.objects.get_attachment_list(page.name)
    attachments = [Page.objects.get_by_name(i) for i in attachments]
    context = {
        'page': page,
        'attachments': attachments,
        'form': AddAttachmentForm()
    }
    if request.method == 'POST':
        if request.POST.get('cancel'):
            messages.info(request, _('Canceled.'))
            if page and page.metadata.get('redirect'):
                url = url_for(page, action='show_no_redirect')
            else:
                url = url_for(page)
            return HttpResponseRedirect(url)
        form = AddAttachmentForm(request.POST, request.FILES)
        if not form.is_valid():
            context['form'] = form
            return context
        d = form.cleaned_data
        attachment_name = d.get('filename') or d['attachment'].name
        filename = d['attachment'].name or d.get('filename')
        if not attachment_name:
            messages.info(request,
                _('Please enter a name for this attachment.'))
            return context
        attachment_name = '%s/%s' % (name, attachment_name)
        attachment_name = normalize_pagename(attachment_name.strip('/'))
        try:
            ap = Page.objects.get_by_name(attachment_name)
        except Page.DoesNotExist:
            ap = None
        if ap is not None and (ap.rev.attachment is None or
                               not d.get('override', False)):
            messages.error(request,
                _('Another page or attachment with the same name exists'))
            return context
        remote_addr = request.META.get('REMOTE_ADDR')
        if ap is None:
            ap = Page.objects.create(user=request.user,
                                     text=d.get('text', ''),
                                     remote_addr=remote_addr,
                                     name=attachment_name,
                                     note=d.get('note', ''),
                                     attachment_filename=filename,
                                     attachment=d['attachment'])
        else:
            ap.edit(user=request.user,
                    text=d.get('text', ap.rev.text),
                    remote_addr=remote_addr,
                    note=d.get('note', ''),
                    attachment_filename=filename,
                    attachment=d['attachment'])
        messages.success(request,
            _('Attachment saved successfully.'))
        if ap.metadata.get('weiterleitung'):
            url = url_for(ap, action='show_no_redirect')
        else:
            url = url_for(ap)
        return HttpResponseRedirect(url)

    context['deny_robots'] = 'noindex'
    return context


@clean_article_name
@require_privilege('attach')
@templated('wiki/action_attach_edit.html', modifier=context_modifier)
@case_sensitive_redirect
def do_attach_edit(request, name):
    page = Page.objects.get_by_name(name)
    form = EditAttachmentForm({
        'text': page.rev.text.value,
    })
    if request.method == 'POST':
        form = EditAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data
            attachment = None
            attachment_filename = None
            if d['attachment']:
                attachment = d['attachment']
                attachment_filename = (d['attachment'].name or
                                       page.rev.attachment.filename)
            page.edit(
                user=request.user,
                text=d.get('text', page.rev.text.value),
                remote_addr=request.META.get('remote_addr'),
                note=d.get('note', ''),
                attachment_filename=attachment_filename,
                attachment=attachment)
            messages.success(request, _('Attachment edited successfully.'))
            return HttpResponseRedirect(url_for(page))
    return {
        'form': form,
        'page': page
    }


@clean_article_name
@login_required
def do_subscribe(request, name):
    """
    Subscribe the user to the page with `page_name`
    """
    page = Page.objects.get_by_name(name)
    if not Subscription.objects.user_subscribed(request.user, page):
        # there's no such subscription yet, create a new one
        Subscription(user=request.user, content_object=page).save()
        messages.success(request,
            _('You will be notified on changes on this page'))
    else:
        messages.error(request, _('You are already subscribed'))
    return HttpResponseRedirect(url_for(page))


@clean_article_name
@login_required
def do_unsubscribe(request, name):
    """
    Unsubscribe the user from the page with `page_name`
    """
    page = Page.objects.get_by_name(name)
    try:
        subscription = Subscription.objects.get_for_user(request.user, page)
    except Subscription.DoesNotExist:
        messages.info(request, _('No subscription for this page found.'))
    else:
        subscription.delete()
        messages.success(request,
            _('You won\'t be notified for changes on this page anymore'))
    # redirect the user to the page he last watched
    if request.GET.get('next', False) and is_safe_domain(request.GET['next']):
        return HttpResponseRedirect(request.GET['next'])
    else:
        return HttpResponseRedirect(url_for(page))


@require_privilege('edit')
@does_not_exist_is_404
@templated('wiki/action_manage_discussion.html')
@case_sensitive_redirect
def do_manage_discussion(request, name):
    page = Page.objects.get_by_name(name)
    if request.method == 'POST':
        form = ManageDiscussionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data.get('topic'):
                page.topic = data['topic']
                page.save()
                messages.success(request,
                                 _('Successfully linked the discussion with the article.'))
                return HttpResponseRedirect(url_for(data['topic']))
            else:
                page.topic = None
                page.save()
                messages.success(request,
                                 _('Successfully unlinked the discussion from the article.'))
                return HttpResponseRedirect(url_for(page))
    elif page.topic is None:
        form = ManageDiscussionForm()
    else:
        form = ManageDiscussionForm(initial={'topic': page.topic.slug})
    return {
        'page': page,
        'form': form,
    }
