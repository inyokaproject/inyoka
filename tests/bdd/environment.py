from selenium import webdriver


def before_all(context):
    context.SERVER_URL = "http://ubuntuusers.local:8080"
    context.browser = webdriver.Chrome()


def after_all(context):
    context.browser.quit()


def after_scenario(context, feature):
    context.browser.get(context.SERVER_URL + "/logout")
