import re

from behave import then


@then('I should see elements')
def step_impl(context):
    for row in context.table:
        assert context.browser.find_element_by_id(row['item'])


@then("I should see elements with values")
def step_impl(context):
    for row in context.table:
        element = context.browser.find_element_by_id(row['element'])
        value = row['value']
        element_text = get_plain_text(element.text)
        assert element_text == value, "'%s' doesn't match expected '%s'" % (element_text, value)


def get_plain_text(text):
    regex = re.compile('<.*?>')
    text = regex.sub('', text)
    return text.replace('\n', '')


@then('it should be successful')
def step_impl(context):
    assert context.browser.find_element_by_css_selector('.message.success')


@then('it should fail')
def step_impl(context):
    assert context.browser.find_element_by_css_selector('.errors')


@then('I should see "{inactive_type}" error')
def step_impl(context, inactive_type):
    messages = {
        'banned': "gesperrt",
        'inactive': 'inaktiv',
        'deleted': 'inaktiv'
    }
    error = context.browser.find_element_by_css_selector('.errors')
    assert messages[inactive_type] in error.text


@then('I should see a link to "{link}"')
def step_impl(context, link):
    link = link.replace('BASE_DOMAIN_NAME', context.base_url[7:])
    assert context.browser.find_element_by_css_selector("[href*='%(link)s']" % {'link': link})


@then('I should see a "{itemtype}" with "{required_keyword}" in a list')
def step_impl(context, itemtype, required_keyword):
    """
    Any element, which has a matching summary, will make this step pass.

    :type context: behave.runner.Context
    :param itemtype: Type of that this steps looks for. Caution: Only supports paste right now.
    :param required_keyword: The summary of the item
    """

    if itemtype == "paste":
        pastes = context.browser.find_elements_by_css_selector(".pastes")
        keywords = [entry.find_element_by_css_selector('li > a:first-of-type').text for entry in pastes]
        assert any(keyword == required_keyword for keyword in keywords)
        return

    raise AssertionError("Not supported app type provided")


@then('I should see a "403" exception')
def step_impl(context):
    caption = context.browser.find_element_by_css_selector('h1')
    assert '403' in caption.text


@then('I should see a "not-found" message')
def step_impl(context):
    text = get_plain_text(context.browser.page_source)
    assert 'Seite nicht gefunden' in text


@then('I should see "{value}"')
def step_impl(context, value):
    text = get_plain_text(context.browser.page_source)
    assert value == text


@then("I should see {information_type} info")
def step_impl(context, information_type):
    messages = {
        'canceled': "abgebrochen"
    }
    error = context.browser.find_element_by_css_selector('.message.info')
    assert messages[information_type] in error.text


@then("I should be on the login page")
def step_impl(context):
    from inyoka.utils.urls import href

    current_url = context.browser.current_url
    expected_url = href('portal', 'login')
    assert current_url.startswith(expected_url), "%s should be %s" % (current_url, expected_url)


@then('I should see a title "{value}"')
def step_impl(context, value):
    headings = context.browser.find_elements_by_css_selector('h1')
    for h in headings:
        text = h.text
        if value in text:
            return

    assert False