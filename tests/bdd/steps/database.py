from behave import given, step
from django.conf import settings
from django.core.cache import cache

from tests.bdd.steps.form import do_form_fill_out
from tests.bdd.steps.navigation import navigate_to_page


@given('The user "{username}" exits')
def step_impl(context, username):
    from inyoka.portal.user import User

    User.objects.register_user(username, '%s@ubuntuusers.local' % username, 'test', False)


@given('The user "{username}" with status "{status_string}" exists')
def step_impl(context, username, status_string):
    from inyoka.portal.user import User

    user = User.objects.register_user(username, '%s@ubuntuusers.local' % username, 'test', False)

    status_type = User.STATUS_ACTIVE
    if status_string == 'banned':
        status_type = User.STATUS_BANNED
    elif status_string == 'inactive':
        status_type = User.STATUS_INACTIVE
    elif status_string == 'deleted':
        status_type = User.STATUS_DELETED

    user.status = status_type
    user.save()


@given('I have the permission "{permission}"')
def step_impl(context, permission):
    from guardian.shortcuts import assign_perm

    group = context.user.groups.get_queryset()[0]
    assign_perm(permission, group)
    cache.delete_pattern('/acl/*')


@step('a "{item}" with caption "{caption}" exists')
def step_impl(context, item, caption):
    """
    This step will create the required item for the test.
    Later steps can access this item with `context.test_item`

    :type context: behave.runner.Context
    :param item: A string with the item's type at the moment only 'paste' is supported
    :param caption: The caption/title/keyword/... part of that item.
    """
    from inyoka.portal.user import User

    default_user = User.objects.register_user("bdd", "mail", None, False)

    if item == 'paste':
        from inyoka.pastebin.models import Entry
        context.test_item = Entry.objects.create(title=caption, author=default_user, code="TEST")
        context.test_item.save(update_fields=['code'])  # Note: needed because the code field only updates on save


@given('I am "{username}"')
def step_impl(context, username):
    """
    This creates the user and does a regular login with this user.
    Except if the user is "anonymous" then only the user is created.

    After this step the user can be accessed from the context with
    `context.user`.

    :type context: behave.runner.Context
    :param username: string
    """

    from django.contrib.auth.models import Group
    from inyoka.portal.user import User

    if username == "anonymous":
        anonymous = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        context.user, created = User.objects.get_or_create(username=settings.ANONYMOUS_USER_NAME)
        context.user.groups.add(anonymous)
    else:
        registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        context.user = User.objects.register_user(username, '%s@ubuntuusers.local' % username, 'test', False)
        context.user.groups.add(registered)
        navigate_to_page(context, '', 'login')
        context.table = (
            {'field': 'id_username', 'value': username},
            {'field': 'id_password', 'value': 'test'}
        )
        do_form_fill_out(context)
