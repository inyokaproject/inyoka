.. _settings:

========
Settings
========

Inyoka is highly configurable. The following list shows all available settings
variables. To use them, add the following line into your script::

    from django.conf import setttings

Every configuration directive can be overridden by using a custom settings file
(see ``example_development_settings.py``) and setting the
``DJANGO_SETTINGS_MODULE`` environment variabel::

    $ export DJANGO_SETTINGS_MODULE="settings"


Generics
========

.. py:data:: CACHES

    Defaults to::

        {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            },
            'request': {
                'BACKEND': 'inyoka.utils.cache.RequestCache',
            }
        }

    A prefix that is automatically added on every cache operation to the key.
    You won't notice anything of it at all but it makes it possible to run more
    than one application on a single memcached server without the risk of cache
    key collision.

.. py:data:: DATABASES

    Defaults to::

        {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'database.db',
            },
        }

    Defines the available databases. See
    https://docs.djangoproject.com/en/1.3/ref/settings/#databases

.. py:data:: DEBUG

    Defaults to: ``False``

    Enable or disable debugging. See
    https://docs.djangoproject.com/en/1.3/ref/settings/#DEBUG

.. py:data:: DEBUG_PROPAGATE_EXCEPTIONS

    Defaults to: ``False``

    Enable or disable Django to push exceptions to a higher level. See
    https://docs.djangoproject.com/en/1.3/ref/settings/#debug-propagate-exceptions

.. py:data:: DEFAULT_FILE_STORAGE

    Defaults to: ``'inyoka.utils.files.InyokaFSStorage'``

.. py:data:: FILE_UPLOAD_HANDLERS

    Defaults to::

        (
            'django.core.files.uploadhandler.MemoryFileUploadHandler',
        )

    We only allow uploads via memory up to 2.5mb and do not stream into
    temporary files.

.. py:data:: INSTALLED_APPS

    Defaults to::

        (
            'django.contrib.contenttypes',
            'django.contrib.staticfiles',
            'django.contrib.humanize',
            'inyoka.portal',
            'inyoka.wiki',
            'inyoka.forum',
            'inyoka.ikhaya',
            'inyoka.pastebin',
            'inyoka.planet',
            'django_openid',
            'raven.contrib.django',
            'south',
            'djcelery',
            'djkombu',
            'django_mobile',
            'django_hosts',
        )

.. py:data:: MIDDLEWARE_CLASSES

    Defaults to::

        (
            'inyoka.middlewares.common.CommonServicesMiddleware',
            'inyoka.middlewares.session.AdvancedSessionMiddleware',
            'inyoka.middlewares.auth.AuthMiddleware',
            'django.middleware.transaction.TransactionMiddleware',
            'inyoka.middlewares.services.ServiceMiddleware',
            'django.middleware.http.ConditionalGetMiddleware',
            'inyoka.middlewares.highlighter.HighlighterMiddleware',
            'inyoka.middlewares.security.SecurityMiddleware',
            'inyoka.middlewares.common.MobileDetectionMiddleware',
            'django_mobile.middleware.SetFlavourMiddleware',
        )

.. py:data:: TEMPLATE_DIRS

    Defaults to::

        (
            join(BASE_PATH, 'templates'),
        )

Installation settings
=====================

Forum
-----

.. py:data:: FORUM_LIMIT_UNREAD

    Defaults to: ``100``

.. py:data:: FORUM_OWNPOST_DELETE_LIMIT

    Defaults to: ``(0, 0)``

.. py:data:: FORUM_OWNPOST_EDIT_LIMIT

    Defaults to: ``(-1, 1800)``

.. py:data:: FORUM_THUMBNAIL_SIZE

    Defaults to: ``(64, 64)``

    Time in seconds after posting a user is allowed to edit/delete his own
    posts, for posts (without, with) replies. -1 for infinitely, 0 for never

General
-------

.. py:data:: ACTIVATION_HOURS

    Defaults to: ``48``

    Hours for a user to activate the account

.. py:data:: AVAILABLE_FEED_COUNTS

    Defaults to::

        {
            None: (10, 25),
            'ikhaya_feed_article': (10, 20, 25),
            'ikhaya_feed_comment': (10, 20, 25),
            'forum_topic_feed': (10, 20, 25, 50),
            'forum_forum_feed': (10, 20, 25, 50, 75, 100),
            'planet_feed': (10, 20, 25, 50),
            'wiki_feed': (10, 20),
        }

.. py:data:: INYOKA_ANONYMOUS_USER

    Defaults to: ``u'anonymous'``

.. py:data:: INYOKA_CONTACT_EMAIL

    Defaults to: ``'@'.join(['contact', BASE_DOMAIN_NAME])``

.. py:data:: INYOKA_SYSTEM_USER

    Defaults to: ``u'ubuntuusers.de'``

.. py:data:: INYOKA_SYSTEM_USER_EMAIL

    Defaults to: ``'@'.join(['system', BASE_DOMAIN_NAME])``

.. py:data:: USER_INACTIVE_DAYS

    Defaults to: ``365``

    Days to describe an inactive user

Ikhaya
------

.. py:data:: IKHAYA_GROUP_ID

    Defaults to: ``1``

    The id of the ikhaya team group

Wiki
----

.. py:data:: WIKI_DISCUSSION_FORUM

    Defaults to: ``'discussions'``

    The forum that should contain the wiki discussions

.. py:data:: WIKI_MAIN_PAGE

    Defaults to: ``'Welcome'``

    Wiki settings

.. py:data:: WIKI_TEMPLATE_BASE

    Defaults to: ``'Wiki/Templates'``

    The page below we have our templates.  The template the user specifies in
    the macro or in the parser is then joined with this page name according to
    our weird joining rules

.. py:data:: WIKI_USER_BASE

    Defaults to: ``'User'``

    The base page of all user wiki pages

.. py:data:: WIKI_USERPAGE_INFO

    Defaults to: ``'Userpage'``

Localization and internationalization
=====================================

.. py:data:: LANGUAGE_CODE

    Defaults to: ``'de-de'``

    Language code for this installation. All choices can be found here:
    http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes

.. py:data:: TIME_ZONE

    Defaults to: ``None``

    Local time zone for this installation. Choices can be found here:
    http://en.wikipedia.org/wiki/List_of_tz_zones_by_name . Although not all
    choices may be available on all operating systems.  The setting here has
    nothing to do with the timezone the user is in.

    We set the TIME_ZONE to `None` on default so that Django does not issue
    time zone aware columns on PostgreSQL. This finally should fix the last
    standing bugs regarding PostgreSQL.

.. py:data:: USE_I18N

    Defaults to: ``True``

    If you set this to False, Django will make some optimizations so as not to
    load the internationalization machinery.

.. py:data:: USE_L10N

    Defaults to: ``True``

Logging
=======

.. py:data:: INYOKA_LOGGER_NAME

    Defaults to: ``u'inyoka'``

    Logger name for remote exception logging

.. py:data:: LOGGING

    Defaults to::

        {
            'version': 1,
            'disable_existing_loggers': False,
        }

.. py:data:: SENTRY_SITE

    Defaults to: ``'example.com'``

    Set the default sentry site

Notification
============

.. py:data:: DEBUG_NOTIFICATIONS

    Defaults to: ``False``

    Print a short message to STDOUT for each notification that is send by mail.

.. py:data:: EMAIL_BACKEND

    Defaults to: ``'inyoka.utils.mail.SendmailEmailBackend'``

.. py:data:: EMAIL_SUBJECT_PREFIX

    Defaults to: ``u'%s: ' % BASE_DOMAIN_NAME``

    Prefix for the system mails

.. py:data:: JABBER_BOT_SERVER

    Defaults to: ``'tcp://127.0.0.1:6203'``

    Settings for the jabber bot

Celery
------

.. py:data:: CELERY_ALWAYS_EAGER

    Defaults to: ``DEBUG``

.. py:data:: CELERY_EAGER_PROPAGATES_EXCEPTIONS

    Defaults to: ``False``

.. py:data:: CELERY_IMPORTS

    Defaults to::

        [
            'inyoka.utils.logger',
            'inyoka.tasks',
            'inyoka.portal.tasks',
            'inyoka.wiki.tasks',
            'inyoka.wiki.notifications',
            'inyoka.utils.notification',
            'inyoka.forum.notifications',
            'inyoka.ikhaya.notifications',
        ]

    Modules that hold task definitions

.. py:data:: CELERY_RESULT_BACKEND

    Defaults to: ``'database'``

    Celery broker preferences.

    http://celeryq.org/docs/configuration.html#celery-result-backend

.. py:data:: CELERY_RESULT_DBURI

    Defaults to: ``'sqlite://'``

    SQLAlchemy compatible URI. **NOTE:** This is some kind of deactivated since
    we are using django-celery for this stuff.

.. py:data:: CELERY_SEND_TASK_ERROR_EMAILS

    Defaults to: ``False``

.. py:data:: CELERYBEAT_SCHEDULER

    Defaults to: ``'djcelery.schedulers.DatabaseScheduler'``

.. py:data:: CELERYD_HIJACK_ROOT_LOGGER

    Defaults to: ``False``

    Do not hijack the root logger, avoids unicode errors

Broker
------

.. py:data:: BROKER_BACKEND

    Defaults to: ``'inyoka.utils.celery_support.DatabaseTransport'``

    http://ask.github.com/kombu/introduction.html#transport-comparison

.. py:data:: BROKER_HOST

    Defaults to: ``'localhost'``

.. py:data:: BROKER_PORT

    Defaults to: ``5672``

.. py:data:: BROKER_USER

    Defaults to: ``''``

.. py:data:: BROKER_PASSWORD

    Defaults to: ``''``

.. py:data:: BROKER_VHOST

    Defaults to: ``''``

Paths and URLs
==============

.. py:data:: ADMIN_MEDIA_PREFIX

    Defaults to: ``STATIC_URL + '/_admin/'``

.. py:data:: BASE_DOMAIN_NAME

    Defaults to: ``'ubuntuusers.de'``

    The base URL (without subdomain)

.. py:data:: BASE_PATH

    Defaults to: ``dirname(__file__)``

    Refers to the directory name of the Inyoka module. Do not override this
    option unless you know what you are doing. **All** paths are constructed by
    this value.

.. py:data:: DEFAULT_HOST

    Defaults to: ``'portal'``

.. py:data:: LOCALE_PATHS

    Defaults to: ``(join(BASE_PATH, 'locale'),)``

.. py:data:: MEDIA_ROOT

    Defaults to: ``join(BASE_PATH, 'media')``

    Absolute path to the directory that holds media and the URL.

.. py:data:: MEDIA_URL

    Defaults to: ``'http://media.%s' % BASE_DOMAIN_NAME``

.. py:data:: ROOT_HOSTCONF

    Defaults to: ``'inyoka.hosts'``

    Host conf for subdomain dispatching

.. py:data:: ROOT_URLCONF

    Defaults to: ``'inyoka.portal.urls'``

    This URL conf is used for contrib stuff like the auth system

.. py:data:: SESSION_COOKIE_DOMAIN

    Defaults to: ``'.ubuntuusers.de'``

.. py:data:: STATIC_ROOT

    Defaults to: ``join(BASE_PATH, 'static-collected')``

.. py:data:: STATIC_URL

    Defaults to: ``'http://static.%s' % BASE_DOMAIN_NAME``

.. py:data:: STATICFILES_DIRS

    Defaults to::

        (
            join(BASE_PATH, 'static'),
        )

.. py:data:: XAPIAN_DATABASE

    Defaults to: ``join(BASE_PATH, 'inyoka.xapdb')``

    Path to the Xapian database. Examples: ``/path/to/inyoka.xapdb``, or ``tcpsrv://localhost:3000/``

Security
========

.. py:data:: GOOGLE_MAPS_APIKEY

    Defaults to: ``''``

    Key for google maps

.. py:data:: OPENID_PROVIDERS

    Defaults to::

        {
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

.. py:data:: SECRET_KEY

    Defaults to: ``'b)l0ju3erxs)od$g&l_0i1za^l+2dwgxuay(nwv$q4^*c#tdwt'``

    Make this unique, and don't share it with anybody.

.. py:data:: USE_ETAGS

    Defaults to: ``True``

    Use etags

Search
======

.. py:data:: SEARCH_DEFAULT_EXCLUDE

    Defaults to: ``[]``

    Some terms to exclude by default to maintain readability

.. py:data:: SEARCH_INDEX_BLOCKSIZE

    Defaults to: ``5000``

    Default blocksize to delmit queries to the search index


..

    .. py:data:: ADMINS

        Defaults to: ``()``

    .. py:data:: IMAGEMAGICK_PATH

        Defaults to: ``''``

        Imagemagick path. Leave empty for auto detection

    .. py:data:: INTERNAL_IPS

        Defaults to: ``('127.0.0.1',)``

    .. py:data:: MANAGERS

        Defaults to: ``()``

    .. py:data:: SEND_EVENTS

        Defaults to: ``True``

    .. py:data:: SOUTH_TESTS_MIGRATE

        Defaults to: ``False``

        Don't use migrations but just syncdb

    .. py:data:: __all__

        Defaults to: ``list(x for x in locals() if x.isupper())``

        Export only uppercase keys
