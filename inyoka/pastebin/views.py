"""
    inyoka.pastebin.views
    ~~~~~~~~~~~~~~~~~~~~~

    Views for the pastebin.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from inyoka.pastebin.forms import AddPasteForm
from inyoka.pastebin.models import Entry
from inyoka.utils.http import templated
from inyoka.utils.templating import flash_message
from inyoka.utils.urls import href


@login_required
@permission_required('pastebin.add_entry', raise_exception=True)
@templated('pastebin/add.html')
def add(request):
    if request.method == 'POST':
        form = AddPasteForm(request.POST)
        if form.is_valid():
            entry = form.save(request.user)
            description = _('Your entry was successfully saved. You can use '
                            'the following code to include it in your post:')
            example = '<code>[paste:%(id)d:%(title)s]</code>' % {
                      'id': entry.id, 'title': entry.title}
            messages.success(request, (' '.join([description, example])))
            return HttpResponseRedirect(href('pastebin', entry.id))
    else:
        form = AddPasteForm()
    return {
        'form': form,
        'page': 'add'
    }


@permission_required('pastebin.view_entry', raise_exception=True)
@templated('pastebin/display.html')
def display(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    return {
        'entry': entry,
        'page': 'browse'
    }


@login_required
@permission_required('pastebin.delete_entry', raise_exception=True)
def delete(request, entry_id):
    """
    Request Handler for Pastebin delete requests.
    """
    entry = get_object_or_404(Entry, id=entry_id)

    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, _('The deletion was canceled'))
        else:
            entry.delete()
            messages.success(request, _('The entry in the pastebin was deleted.'))
            return HttpResponseRedirect(href('pastebin'))
    else:
        flash_message(request, 'pastebin/delete_entry.html', {'entry': entry})

    return HttpResponseRedirect(href('pastebin', entry.id))


@permission_required('pastebin.view_entry', raise_exception=True)
def raw(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)
    return HttpResponse(entry.code, content_type='text/plain; charset=utf-8')


@permission_required('pastebin.view_entry', raise_exception=True)
@templated('pastebin/browse.html')
def browse(request):
    return {
        'entries': list(Entry.objects.select_related().all()[:50]),
        'page': 'browse'
    }
