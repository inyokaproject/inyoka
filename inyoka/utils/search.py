#-*- coding: utf-8 -*-
"""
    inyoka.utils.search
    ~~~~~~~~~~~~~~~~~~~

    Abstract search helpers to ease PyES and ElasticSearch integration.

    :copyright: (c) 2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import partial

from django.conf import settings

from pyes import ES, Search, FilteredQuery, StringQuery, Filter, ANDFilter, ORFilter



SIMPLE_TYPES = (int, long, str, list, dict, tuple, bool,
                float, bool, unicode, type(None))


class TypeFilter(Filter):
    _internal_name = "type"

    def __init__(self, type, **kwargs):
        super(TypeFilter, self).__init__(**kwargs)
        self._type = type

    def serialize(self):
        if not self._type:
            raise RuntimeError("A least a field/value pair must be added")
        return {self._internal_name : {'value': self._type}}


def _get_attrs(obj):
    not_underscore = partial(filter, lambda k: not k.startswith('_'))
    return not_underscore(obj._meta.get_all_field_names())


def serialize_instance(instance, doctype, extra):
    """Serializes a django model instance using the `mapping` supplied by the
    `doctype`. Data in `extra` takes precedence over field values. If the
    `doctype` has a `prepare_fieldname` attribute the data for this mapping
    field is run through that function (Useful for m2m relations etc).
    """
    data = {}

    instance_fields = dir(instance)
    prepared_fields = [x[8:] for x in dir(doctype) if x.startswith('prepare_')]

    for field_name in doctype.mapping['properties']:
        if extra and field_name in extra:
            obj = extra[field_name]
        elif field_name in instance_fields:
            obj = getattr(instance, field_name)
        else:
            raise ValueError('Field not found in `extra` or on the instance.')

        if field_name in prepared_fields:
            obj = getattr(doctype, 'prepare_%s' % field_name)(obj)

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

    def __init__(self, search):
        self.search = search

    def store_object(self, obj, type, extra):
        """Store `obj`.

        :param obj: The object to store in the elastic search index.
        :param type: The document type class that describes `obj`.
        """
        self.search.get_connection().index(type.serialize(obj, extra), self.name,
                                           type.name, obj.pk)

    @property
    def type_map(self):
        return dict((t.name, t) for t in self.types)


class DocumentType(object):
    """A document type.

    This object holds the data that will be indexed.
    """

    #: The name of this document type
    name = None

    #: The model this document type implements. This is currently unused
    #: but can be used for documentation.
    model = None

    #: A dictionary to describe a elastic search mapping.
    #: Example:
    #:
    #: mapping = {'properties': {
    #: 'name': {
    #: 'type': 'string',
    #: 'store': 'yes',
    #: 'index': 'analyzed'
    #: }
    #: }}
    mapping = {}

    @classmethod
    def serialize(cls, obj, extra):
        return serialize_instance(obj, cls, extra)


class SearchSystem(object):
    """
    The central object that is used by applications to register their
    search interfaces.
    """

    def __init__(self):
        if not settings.SEARCH_NODES:
            raise RuntimeError('You must specify search nodes!')
        self.indices = {}

    def register(self, index):
        """Register an index for indexing and retrieving."""
        assert index.name is not None
        self.indices[index.name] = index(self)

    def store(self, index, type, obj, extra=None):
        if isinstance(index, basestring):
            index = self.indices[index]
        index.store_object(obj, index.type_map[type], extra)

    def get_connection(self, *args, **kwargs):
        return ES(settings.SEARCH_NODES, *args, **kwargs)

    def refresh_indices(self, recreate_mapping=False):
        connection = self.get_connection()
        for index in self.indices.itervalues():
            connection.create_index_if_missing(index.name)
            for doctype in index.types:
                if recreate_mapping:
                    # delete_mapping deletes data + mapping
                    connection.delete_mapping(index.name, doctype.name)
                connection.put_mapping(doctype.name, doctype.mapping,
                                       [index.name])

    def reindex(self):
        self.refresh_indices(True)
        connection = self.get_connection()
        for index in self.indices.itervalues():
            for doctype in index.types:
                for obj in doctype.model.objects.all():
                    self.store(index, doctype.name, obj)

    def search(self, query, indices=None, *args, **kwargs):
        if isinstance(query, basestring):
            query = StringQuery(query)

        if indices is None:
            indices = self.indices

        user = kwargs.pop('user', None)
        filters = []

        if user:
            for name, index in indices.iteritems():
                for type in index.types:
                    filter = type().get_filter(user)
                    if filter is not None:
                        filters.append(ANDFilter((TypeFilter('post'), filter)))

        if filters:
            query = FilteredQuery(query, filter=ORFilter(filters))
        search = Search(query=query, *args, **kwargs)
        return self.get_connection().search(query=search)


def autodiscover():
    """
    Auto-discover INSTALLED_APPS search.py modules and fail silently when
    not present. This forces an import on them to register any search bits they
    may want.
    """

    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's search module.
        try:
            import_module('%s.search' % app)
        except Exception:
            # Decide whether to bubble up this error. If the app just
            # doesn't have a search module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'search'):
                raise


#: Singleton that implements the search system
search = SearchSystem()
