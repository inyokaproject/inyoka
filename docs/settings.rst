.. _settings:

========
Settings
========

Inyoka is highly configurable. The following list shows the most important setting
variables. To use them, add the following line into your script::

    from django.conf import setttings

Every configuration directive can be overridden by using a custom settings file
(see ``example_development_settings.py``) and setting the
``DJANGO_SETTINGS_MODULE`` environment variable:

.. code-block:: console

    $ export DJANGO_SETTINGS_MODULE="settings"

Any settings variable that is shown in the `Django settings documentation
<https://docs.djangoproject.com/en/2.2/ref/settings/>`_ can be used.

The development, test and production configuration files should start with::

    from inyoka.default_settings import *

This file is not referenced by the application code itself which means
that you can import it as part of the Django setup without causing
circular bootstrapping dependencies.

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

    The caches that will be used by Inyoka and Django. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#caches

.. py:data:: DATABASES

    Defaults to::

        {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'database.db',
            },
        }

    Defines the available databases. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#databases

.. py:data:: DEBUG

    Defaults to: ``False``

    Enable or disable debugging. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#DEBUG

.. py:data:: DEBUG_PROPAGATE_EXCEPTIONS

    Defaults to: ``False``

    Enable or disable Django to push exceptions to a higher level. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#debug-propagate-exceptions

.. py:data:: FILE_UPLOAD_HANDLERS

    Defaults to::

        (
            'django.core.files.uploadhandler.MemoryFileUploadHandler',
        )

    We only allow uploads via memory up to 2.5mb and do not stream into
    temporary files. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#file-upload-handlers


Installation settings
=====================

Forum
-----

.. py:data:: FORUM_LIMIT_UNREAD

    Defaults to: ``100``

.. py:data:: FORUM_OWNPOST_DELETE_LIMIT

    Defaults to: ``(0, 0)``

    Time in seconds after posting a user is allowed to delete his own posts,
    for posts (w/o, w/) replies. -1 for infinitely, 0 for never

.. py:data:: FORUM_OWNPOST_EDIT_LIMIT

    Defaults to: ``(-1, 1800)``

    Time in seconds after posting a user is allowed to edit his own posts, for
    posts (w/o, w/) replies. -1 for infinitely, 0 for never

.. py:data:: FORUM_THUMBNAIL_SIZE

    Defaults to: ``(64, 64)``

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

.. py:data:: ANONYMOUS_USER_NAME

    Defaults to: ``'anonymous'``

.. py:data:: INYOKA_CONTACT_EMAIL

    Defaults to: ``'contact@example.com'``

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: INYOKA_SYSTEM_USER

    Defaults to: ``'example.com'``

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: INYOKA_SYSTEM_USER_EMAIL

    Defaults to: ``'system@example.com'``

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: USER_INACTIVE_DAYS

    Defaults to: ``365``

    Days to describe an inactive user

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

    The page below we have our templates. The template the user specifies in
    the macro or in the parser is then joined with this page name according to
    our weird joining rules

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

.. py:data:: SENTRY_SITE

    Defaults to: ``'example.com'``

    Set the default sentry site

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

Notification
============

.. py:data:: DEBUG_NOTIFICATIONS

    Defaults to: ``False``

    Print a short message to STDOUT for each notification that is send by mail.

.. py:data:: EMAIL_BACKEND

    Defaults to: ``'inyoka.utils.mail.SendmailEmailBackend'``

    See https://docs.djangoproject.com/en/2.2/ref/settings/#email-backend

.. py:data:: EMAIL_SUBJECT_PREFIX

    Defaults to: ``'example.com: '``

    Prefix for the system mails

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: JABBER_BOT_SERVER

    Defaults to: ``'tcp://127.0.0.1:6203'``

    Settings for the jabber bot


Paths and URLs
==============

.. py:data:: BASE_DOMAIN_NAME

    Defaults to: ``'example.com'``

    The base URL (without subdomain)

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: BASE_PATH

    Defaults to: ``dirname(__file__)``

    Refers to the directory name of the Inyoka module. In case the
    ``__init__.py`` file is at ``~/inyoka/inyoka/__init__.py``, this refers to
    ``~/inyoka/inyoka/``. Do not override this option unless you know what you
    are doing. **All** paths are constructed by this value.

.. py:data:: DEFAULT_HOST

    Defaults to: ``'portal'``

.. py:data:: LOCALE_PATHS

    Defaults to: ``('~/inyoka/inyoka/locale',)``

    See https://docs.djangoproject.com/en/2.2/ref/settings/#locale-paths

    .. seealso:: :py:data:`BASE_PATH`

.. py:data:: MEDIA_ROOT

    Defaults to: ``'~/inyoka/inyoka/media'``

    Absolute path to the directory that holds media and the URL. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#media-root

    .. seealso:: :py:data:`BASE_PATH`

.. py:data:: MEDIA_URL

    Defaults to: ``'http://media.example.com'``

    See https://docs.djangoproject.com/en/2.2/ref/settings/#media-url

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: ROOT_HOSTCONF

    Defaults to: ``'inyoka.hosts'``

    Host conf for subdomain dispatching

.. py:data:: ROOT_URLCONF

    Defaults to: ``'inyoka.portal.urls'``

    This URL conf is used for contrib stuff like the auth system. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#root-urlconf

.. py:data:: SESSION_COOKIE_DOMAIN

    Defaults to: ``'.example.com'``

    See
    https://docs.djangoproject.com/en/2.2/ref/settings/#session-cookie-domain

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

.. py:data:: STATIC_ROOT

    Defaults to: ``'~/inyoka/inyoka/static-collected'``

    See https://docs.djangoproject.com/en/2.2/ref/settings/#static-root

    .. seealso:: :py:data:`BASE_PATH`

.. py:data:: STATIC_URL

    Defaults to: ``'http://static.example.com'``

    See https://docs.djangoproject.com/en/2.2/ref/settings/#static-url

    .. seealso:: :py:data:`BASE_DOMAIN_NAME`

Security
========

.. py:data:: SECRET_KEY

    Defaults to: ``None``

    Make this unique, and don't share it with anybody. See
    https://docs.djangoproject.com/en/2.2/ref/settings/#secret-key

..
    .. py:data:: INTERNAL_IPS

        Defaults to: ``('127.0.0.1',)``

    .. py:data:: __all__

        Defaults to: ``list(x for x in locals() if x.isupper())``

        Export only uppercase keys
