# -*- coding: utf-8 -*-
"""
    inyoka.utils.database
    ~~~~~~~~~~~~~~~~~~~~~

    This module provides some helpers to work with the database.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from django.core.cache import cache

from inyoka.utils.text import get_next_increment


def _strip_ending_nums(string):
    if '-' in string and string.rsplit('-', 1)[-1].isdigit():
        return string.rsplit('-', 1)[0]
    return string


def find_next_increment(model, column, string, stripdate=False, **query_opts):
    """Get the next incremented string based on `column` and string`.
    This function is the port of `find_next_increment` for Django models.

    Example::

        find_next_increment(Article, 'slug', 'article name')
    """
    field = model._meta.get_field_by_name(column)
    max_length = field.max_length if hasattr(field, 'max_length') else None
    string = _strip_ending_nums(string)
    slug = string[:max_length - 4] if max_length is not None else string
    slug_taken = model.objects.filter(**{column: slug}).filter(**query_opts).exists()
    if not slug_taken:
        return slug
    filter = {'%s__startswith' % column: slug + '-'}
    filter.update(query_opts)
    existing =  list(model.objects.filter(**filter).values_list(column, flat=True))
    return get_next_increment([slug] + existing, slug, max_length,
                              stripdate=stripdate)


def get_simplified_queryset(queryset):
    """Returns a QuerySet with following modifications:

     * without Aggregators
     * unused select fields
     * .only('id')
     * no order_by

    The resultung QuerySet cann be used for efficient .count() queries.
    """
    cqry = queryset._clone().only('id')
    cqry.query.clear_select_fields()
    cqry.query.clear_ordering(True)
    cqry.query.clear_limits()
    cqry.query.select_for_update = False
    cqry.query.select_related = False
    cqry.query.related_select_cols = []
    cqry.query.related_select_fields = []
    return cqry


class LockableObject(object):

    #: Must be defined by an inherited model.
    lock_key_base = None

    def _get_lock_key(self):
        return u'/'.join((self.lock_key_base.strip('/'), unicode(self.id)))

    def lock(self, request):
        """Lock for 15 Minutes"""
        existing = cache.get(self._get_lock_key())
        if existing is None and self.id:
            cache.set(self._get_lock_key(), request.user.username, 900)
        if existing is not None and existing != request.user.username:
            return existing
        return False

    def unlock(self):
        cache.delete(self._get_lock_key())
