from behave import given

from inyoka.portal.user import User


@given('The user "{username}" exits')
def step_impl(context, username):
    User.objects.register_user(username, '%s@ubuntuusers.local' % username, 'test', False)


@given('The user "{username}" with status "{status_string}" exists')
def step_impl(context, username, status_string):
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
