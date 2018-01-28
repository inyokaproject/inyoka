import django
import os
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.bdd.settings.headless'


def before_all(context):
    context.LOG_DIR = "bdd_screenshots"

    django.setup()
    context.test_runner = DiscoverRunner()
    context.test_runner.keepdb = True
    context.test_runner.parallel = True
    context.test_runner.setup_test_environment()


def before_scenario(context, scenario):
    context.old_db_config = context.test_runner.setup_databases()

    context.test_case = StaticLiveServerTestCase
    context.test_case.host = 'ubuntuusers.local'
    context.test_case.setUpClass()

    context.base_url = context.test_case.live_server_url
    settings.BASE_DOMAIN_NAME = context.base_url[7:]
    settings.MEDIA_URL = '//media.%s/' % settings.BASE_DOMAIN_NAME
    settings.STATIC_URL = '//static.%s/' % settings.BASE_DOMAIN_NAME
    settings.LOGIN_URL = '//%s/login/' % settings.BASE_DOMAIN_NAME

    options = Options()
    options.set_headless(settings.HEADLESS)
    context.browser = webdriver.Chrome(chrome_options=options)
    context.browser.set_window_size(1024, 1900)
    context.browser.implicitly_wait(30)


def after_step(context, step):
    if step.status == "failed":
        directory = os.path.join(context.LOG_DIR, context.feature.name, context.scenario.name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = os.path.join(directory, step.name + ".png")
        context.browser.get_screenshot_as_file(filename)


def after_scenario(context, scenario):
    context.browser.quit()
    context.test_case.tearDownClass()

    context.test_runner.teardown_databases(context.old_db_config)
    del context.test_case


def after_all(context):
    context.test_runner.teardown_test_environment()
