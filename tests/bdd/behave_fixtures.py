import django
from behave import fixture
from django.conf import settings
from django.db import connections, OperationalError
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

    # via https://stackoverflow.com/a/57000493
    # from https://github.com/cga-harvard/Hypermap-Registry/blob/cd4efad61f18194ddab2c662aa431aa21dec03f4/hypermap/tests/test_csw.py (MIT)
    # Workaround for https://code.djangoproject.com/ticket/22414
    # Persistent connections not closed by LiveServerTestCase, preventing dropping test databases
    # https://github.com/cjerdonek/django/commit/b07fbca02688a0f8eb159f0dde132e7498aa40cc
    def close_sessions(conn):
        close_sessions_query = """
            SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE
                datname = current_database() AND
                pid <> pg_backend_pid();
        """
        with conn.cursor() as cursor:
            try:
                cursor.execute(close_sessions_query)
            except OperationalError:
                # We get kicked out after closing.
                pass

    for alias in connections:
        close_sessions(connections[alias])

    del context.test_case


@fixture
def browser_chrome(context):
    options = Options()
    options.headless = settings.HEADLESS
    context.browser = Chrome(options=options)
    context.browser.set_window_size(1024, 1900)
    yield context.browser
    context.browser.quit()
