import django
from behave import fixture
from django.conf import settings
from django.test.runner import DiscoverRunner
from django.test.testcases import LiveServerTestCase
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


@fixture
def django_test_runner(context):
    django.setup()
    context.test_runner = DiscoverRunner()
    context.old_db_config = context.test_runner.setup_databases()
    context.test_runner.setup_test_environment()
    yield
    context.test_runner.teardown_test_environment()
    context.test_runner.teardown_databases(context.old_db_config)


@fixture
def django_test_case(context):
    context.test_case = LiveServerTestCase
    context.test_case.host = 'ubuntuusers.local'
    context.test_case = context.test_case(methodName='run')
    context.test_case._pre_setup()
    context.test_case.setUpClass()
    context.test_case()
    context.base_url = context.test_case.live_server_url
    yield context.base_url
    context.test_case.tearDownClass()
    context.test_case._post_teardown()

    del context.test_case


@fixture
def browser_chrome(context):
    options = Options()
    if settings.HEADLESS:
        options.add_argument("--headless=new")
    context.browser = Chrome(options=options)
    context.browser.set_window_size(1024, 1900)
    yield context.browser
    context.browser.quit()
