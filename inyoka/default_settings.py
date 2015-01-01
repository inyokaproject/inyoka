# -*- coding: utf-8 -*-
"""
    inyoka.default_settings
    ~~~~~~~~~~~~~~~~~~~~~~~

    The inyoka default settings.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from os.path import join, dirname

from django.conf.global_settings import *  # NOQA

import djcelery

gettext_noop = lambda x: x

#: Base path of this application
BASE_PATH = dirname(__file__)

#: Disable all debugging by default
DEBUG = False
DEBUG_NOTIFICATIONS = False
DEBUG_PROPAGATE_EXCEPTIONS = False

# per default there are no managers and admins.  I guess that's
# unused :)
MANAGERS = ADMINS = ()


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'database.db',
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# the setting here has nothing to do with the timezone the user is
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
LANGUAGE_CODE = 'de-de'
LOCALE_PATHS = (join(BASE_PATH, 'locale'),)

# the base url (without subdomain)
BASE_DOMAIN_NAME = 'ubuntuusers.de'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
#SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_COOKIE_DOMAIN = '.%s' % BASE_DOMAIN_NAME.split(':')[0]
SESSION_COOKIE_NAME = 'session'
SESSION_COOKIE_HTTPONLY = True

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

# this url conf is used for contrib stuff like the auth system
ROOT_URLCONF = 'inyoka.portal.urls'
# host conf for subdomain dispatching
ROOT_HOSTCONF = 'inyoka.hosts'
DEFAULT_HOST = 'portal'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media and the URL
MEDIA_ROOT = join(BASE_PATH, 'media')
MEDIA_URL = 'http://media.%s/' % BASE_DOMAIN_NAME

# same for static
STATIC_ROOT = join(BASE_PATH, 'static-collected')
STATIC_URL = 'http://static.%s/' % BASE_DOMAIN_NAME

# system settings
INYOKA_SYSTEM_USER = u'ubuntuusers.de'
INYOKA_SYSTEM_USER_EMAIL = '@'.join(['system', BASE_DOMAIN_NAME])
INYOKA_ANONYMOUS_USER = u'anonymous'
INYOKA_CONTACT_EMAIL = '@'.join(['contact', BASE_DOMAIN_NAME])
DEFAULT_FROM_EMAIL = INYOKA_SYSTEM_USER_EMAIL

# logger name for remote exception logging
INYOKA_LOGGER_NAME = u'inyoka'

# use etags
USE_ETAGS = True

# prefix for the system mails
EMAIL_SUBJECT_PREFIX = u'%s: ' % BASE_DOMAIN_NAME

EMAIL_BACKEND = 'inyoka.utils.mail.SendmailEmailBackend'

# path to the xapian database
# Examples: /path/to/inyoka.xapdb, or tcpsrv://localhost:3000/
XAPIAN_DATABASE = join(BASE_PATH, 'inyoka.xapdb')

# forum settings
FORUM_LIMIT_UNREAD = 100
FORUM_THUMBNAIL_SIZE = (64, 64)
# time in seconds after posting a user is allowed to edit/delete his own posts,
# for posts (without, with) replies. -1 for infinitely, 0 for never
FORUM_OWNPOST_EDIT_LIMIT = (-1, 1800)
FORUM_OWNPOST_DELETE_LIMIT = (0, 0)

# Number of days a user is allowed to perform the respective action with his
# user account.
USER_REACTIVATION_LIMIT = 31
USER_SET_NEW_EMAIL_LIMIT = 7
USER_RESET_EMAIL_LIMIT = 31

# the id of the ikhaya team group
IKHAYA_GROUP_ID = 1

# settings for the jabber bot
JABBER_BOT_SERVER = 'tcp://127.0.0.1:6203'

# hours for a user to activate the account
ACTIVATION_HOURS = 48

# days to describe an inactive user
USER_INACTIVE_DAYS = 365

# key for google maps
GOOGLE_MAPS_APIKEY = ''

# wiki settings
WIKI_MAIN_PAGE = 'Welcome'

# The forum that should contain the wiki discussions
WIKI_DISCUSSION_FORUM = 'discussions'

# the page below we have our templates.  The template the
# user specifies in the macro or in the parser is then
# joined with this page name according to our weird joining
# rules
WIKI_TEMPLATE_BASE = 'Wiki/Templates'

# the base page of all user wiki pages
WIKI_USER_BASE = 'User'
WIKI_USERPAGE_INFO = 'Userpage'

# Make this unique, and don't share it with anybody.
SECRET_KEY = None

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'request': {
        'BACKEND': 'inyoka.utils.cache.RequestCache',
    }
}


AVAILABLE_FEED_COUNTS = {
    None: (10, 25),
    'ikhaya_feed_article': (10, 20, 25),
    'ikhaya_feed_comment': (10, 20, 25),
    'forum_topic_feed': (10, 20, 25, 50),
    'forum_forum_feed': (10, 20, 25, 50, 75, 100),
    'planet_feed': (10, 20, 25, 50),
    'wiki_feed': (10, 20),
}

MIDDLEWARE_CLASSES = (
    'inyoka.middlewares.common.CommonServicesMiddleware',
    'inyoka.middlewares.session.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'inyoka.middlewares.auth.AuthMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'inyoka.middlewares.tz.TimezoneMiddleware',
    'inyoka.middlewares.services.ServiceMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'inyoka.middlewares.common.MobileDetectionMiddleware',
    'django_mobile.middleware.SetFlavourMiddleware',
)

#: We only allow uploads via memory up to 2.5mb and do not stream into
#: temporary files.
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'inyoka.core',
    'django.contrib.auth',
    'inyoka.forum',
    'inyoka.portal',
    'inyoka.wiki',
    'inyoka.ikhaya',
    'inyoka.pastebin',
    'inyoka.planet',
    'inyoka.markup',
    'django_openid',
    'raven.contrib.django',
    'south',
    # *must* be installed after south
    'kombu.transport.django',
    'djcelery',
    'django_mobile',
    'django_hosts',
)

# don't use migrations but just syncdb
SOUTH_TESTS_MIGRATE = False

OPENID_PROVIDERS = {
    'openid': {
        'name': gettext_noop('OpenID'),
        'url': None
    },
    'launchpad': {
        'name': gettext_noop('Launchpad'),
        'url': 'https://launchpad.net/~{username}'
    },
    'claimid': {
        'name': gettext_noop('ClaimID'),
        'url': 'http://claimid.com/{username}'
    },
    'google': {
        'name': gettext_noop('Google'),
        'url': 'https://www.google.com/accounts/o8/id'
    },
}

# some terms to exclude by default to maintain readability
SEARCH_DEFAULT_EXCLUDE = []

# Default blocksize to delmit queries to the search index
SEARCH_INDEX_BLOCKSIZE = 5000

# Set the default sentry site
SENTRY_SITE = 'example.com'


# Import and activate django-celery support
djcelery.setup_loader()

# Celery broker preferences.
# http://celeryq.org/docs/configuration.html#celery-result-backend
CELERY_RESULT_BACKEND = 'database'

# SQLAlchemy compatible uri.
# NOTE: This is some kind of deactivated since we are using
# django-celery for this stuff.
CELERY_RESULT_DBURI = 'sqlite://'

# Modules that hold task definitions
CELERY_IMPORTS = [
    # register special celery task logger
    'inyoka.utils.logger',
    # general (e.g monitoring) tasks
    'inyoka.tasks',
    # Application specific tasks
    'inyoka.portal.tasks',
    'inyoka.wiki.tasks',
    # Notification specific tasks
    'inyoka.wiki.notifications',
    'inyoka.utils.notification',
    'inyoka.forum.notifications',
    'inyoka.ikhaya.notifications',
]

CELERY_SEND_TASK_ERROR_EMAILS = False
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_EAGER_PROPAGATES_EXCEPTIONS = False
CELERY_ALWAYS_EAGER = DEBUG

# Do not hijack the root logger, avoids unicode errors
CELERYD_HIJACK_ROOT_LOGGER = False

CELERY_SEND_EVENTS = True

# Make the template context available as tmpl_context in the TemplateResponse.
# Useful for tests in combination with override_settings.
PROPAGATE_TEMPLATE_CONTEXT = False

# http://ask.github.com/kombu/introduction.html#transport-comparison
BROKER_URL = 'django://'

INTERNAL_IPS = ('127.0.0.1',)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
}

WSGI_APPLICATION = 'inyoka.wsgi.application'

X_FRAME_OPTIONS = 'DENY'

CSRF_FAILURE_VIEW = 'inyoka.portal.views.csrf_failure'

DEFAULT_FILE_STORAGE = 'inyoka.utils.files.InyokaFSStorage'

TEST_RUNNER = 'discover_runner.DiscoverRunner'

AUTH_USER_MODEL = 'portal.User'
AUTHENTICATION_BACKENDS = ('inyoka.portal.auth.InyokaAuthBackend',)

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'inyoka.utils.user.UnsaltedMD5PasswordHasher',
)

TEMPLATE_LOADERS = (
    'inyoka.utils.templating.DjangoLoader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = ()

ALLOWED_HOSTS = ['.ubuntuusers.de']

FORMAT_MODULE_PATH = 'inyoka.locale'

# export only uppercase keys
__all__ = list(x for x in locals() if x.isupper())
