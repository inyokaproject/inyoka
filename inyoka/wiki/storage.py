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
    If a page is a storage container is defined by the settings variable
    ``WIKI_STORAGE_PAGES``.  There can be multiple pages for the same type, the
    contents of those pages are combined afterwards.

    The following keys for the mentioned dict are known so far:

    ``smilies``
        this page must contain a pre block that binds smiley codes to their
        image location.  If the link is relative it's assumed to be a link to
        an attachment, otherwise a full url.

    ``interwiki``
        Binds shortnames to wiki URLs.

    ``acl``
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
from inyoka.wiki.models import Page

_block_re = re.compile(r'\{\{\{(?:\n?#.*?$)?(.*?)\}\}\}(?sm)')


CACHE_PREFIX = 'wiki/storage/'


class StorageManager(object):
    """
    Manager multiple storages.
    """

    def __init__(self, **storages):
        self._storages = storages
        self.storages = {}

    def __getattr__(self, key):
        st = self._get_or_create(key)
        if st:
            return st.data
        raise AttributeError(key)

    def _get_or_create(self, key):
        if key in self.storages:
            return self.storages[key]
        elif key in self._storages:
            self.storages[key] = self._storages[key]()
            return self.storages[key]
        return None

    def clear_cache(self, key):
        """Clear caches for ``key``."""
        st = self._get_or_create(key)
        if st:
            st.update()


class BaseStorage(object):
    """
    Abstract base class for all the storage objects that contains the shared
    logic like flushing the cache and storing back to it.
    """

    #: the name of the storage type this storage looks for. If it's `None`
    #: this storage is abstract and useful as baseclass for concrete storages.
    storage_type = None

    def __init__(self):
        self.data = request_cache.get(CACHE_PREFIX + self.storage_type)
        if not self.data:
            self.update()

    def update(self):
        data = Page.objects.values_list('last_rev__text__value', 'name') \
            .filter(name__in=settings.WIKI_STORAGE_PAGES[self.storage_type],
                    last_rev__deleted=False) \
            .order_by('name').all()

        objects = []
        for raw_text, page_name in data:
            block = self.find_block(raw_text)
            objects.append(self.extract_data(block))

        self.data = self.combine_data(objects)
        request_cache.set(CACHE_PREFIX + self.storage_type, self.data, 10000)

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


class SetStorage(BaseStorage):
    """
    Stores a set.
    """

    def extract_data(self, text):
        for line in text.splitlines():
            line = line.strip()
            if line:
                yield line

    def combine_data(self, objects):
        result = set()
        for obj in objects:
            result.update(obj)
        return result


class SmileyMap(DictStorage):
    """
    Stores smiley code to image mappings.
    """
    storage_type = 'smilies'
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
    storage_type = 'interwiki'


class AccessControlList(BaseStorage):
    """
    This storage holds the access control lists for the whole wiki.  The rules
    are similar to the basic expansion rules we also use for the `PageList`
    macro but they are always case sensitive.
    """
    storage_type = 'acl'

    def extract_data(self, text):
        from inyoka.wiki import acl
        privileges = acl.privilege_map

        groups = ['*']
        for line in text.splitlines():
            # comments and empty lines
            line = line.strip()
            if not line or line.startswith('##'):
                continue

            # group sections
            if line[0] == '[' and line[-1] == ']':
                groups = [x.strip() for x in line[1:-1].split(',')]
                continue

            bits = line.split('=', 1)
            if len(bits) != 2:
                continue

            subjects = set(s.strip() for s in bits[0].split(','))
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

            for group in groups:
                pattern = re.compile(r'^%s$' % re.escape(group).
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
