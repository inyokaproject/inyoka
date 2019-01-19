# -*- coding: utf-8 -*-
"""
    inyoka.default_settings
    ~~~~~~~~~~~~~~~~~~~~~~~

    The inyoka default settings.

    :copyright: (c) 2007-2019 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from collections import OrderedDict
from datetime import timedelta
from os.path import dirname, join

from celery.schedules import crontab

gettext_noop = lambda x: x

#: Base path of this application
BASE_PATH = dirname(__file__)

#: Disable all debugging by default
DEBUG = False
DEBUG_NOTIFICATIONS = False
DEBUG_PROPAGATE_EXCEPTIONS = False

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
# LANGUAGE_CODE = 'en-US'
LOCALE_PATHS = (join(BASE_PATH, 'locale'),)
LC_ALL = 'en_US.UTF-8'

# the base url (without subdomain)
BASE_DOMAIN_NAME = 'ubuntuusers.de'
INYOKA_URI_SCHEME = 'http'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
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
MEDIA_URL = '//media.%s/' % BASE_DOMAIN_NAME

# same for static
STATIC_ROOT = join(BASE_PATH, 'static-collected')
STATIC_URL = '//static.%s/' % BASE_DOMAIN_NAME

# system user and group related settings
INYOKA_SYSTEM_USER = u'ubuntuusers.de'
INYOKA_IKHAYA_GROUP_NAME = u'ikhayateam'
INYOKA_REGISTERED_GROUP_NAME = u'registered'
INYOKA_TEAM_GROUP_NAME = u'team'
INYOKA_ANONYMOUS_GROUP_NAME = u'anonymous'

# E-Mail settings
INYOKA_SYSTEM_USER_EMAIL = '@'.join(['system', BASE_DOMAIN_NAME])
INYOKA_CONTACT_EMAIL = '@'.join(['contact', BASE_DOMAIN_NAME])
DEFAULT_FROM_EMAIL = INYOKA_SYSTEM_USER_EMAIL

# Disable portal registration, useful in case of a spam problem
INYOKA_DISABLE_REGISTRATION = False

# Spam prevention
INYOKA_USE_AKISMET = False
INYOKA_AKISMET_KEY = None
INYOKA_AKISMET_URL = None
INYOKA_AKISMET_DEFAULT_IS_SPAM = False
INYOKA_SPAM_COUNTER_TIMEOUT = 60 * 5  # seconds
INYOKA_SPAM_COUNTER_MAX = 5
INYOKA_SPAM_DETECT_LIMIT = 100

# restrictions for user avatar images
INYOKA_AVATAR_MAXIMUM_WIDTH = 80  # in px
INYOKA_AVATAR_MAXIMUM_HEIGHT = 100  # in px
INYOKA_AVATAR_MAXIMUM_FILE_SIZE = 15  # in KiB, 0 → unlimited

# restrictions for user signatures in the forum
INYOKA_SIGNATURE_MAXIMUM_CHARACTERS = 500  # <= -1 → no restriction
INYOKA_SIGNATURE_MAXIMUM_LINES = 4  # <= -1 → no restriction

# download link on the start page
INYOKA_GET_UBUNTU_LINK = u'%s://wiki.%s/Downloads' % (INYOKA_URI_SCHEME,
                                                      BASE_DOMAIN_NAME)
INYOKA_GET_UBUNTU_DESCRIPTION = u'Downloads'

# inyoka should deliver the statics
INYOKA_HOST_STATICS = False

# use etags
USE_ETAGS = True

# maximal number of tags shown in the tag cloud
TAGCLOUD_SIZE = 100

# prefix for the system mails
EMAIL_SUBJECT_PREFIX = u'%s: ' % BASE_DOMAIN_NAME

EMAIL_BACKEND = 'inyoka.utils.mail.SendmailEmailBackend'

# forum settings
FORUM_LIMIT_UNREAD = 100
FORUM_THUMBNAIL_SIZE = (64, 64)
# time in seconds after posting a user is allowed to edit/delete his own posts,
# for posts (without, with) replies. -1 for infinitely, 0 for never
FORUM_OWNPOST_EDIT_LIMIT = (-1, 1800)
FORUM_OWNPOST_DELETE_LIMIT = (0, 0)

FORUM_SURGE_PROTECTION_TIMEOUT = 90  # seconds

FORUM_DISABLE_POSTING = False

# Number of days a user is allowed to perform the respective action with his
# user account.
USER_REACTIVATION_LIMIT = 31
USER_SET_NEW_EMAIL_LIMIT = 7
USER_RESET_EMAIL_LIMIT = 31

# settings for the jabber bot (client)
JABBER_BOT_SERVER = 'tcp://127.0.0.1:6203'

# settings for the jabber bot (server)
# where to listen for client connections:
JABBER_BIND = 'tcp://127.0.0.1:6203'
# Jabber-ID without ressource
JABBER_ID = None
JABBER_PASSWORD = None

# hours for a user to activate the account
ACTIVATION_HOURS = 48

# days to describe an inactive user
USER_INACTIVE_DAYS = 365

# wiki settings
WIKI_MAIN_PAGE = 'Welcome'

# The forum that should contain the wiki discussions
WIKI_DISCUSSION_FORUM = 'discussions'

# the page below we have our templates.  The template the
# user specifies in the macro or in the parser is then
# joined with this page name according to our weird joining
# rules
WIKI_TEMPLATE_BASE = 'Wiki/Templates'

WIKI_PRIVILEGED_PAGES = []

WIKI_RECENTCHANGES_MAX = 250
WIKI_RECENTCHANGES_DAYS = 7

WIKI_REVISIONS_PER_PAGE = 100

# 2h is the recommended and tested Cache Timeout for
# wiki internal stuff like page or attachment lists.
WIKI_CACHE_TIMEOUT = 60 * 60 * 2

# Make this unique, and don't share it with anybody.
SECRET_KEY = None


# 24h is the recommended and tested Cache Timeout
CACHE_TIMEOUT = 60 * 60 * 24
# Cache Setup
CACHES = {
    'default': {
        'BACKEND': 'inyoka.utils.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': CACHE_TIMEOUT
    },
    'content': {
        'BACKEND': 'inyoka.utils.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'TIMEOUT': CACHE_TIMEOUT
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
    'inyoka.middlewares.tz.TimezoneMiddleware',
    'inyoka.middlewares.services.ServiceMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'inyoka.middlewares.common.MobileDetectionMiddleware',
    'django_mobile.middleware.SetFlavourMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
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
    'django.contrib.auth',
    'inyoka.forum.apps.ForumAppConfig',
    'inyoka.portal.apps.PortalAppConfig',
    'inyoka.wiki.apps.WikiAppConfig',
    'inyoka.ikhaya.apps.IkhayaAppConfig',
    'inyoka.pastebin.apps.PastebinAppConfig',
    'inyoka.planet.apps.PlanetAppConfig',
    'inyoka.markup.apps.MarkupAppConfig',
    'django_mobile',
    'django_hosts',
    'guardian',
)

# Set the default sentry site
SENTRY_SITE = 'example.com'


# Celery broker.
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERY_SEND_TASK_ERROR_EMAILS = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_ALWAYS_EAGER = DEBUG

# Do not hijack the root logger, avoids unicode errors
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_SEND_EVENTS = True

# Modules that hold task definitions
CELERY_IMPORTS = [
    'inyoka.utils.logger',
    'inyoka.portal.tasks',
    'inyoka.planet.tasks',
    'inyoka.wiki.tasks',
    'inyoka.utils.notification',
    'inyoka.forum.notifications',
]

# Run tasks at specific time
CELERY_BEAT_SCHEDULE = {
    'check-for-new-session-record': {
        'task': 'inyoka.portal.tasks.check_for_user_record',
        'schedule': timedelta(minutes=5),
    },
    'cleanup_wiki_stale_attachments': {
        'task': 'inyoka.wiki.tasks.cleanup_stale_attachments',
        'schedule': crontab(hour=4, minute=15, day_of_week='monday'),
    },
    'delete-not-activated-users': {
        'task': 'inyoka.portal.tasks.clean_expired_users',
        'schedule': crontab(hour=5, minute=30),
    },
    'delete-users-with-no-content': {
        'task': 'inyoka.portal.tasks.clean_inactive_users',
        'schedule': crontab(hour=4, minute=15, day_of_week='sunday'),
    },
    'sync-planet': {
        'task': 'inyoka.planet.tasks.sync',
        'schedule': timedelta(minutes=15),
    },
    'update_wiki_recent_changes': {
        'task': 'inyoka.wiki.tasks.update_recentchanges',
        'schedule': timedelta(minutes=15),
    },
    'update_page_by_slug': {
        'task': 'inyoka.wiki.tasks.update_page_by_slug',
        'schedule': timedelta(hours=1),
    }
}


# Make the template context available as tmpl_context in the TemplateResponse.
# Useful for tests in combination with override_settings.
PROPAGATE_TEMPLATE_CONTEXT = False

INTERNAL_IPS = ('127.0.0.1',)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'formatters': {
        'console': {
            'format': '[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'filters': ['require_debug_true'],
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['require_debug_false'],
        },
        'inyokalog': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'console',
            'filename': 'inyoka.log',
            'filters': ['require_debug_true'],
        },
        'celerylog': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'console',
            'filename': 'celery.log',
            'filters': ['require_debug_true'],
        },
        'null': {
            'class': 'logging.NullHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'sentry.errors': {
            'handlers': ['console',],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['inyokalog',],
            'level': 'INFO',
            'propagate': False,
        },
        'PIL': {
            'handlers': ['null',],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celerylog',],
            'level': 'INFO',
            'propagate': False,
        },
        'kombu': {
            'handlers': ['console', 'celerylog',],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

WSGI_APPLICATION = 'inyoka.wsgi.application'

X_FRAME_OPTIONS = 'DENY'

CSRF_FAILURE_VIEW = 'inyoka.portal.views.csrf_failure'

DEFAULT_FILE_STORAGE = 'inyoka.utils.files.InyokaFSStorage'

AUTH_USER_MODEL = 'portal.User'
AUTHENTICATION_BACKENDS = (
    'inyoka.portal.auth.InyokaAuthBackend',
    'guardian.backends.ObjectPermissionBackend',
)

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

# Used for user.post_count, forum.topic_count etc.
COUNTER_CACHE_TIMEOUT = 60 * 60 * 24 * 2  # two weeks

# disable anonymous user creating in django-guardian
ANONYMOUS_USER_NAME = u'anonymous'

# disable guardian monkey patching, for custom user model support
GUARDIAN_MONKEY_PATCH = False

# Raven config
RAVEN_PUBLIC_DSN = None

SMILIES = OrderedDict([
    (u':?:', u'❓'),  # has to come before :?
    (u':???:', u'⁇'),  # has to come before :?
    # normal smilies
    (u':-)', u'☺'),
    (u':)', u'☺'),
    (u':-(', u'☹'),
    (u':(', u'☹'),
    (u';-)', u'😉'),
    (u';)', u'😉'),
    (u':-P', u'😛'),
    (u':P', u'😛'),
    (u':-D', u'😀'),
    (u':D', u'😀'),
    (u':-o', u'😮'),
    (u':-O', u'😮'),
    (u':o', u'😮'),
    (u':-?', u'😕'),
    (u':?', u'😕'),
    (u':-x', u'😠'),
    (u':x', u'😠'),
    (u'8-)', u'😎'),
    (u'# 8)', u'😎'),
    (u':-$', u'😳'),
    (u'<3', u'♥'),
    (u':[]', u'😬'),
    (u':-[]', u'😬'),
    (u'§)', u'🤓'),
    (u'8-o', u'😲'),
    (u'8-}', u'🐸'),
    (u':-|', u'😐'),
    (u':|', u'😐'),
    (u';-(', u'😢'),
    (u']:-(', u'👿'),
    (u']:-)', u'😈'),
    (u'O:-)', u'😇'),
    (u':->', u'😊'),
    # text smilies
    (u':!:', u'❗'),
    (u':arrow:', u'▶'),
    (u':backarrow:', u'◀'),
    (u':cool:', u'😎'),
    (u':cry:', u'😢'),
    (u':eek:', u'😮'),
    (u':ente:', u'🦆'),
    (u':grin:', u'😀'),
    (u':idea:', u'💡'),
    (u':lol:', u'🤣'),
    (u':mad:', u'😠'),
    (u':mrgreen:', u'😀'),
    (u':neutral:', u'😐'),
    (u':oops:', u'😳'),
    (u':razz:', u'😛'),
    (u':roll:', u'🙄'),
    (u':sad:', u'☹'),
    (u':shock:', u'😲'),
    (u':smile:', u'☺'),
    (u':thumbsup:', u'👍'),
    (u':wink:', u'😉'),
    (u'{dl}', u'⮷'),
    # icons (with no equivalent in unicode)
    (u'# <8-} ', u'css-class:icon-frog-xmas'),
    (u':tux:', u'css-class:icon-tux'),
    (u'{*}', u'css-class:icon-ubuntu'),
    (u'{g}', u'css-class:icon-ubuntugnome'),
    (u'{k}', u'css-class:icon-kubuntu'),
    (u'{l}', u'css-class:icon-lubuntu'),
    (u'{ma}', u'css-class:icon-ubuntumate'),
    (u'{m}', u'css-class:icon-mythbuntu'),
    (u'{ut}', u'css-class:icon-ubuntutouch'),
    (u'{x}', u'css-class:icon-xubuntu'),
    (u'{Übersicht}', u'css-class:icon-overview')
])

# export only uppercase keys
__all__ = list(x for x in locals() if x.isupper())
