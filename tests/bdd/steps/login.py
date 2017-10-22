from behave import when


@when('I enter the credentials')
def step_impl(context):
    context.browser.find_element_by_id('id_username').send_keys(context.table[0]['username'])
    context.browser.find_element_by_id('id_password').send_keys(context.table[0]['password'])
    context.browser.find_element_by_id('login').submit()
