from behave import *


@given('I am on the login page')
def step_impl(context):
    context.browser.get(context.SERVER_URL + '/login')


@when('I enter the credentials')
def step_impl(context):
    context.browser.find_element_by_id('id_username').send_keys(context.table[0]['username'])
    context.browser.find_element_by_id('id_password').send_keys(context.table[0]['password'])
    context.browser.find_element_by_id('login').submit()


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


@then('I should see information about')
def step_impl(context):
    messages = {
        'banned': "gesperrt",
        'inactive': 'inaktiv',
        'deleted': 'inaktiv'
    }
    error = context.browser.find_element_by_css_selector('.errors')
    assert messages[context.text] in error.text
