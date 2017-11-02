import os

import django
from django.test import LiveServerTestCase
from django.test.runner import DiscoverRunner
from selenium import webdriver

os.environ['DJANGO_SETTINGS_MODULE'] = 'development_settings'
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'ubuntuusers.local:8080'


def before_all(context):
    django.setup()
    context.test_runner = DiscoverRunner()
    context.test_runner.setup_test_environment()
    context.old_db_config = context.test_runner.setup_databases()

    context.SERVER_URL = "http://" + os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS']
    context.browser = webdriver.Chrome()
    context.browser.implicitly_wait(10)


def after_all(context):
    context.browser.quit()
    context.test_runner.teardown_databases(context.old_db_config)
    context.test_runner.teardown_test_environment()


def before_scenario(context, scenario):
    context.test_case = LiveServerTestCase
    context.test_case.setUpClass()


def after_scenario(context, feature):
    context.test_case.tearDownClass()
    del context.test_case
