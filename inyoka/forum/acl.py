# -*- coding: utf-8 -*-
"""
    inyoka.forum.acl
    ~~~~~~~~~~~~~~~~

    Authentification systen for the forum.

    :copyright: (c) 2007-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import operator as ops

from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.core.cache import cache
from django.utils.translation import ugettext_lazy

from inyoka.portal.user import DEFAULT_GROUP_ID

#: Mapping from privilege strings to human readable descriptions
PRIVILEGES_DETAILS = [
    ('read', ugettext_lazy(u'can read')),
    ('vote', ugettext_lazy(u'can vote')),
    ('create', ugettext_lazy(u'can create topics')),
    ('reply', ugettext_lazy(u'can reply')),
    ('upload', ugettext_lazy(u'can upload attachments')),
    ('create_poll', ugettext_lazy(u'can create polls')),
    ('sticky', ugettext_lazy(u'can make sticky')),
    ('moderate', ugettext_lazy(u'can moderate'))
]

#: List of available privilege strings
PRIVILEGES = [x[0] for x in PRIVILEGES_DETAILS]

#: Mapping from privilege strings to bit representations
PRIVILEGES_BITS = {PRIVILEGES[i - 1]: 2 ** i
                   for i in xrange(1, len(PRIVILEGES_DETAILS) + 1)}
#: Similar to :data:`PRIVILEGES_BITS` except a mapping from the bits to the strings
REVERSED_PRIVILEGES_BITS = {y: x for x, y in PRIVILEGES_BITS.iteritems()}

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


def join_bits(result, forum_ids, rows):
    """
    Join the positive bits of all forums and subtract the negative ones of
    them.
    """
    negative_set = {forum_id: set() for forum_id in forum_ids}
    for forum_id, _, __, positive, negative in rows:
        result[forum_id] |= positive
        negative_set[forum_id].add(negative)
    for forum_id, bits in negative_set.iteritems():
        for bit in bits:
            if result[forum_id] & bit:
                result[forum_id] -= bit
    return result


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


def get_forum_privileges(user, forum):
    """Get a dict of all the privileges for a user."""
    return get_privileges(user, forums=[forum])[forum.id]


def _get_privilege_map(user, forum_ids):
    # circular imports
    from inyoka.forum.models import Privilege, Forum
    group_ids = set(user.groups.values_list('id', flat=True))
    if user.is_authenticated():
        group_ids.add(DEFAULT_GROUP_ID)

    cols = ('forum_id', 'user_id', 'group_id', 'positive', 'negative')

    filter = Q(user_id=user.id)

    if len(group_ids) == 1:
        filter |= Q(group_id=list(group_ids)[0])
    else:
        filter |= Q(group_id__in=group_ids)

    query = Privilege.objects.filter(filter)

    if user.is_anonymous:
        # If we have an anonymous user we can cache the results. We MUST that
        # for all forums, this makes it possible to cache the privileges. Once
        # we get an authenticated user we filter for the ids requested.
        cache_key = 'forum/acls/anonymous'
        privilege_map = cache.get(cache_key)
        if privilege_map is None:
            privilege_map = query.values_list(*cols)
            cache.set(cache_key, list(privilege_map), 86400)
        # filter the privilege_map for ids not requested (api compatibility)
        # XXX: We might consider do use get_many and store the privileges
        #      per forum id: 'forum/acls/anonymous/<forum_id>'
        privilege_map = [row for row in privilege_map if row[0] in forum_ids]
    else:
        # we filter for the privilege ids if we don't have an anonymous user
        all_ids = Forum.objects.get_ids()
        # Do only filter IN if required.  This is not required most of the time
        # so that this saves a bit bandwith and quite a few time for the query
        if len(forum_ids) != len(all_ids):
            if len(forum_ids) == 1:
                query = query.filter(forum_id=forum_ids[0])
            else:
                query = query.filter(forum_id__in=forum_ids)
        privilege_map = query.values_list(*cols)

    return privilege_map


def get_privileges(user, forums):
    """Return all privileges of the applied forums for the `user`"""
    if not forums:
        return {}

    if isinstance(forums, (tuple, list)):
        forum_ids = [forum.id for forum in forums]
    elif forums == EmptyQuerySet:
	forum_ids = []
    else:
        forum_ids = forums.values_list('id', flat=True)
    privilege_map = _get_privilege_map(user, forum_ids)

    result = {forum_id: DISALLOW_ALL for forum_id in forum_ids}
    # `row[1]` maps to `user_id` in the `cols` as defined in the
    # `_get_privilege_map()` function
    # first join the group privileges
    result = join_bits(result, forum_ids, [row for row in privilege_map if not row[1]])
    # now join the user privileges (this allows to override group privileges)
    result = join_bits(result, forum_ids, [row for row in privilege_map if row[1]])
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
