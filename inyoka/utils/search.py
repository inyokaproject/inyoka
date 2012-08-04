#-*- coding: utf-8 -*-
"""
    inyoka.utils.search
    ~~~~~~~~~~~~~~~~~~~

    Abstract search helpers to ease PyES and ElasticSearch integration.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import partial

from django.conf import settings
from django.db.models import signals

from pyes import ES, Search, FilteredQuery, StringQuery, Filter, ORFilter, \
    MatchAllQuery, DisMaxQuery, ANDFilter, NotFilter
from pyes.exceptions import NotFoundException, NoServerAvailable, ElasticSearchException

from inyoka.tasks import update_index


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


def _get_remove_instance_handler(search, index, type):
    def handler(sender, instance, using, type_name=type.name, **kwargs):
        if search.has_connection():
            try:
                conn =  search.get_connection()
                conn.delete(index.name, type_name, instance.pk)
            except (NotFoundException, NoServerAvailable):
                pass
    return handler


def _get_update_instance_handler(search, index, type):
    def handler(sender, instance, using, type_name=type.name, **kwargs):
        if search.has_connection() and not kwargs.get('created', False):
            try:
                conn = search.get_connection()
                conn.update(type.serialize(instance, {}), index.name, type_name, instance.pk)
            except (ElasticSearchException, instance.DoesNotExist):
                return
    return handler


class Index(object):
    """Index type that containes `DocumentType` objects to define actual objects"""

    #: The name of this index
    name = None

    #: A list of document types
    types = []

    def __init__(self, search):
        self.search = search
        for type in self.types:
            if type.autodelete:
                handler = _get_remove_instance_handler(search, self, type)
                signals.post_delete.connect(handler, sender=type.model,
                                            weak=False)
            if type.autoupdate:
                handler = _get_update_instance_handler(search, self, type)
                signals.post_save.connect(handler, sender=type.model,
                                          weak=False)

    def store_object(self, obj, type, extra, bulk=False):
        """Store `obj`.

        :param obj: The object to store in the elastic search index.
        :param type: The document type class that describes `obj`.
        """
        self.search.get_connection().index(type.serialize(obj, extra), self.name,
                                           type.name, obj.pk, bulk=bulk)

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

    #: Automatically delete the entry if the model is deleted
    autodelete = True

    #: Automatically update the entry if the model is saved
    autoupdate = True

    @classmethod
    def get_filter(cls, user):
        return None

    @classmethod
    def get_objects(cls, docpks):
        return self.model.objects.filter(pk__in=docpks).all()

    @classmethod
    def get_doc_ids(cls):
        qry = self.model.objects.values_list('id', flat=True).oder_by('id')
        for idx in qry:
            yield idx

    @classmethod
    def get_boost_query(cls, query):
        return None

    @classmethod
    def serialize(cls, obj, extra):
        return serialize_instance(obj, cls, extra)


class SearchSystem(object):
    """
    The central object that is used by applications to register their
    search interfaces.
    """

    def __init__(self, server=None):
        if not settings.SEARCH_NODES and not server:
            raise RuntimeError('You must specify search nodes!')
        self.server = server or settings.SEARCH_NODES
        self.indices = {}

    def register(self, index):
        """Register an index for indexing and retrieving."""
        assert index.name is not None
        self.indices[index.name] = index(self)

    def store(self, index, type, obj, extra=None, bulk=False):
        if isinstance(index, basestring):
            index = self.indices[index]
        if isinstance(type, basestring):
            type = index.type_map[type]
        index.store_object(obj, type, extra, bulk=bulk)

    def get_indices(self, *names):
        return {name: index for name, index in self.indices.iteritems()
                if name in names}

    def get_connection(self, *args, **kwargs):
        return ES(self.server, *args, **kwargs)

    def has_connection(self):
        return self.get_connection().collect_info()

    def refresh_indices(self, recreate_mapping=False):
        connection = self.get_connection()
        for index in self.indices.itervalues():
            connection.create_index_if_missing(index.name)
            for doctype in index.types:
                if (recreate_mapping == index.name) or (recreate_mapping is True):
                    # delete_mapping deletes data + mapping
                    connection.delete_mapping(index.name, doctype.name)
                connection.put_mapping(doctype.name, doctype.mapping,
                                       [index.name])
        connection.refresh(self.indices.iterkeys())

    def reindex(self, index=None):
        block_size = settings.SEARCH_INDEX_BLOCKSIZE
        self.refresh_indices(True if index is None else index)
        if index is None:
            indices = self.indices.itervalues()
        else:
            indices = [self.indices[index]]
        for index in indices:
            self.get_connection().delete_index_if_exists(index.name)
            self.get_connection().create_index_if_missing(index.name)
            for doctype in index.types:
                docids = list(doctype.get_doc_ids())
                for idx in xrange(0, len(docids), block_size):
                    update_index.delay(docids[idx:idx+block_size],
                                       doctype.name, index.name)

    def parse_query(self, query, indices=None, user=None):
        original_query = ''
        filters = []
        boost_queries = []
        if not query:
            query = MatchAllQuery()
        elif isinstance(query, basestring):
            original_query = query
            query = StringQuery(query, default_operator='AND')


        if indices is None:
            indices = self.indices

        filtered_indices = []

        for name, index in indices.iteritems():
            for type in index.types:
                if user:
                    filter = type.get_filter(user)
                    if filter is not None:
                        filters.append(ANDFilter((TypeFilter(type.name), NotFilter(filter))))
                        filtered_indices.append(type.name)
                boost_query = type.get_boost_query(original_query)
                if boost_query:
                    boost_queries.append(boost_query)

        if filtered_indices:
            for index in self.indices.values():
                for type in index.types:
                    if type.name in filtered_indices:
                        filters.append(TypeFilter(type.name))

        if boost_queries:
            query = DisMaxQuery(query)
            query.add(boost_queries)

        if filters and user:
            query = FilteredQuery(query, filter=ORFilter(filters))
        return query

    def search(self, query, indices=None, *args, **kwargs):
        query = self.parse_query(query, indices, kwargs.pop('user', None))
        search = Search(query=query, *args, **kwargs)
        result = self.get_connection().search(query=search)
        result._do_search()
        result.fix_keys()
        return result


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
autodiscover()
