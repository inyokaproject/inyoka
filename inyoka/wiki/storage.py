# -*- coding: utf-8 -*-
"""
    inyoka.wiki.storage
    ~~~~~~~~~~~~~~~~~~~

    Beside the metadata the wiki has a storage concept which is a bit simpler
    in terms of implementation.  Basically a wiki storage is a preformatted
    block in a special wiki page that is know at compile time.  That block is
    then processed by a storage class and converted into a list of tuples or
    a dict, or something different, depending what the class wants to have.

    This is used for similies, interwiki links, access control and much more.
    If a page is a storage container is determined by the special 'X-Behave'
    metadata header.  There can be multiple pages with the same behave header,
    the contents of those pages are combined afterwards.

    The following behave headers are known so far:

    ``X-Behave: Smiley-Map``
        this page must contain a pre block that binds smiley codes to their
        image location.  If the link is relative it's assumed to be a link to
        an attachment, otherwise a full url.

    ``X-Behave: Interwiki-Map``
        Binds shortnames to wiki URLs.

    ``X-Behave: Access-Control-List``
        This storage contains ACL information

    Storage objects are read only because they combine the information from
    multiple pages.

    It's important to know that the storage system does not use the normal
    parser but a lightweight version of it that just looks for the pre tag.
    This is not only faster but also ensures that we don't get bootstrapping
    problems.


    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from urlparse import urljoin
from collections import OrderedDict

from django.conf import settings

from inyoka.utils.cache import request_cache
from inyoka.utils.text import normalize_pagename
from inyoka.utils.user import normalize_username
from inyoka.wiki.models import Page, MetaData


_block_re = re.compile(r'\{\{\{(?:\n?#.*?$)?(.*?)\}\}\}(?sm)')


class StorageManager(object):
    """
    Manager multiple storages.
    """

    def __init__(self, **storages):
        self.storages = storages

    def __getattr__(self, key):
        if key in self.storages:
            return self.storages[key]().data
        raise AttributeError(key)

    def clear_cache(self):
        """Clear all active caches."""
        for obj in self.storages.itervalues():
            request_cache.delete('wiki/storage/' + obj.behavior_key)


class BaseStorage(object):
    """
    Abstract base class for all the storage objects that contains the shared
    logic like flushing the cache and storing back to it.
    """

    #: the name of the behavior key this storage looks for. If it's `None`
    #: this storage is abstract and useful as baseclass for concrete storages.
    behavior_key = None

    def __init__(self):
        key = 'wiki/storage/' + self.behavior_key
        self.data = request_cache.get(key)
        if self.data is not None:
            return

        data = MetaData.objects.values_list('page__last_rev__text__value',
                                            'page__name') \
            .filter(key='X-Behave',
                    page__last_rev__deleted=False,
                    value=self.behavior_key) \
            .order_by('page__name').all()

        objects = []
        for raw_text, page_name in data:
            block = self.find_block(raw_text)
            objects.append(self.extract_data(block))

        self.data = self.combine_data(objects)
        request_cache.set(key, self.data, 10000)

    def find_block(self, text):
        """Helper method that finds a processable block in the text."""
        m = _block_re.search(text)
        if m:
            return m.group(1).strip('\r\n')
        return u''

    def extract_data(self, text):
        """
        This is passed the text of the first preformatted node on a page where
        the behavior header matched.  The returned object is probably post-
        processed by `combine_data` to comine multiple results.
        """

    def combine_data(self, objects):
        """Combine multiple results."""
        return objects


class DictStorage(BaseStorage):
    """
    Helper for storing dicts.
    """

    _line_re = re.compile(r'(?<!!)=')
    multi_key = False

    def extract_data(self, text):
        for line in text.splitlines():
            if self.multi_key:
                bits = self._line_re.split(line)
                if len(bits) > 1:
                    for key in bits[:-1]:
                        yield key.strip(), bits[-1].strip()
            else:
                bits = self._line_re.split(line, 1)
                if len(bits) == 2:
                    yield bits[0].strip(), bits[1].strip()

    def combine_data(self, objects):
        result = {}
        for obj in objects:
            for key, value in obj:
                result[key] = value
        return result


class SmileyMap(DictStorage):
    """
    Stores smiley code to image mappings.
    """
    behavior_key = 'Smiley-Map'
    multi_key = True

    def combine_data(self, objects):
        mapping = OrderedDict()
        for obj in objects:
            for code, page in obj:
                mapping.setdefault(page, []).append(code)
        if not mapping:
            return []

        data = Page.objects.values_list('last_rev__attachment__file', 'name') \
            .filter(name__in=mapping.keys(),
                    last_rev__deleted=False).all()

        result = []
        for filename, page in data:
            path = urljoin(settings.MEDIA_URL, filename)
            for code in mapping[page]:
                result.append((code, path))
        return result


class InterwikiMap(DictStorage):
    """
    Map shortnames to full interwiki links.
    """
    behavior_key = 'Interwiki-Map'


class AccessControlList(BaseStorage):
    """
    This storage holds the access control lists for the whole wiki.  The rules
    are similar to the basic expansion rules we also use for the `PageList`
    macro but they are always case sensitive.
    """
    behavior_key = 'Access-Control-List'

    def extract_data(self, text):
        from inyoka.wiki import acl
        privileges = acl.privilege_map

        pages = [u'*']
        for line in text.splitlines():
            # comments and empty lines
            line = line.split('#', 1)[0].strip()
            if not line:
                continue

            # group sections
            if line[0] == '[' and line[-1] == ']':
                pages = [normalize_pagename(x.strip())
                         for x in line[1:-1].split(',')]
                continue

            bits = line.split('=', 1)
            if len(bits) != 2:
                continue

            subjects = [normalize_username(s.strip())
                        for s in bits[0].split(',')]

            add_privs = del_privs = 0
            for s in bits[1].split(','):
                s = s.strip().lower()
                if s in ('all', '-none'):
                    add_privs = acl.PRIV_ALL
                elif s in ('-all', 'none'):
                    del_privs = acl.PRIV_ALL
                else:
                    if s.startswith('-'):
                        s = s[1:]
                        if s in privileges:
                            del_privs |= privileges[s]
                    else:
                        if s in privileges:
                            add_privs |= privileges[s]

            for page_name in pages:
                pattern = re.compile(r'^%s$' % re.escape(page_name).
                                     replace('\\*', '.*?'), re.I)
                for subject in subjects:
                    yield pattern, subject, add_privs, del_privs

    def combine_data(self, objects):
        rv = []
        for obj in objects:
            rv.extend(obj)
        return rv


storage = StorageManager(
    smilies=SmileyMap,
    interwiki=InterwikiMap,
    acl=AccessControlList
)
