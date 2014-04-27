# -*- coding: utf-8 -*-
"""
    inyoka.utils.storage
    ~~~~~~~~~~~~~~~~~~~~

    Dict like interface to the portal.storage model.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.db import transaction

from inyoka.utils.cache import request_cache


class CachedStorage(object):
    """
    This is a dict like interface for the `Storage` model from the portal.
    It's used to store cached values also in the database.
    """

    def get(self, key, default=None, timeout=None):
        """get *key* from the cache or if not exist return *default*"""
        from inyoka.portal.models import Storage
        value = request_cache.get('storage/' + key)
        if value is not None:
            return value
        try:
            storage_object = Storage.objects.get(key=key)
            value = storage_object.value
        except Storage.DoesNotExist:
            return default

        self._update_cache(key, value, timeout)
        return value

    @transaction.commit_on_success
    def set(self, key, value, timeout=None):
        """
        Set *key* with *value* and if needed with a
        *timeout*.
        """
        from inyoka.portal.models import Storage
        row, created = Storage.objects.get_or_create(key=key,
                defaults={'value': value})
        if not created:
            row.value = value
            row.save()
        self._update_cache(key, value, timeout)

    def get_many(self, keys, timeout=None):
        """
        Get many cached values with just one cache hit or database query.
        """
        from inyoka.portal.models import Storage
        objects = request_cache.get_many(['storage/%s' % key for key in keys])
        values = {}
        for key, value in objects.iteritems():
            values[key[8:]] = value
        #: a list of keys that aren't yet in the cache.
        #: They are queried using a database call.
        to_fetch = [k for k in keys if k not in values]
        if not to_fetch:
            return values
        # get the items that are not in cache using a database query
        query = Storage.objects.filter(key__in=to_fetch) \
                               .values_list('key', 'value')

        for key, value in query:
            values[key] = value
            self._update_cache(key, value, timeout)
        return values

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def _update_cache(self, key, value, timeout=None):
        request_cache.set('storage/%s' % key, value, timeout)


storage = CachedStorage()
