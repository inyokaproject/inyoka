# -*- coding: utf-8 -*-
"""
    inyoka.planet.views
    ~~~~~~~~~~~~~~~~~~~

    Views for the planet.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.conf import settings
from django.contrib import messages
from django.utils.text import truncate_html_words
from django.db.models import Max
from inyoka.portal.user import Group
from inyoka.portal.utils import check_login, require_permission
from inyoka.utils import generic
from inyoka.utils.urls import href
from inyoka.utils.http import templated, HttpResponseRedirect, \
                              does_not_exist_is_404, HttpResponse
from inyoka.utils.html import escape
from inyoka.utils.templating import render_template
from inyoka.utils.pagination import Pagination
from inyoka.utils.mail import send_mail
from inyoka.utils.dates import group_by_day
from inyoka.planet.models import Blog, Entry
from inyoka.planet.forms import SuggestBlogForm, EditBlogForm
from inyoka.utils.feeds import atom_feed, AtomFeed



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
    required_permission='blog_edit',
    base_link = href('planet', 'blogs'))


blog_edit = generic.CreateUpdateView(model=Blog,
    form_class=EditBlogForm,
    template_name='planet/blog_edit.html',
    context_object_name='blog', slug_field='id',
    required_permission='blog_edit')


@templated('planet/index.html', modifier=context_modifier)
def index(request, page=1):
    """
    The index function just returns the 30 latest entries of the planet.
    The page number is optional.
    """
    entries = Entry.objects.select_related('blog')
    if not request.user.can('blog_edit'):
        entries = entries.filter(hidden=False)

    pagination = Pagination(request, entries, page, 25, href('planet'))
    queryset = pagination.get_queryset()
    return {
        'days':         group_by_day(queryset),
        'articles':     queryset,
        'pagination':   pagination,
        'page':         page,
    }


@check_login(message=u'Du musst eingeloggt sein, um einen Blog'
                     u' vorzuschlagen.')
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
            ikhaya_group = Group.objects.get(id=settings.IKHAYA_GROUP_ID)
            users = ikhaya_group.user_set.all()
            text = render_template('mails/planet_suggest.txt',
                                   form.cleaned_data)
            for user in users:
                send_mail('Neuer Blogvorschlag', text,
                          settings.INYOKA_SYSTEM_USER_EMAIL,
                          [user.email])
            if not users:
                messages.error(request, u'Es sind keine Benutzer als '
                               u'Planet-Administratoren eingetragen.')
                return HttpResponseRedirect(href('planet'))
            messages.info(request, u'Der Blog „%s“ wurde vorgeschlagen.' %
                  escape(form.cleaned_data['name']))
            return HttpResponseRedirect(href('planet'))
    else:
        form = SuggestBlogForm()
    return {'form': form}


@atom_feed(name='planet_feed')
def feed(request, mode='short', count=10):
    """show the feeds for the planet"""
    feed = AtomFeed(u'ubuntuusers Planet', url=href('planet'),
                    feed_url=request.build_absolute_uri(),
                    id=href('planet'),
                    subtitle=u'Der ubuntuusers-Planet sammelt '
                             u'verschiedene Blogs zu Ubuntu und Linux',
                    rights=href('portal', 'lizenz'),
                    icon=href('static', 'img', 'favicon.ico'))

    entries = Entry.objects.get_latest_entries(count)

    for entry in entries:
        kwargs = {}
        if mode == 'full':
            kwargs['content'] = u'<div xmlns="http://www.w3.org/1999/' \
                                u'xhtml">%s</div>' % entry.text
            kwargs['content_type'] = 'xhtml'
        if mode == 'short':
            summary = truncate_html_words(entry.text, 100)
            kwargs['summary'] = u'<div xmlns="http://www.w3.org/1999/' \
                                u'xhtml">%s</div>' % summary
            kwargs['content_type'] = 'xhtml'
        if entry.author_homepage:
            kwargs['author'] = {'name': entry.author,
                                'uri':  entry.author_homepage}
        else:
            kwargs['author'] = entry.author

        feed.add(title=entry.title,
                 url=entry.url,
                 id=entry.guid,
                 updated=entry.updated,
                 published=entry.pub_date,
                 **kwargs)
    return feed


@require_permission('blog_edit')
@does_not_exist_is_404
def hide_entry(request, id):
    """Hide a planet entry"""
    entry = Entry.objects.get(id=id)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            messages.info(request, u'Aktion wurde abgebrochen.')
        else:
            entry.hidden = False if entry.hidden else True
            if entry.hidden:
                entry.hidden_by = request.user
            entry.save()
            msg = (u'Der Eintrag „%s” wurde erfolgreich %s.' %
                (entry.title, 'versteckt' if entry.hidden
                                          else 'wiederhergestellt'))
            messages.success(request, msg)
    else:
        messages.info(request, render_template('planet/hide_entry.html',
                      {'entry': entry}))
    return HttpResponseRedirect(href('planet'))


def export(request, export_type):
    """Export the blog ist as OPML or FOAF"""
    blogs = Blog.objects.filter(active=True).all()
    assert export_type in ('foaf', 'opml')
    ext = {'foaf': 'rdf', 'opml': 'xml'}

    data = render_template('planet/%s.xml' % export_type,
                           {'blogs': blogs})
    response = HttpResponse(data, mimetype='text/xml; charset=utf-8')
    response['Content-Disposition'] = ('attachment; filename=ubuntuusers_%s.%s'
                                       % (export_type, ext[export_type]))
    return response
