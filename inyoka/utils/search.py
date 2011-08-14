#-*- coding: utf-8 -*-
"""
    inyoka.utils.search
    ~~~~~~~~~~~~~~~~~~~

    Abstract search helpers to ease PyES and ElasticSearch integration.

    :copyright: (c) 2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import inspect
import datetime
from functools import partial
from itertools import ifilter

from django.conf import settings

from pyes import ES



SIMPLE_TYPES = (int, long, str, list, dict, tuple, bool,
                float, bool, unicode, type(None))


def _get_attrs(obj):
    not_underscore = partial(filter, lambda k: not k.startswith('_'))
    return not_underscore(obj._meta.get_all_field_names())


def serialize_instance(instance, doctype):
    """Serialize a django model instance with taking `doctype` into account."""
    data = {}

    for field_name in _get_attrs(instance):
        if doctype.fields and field_name not in doctype.fields:
            continue
        if doctype.excludes and field_name in excludes:
            continue

        obj = getattr(instance, field_name)
        if not isinstance(obj, SIMPLE_TYPES) :
            raise ValueError('%r is not supported yet.' % obj)
        data[field_name] = obj

    return data


class Index(object):
    """Index type that containes `DocumentType` objects to define actual objects"""

    #: The name of this index
    name = None

    #: A list of document types
    types = []

    def store_object(self, obj, type):
        """Store `obj`.

        :param obj: The object to store in the elastic search index.
        :param type: The document type class that describes `obj`.
        """
        search.get_connection().index(type.serialize(obj), self.name,
                                      type.name, obj.pk)

    def get_type_map(self):
        return dict((t.name, t) for t in self.types)


class DocumentType(object):
    """A document type.

    This object holds the data that will be indexed.
    """

    #: The name of this document type
    name = None

    #: The model this document type implements.  This is currently unused
    #: but can be used for documentation.
    model = None

    #: A list of fields to store. Optional.
    fields = None

    #: A list of fields not to store. Optional.
    excludes = None

    #: A dictionary to describe a elastic search mapping.
    #: Example:
    #:
    #:     mapping = {'properties': {
    #:           'name': {
    #:               'type': 'string',
    #:               'store': 'yes',
    #:               'index': 'analyzed'
    #:           }
    #:     }}
    mapping = {}

    @classmethod
    def serialize(cls, obj):
        return serialize_instance(obj, cls)


class SearchSystem(object):
    """
    The central object that is used by applications to register their
    search interfaces.
    """

    def __init__(self):
        if not settings.SEARCH_NODES:
            raise RuntimeError('You must specify search nodes!')
        self.indexes = {}

    def register(self, index):
        """Register a index for indexing and retrieving."""
        assert index.name is not None
        self.indexes[index.name] = index

    def store(self, index, type, obj):
        if isinstance(index, basestring):
            index = self.indexes[index]()
        index.store_object(obj, index.get_type_map()[type])

    def get_connection(self, *args, **kwargs):
        return ES(settings.SEARCH_NODES, *args, **kwargs)

    def refresh_indexes(self):
        connection = self.get_connection()
        for index in self.indexes:
            connection.create_index_if_missing(index.name)
            for doctype in index.types:
                connection.put_mapping(doctype.name, doctype.mapping,
                                       [index.name])


#: Singleton that implements the search system
search = SearchSystem()
