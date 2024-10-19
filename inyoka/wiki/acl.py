"""
    inyoka.wiki.acl
    ~~~~~~~~~~~~~~~

    This module handles security levels for the wiki.  The system uses the
    wiki storage to store the patterns.  Whenever the data is loaded from the
    wiki pages that hold access control information the `storage` module
    splits the data already into easy processable data.

    This is an important detail because the ACL module knows nothing about the
    names of the privileges on the frontend.  Internally the names of the
    privileges are mapped to integer flags.

    All privilege functions consume either the privilege flags or the internal
    short name of the privilege.  The shortnames are specified in the
    `privilege_map` dict and different from the user interface which uses
    translated versions of the variables.

    Because metadata is part of a page the views have to check if the metadata
    changed in a way the user is not allowed to change it.  This module
    provides a function called `test_changes_allowed` that checks for that.


    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect

from inyoka.portal.user import User
from inyoka.utils.decorators import patch_wrapper
from inyoka.utils.text import normalize_pagename
from inyoka.utils.urls import href
from inyoka.wiki.models import Page
from inyoka.wiki.storage import storage

#: metadata users without the `PRIV_MANAGE` privilege can edit.
LENIENT_METADATA_KEYS = frozenset(('X-Link', 'X-Attach', 'X-Redirect'))


#: the internal privilege representations. because we try to keep
#: the interface as fast as possible the privilegs are bit fields and
#: not python sets.
PRIV_READ = 1
PRIV_EDIT = 2
PRIV_CREATE = 4
PRIV_ATTACH = 8
PRIV_DELETE = 16
PRIV_MANAGE = 32

#: keep this updated when adding privileges
PRIV_NONE = 0
PRIV_DEFAULT = PRIV_ALL = 63

#: because we use different names in the german frontend these
#: constants hold the name used in the frontend.  i call bullshit,
#: we use english names again and the constants are left as an
#: exercise for the reader.
GROUP_OWNER = 'owner'

#: used by the decorator
privilege_map = {
    'read': PRIV_READ,
    'edit': PRIV_EDIT,
    'create': PRIV_CREATE,
    'attach': PRIV_ATTACH,
    'delete': PRIV_DELETE,
    'manage': PRIV_MANAGE
}


class PrivilegeTest:
    """
    An instance of this class is passed to all the action templates.  Attribute
    access can then be used to check if the current user has a privilege the
    current page.
    """

    jinja_allowed_attributes = list(privilege_map.keys())

    def __init__(self, user, page_name):
        self._user = user
        self._page_name = page_name
        self._privilege_cache = None

    def __getattr__(self, name):
        if self._privilege_cache is None:
            self._privilege_cache = get_privileges(self._user, self._page_name)
        return self._privilege_cache.get(name, False)


class GroupContainer:
    """
    This class fetches the groups for an user in a lazy way.  This is used by
    the `get_privilege_flags` to not load groups if they are not used for a
    specific query.

    Use it with the in-Operator::

        >>> user = User.objects.get_anonymous_user()
        >>> groups = GroupContainer(user, 'Main_Page')
        >>> 'All' in groups
        False
        >>> 'something' in groups
        False
    """

    def __init__(self, user, page_name):
        self.user = user
        self.page = page_name
        self.cache = None

    def load(self):
        """Load the data from the database."""
        self.cache = set(self.user.groups.values_list('name', flat=True))
        for item in Page.objects.get_owners(self.page):
            if item == self.user.username or \
               (item.startswith('@') and item[1:] in self.cache):
                self.cache.add(GROUP_OWNER)
                break

    def __contains__(self, obj):
        if self.cache is None:
            self.load()
        return obj in self.cache


class MultiPrivilegeTest:
    """
    Efficient way for multiple privilege tests for one users to many pages.
    """

    def __init__(self, user):
        self.user = user
        self.groups = set(self.user.groups.values_list('name', flat=True))
        self.owned_pages = set(Page.objects.get_owned(self.groups))

    def get_groups(self, page_name):
        if page_name in self.owned_pages:
            return self.groups & {GROUP_OWNER}
        return self.groups

    def get_privilege_flags(self, page_name):
        groups = self.get_groups(page_name)
        return get_privilege_flags(self.user, page_name, groups)

    def get_privileges(self, page_name):
        groups = self.get_groups(page_name)
        return get_privileges(self.user, page_name, groups)

    def has_privilege(self, page_name, privilege):
        groups = self.get_groups(page_name)
        return has_privilege(self.user, page_name, privilege, groups)


def get_privilege_flags(user, page_name, groups=None):
    """
    Return an integer with the privilege flags for a user for the given
    page name.  Like any other page name depending function the page name
    must be in a normalized state.

    :param groups: used internally by the `MultiPrivilegeTest`
    """
    if user is None:
        user = User.objects.get_anonymous_user()
    elif isinstance(user, str):
        user = User.objects.get(username__iexact=user)
    if groups is None:
        groups = GroupContainer(user, page_name)

    page_name = normalize_pagename(page_name)

    rules = storage.acl
    if not rules:
        return PRIV_DEFAULT
    privileges = PRIV_NONE
    for pattern, subject, add_privs, del_privs in rules:
        if (subject == user.username or
            (subject.startswith('@') and subject[1:] in groups)) and \
                pattern.match(page_name) is not None:
            privileges = (privileges | add_privs) & ~del_privs
    return privileges


def get_privileges(user, page_name, groups=None):
    """
    Get a dict with the privileges a user has for a page (or doesn't).  `user`
    must be a user object or `None` in which case the privileges for an
    anonymous user are returned.

    :param groups: used internally by the `MultiPrivilegeTest`
    """
    result = {}
    flags = get_privilege_flags(user, page_name, groups)
    for name, flag in privilege_map.items():
        result[name] = (flags & flag) != 0
    return result


def has_privilege(user, page_name, privilege, groups=None):
    """
    Check if a user has a special privilege on a page.  If you want to check
    for multiple privileges (for example if you want to display what a user
    can do or not do) you should use `get_privileges` which is faster for
    multiple checks and also returns it automatically as a dict.

    :param groups: used internally by the `MultiPrivilegeTest`
    """
    if isinstance(privilege, str):
        privilege = privilege_map[privilege]
    return (get_privilege_flags(user, page_name, groups) & privilege) != 0


def require_privilege(privilege):
    """
    Helper action decorator that checks if the currently logged in
    user does have the privilege required to perform that action.
    """
    def decorate(f):
        def oncall(request, name, *args, **kwargs):
            if has_privilege(request.user, name, privilege):
                return f(request, name, *args, **kwargs)
            if not request.user.is_authenticated:
                url = href('portal', 'login', next='//%s%s' % (
                    request.get_host(),
                    request.path
                ))
                return HttpResponseRedirect(url)
            raise PermissionDenied
        return patch_wrapper(oncall, f)
    return decorate


def test_changes_allowed(user, page_name, old_text, new_text):
    """
    This method returns `True` if the user is allowed to change the text of
    a page from `old_text` to `new_text`.  At the moment this just checks for
    changed metadata, in the future however it makes sense to also check for
    banned words here.
    """
    if has_privilege(user, page_name, PRIV_MANAGE):
        return True
    from inyoka.markup.base import parse
    from inyoka.markup.nodes import MetaData

    old = set()
    new = set()
    for tree, metadata in (old_text, old), (new_text, new):
        if isinstance(tree, str):
            tree = parse(tree)
        for node in tree.query.by_type(MetaData):
            if node.key.startswith('X-') and \
               node.key not in LENIENT_METADATA_KEYS:
                for value in node.values:
                    metadata.add((node.key, value))
    return old == new
