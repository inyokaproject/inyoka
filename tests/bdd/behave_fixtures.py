from behave import fixture
import django

from django.conf import settings
from django.core.cache import cache
from django.test.runner import DiscoverRunner
from django.test.testcases import LiveServerTestCase
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome


@fixture
def django_test_runner(context):
    django.setup()
    context.test_runner = DiscoverRunner(keepdb=False)
    context.old_db_config = context.test_runner.setup_databases()
    context.test_runner.setup_test_environment()
    yield
    context.test_runner.teardown_test_environment()
    context.test_runner.teardown_databases(context.old_db_config)


@fixture
def django_test_case(context):
    context.test_case = LiveServerTestCase
    context.test_case.host = 'ubuntuusers.local'
    context.test_case.setUpClass()
    context.base_url = context.test_case.live_server_url
    yield context.base_url
    context.test_case.tearDownClass()
    del context.test_case


@fixture()
def setup_cache(context):
    cache.clear()


@fixture
def browser_chrome(context):
    options = Options()
    options.set_headless(settings.HEADLESS)
    context.browser = Chrome(chrome_options=options)
    context.browser.set_window_size(1024, 1900)
    yield context.browser
    context.browser.quit()
