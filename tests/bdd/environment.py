import os

from django.conf import settings
from django.contrib.auth.models import Group
from selenium import webdriver

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = settings.BASE_DOMAIN_NAME


def before_all(context):
    context.SERVER_URL = "http://" + settings.BASE_DOMAIN_NAME

    if settings.HEADLESS:
        context.browser = webdriver.PhantomJS('node_modules/phantomjs-prebuilt/bin/phantomjs')


def before_scenario(context, scenario):
    if not settings.HEADLESS:
        context.browser = webdriver.Chrome()

    Group.objects.get_or_create(name=settings.INYOKA_REGISTERED_GROUP_NAME)
    context.browser.implicitly_wait(10)


def after_scenario(context, feature):
    if not settings.HEADLESS:
        context.browser.quit()

def after_all(context):
    if settings.HEADLESS:
        context.browser.quit()
