from behave import given


@given('I am on the login page')
def step_impl(context):
    context.browser.get(context.SERVER_URL + '/login')


@given('I am on the page')
def step_impl(context):
    location = context.SERVER_URL + "/" + context.table[0]['page_name']
    context.browser.get(location)
