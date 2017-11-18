import os

from selenium import webdriver

os.environ['DJANGO_SETTINGS_MODULE'] = 'development_settings'
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'ubuntuusers.local:8080'


def before_all(context):
    context.SERVER_URL = "http://" + os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS']


def before_scenario(context, scenario):
    context.browser = webdriver.Chrome()


def after_scenario(context, feature):
    context.browser.quit()
