from behave import given, step
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait


@given('I am on the "{page_slug}" page')
def step_impl(context, page_slug):
    navigate_to_page(context, app='', page_slug=page_slug)


@step('I use the "{app}" and visit the "{page_slug}" page')
def navigate_to_page(context, app, page_slug):
    from inyoka.utils.urls import href

    if not app:
        app = 'portal'
    if page_slug == 'main':
        page_slug = ''
    location = href(app, page_slug)

    driver = context.browser
    driver.get(location)

    wait = WebDriverWait(driver, 10)
    wait.until(presence_of_element_located((By.CLASS_NAME, 'license')))


@step('I open the "{app}" in {view_type} view')
def step_impl(context, app, view_type):
    assert context.test_item, "No item to open has been created!"
    go_to_item(context, app, view_type, context.test_item.id)


@step('I open the "{app}" {view_type} view of "{item_id}"')
def go_to_item(context, app, view_type, item_id):
    from inyoka.utils.urls import href

    view_string = None
    if view_type and view_type != "detail":
        view_string = view_type

    if view_string:
        location = href(app, view_string, item_id)
    else:
        location = href(app, item_id)

    driver = context.browser
    driver.get(location)

    if view_type != "raw":
        wait = WebDriverWait(driver, 10)
        wait.until(presence_of_element_located((By.CLASS_NAME, 'license')))


@step("I click on {action}")
def step_impl(context, action):
    context.browser.find_element(by=By.NAME, value=action).click()
