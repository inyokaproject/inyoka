# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.views
    ~~~~~~~~~~~~~~~~~~~~~

    Views for the pastebin.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.contrib import messages

from inyoka.utils.urls import href, global_not_found
from inyoka.utils.http import templated, HttpResponseRedirect, HttpResponse, \
        PageNotFound
from inyoka.utils.templating import render_template
from inyoka.pastebin.forms import AddPasteForm
from inyoka.pastebin.models import Entry
from inyoka.portal.utils import require_permission


@templated('pastebin/add.html')
def index(request):
    if request.method == 'POST':
        form = AddPasteForm(request.POST)
        if form.is_valid() and 'renew_captcha' not in request.POST:
            entry = form.save(request.user)
            messages.success(request,
                u'Dein Eintrag wurde erfolgreich gespeichert. Du kannst '
                u'folgenden Code verwenden, um ihn einzubinden: '
                u'<code>[paste:%s:%s]</code>' % (entry.id, entry.title))
            return HttpResponseRedirect(href('pastebin', entry.id))
        if 'renew_captcha' in request.POST and 'captcha' in form.errors:
            del form.errors['captcha']
    else:
        form = AddPasteForm()
    return {
        'form': form,
        'page': 'add'
    }


@templated('pastebin/display.html')
def display(request, entry_id):
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        return global_not_found(request, u'Paste Nummer %s konnte nicht gefunden '
                                  u'werden' % entry_id)
    referrer = request.META.get('HTTP_REFERER')
    if referrer and entry.add_referrer(referrer):
        entry.save()
    return {
        'entry': entry,
        'page':  'browse'
    }


@require_permission('manage_pastebin')
def delete(request, entry_id):
    """
    Request Handler for Pastebin delete requests.
    """
    entry = Entry.objects.get(id=entry_id)
    if not entry:
        raise PageNotFound
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, u'Das Löschen wurde abgebrochen.')
        else:
            entry.delete()
            messages.info(request, u'Der Eintrag in der Ablage wurde gelöscht.')
            return HttpResponseRedirect(href('pastebin'))
    else:
        messages.info(request, render_template('pastebin/delete_entry.html',
                      {'entry': entry}))
    return HttpResponseRedirect(href('pastebin', entry.id))


def raw(request, entry_id):
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        raise PageNotFound
    return HttpResponse(entry.code, content_type='text/plain')


@templated('pastebin/browse.html')
def browse(request):
    return {
        'entries':      list(Entry.objects.all()[:50]),
        'page':         'browse'
    }
