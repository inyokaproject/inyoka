from behave import step


@step("take a screen shot")
def step_impl(context):
    context.browser.get_screenshot_as_file('test.png')
