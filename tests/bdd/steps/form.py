from behave import when


@when('I fill out the form')
def do_form_fill_out(context):
    for row in context.table:
        field = context.browser.find_element_by_id(row['field'])
        field.send_keys(row['value'])
    button = context.browser.find_elements_by_css_selector('input[type=submit]')[-1]
    button.click()
