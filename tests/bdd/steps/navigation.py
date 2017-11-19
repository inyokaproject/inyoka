from behave import given


@given('I am on the "{page_slug}" page')
def step_impl(context, page_slug):
    location = context.SERVER_URL + "/" + page_slug
    context.browser.get(location)
