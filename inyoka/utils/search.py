#-*- coding: utf-8 -*-
"""
    inyoka.utils.search
    ~~~~~~~~~~~~~~~~~~~

    This module implements an extensible search interface for all components
    of the inyoka system.  For the concrete implementations have a look at the
    `inyoka.app.search` modules, where app is the name of the application.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import time
import xapian
from weakref import WeakKeyDictionary
from collections import OrderedDict
from threading import currentThread as get_current_thread, local
from datetime import datetime, date
from cPickle import dumps, loads
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_unicode
from inyoka.utils import get_significant_digits

#TODO: i18n note: This module will be rewritten and with this rewrite
#                 i18n support will land in the search, for now it's
#                 german only.

LANGUAGE = 'de'
search = None

_tls = local()


def get_stemmer(language_code=LANGUAGE):
    """Get a stemmer for a given language.

    Thread local storage is
    used to ensure that the returned stemmer is specific to the current thread,
    since stemmers aren't threadsafe.

    """
    try:
        return _tls.stemmers[language_code]
    except KeyError:
        stemmer = xapian.Stem(language_code)
        _tls.stemmers[language_code] = stemmer
        return stemmer
    except AttributeError:
        stemmer = xapian.Stem(language_code)
        _tls.stemmers = {language_code: stemmer}
        return stemmer


_description_re = re.compile(r'([\w]+):\(pos=[\d+]\)')
_tcpsrv_re = re.compile(r'tcpsrv://([\w\d\.]+):(\d+)/?')


def get_human_readable_estimate(mset):
    lower = mset.get_matches_lower_bound()
    upper = mset.get_matches_upper_bound()
    est = mset.get_matches_estimated()
    return get_significant_digits(est, lower, upper)


def get_full_id(match):
    return match.document.get_value(0).split(':')


def _marshal_value(value):
    """Convert python values to a string of suitable xapian values."""
    if isinstance(value, datetime):
        value = _marshal_datetime(value)
    elif isinstance(value, date):
        value = _marshal_date(value)
    elif isinstance(value, bool):
        if value:
            value = u't'
        else:
            value = u'f'
    elif isinstance(value, float):
        value = xapian.sortable_serialise(value)
    elif isinstance(value, (int, long)):
        value = u'%012d' % value
    else:
        value = force_unicode(value).lower()
    return value


def _marshal_term(term):
    """Convert python terms to a string of suitable xapian terms."""
    if isinstance(term, datetime):
        term = _marshal_datetime(term)
    elif isinstance(term, date):
        term = _marshal_date(term)
    else:
        term = force_unicode(term).lower()
    return term


def _marshal_date(d):
    return u'%04d%02d%02d000000' % (d.year, d.month, d.day)


def _marshal_datetime(dt):
    if dt.microsecond:
        return u'%04d%02d%02d%02d%02d%02d%06d' % (
            dt.year, dt.month, dt.day, dt.hour,
            dt.minute, dt.second, dt.microsecond
        )
    else:
        return u'%04d%02d%02d%02d%02d%02d' % (
            dt.year, dt.month, dt.day, dt.hour,
            dt.minute, dt.second
        )


def simplify(text):
    """Remove markup of a text"""
    from inyoka.wiki.parser import parse
    return parse(text).text


class EmptySearchResult(object):
    """This class more or less is a dummy to define an emtpy result set"""

    def __init__(self, mset=None, enq=None, query=None, user_query=None,
                 page=1, per_page=25, adapters=None, success=False):
        self.page, self.page_count, self.per_page = (page, 1, per_page)
        self.results = []
        self.terms = []
        self.success = success

    @property
    def highlight_string(self):
        return ' '.join(term for term in self.terms)


class SearchResult(EmptySearchResult):
    """
    This class holds all search results.
    """

    def __init__(self, mset, enq, query, user_query, page, per_page,
                 adapters=None, success=True):
        self.page = page
        self.page_count = get_human_readable_estimate(mset) / per_page + 1
        self.per_page = per_page
        self.success = success
        self.terms = [term for term in query if not term[0] == 'C']
        self.user_query = user_query

        results = OrderedDict()
        for match in mset:
            adapter, id = match.document.get_value(0).split(':')
            results[(adapter, int(id))] = match

        for adapter, instance in adapters.iteritems():
            to_load = [id[1] for id in results if id[0] == adapter]
            if not to_load:
                continue
            values = instance.recv_multi(to_load)
            if values is None:
                continue

            mapping = zip((res for res in results if res[0] == adapter), values)

            for mq, data in mapping:
                match = results[mq]
                if data is None:
                    continue
                try:
                    text = data.pop('text')
                except KeyError:
                    text = None
                if text:
                    data['excerpt'] = create_excerpt(text, user_query)
                data['title'] = data['title']
                data['score'] = match.percent
                results[mq] = data
        self.results = results.values()

    @property
    def highlight_string(self):
        return self.user_query


class SearchSystem(object):
    """
    The central object that is used by applications to register their
    search interfaces.
    """

    def __init__(self):
        if search is not None:
            raise TypeError('cannot create %r instances, use the search '
                            "object instead" % self.__class__.__name__)
        self.connections = WeakKeyDictionary()
        self.prefix_handlers = {}
        self.auth_deciders = {}
        self.adapters = {}
        self._connection = None

    def index(self, component, docid, connection=None):
        """Update the search index for an docid

        :param component: A string determining the relationship, e.g forum, wiki.
        :param docid: A document id.
        :param connection: Optional connection object to allow passing
                           open connections around.
        """
        try:
            adapter = self.adapters[component]
            adapter.store_object(adapter.get_objects([docid])[0], connection)
            self.adapters[component].store(docid, connection)
        except (ObjectDoesNotExist, AttributeError):
            self.delete(component, docid, connection)

    def index_objects(self, component, objects, connection=None):
        """Update the search index for many documents."""
        adapter = self.adapters[component]
        for object in objects:
            try:
                adapter.store_object(object, connection)
            except (ObjectDoesNotExist, AttributeError):
                self.delete(component, object.id, connection)

    def delete(self, component, docid, connection=None):
        connection = connection or self.get_connection(True)
        full_id = (component.lower(), docid)
        connection.delete_document('Q%s:%d' % full_id)

    def flush(self):
        if self._connection:
            self._connection.flush()

    def queue(self, component, docid):
        from inyoka.portal.models import SearchQueue
        SearchQueue.objects.append(component, docid)

    def get_connection(self, writeable=False):
        """Get a new connection to the database."""
        if writeable:
            if not self._connection:
                if _tcpsrv_re.match(settings.XAPIAN_DATABASE):
                    host, port = _tcpsrv_re.match(settings.XAPIAN_DATABASE).groups()
                    self._connection = xapian.remote_open_writable(host, int(port))
                else:
                    self._connection = xapian.WritableDatabase(
                        settings.XAPIAN_DATABASE, xapian.DB_CREATE_OR_OPEN)
            return self._connection
        thread = get_current_thread()
        if thread not in self.connections:
            if _tcpsrv_re.match(settings.XAPIAN_DATABASE):
                host, port = _tcpsrv_re.match(settings.XAPIAN_DATABASE).groups()
                self.connections[thread] = connection = \
                    xapian.remote_open(host, int(port))
            else:
                self.connections[thread] = connection = \
                    xapian.Database(settings.XAPIAN_DATABASE)
            return self.connections[thread]
        else:
            connection = self.connections[thread]

        _connection_attemts = 0
        while _connection_attemts <= 3:
            try:
                connection.reopen()
            except xapian.DatabaseOpeningError:
                time.sleep(0.1)
                connection.reopen()
                _connection_attemts += 1
            else:
                break

        return connection

    def register(self, adapter):
        """
        Register a search adapter for indexing and retrieving.
        """
        if not adapter.type_id:
            raise ValueError('You must specify a type_id fot the adapter')
        self.adapters[adapter.type_id] = adapter
        if adapter.auth_decider:
            self.auth_deciders[adapter.type_id] = adapter.auth_decider

    def register_prefix_handler(self, prefixes, handler):
        """
        Register a prefix handler which can be used to search for
        specific terms in the database.  Instead of a simple prefix->value
        map, we use own handlers which can do additional transformations
        and database lookups, but they must all return a xapian.Query
        object (or None in case of failure).
        """
        for prefix in prefixes:
            self.prefix_handlers[prefix] = handler

    def parse_query(self, query):
        """Parse a query."""
        query = re.sub(r'\b(UND\s+)NICHT\b', 'AND NOT', query)
        query = re.sub(r'\bUND\b', 'AND', query)
        query = re.sub(r'\bODER\b', 'OR', query)

        def handle_custom_prefix(match):
            prefix = match.group(1)
            data = match.group(2).strip()
            if prefix in (u'user', u'author'):
                from inyoka.portal.user import User
                try:
                    user = User.objects.get(data)
                except User.DoesNotExist:
                    pass
                else:
                    return u'user_id:%s' % user.id
            elif prefix in (u'area', u'bereich'):
                map = {
                    'forum': 'f',
                    'wiki': 'w',
                    'ikhaya': 'i',
                    'planet': 'p',
                }
                return u'component_id:%s' % map.get(data.lower())
            elif prefix in (u'solved', u'gelöst'):
                try:
                    return u'solved_id:%s' % int(data)
                except ValueError:
                    return u'solved_id:%s' % (1 if data.lower() == "true" else 0)
            return '%s:"%s"' % (prefix, data)

        query = re.sub(ur'(?u)\b([\w_]+):"([^"]+)\b"', handle_custom_prefix, query)
        query = re.sub(ur'(?u)\b([\w_]+):([\w.]+)\b', handle_custom_prefix, query)

        qp = xapian.QueryParser()
        qp.set_default_op(xapian.Query.OP_AND)
        qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
        qp.set_stemmer(get_stemmer())

        qp.add_prefix('user_id', 'U')
        qp.add_prefix('component_id', 'P')
        qp.add_boolean_prefix('solved_id', 'S')
        qp.add_prefix('title', 'T')
        qp.add_prefix('titel', 'T')
        qp.add_prefix('version', 'V')
        qp.add_boolean_prefix('category', 'C')
        qp.add_boolean_prefix('kategorie', 'C')

        flags = xapian.QueryParser.FLAG_PHRASE \
              | xapian.QueryParser.FLAG_BOOLEAN \
              | xapian.QueryParser.FLAG_LOVEHATE \
              | xapian.QueryParser.FLAG_WILDCARD \
              | xapian.QueryParser.FLAG_PURE_NOT

        return qp.parse_query(query, flags)

    def query(self, user, query, page=1, per_page=20, date_begin=None,
              date_end=None, collapse=True, component=None, exclude=[],
              sort='date'):
        """Search for something."""
        #: Save for later highlighting
        original_query = query

        auth = AuthMatchDecider(user, self.auth_deciders)
        try:
            qry = self.parse_query(query)
        except xapian.QueryParserError:
            return EmptySearchResult(success=False)

        offset = (page - 1) * per_page

        if component:
            qry = xapian.Query(xapian.Query.OP_FILTER, qry,
                               xapian.Query('P%s' % component.lower()))
        if exclude:
            qry = xapian.Query(xapian.Query.OP_AND_NOT, qry,
                               xapian.Query(xapian.Query.OP_OR, exclude))
        if date_begin or date_end:
            d1 = date_begin or 0
            d2 = date_end or datetime.utcnow()
            range = xapian.Query(xapian.Query.OP_VALUE_RANGE, 2,
                                 _marshal_value(d1),
                                 _marshal_value(d2))
            qry = xapian.Query(xapian.Query.OP_FILTER, qry, range)

        connection = self.get_connection()

        _connection_attemts = 0

        # Try to reopen the database if the revision has been discarded
        # or otherwise modified.
        while _connection_attemts <= 3:
            try:
                enq = xapian.Enquire(self.get_connection())
                if sort == 'magic':
                    enq.set_sort_by_value_then_relevance(2, True)
                elif sort == 'date':
                    enq.set_sort_by_value(2, True)
                    enq.set_weighting_scheme(xapian.BoolWeight())
                else:
                    enq.set_sort_by_relevance()
                if collapse:
                    enq.set_collapse_key(1)
                enq.set_docid_order(xapian.Enquire.DESCENDING)
                enq.set_query(qry)

                mset = enq.get_mset(offset, per_page, per_page, None, auth)
                return SearchResult(mset, enq, qry, original_query, page, per_page,
                                    self.adapters, success=True)
            except (xapian.DatabaseModifiedError, xapian.DatabaseError):
                time.sleep(0.1)
                connection.reopen()
                _connection_attemts += 1

    def do_spelling_suggestion(self, query):
        """Return a single spelling suggestion based on `query`."""
        term_set = set()
        for term in query:
            term_set.add(self.get_connection().get_spelling_suggestion(term))

        return ' '.join(term_set)

    def store(self, connection=None, **data):
        if connection is None:
            connection = self.get_connection(True)
        doc = xapian.Document()
        tg = xapian.TermGenerator()
        tg.set_database(connection)
        tg.set_stemmer(get_stemmer())
        tg.set_flags(xapian.TermGenerator.FLAG_SPELLING)
        tg.set_document(doc)

        add_marshal_value = lambda c, v: doc.add_value(c, _marshal_value(v))
        add_marshal_term = lambda t: doc.add_term(_marshal_term(t))

        # identification (required)
        full_id = (data['component'].lower(), data['uid'])
        doc.add_term('P%s' % full_id[0])
        doc.add_term('Q%s:%d' % full_id)
        doc.add_value(0, '%s:%d' % full_id)

        # collapse key (optional)
        if data.get('collapse'):
            add_marshal_value(1, '%s:%s' % (full_id[0], data['collapse']))
            add_marshal_term('R%s:%s' % (full_id[0], data['collapse']))

        # title (optional)
        if data.get('title'):
            tg.index_text(data['title'], 5, 'T')

        # user (optional)
        if data.get('user'):
            add_marshal_term('U%d' % data['user'])

        # date (optional)
        if data.get('date'):
            add_marshal_value(2, data['date'])

        # authentification informations (optional)
        if data.get('auth'):
            # Do not marshal dumped data
            doc.add_value(3, dumps(data['auth']))

        # category (optional)
        if data.get('category'):
            categories = data.get('category')
            if isinstance(categories, (str, unicode)):
                categories = [categories]
            for category in categories:
                doc.add_term('C%s' % category.lower())

        # text (optional, can contain multiple items)
        if data.get('text'):
            text = data['text']
            if isinstance(text, (str, unicode)):
                text = [text]
            for block in text:
                tg.index_text(block, 1)

        # Solved (optional)
        if data.get('solved'):
            doc.add_term('S%d' % int(data['solved']), 1)

        # Ubuntu-Version (optional)
        if data.get('version'):
            text = data['version'].replace('(', '').replace(')', '').lower()
            for token in text.split():
                doc.add_term('V%s' % token, 1)

        # Add a gap between each field instance, so that phrase searches don't
        # match across instances.
        tg.increase_termpos(10)

        connection.replace_document('Q%s:%d' % full_id, doc)


# setup the singleton instance
search = None
search = SearchSystem()


def search_handler(*prefixes):
    """A decorator which registers the search handler."""
    def decorate(f):
        search.register_prefix_handler(prefixes, f)
        return f
    return decorate


class AuthMatchDecider(xapian.MatchDecider):

    def __init__(self, user, deciders):
        xapian.MatchDecider.__init__(self)
        self.deciders = {key: dec(user) for key, dec in deciders.iteritems()}

    def __call__(self, doc):
        component = doc.get_value(0).split(':')[0]
        auth = doc.get_value(3)
        decider = self.deciders.get(component)
        if auth and decider is not None:
            return decider(loads(auth))
        else:
            pass
        return True


class SearchAdapter(object):
    type_id = None
    auth_decider = None
    support_multi = False

    @classmethod
    def queue(self, docid):
        from inyoka.portal.models import SearchQueue
        SearchQueue.objects.append(self.type_id, docid)

    def store(self, docid, connection=None):
        raise NotImplementedError('store')

    def store_object(self, object, connection=None):
        raise NotImplementedError('store_object')

    def store_multi(self, docids):
        raise NotImplementedError('store_multi')

    def recv(self, docid):
        raise NotImplementedError('recv')

    def recv_multi(self, docids):
        raise NotImplementedError('recv_multi')

    def get_doc_ids(self):
        raise NotImplementedError('get_doc_ids')


# circ import
from inyoka.utils.highlight import create_excerpt
