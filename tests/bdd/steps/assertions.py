from behave import then


@then('I should see elements')
def step_impl(context):
    for row in context.table:
        assert context.browser.find_element_by_id(row['item'])


@then('it should be successful')
def step_impl(context):
    assert context.browser.find_element_by_css_selector('.message.success')


@then('it should fail')
def step_impl(context):
    assert context.browser.find_element_by_css_selector('.errors')


@then('I should see "{inactive_type}" information')
def step_impl(context, inactive_type):
    messages = {
        'banned': "gesperrt",
        'inactive': 'inaktiv',
        'deleted': 'inaktiv'
    }
    error = context.browser.find_element_by_css_selector('.errors')
    assert messages[inactive_type] in error.text


@then(u'I should see a link to "{link_location}"')
def step_impl(context, link_location):
    link = context.SERVER_URL + '/' + link_location
    assert context.browser.find_element_by_css_selector("[href*='%(link)s']" % {'link': link})
