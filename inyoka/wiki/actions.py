# -*- coding: utf-8 -*-
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


    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from django.db import models
from django.utils.translation import ugettext as _
from inyoka.utils.urls import href, url_for, is_safe_domain
from inyoka.utils.http import templated, does_not_exist_is_404, \
     TemplateResponse, AccessDeniedResponse, PageNotFound, \
     HttpResponseRedirect, HttpResponse
from inyoka.utils.flashing import flash
from inyoka.utils.cache import request_cache
from inyoka.utils.diff3 import merge
from inyoka.utils.templating import render_template
from inyoka.utils.pagination import Pagination
from inyoka.utils.text import normalize_pagename, get_pagetitle, join_pagename
from inyoka.utils.html import escape
from inyoka.utils.urls import urlencode
from inyoka.utils.storage import storage
from inyoka.wiki.models import Page, Revision
from inyoka.wiki.forms import PageEditForm, AddAttachmentForm, \
    EditAttachmentForm, ManageDiscussionForm, MvBaustelleForm
from inyoka.wiki.parser import parse, RenderContext
from inyoka.wiki.acl import require_privilege, has_privilege, PrivilegeTest
from inyoka.portal.models import Subscription
from inyoka.portal.utils import simple_check_login
from inyoka.wiki.notifications import send_edit_notifications
from inyoka.wiki.tasks import update_object_list


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


@require_privilege('read')
@templated('wiki/action_show.html', modifier=context_modifier)
def do_show(request, name):
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
            maked as deleted.
    """
    rev = request.GET.get('rev')
    try:
        if rev is None or not rev.isdigit():
            page = Page.objects.get_by_name(name)
            rev = None
        else:
            page = Page.objects.get_by_name_and_rev(name, rev)
    except Page.DoesNotExist:
        return do_missing_page(request, name)
    if request.GET.get('redirect') != 'no':
        redirect = page.metadata.get('X-Redirect')
        if redirect:
            flash(_(u'Redirected from “<a href="%(link)s">%(title)s</a>“.') % {
                'link': escape(href('wiki', page.name, redirect='no')),
                'title': escape(page.title)
            })
            anchor = None
            if '#' in redirect:
                redirect, anchor = redirect.rsplit('#', 1)
            return HttpResponseRedirect(href('wiki', redirect, redirect='no', _anchor=anchor))
    if page.rev.deleted:
        return do_missing_page(request, name, page)

    return {
        'page':         page,
        'tags':         page.metadata['tag'],
        'deny_robots':  rev is not None,
    }


@require_privilege('read')
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
        return HttpResponse(u'', content_type='text/plain; charset=utf-8',
                            status=404)
    metadata = []
    for key, values in page.metadata.iteritems():
        for value in values:
            metadata.append(u'%s: %s' % (key, value))
    return HttpResponse(u'\n'.join(metadata).encode('utf-8'),
                        content_type='text/plain; charset=utf-8')


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
        create_link = href('wiki', name, action='edit')
    else:
        new_name = u'%s/%s' % (storage['wiki_newpage_root'], name)
        if has_privilege(request.user, new_name, 'create'):
            create_link = href('wiki', new_name, action='edit')
        else:
            create_link = None

    # If there's an info page for the creation of new pages configured
    # we overwrite that create_link to that configuration.
    if create_link is not None:
        create_link = storage['wiki_newpage_infopage'] or create_link

    try:
        not_finished = Page.objects.get_by_name(join_pagename(
            storage['wiki_newpage_root'], name
        ))
    except Page.DoesNotExist:
        not_finished = None

    return {
        'page':         _page,
        'page_name':    name,
        'create_link':  create_link,
        'title':        get_pagetitle(name),
        'similar': [{
            'name':     x,
            'title':    get_pagetitle(x)
        } for x in sorted(Page.objects.get_similar(name))],
        'backlinks': [{
            'name':     x.name,
            'title':    x.title
        } for x in sorted(Page.objects.find_by_metadata('X-Link', name),
                          key=lambda x: x.title.lower())],
        'not_finished': not_finished
    }


@require_privilege('manage')
@does_not_exist_is_404
def do_revert(request, name):
    """The revert action has no template, it uses a flashed form."""
    try:
        rev = int(request.GET['rev'])
    except (KeyError, ValueError):
        raise PageNotFound()
    url = href('wiki', name, rev=rev)
    page = Page.objects.get_by_name_and_rev(name, rev)
    latest_rev = page.revisions.latest()
    if latest_rev == page.rev:
        flash(_(u'Revision is the latest one, revert aborted.'), success=False)
    elif request.method == 'POST':
        if 'cancel' in request.POST:
            flash(_(u'Revert aborted'))
            url = href('wiki', name, rev=page.rev.id)
        else:
            new_revision = page.rev.revert(request.POST.get('note'),
                                           request.user,
                                           request.META.get('REMOTE_ADDR'))
            page.last_rev = new_revision
            flash(_(u'“%(title)s” was reverted successfully') % {
                'title': escape(page.rev.title)}, success=True)
            url = href('wiki', name)
    else:
        flash(render_template('wiki/action_revert.html', {'page': page}))
    return HttpResponseRedirect(url)


def _rename(request, page, new_name, force=False, new_text=None):
    """
    Rename all revisions of `page` to `new_name`.
    :FIXME: attachments renamings do not work sometimes

    Return True if renaming was successful, else False
    """
    name = page.name
    # check that there are no duplicate attachments existing
    # pointing to the new page name.
    new_page_attachments = (p.split('/')[-1] for p in
                            Page.objects.get_attachment_list(new_name, False))
    old_page_attachments = (p.split('/')[-1] for p in
                            Page.objects.get_attachment_list(page.name, False))
    duplicate = set(new_page_attachments).intersection(set(old_page_attachments))
    if duplicate and not force:
        linklist = u', '.join('<a href="%s">%s</a>' %
            (join_pagename(new_name, name), name.split('/')[-1])
            for name in duplicate)
        flash(_(u'These attachments are already attached to the new page name: %(names)s. '
                u'Please make sure that they are not required anymore. '
                u'<a href="%(link)s">Force rename and deletion of duplicate attachments</a>,') % {
                    'names': linklist,
                    'link': href('wiki', page.name, action='rename', force=True)},
              False)
        return False

    elif duplicate and force:
        for attachment in duplicate:
            obj = Page.objects.get_by_name(join_pagename(new_name, attachment))
            models.Model.delete(obj)

    title = page.title
    page.name = new_name
    if new_text:
        page.edit(note=_(u'Renamed from %(old_name)s') % {'old_name': title},
                  user=request.user,
                  text=new_text, remote_addr=request.META.get('REMOTE_ADDR'))
    else:
        page.edit(note=_(u'Renamed from %(old_name)s') % {'old_name': title},
                  user=request.user,
                  remote_addr=request.META.get('REMOTE_ADDR'))

    if request.POST.get('add_redirect'):
        old_text = u'# X-Redirect: %s\n' % new_name
        Page.objects.create(
            name=name, text=old_text, user=request.user,
            note=_(u'Renamed to %(new_name)s') % {'new_name': page.title},
            remote_addr=request.META.get('REMOTE_ADDR'))

    # move all attachments
    for attachment in Page.objects.get_attachment_list(name):
        ap = Page.objects.get_by_name(attachment)
        old_attachment_name = ap.title
        ap.name = normalize_pagename(join_pagename(page.trace[-1],
                                                  ap.short_title))
        ap.edit(note=_(u'Renamed from %(old_name)s') % {'old_name': old_attachment_name},
                remote_addr=request.META.get('REMOTE_ADDR'))

    update_object_list.delay(page.last_rev)
    return True


@require_privilege('manage')
@does_not_exist_is_404
def do_rename(request, name):
    """Rename all revisions."""
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    new_name = request.GET.get('page_name') or page.name
    force = request.GET.get('force', False)
    if request.method == 'POST':
        force = request.POST.get('force', False)
        new_name = normalize_pagename(request.POST.get('new_name', ''))
        if not new_name:
            flash(_(u'No page name given.'), success=False)
        else:
            try:
                Page.objects.get_by_name(new_name)
            except Page.DoesNotExist:
                if _rename(request, page, new_name, force):
                    flash(_(u'Renamed the page successfully.'), success=True)
            else:
                flash(_(u'A page with this name already exists.'), False)
                return HttpResponseRedirect(href('wiki', name))


        return HttpResponseRedirect(url_for(page))
    flash(render_template('wiki/action_rename.html', {
        'page':         page,
        'new_name':     new_name,
        'force':        force
    }))
    return HttpResponseRedirect(url_for(page, 'show_no_redirect'))


@require_privilege('edit')
@templated('wiki/action_edit.html', modifier=context_modifier)
def do_edit(request, name):
    """
    Edit or create a wiki page.  If the page is an attachment this displays a
    form to update the attachment next to the description box.  If it's a
    normal page or no page yet this just displays a text box for the page
    text and an input field for the change note.
    If the user is not logged in, he gets a warning that his IP will be
    visible for everyone until Sankt-nimmerleinstag (forever).

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
    rev = request.REQUEST.get('rev')
    rev = rev is not None and rev.isdigit() and int(rev) or None
    try:
        page = Page.objects.get_by_name_and_rev(name, rev)
    except Page.DoesNotExist:
        page = None
        if not has_privilege(request.user, name, 'create'):
            if has_privilege(request.user, u'%s/%s' % (
                                           storage['wiki_newpage_template'],
                                           name),
                             'create'):
                return HttpResponseRedirect(href('wiki', storage['wiki_newpage_template'], name, action='edit'))
            return AccessDeniedResponse()
        current_rev_id = ''
    else:
        # If the page is deleted it requires creation privilege
        if page.rev.deleted and not has_privilege(request.user, name, 'create'):
            return AccessDeniedResponse()
        current_rev_id = str(page.rev.id)

    # attachments have a custom editor
    if page and page.rev.attachment:
        return do_attach_edit(request, page.name)

    # form defaults
    form_data = request.POST.copy()
    preview = None
    form = PageEditForm()
    if page is not None:
        form.initial = {'text': page.rev.text.value}
    else:
        form.initial = {'text': storage['wiki_newpage_template'] or ''}

    # if there a template is in use, load initial text from the template
    template = request.GET.get('template')
    if not request.method == 'POST' and template and \
       has_privilege(request.user, template, 'read'):
        try:
            template = Page.objects.get_by_name(template)
        except Page.DoesNotExist:
            pass
        else:
            form.initial['text'] = template.rev.text.value
            flash(_(u'Used the template “<a href="%(link)s">%(name)s</a>” for this page') % {
                'link': url_for(template),
                'name': escape(template.title)
            })

    # check for edits by other users.  If we have such an edit we try
    # to merge and set the edit time to the time of the last merge or
    # conflict.  We do that before the actual form processing
    merged_this_request = False
    try:
        # Don't change to utcfromtimestamp, the data is already in utc.
        edit_time = datetime.fromtimestamp(int(request.POST['edit_time']))
    except (KeyError, ValueError):
        edit_time = datetime.utcnow()
    if rev is None:
        latest_rev = page and page.rev or None
    else:
        try:
            latest_rev = Page.objects.get_by_name(name).rev
        except Page.DoesNotExist:
            latest_rev = None
    if latest_rev is not None and edit_time < latest_rev.change_date:
        form_data['text'] = merge(page.rev.text.value,
                                  latest_rev.text.value,
                                  form_data.get('text', ''))
        edit_time = latest_rev.change_date
        merged_this_request = True

    # form validation and handling
    if request.method == 'POST':
        if request.POST.get('cancel'):
            flash(_(u'Canceled'))
            if page and page.metadata.get('redirect'):
                url = href('wiki', page.name, redirect='no')
            else:
                url = href('wiki', name)
            return HttpResponseRedirect(url)
        elif request.POST.get('preview'):
            text = request.POST.get('text') or ''
            context = RenderContext(request, page)
            preview = parse(text).render(context, 'html')
            form.initial['text'] = text
        else:
            form = PageEditForm(request.user, name, page and
                                page.rev.text.value or '', form_data)
            if form.is_valid() and not merged_this_request:
                remote_addr = request.META.get('REMOTE_ADDR')
                if page is not None:
                    if form.cleaned_data['text'] == page.rev.text.value:
                        flash(_(u'No changes'))
                    else:
                        page.edit(user=request.user,
                                  deleted=False,
                                  remote_addr=remote_addr,
                                  **form.cleaned_data)
                        if page.rev.deleted:
                            msg = _(u'The page <a href="%(link)s">%(name)s</a> has been created.')
                        else:
                            msg = _(u'The page <a href="%(link)s">%(name)s</a> has been edited.')

                        flash(msg % {'link': escape(href('wiki', page.name)),
                                     'name': escape(page.title)}, True)
                else:
                    page = Page.objects.create(user=request.user,
                                               remote_addr=remote_addr,
                                               name=name,
                                               **form.cleaned_data)
                    flash(_(u'The page <a href="%(link)s">%(name)s</a> has been created.') % {
                        'link': escape(href('wiki', page.name)),
                        'name': escape(page.title)
                    }, True)

                last_revisions = page.revisions.all()[:2]
                if len(last_revisions) > 1:
                    rev, old_rev = last_revisions
                else:
                    rev = old_rev = page.last_rev

                # send notifications
                send_edit_notifications(request.user, rev, old_rev)

                if page.metadata.get('redirect'):
                    url = href('wiki', page.name, redirect='no')
                else:
                    url = href('wiki', page.name)
                return HttpResponseRedirect(url)
    elif not request.user.is_authenticated:
        flash(_(u'You are in the process of editing this page unauthenticated. '
                u'If you save, your IP-Address will be recorded in the '
                u'revision history and is irrevocable publicly visible.'))


    # if we have merged this request we should inform the user about that,
    # and that we haven't saved the page yet.
    if merged_this_request:
        flash(_(u'Another user edited this page also.  '
                u'Please check if the automatic merging is satisfying.'))

    return {
        'name':         name,
        'title':        get_pagetitle(name),
        'page':         page,
        'form':         form,
        'preview':      preview,
        'edit_time':    edit_time.strftime('%s'),
        'rev':          current_rev_id,
        'storage':      storage,
        'deny_robots':  True,
    }


@require_privilege('delete')
@does_not_exist_is_404
def do_delete(request, name):
    """Delete the page (deletes the last recent revision)."""
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            flash(_(u'Canceled'))
        else:
            page.edit(user=request.user, deleted=True,
                      remote_addr=request.META.get('REMOTE_ADDR'),
                      note=request.POST.get('note', '') or
                           _(u'Page deleted'))
            flash(_(u'Page deleted'), success=True)
    else:
        flash(render_template('wiki/action_delete.html', {'page': page}))
    return HttpResponseRedirect(url_for(page))


#TODO: This damn function is much too specific as translation would
#      make sense.  We need to figure out how to rewrite this properly.
@require_privilege('manage')
@templated('wiki/action_mv_baustelle.html')
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
                text = text[text.find('\n')+1:]
            new_text = u'[[Vorlage(Überarbeitung, %s%s, %s)]]\n%s' % (date,
                       name, data['user'], text)
            try:
                Page.objects.get_by_name(data['new_name'])
            except Page.DoesNotExist:
                if not _rename(request, page, data['new_name'],
                               new_text=new_text):
                    flash(u'Beim Verschieben in die Baustelle ist ein Fehler '
                          u'aufgereten.', success=False)
                    return HttpResponseRedirect(url_for(page))
            else:
                flash(u'In der Baustelle befindet sich bereits eine Seite '
                      u'mit dem Namen „%s”.' % data['new_name'], False)
                return HttpResponseRedirect(url_for(page))

            # Create copy (and include box)
            if not discontinued:
                copy_text = u'[[Vorlage(Kopie, %s)]]\n' % name + text
                Page.objects.create(name=name, text=copy_text,
                    user=request.user,
                    note=u'Kopie; Original in der Baustelle')
            return HttpResponseRedirect(url_for(page))

    form = MvBaustelleForm()
    if discontinued:
        init_name = name.replace('Baustelle/Verlassen/', 'Baustelle/')
    else:
        init_name = 'Baustelle/%s' % name
    form.initial = {'new_name': init_name, 'user': request.user}
    return {
        'page':page,
        'form':form,
    }


#TODO: This damn function is way too specific as translation would
#      make sense.  We need to figure out how to rewrite this properly.
@require_privilege('manage')
@does_not_exist_is_404
def do_mv_discontinued(request, name):
    """Move page from ``Baustelle`` to ``Baustelle/Verlassen``"""
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            flash(u'Verschieben wurde abgebrochen.')
        else:
            new_name = name.replace('Baustelle', 'Baustelle/Verlassen')
            text = page.revisions.latest().text.value
            if text.startswith('[[Vorlage(Baustelle'):
                text = text[text.find('\n')+1:]
            text = u'[[Vorlage(Verlassen)]]\n' + text
            try:
                Page.objects.get_by_name(new_name)
            except Page.DoesNotExist:
                if not _rename(request, page, new_name, new_text=text):
                    flash(u'Beim Verschieben ist ein Fehler aufgereten.', False)
                    return HttpResponseRedirect(url_for(page))
            else:
                flash(u'Die Seite „%s” existiert bereits.' % new_name, False)
                return HttpResponseRedirect(url_for(page))

            request_cache.delete('wiki/page/' + name)
            flash(u'Seite wurde erfolgreich verschoben.', success=True)
    else:
        flash(render_template('wiki/action_mv_discontinued.html', {'page': page}))
    return HttpResponseRedirect(url_for(page))


#TODO: This damn function is way too specific as translation would
#      make sense.  We need to figure out how to rewrite this properly.
@require_privilege('manage')
@does_not_exist_is_404
def do_mv_back(request, name):
    """
    Move page back from ``Baustelle`` to its origin, move copy (which may exist
    at this origin) to ``Trash/`` and remove box (so revert ``do mv_baustelle``
    """
    page = Page.objects.get_by_name(name, raise_on_deleted=True)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            flash(u'Wiederherstellen wurde abgebrochen.')
        else:
            new_name = name.lstrip('Baustelle/')
            ## Move copy to Trash
            try:
                copy = Page.objects.get_by_name(new_name)
            except Page.DoesNotExist:
                # no need to move to Trash
                pass
            else:
                copy_text = copy.revisions.latest().text.value
                if copy_text.startswith('[[Vorlage(Kopie'):
                    copy_text = copy_text[copy_text.find('\n')+1:]
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
                    flash(u'Kopie konnte nicht nach Trash verschoben werden', False)
                    return HttpResponseRedirect(url_for(page))
            ## Remove box
            text = page.revisions.latest().text.value
            if text.startswith(u'[[Vorlage(Baustelle') or \
                text.startswith(u'[[Vorlage(Überarbeitung'):
                text = text[text.find('\n')+1:]
            ## Rename
            if not _rename(request, page, new_name, new_text=text):
                flash(u'Beim Verschieben ist ein Fehler aufgereten.', False)
                return HttpResponseRedirect(url_for(page))

            request_cache.delete('wiki/page/' + name)

            flash(u'Seite wurde erfolgreich ins Wiki verschoben.', success=True)
            return HttpResponseRedirect(url_for(page))
    else:
        flash(render_template('wiki/action_mv_back.html', {'page': page}))
    return HttpResponseRedirect(url_for(page))


@require_privilege('read')
@templated('wiki/action_log.html', modifier=context_modifier)
def do_log(request, name):
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
    try:
        pagination_page = int(request.GET['page'])
    except (ValueError, KeyError):
        pagination_page = 1
    page = Page.objects.get(name__exact=name)

    def link_func(p, parameters):
        if p == 1:
            parameters.pop('page', None)
        else:
            parameters['page'] = str(p)
        rv = url_for(page)
        if parameters:
            rv += '?' + urlencode(parameters)
        return rv

    if request.GET.get('format') == 'atom':
        return HttpResponseRedirect(href('wiki', '_feed', page.name, 20))

    pagination = Pagination(request, page.revisions.all().order_by('-id'), pagination_page,
                            20, link_func)
    return {
        'page':         page,
        'revisions':    pagination.get_queryset(),
        'pagination':   pagination,
        'deny_robots':  True,
    }


@require_privilege('read')
@templated('wiki/action_diff.html', modifier=context_modifier)
def do_diff(request, name):
    """Render a diff between two pages."""
    old_rev = request.GET.get('rev', '')
    if not old_rev.isdigit():
        old_rev = Page.objects.get_head(name, -1)
        if old_rev is None:
            raise Revision.DoesNotExist()
    new_rev = request.GET.get('new_rev') or None
    if new_rev and not new_rev.isdigit():
        raise PageNotFound()
    diff = Page.objects.compare(name, old_rev, new_rev)
    if request.GET.get('format') == 'udiff':
        return HttpResponse(diff.udiff, mimetype='text/plain; charset=utf-8')

    return {
        'diff':         diff,
        'page':         diff.page,
        'deny_robots':  True,
    }


@require_privilege('read')
@templated('wiki/action_backlinks.html', modifier=context_modifier)
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
        'deny_robots':  True,
    }


@require_privilege('read')
@does_not_exist_is_404
def do_export(request, name):
    """
    Export the given revision or the most recent one to the specified format
    (raw, html or ast so far).

    =============== ======= ==================================================
    Format          Partial Full    Description
    =============== ======= ==================================================
    ``raw``         yes     no      The raw wiki markup exported.
    ``HTML``        yes     yes     The wiki markup converted to HTML4.
    ``AST``         yes     no      The wiki markup as internal abstract
                                    syntax tree.  Useful for debugging.
    =============== ======= ==================================================


    **Template**
        Depending on the output format either no template at all or one of
        the following ones:
        -   ``'wiki/export.html'``

    **Context**
        The context is of course only passed if a template is rendered but
        the same for all the templates.

        ``fragment``
            `True` if a fragment should be rendered (no xml preamble etc)

        ``page``
            The bound `Page` object which should be rendered.
    """
    rev = request.GET.get('rev')
    if rev is None or not rev.isdigit():
        page = Page.objects.get_by_name(name, raise_on_deleted=True)
    else:
        page = Page.objects.get_by_name_and_rev(name, rev,
                                                raise_on_deleted=True)
    ctx = {
        'fragment': request.GET.get('fragment', 'no') == 'yes',
        'page':     page
    }
    format = request.GET.get('format', 'raw').lower()
    if format == 'html':
        return TemplateResponse('wiki/export.html', ctx,
                                content_type='text/html; charset=utf-8')
    elif format == 'ast':
        return HttpResponse(repr(page.rev.text.parse()),
                            content_type='text/plain; charset=ascii')
    else:
        return HttpResponse(page.rev.text.value.encode('utf-8'),
                            content_type='text/plain; charset=utf-8')


@require_privilege('attach')
@templated('wiki/action_attach.html', modifier=context_modifier)
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
        flash(_(u'Attachments within attachments are not allowed!'), False)
        return HttpResponseRedirect(url_for(page))
    attachments = Page.objects.get_attachment_list(page.name)
    attachments = [Page.objects.get_by_name(i) for i in attachments]
    context = {
        'page':        page,
        'attachments': attachments,
        'form':        AddAttachmentForm()
    }
    if request.method == 'POST':
        if request.POST.get('cancel'):
            flash(_(u'Canceled'))
            if page and page.metadata.get('redirect'):
                url = href('wiki', page.name, redirect='no')
            else:
                url = href('wiki', name)
            return HttpResponseRedirect(url)
        form = AddAttachmentForm(request.POST, request.FILES)
        if not form.is_valid():
            context['form'] = form
            return context
        d = form.cleaned_data
        attachment_name = d.get('filename') or d['attachment'].name
        filename = d['attachment'].name or d.get('filename')
        if not attachment_name:
            flash(_(u'Please enter a name for this attachment.'))
            return context
        attachment_name = u'%s/%s' % (name, attachment_name)
        attachment_name = normalize_pagename(attachment_name.strip('/'))
        try:
            ap = Page.objects.get_by_name(attachment_name)
        except Page.DoesNotExist:
            ap = None
        if ap is not None and (ap.rev.attachment is None or
                               not d.get('override', False)):
            flash(_(u'Another page or attachment with the same name exists'),
                  False)
            return context
        remote_addr = request.META.get('REMOTE_ADDR')
        if ap is None:
            ap = Page.objects.create(user=request.user,
                                     text=d.get('text', u''),
                                     remote_addr=remote_addr,
                                     name=attachment_name,
                                     note=d.get('note', u''),
                                     attachment_filename=filename,
                                     attachment=d['attachment'])
        else:
            ap.edit(user=request.user,
                    text=d.get('text', ap.rev.text),
                    remote_addr=remote_addr,
                    note=d.get('note', u''),
                    attachment_filename=filename,
                    attachment=d['attachment'])
        flash(_(u'Attachment saved successfully.'), True)
        if ap.metadata.get('weiterleitung'):
            url = href('wiki', ap, redirect='no')
        else:
            url = href('wiki', ap)
        return HttpResponseRedirect(url)

    context['deny_robots'] = 'noindex'
    return context


@require_privilege('attach')
@templated('wiki/action_attach_edit.html', modifier=context_modifier)
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
                attachment_filename = d['attachment'].name or \
                                        page.rev.attachment.filename
            page.edit(user=request.user,
                        text=d.get('text', page.rev.text.value),
                        remote_addr=request.META.get('remote_addr'),
                        note=d.get('note', u''),
                        attachment_filename=attachment_filename,
                        attachment=attachment)
            flash(_(u'Attachment edited successfully.'), True)
            return HttpResponseRedirect(url_for(page))
    return {
        'form': form,
        'page': page
    }


@require_privilege('manage')
@does_not_exist_is_404
def do_prune(request, name):
    """Clear the page cache."""
    page = Page.objects.get_by_name(name)
    page.prune()
    flash(_(u'Emptied the page cache.'), True)
    return HttpResponseRedirect(url_for(page))


@templated('wiki/action_manage.html', modifier=context_modifier)
def do_manage(request, name):
    """
    Show a list of all actions for this page.

    **Template**
        ``'wiki/action_manage.html'``
    """
    return {
        'page':         Page.objects.get_by_name(name),
        'deny_robots':  True,
    }


@simple_check_login
def do_subscribe(request, page_name):
    """
    Subscribe the user to the page with `page_name`
    """
    page = Page.objects.get(name__exact=page_name)
    if not Subscription.objects.user_subscribed(request.user, page):
        # there's no such subscription yet, create a new one
        Subscription(user=request.user, content_object=page).save()
        flash(_(u'You will be notified on changes on this page'), True)
    else:
        flash(_(u'You are already subscribed'))
    return HttpResponseRedirect(url_for(page))


@simple_check_login
def do_unsubscribe(request, page_name):
    """
    Unsubscribe the user from the page with `page_name`
    """
    page = Page.objects.get(name__exact=page_name)
    try:
        subscription = Subscription.objects.get_for_user(request.user, page)
    except Subscription.DoesNotExist:
        flash(_(u'No subscription for this page found.'), False)
    else:
        subscription.delete()
        flash(_(u'You won\'t be notified on changes on this page anymore'),
              True)
    # redirect the user to the page he last watched
    if request.GET.get('next', False) and is_safe_domain(request.GET['next']):
        return HttpResponseRedirect(request.GET['next'])
    else:
        return HttpResponseRedirect(url_for(page))



@require_privilege('edit')
@does_not_exist_is_404
@templated('wiki/action_manage_discussion.html')
def do_manage_discussion(request, name):
    page = Page.objects.get(name=name)
    if request.method == 'POST':
        form = ManageDiscussionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data['topic']:
                page.topic = data['topic']
                page.save()
                return HttpResponseRedirect(url_for(data['topic']))
            else:
                page.topic = None
                page.save()
                return HttpResponseRedirect(url_for(page))
    elif page.topic is None:
        form = ManageDiscussionForm()
    else:
        form = ManageDiscussionForm(initial={'topic': page.topic.slug})
    return {
        'page': page,
        'form': form,
    }

PAGE_ACTIONS = {
    'show':              do_show,
    'metaexport':        do_metaexport,
    'log':               do_log,
    'diff':              do_diff,
    'revert':            do_revert,
    'rename':            do_rename,
    'edit':              do_edit,
    'delete':            do_delete,
    'mv_baustelle':      do_mv_baustelle,
    'mv_discontinued':   do_mv_discontinued,
    'mv_back':           do_mv_back,
    'backlinks':         do_backlinks,
    'export':            do_export,
    'attach':            do_attach,
    'prune':             do_prune,
    'manage':            do_manage,
    'subscribe':         do_subscribe,
    'unsubscribe':       do_unsubscribe,
    'manage_discussion': do_manage_discussion,
}
