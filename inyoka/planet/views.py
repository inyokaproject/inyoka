"""
    inyoka.planet.views
    ~~~~~~~~~~~~~~~~~~~

    Views for the planet.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import html

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import escape, smart_urlquote
from django.utils.translation import gettext as _

from inyoka.planet.forms import EditBlogForm, SuggestBlogForm
from inyoka.planet.models import Blog, Entry
from inyoka.utils import generic
from inyoka.utils.dates import group_by_day
from inyoka.utils.feeds import InyokaAtomFeed
from inyoka.utils.http import does_not_exist_is_404, templated
from inyoka.utils.mail import send_mail
from inyoka.utils.pagination import Pagination
from inyoka.utils.storage import storage
from inyoka.utils.templating import flash_message
from inyoka.utils.urls import href


def context_modifier(request, context):
    """
    This function is called of ``templated`` automatically to copy the list of
    blogs into the context.
    """
    context['blogs'] = Blog.objects.filter(active=True).all()


blog_list = generic.ListView.as_view(default_column='-latest_update',
                                     queryset=Blog.objects.annotate(latest_update=Max('entry__pub_date')),
                                     template_name='planet/blog_list.html',
                                     columns=['name', 'user', 'latest_update', 'active'],
                                     permission_required='planet.change_blog',
                                     base_link=href('planet', 'blogs'))

blog_edit = generic.CreateUpdateView(model=Blog,
                                     form_class=EditBlogForm,
                                     template_name='planet/blog_edit.html',
                                     context_object_name='blog', slug_field='id',
                                     permission_required='planet.change_blog')


@templated('planet/index.html', modifier=context_modifier)
def index(request, page=1):
    """
    The index function just returns the 30 latest entries of the planet.
    The page number is optional.
    """
    entries = Entry.objects.select_related('blog')
    if not request.user.has_perm('planet.hide_entry'):
        entries = entries.filter(hidden=False)

    pagination = Pagination(request, entries, page, 25, href('planet'))
    queryset = pagination.get_queryset()
    return {
        'planet_description_rendered': storage['planet_description_rendered'],
        'days': group_by_day(queryset),
        'articles': queryset,
        'pagination': pagination,
        'page': page,
    }


@login_required
@permission_required('planet.suggest_blog', raise_exception=True)
@templated('planet/suggest.html', modifier=context_modifier)
def suggest(request):
    """
    A Page to suggest a new blog.  It just sends an email to the planet
    administrators.
    """
    if 'abort' in request.POST:
        return HttpResponseRedirect(href('planet'))

    if request.method == 'POST':
        form = SuggestBlogForm(request.POST)
        if form.is_valid():
            users = Group.objects.get(name__iexact=settings.INYOKA_IKHAYA_GROUP_NAME).user_set.all()
            if not users:
                messages.error(request, _('No user is registered as a planet administrator.'))
                return HttpResponseRedirect(href('planet'))

            text = render_to_string('mails/planet_suggest.txt',
                                    form.cleaned_data)
            for user in users:
                send_mail(_('A new blog was suggested.'), text,
                          settings.INYOKA_SYSTEM_USER_EMAIL,
                          [user.email])

            messages.success(request, _('The blog “%(title)s” was suggested.')
                             % {'title': escape(form.cleaned_data['name'])})
            return HttpResponseRedirect(href('planet'))
    else:
        form = SuggestBlogForm()
    return {
        'form': form,
        'planet_description_rendered': storage['planet_description_rendered'],
    }


class PlanetAtomFeed(InyokaAtomFeed):
    title = _('%(sitename)s planet') % {'sitename': settings.BASE_DOMAIN_NAME}
    name = 'planet_feed'

    def link(self):
        return href('planet')

    def _subtitle(self, _):
        return storage['planet_description_rendered']

    def items(self):
        return Entry.objects.get_latest_entries(self.count)

    def item_title(self, item):
        if not item.title:
            return _("No title given")

        return html.unescape(item.title)

    def item_description(self, item):
        if self.mode == 'full':
            return item.text

        if self.mode == 'short':
            return self._shorten_html(item.text)

    def item_link(self, item):
        return item.url

    def item_guid(self, item):
        return smart_urlquote(item.guid)

    def item_author_name(self, item):
        return item.author

    def item_author_link(self, item):
        if item.author_homepage:
            return item.author_homepage

    def item_pubdate(self, item):
        return item.pub_date

    def item_updateddate(self, item):
        return item.updated


@login_required
@permission_required('planet.hide_entry', raise_exception=True)
@does_not_exist_is_404
def hide_entry(request, id):
    """Hide a planet entry"""
    entry = Entry.objects.get(id=id)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, _('Canceled'))
        else:
            entry.hidden = False if entry.hidden else True
            entry.hidden_by = request.user if entry.hidden else None
            entry.save()
            if entry.hidden:
                msg = _('The entry “%(title)s” was successfully hidden.')
            else:
                msg = _('The entry “%(title)s” was successfully restored.')
            messages.success(request, msg % {'title': entry.title})
    else:
        flash_message(request, 'planet/hide_entry.html', {'entry': entry})
    return HttpResponseRedirect(href('planet'))


def export(request, export_type):
    """Export the blog list as OPML or FOAF"""
    blogs = Blog.objects.filter(active=True).all()
    assert export_type in ('foaf', 'opml')
    ext = {'foaf': 'rdf', 'opml': 'xml'}

    response = render('planet/%s.xml' % export_type, {'blogs': blogs},
                      content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = ('attachment; filename=ubuntuusers_%s.%s'
                                       % (export_type, ext[export_type]))
    return response
