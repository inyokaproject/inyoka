from behave import when


@when('I fill out the form')
def do_form_fill_out(context):
    for row in context.table:
        field = context.browser.find_element_by_id(row['field'])
        value = row['value']
        if value == "on" or value == "off":
            if value == "on" and not field.is_selected() or value == "off" and field.is_selected():
                field.click()
        else:
            field.send_keys(row['value'])
    context.browser.find_elements_by_css_selector('input[type=submit]')[-1].submit()
