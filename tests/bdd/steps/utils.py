import os


def take_screenshot(context, name):
    directory = os.path.join(context.LOG_DIR, context.feature.name, context.scenario.name)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, name + ".png")
    context.browser.get_screenshot_as_file(filename)
