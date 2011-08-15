# -*- coding: utf-8 -*-
"""
    inyoka.forum.acl
    ~~~~~~~~~~~~~~~~

    Authentification systen for the forum.

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import operator as ops
from django.core.cache import cache
from django.db.models import Q


PRIVILEGES_DETAILS = [
    ('read', 'kann lesen'),
    ('vote', 'kann abstimmen'),
    ('create', 'kann Themen erstellen'),
    ('reply', 'kann antworten'),
    ('upload', u'kann Anhänge erstellen'),
    ('create_poll', 'kann Umfragen erstellen'),
    ('sticky', 'kann Themen anpinnen'),
    ('moderate', 'kann moderieren')
]

PRIVILEGES = [x[0] for x in PRIVILEGES_DETAILS]
PRIVILEGES_BITS = dict((PRIVILEGES[i-1], 2**i)
                       for i in xrange(1, len(PRIVILEGES_DETAILS) + 1))
REVERSED_PRIVILEGES_BITS = dict((y,x) for x,y in PRIVILEGES_BITS.iteritems())

#: create some constants for easy access
g = globals()
for desc, bits in PRIVILEGES_BITS.iteritems():
    g['CAN_%s' % desc.upper()] = bits
DISALLOW_ALL = 0

del desc, bits


def join_flags(*flags):
    """
    Small helper function for the admin-panel
    to join some flags to one bit-mask.
    """
    if not flags:
        return DISALLOW_ALL
    result = DISALLOW_ALL
    for flag in flags:
        if isinstance(flag, basestring):
            flag = PRIVILEGES_BITS[flag]
        if flag == 0:
            return 0
        result |= flag
    return result


def split_bits(mask=None):
    """
    Return an iterator with all bits splitted
    from the `mask`.
    """
    if mask is None:
        return
    for desc, bits in PRIVILEGES_BITS.iteritems():
        if mask & bits != 0:
            yield bits


def get_forum_privileges(user, forum):
    """Get a dict of all the privileges for a user."""
    return get_privileges(user, forums=[forum])[forum.id]


def _get_privilege_map(user, forum_ids):
    from inyoka.forum.models import Privilege, Forum
    group_ids = user.groups.values_list('id', flat=True)

    cols = ('forum__id', 'user__id', 'group__id', 'positive', 'negative')

    # construct the query, but do not execute it yet for caching reasons
    filter = (Q(user__id = user.id) |
              Q(group__id = (-1 if user.is_anonymous else DEFAULT_GROUP_ID)))

    # Small performance optimization that actually matters
    if len(group_ids) > 1:
        filter |= Q(group__id__in=group_ids)
    elif group_ids:
        filter |= Q(group__id=group_ids[0])

    query = Privilege.objects.filter(filter)

    # If we have an anonymous user we can cache the results
    # We do that for all forums, this makes it possible to cache the privileges.
    # Once we get an authenticated user we filter for the ids requested.
    cache_key = 'forum/acls/anonymous'
    if user.is_anonymous:
        privilege_map = cache.get(cache_key)
        if privilege_map is None:
            privilege_map = query.values_list(*cols)
            cache.set(cache_key, list(privilege_map), 86400)
        # filter the privilege_map for ids not requested (api compatibility)
        privilege_map = [row for row in privilege_map if row[0] in forum_ids]
    else:
        # we filter for the privilege ids if we don't have an anonymous user
        all_ids = Forum.objects.get_ids()
        # Do only filter IN if required.  This is not required most of the time
        # so that this saves a bit bandwith and quite a few time for the query
        if len(forum_ids) != len(all_ids):
            if len(forum_ids) > 1:
                query = query.filter(forum__id__in=forum_ids)
            elif forum_ids:
                query = query.filter(forum__id=forum_ids[0])
        privilege_map = query.values_list(*cols)

    return privilege_map


def get_privileges(user, forums):
    """Return all privileges of the applied forums for the `user`"""
    if not forums:
        return {}

    if isinstance(forums, (tuple, list)):
        forum_ids = [forum.id for forum in forums]
    else:
        forum_ids = forums.values_list('id', flat=True)
    privilege_map = _get_privilege_map(user, forum_ids)

    def join_bits(result, rows):
        """
        Join the positive bits of all forums and subtract the negative ones of
        them.
        """
        negative_set = dict(map(lambda a: (a, set()), forum_ids))
        for forum_id, _, __, positive, negative in rows:
            result[forum_id] |= positive
            negative_set[forum_id].add(negative)
        for forum_id, bits in negative_set.iteritems():
            for bit in bits:
                if result[forum_id] & bit:
                    result[forum_id] -= bit
        return result

    result = dict(map(lambda a: (a, DISALLOW_ALL), forum_ids))
    # first join the group privileges
    result = join_bits(result, [row for row in privilege_map if not row[1]])
    # now join the user privileges (this allows to override group privileges)
    result = join_bits(result, [row for row in privilege_map if row[1]])
    return result


def have_privilege(user, obj, privilege):
    """Check if a user has a privilege on a forum or a topic."""
    if isinstance(privilege, basestring):
        privilege = PRIVILEGES_BITS[privilege]
    if hasattr(obj, 'forum'):
        # obj is a topic
        forum = obj.forum
    else:
        # obj is a forum
        forum = obj
    return get_forum_privileges(user, forum) & privilege != 0


def check_privilege(mask, privilege):
    """
    Check for an privilege on an existing mask.
    Note: This does not touch the database so use
    this as much as possible instead of many
    `have_privilege` statements.

    `mask`
        The Bit-mask representing all forum-privileges
    `privilege`
        A string or Bit-mask representing one privilege
    """
    if isinstance(privilege, basestring):
        privilege = PRIVILEGES_BITS[privilege]
    return mask & privilege != 0


def filter(user, forums=None, priv=CAN_READ, privileges=None, operator=ops.eq):
    """Filter all forums where the user has a privilege on it."""
    forums = forums or []
    privileges = privileges or get_privileges(user, forums)
    result = []
    for forum in forums:
        if operator(privileges.get(forum.id, DISALLOW_ALL) & priv, 0):
            result.append(forum)
    return result


#: Shortcut to filter all visible forums
filter_visible = lambda u, f=None, priv=CAN_READ, perm=None: filter(u, f, priv, perm, ops.eq)

#: Shortcut to filter all invisible forums
filter_invisible = lambda u, f=None, priv=CAN_READ, perm=None: filter(u, f, priv, perm, ops.ne)


def split_negative_positive(value):
    """Split a string into negative and positive permissions.

    :return: A tuple of joined (negative, positive) permissions.
    """
    positive, negative = 0, 0
    for bit in value.split(','):
        try:
            bit = int(bit)
        except ValueError:
            continue
        if bit > 0:
            positive |= abs(bit)
        else:
            negative |= abs(bit)
    return negative, positive

# circular imports
from inyoka.portal.user import DEFAULT_GROUP_ID
