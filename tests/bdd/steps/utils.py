import os

import allure


def take_screenshot(context, name):
    directory = os.path.join(context.LOG_DIR, context.feature.name, context.scenario.name)
    if not os.path.exists(directory):
        os.makedirs(directory)
    cleaned_name = name.replace('"', '').replace('/', '')
    filename = os.path.join(directory, cleaned_name + ".png")
    context.browser.get_screenshot_as_file(filename)
    allure.attach.file(filename, name)
