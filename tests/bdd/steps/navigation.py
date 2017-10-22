from behave import given


@given('I am on the login page')
def step_impl(context):
    context.browser.get(context.SERVER_URL + '/login')

