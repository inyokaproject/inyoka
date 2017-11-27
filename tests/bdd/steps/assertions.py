# -*- coding: utf-8 -*-
import re
from pprint import pprint

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
        element_text = get_plain_text(element.text or element.get_property('value'))
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


@then(u'I should see a link to "{link}"')
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
    assert context.browser.find_element_by_css_selector('.not_found')


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


@then("the {item_type} should be {visible_type} by {username}")
def check_item_visibility(context, item_type, visible_type, username):
    expected_hidden_value = None
    if visible_type == "visible":
        expected_hidden_value = False
    elif visible_type == "hidden":
        expected_hidden_value = True

    if item_type == 'blogpost':
        from inyoka.planet.models import Entry

        blogpost = Entry.objects.get(id=context.test_item.id)
        assert blogpost.hidden == expected_hidden_value, "The blogpost should be %s" % visible_type
        if expected_hidden_value:
            assert blogpost.hidden_by.username == username
        else:
            assert blogpost.hidden_by is None
        return

    raise ValueError("The item type isn't supported")


@then("the {item_type} should be {visible_type}")
def step_impl(context, item_type, visible_type):
    username = context.user.username
    check_item_visibility(context, item_type, visible_type, username)


field_error_messages = {
    "user not found": u"Diesen Benutzer gibt es nicht",
    "invalid url": u"Bitte eine gültige Adresse eingeben.",
    "field is required": u"Dieses Feld ist zwingend erforderlich"
}


@then('I should see a "{error_type}" field error')
def step_impl(context, error_type):
    expected_error_text = field_error_messages[error_type]
    error_text = context.browser.find_element_by_css_selector(".errorlist > li").text

    assert expected_error_text == error_text
