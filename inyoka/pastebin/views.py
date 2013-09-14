# -*- coding: utf-8 -*-
"""
    inyoka.pastebin.views
    ~~~~~~~~~~~~~~~~~~~~~

    Views for the pastebin.

    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _

from inyoka.utils.urls import href
from inyoka.utils.http import templated, global_not_found
from inyoka.portal.utils import require_permission
from inyoka.pastebin.forms import AddPasteForm
from inyoka.pastebin.models import Entry
from inyoka.utils.templating import render_template


@templated('pastebin/add.html')
def index(request):
    if request.method == 'POST':
        form = AddPasteForm(request.POST)
        if form.is_valid() and 'renew_captcha' not in request.POST:
            entry = form.save(request.user)
            description = _(u'Your entry was successfully saved. You can use '
                            u'the following code to include it in your post:')
            example = u'<code>[paste:%(id)d:%(title)s]</code>' % {
                      'id': entry.id, 'title': entry.title}
            messages.success(request, (u' '.join([description, example])))
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
        return global_not_found(request, _(u'Paste number %(id)d could not be found')
                                  % {'id': int(entry_id)})
    referrer = request.META.get('HTTP_REFERER')
    if referrer and entry.add_referrer(referrer):
        entry.save()
    return {
        'entry': entry,
        'page': 'browse'
    }


@require_permission('manage_pastebin')
def delete(request, entry_id):
    """
    Request Handler for Pastebin delete requests.
    """
    entry = Entry.objects.get(id=entry_id)
    if not entry:
        raise Http404()
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, _(u'The deletion was canceled'))
        else:
            entry.delete()
            messages.success(request, _(u'The entry in the pastebin was deleted.'))
            return HttpResponseRedirect(href('pastebin'))
    else:
        messages.info(request, render_template('pastebin/delete_entry.html',
                      {'entry': entry}))
    return HttpResponseRedirect(href('pastebin', entry.id))


def raw(request, entry_id):
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        raise Http404()
    return HttpResponse(entry.code, content_type='text/plain; charset=utf-8')


@templated('pastebin/browse.html')
def browse(request):
    return {
        'entries': list(Entry.objects.all()[:50]),
        'page': 'browse'
    }
