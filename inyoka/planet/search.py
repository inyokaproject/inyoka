#-*- coding: utf-8 -*-
"""
    inyoka.planet.search
    ~~~~~~~~~~~~~~~~~~~~

    Search interfaces for the planet.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.planet.models import Entry
from inyoka.utils.search import search, SearchAdapter
from inyoka.utils.urls import url_for


class PlanetSearchAdapter(SearchAdapter):
    type_id = 'p'

    def get_objects(self, docids):
        return Entry.objects.select_related(depth=1) \
                    .filter(id__in=docids).all()

    def extract_data(self, entry):
        return {'title': entry.title,
                'user': entry.blog.name,
                'user_url': entry.blog.blog_url,
                'date': entry.pub_date,
                'url': url_for(entry),
                'component': u'Planet',
                'group': entry.blog.name,
                'group_url': url_for(entry.blog),
                'text': entry.text,
                'hidden': entry.hidden}

    def recv(self, entry_id):
        entry = Entry.objects.select_related(depth=1).get(id=entry_id)
        return self.extract_data(entry)

    def recv_multi(self, entry_ids):
        entries = Entry.objects.select_related(depth=1).filter(id__in=entry_ids)
        return [self.extract_data(entry) for entry in entries]

    def store_object(self, entry, connection=None):
        search.store(connection,
            component='p',
            uid=entry.id,
            title=entry.title,
            text=entry.simplified_text,
            date=entry.pub_date,
            category=entry.blog.name
        )

    def get_doc_ids(self):
        ids = Entry.objects.values_list('id', flat=True)
        for id in ids:
            yield id


search.register(PlanetSearchAdapter())
