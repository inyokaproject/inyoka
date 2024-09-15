================
Inyoka Changelog
================

..
   Unreleased AA.BB.CC (YYYY-MM-DD)
   =====================

   ✨ New features
   ---------------

   🏗 Changes
   ----------

   🗑 Deprecations
   --------------

   🔥 Removals
   -----------

   🐛 Fixes
   --------

   🔒 Security
   -----------


Unreleased AA.BB.CC (2024-MM-DD)
=====================

Deployment notes
----------------

#. Update requirements

✨ New features
---------------

🏗 Changes
----------

* Add default theme based on ubuntuusers theme to the inyoka repository
* Migrate from ``setup.py`` to ``pyproject.toml``
* Introduce ruff for code formatting
* Render ``<mark>`` for highlighted text

🗑 Deprecations
--------------

🔥 Removals
-----------

* Remove unused javascript on register and for escaping

🐛 Fixes
--------

* Splittopic form: Fix maximum length for title of new topic

🔒 Security
-----------

* Add ``SECURITY.md``


0.36.1 (2024-08-06)
===================

Deployment notes
----------------

#. Update requirements

🔒 Security
-----------

* Update ``Django`` due to a security vulnerability → <https://www.djangoproject.com/weblog/2024/aug/06/security-releases/>

0.36.0 (2024-07-14)
===================

Deployment notes
----------------

#. Update requirements
#. Run migrations
#. Fix CVE-2024-4317 in existing postgresql instances
   (see https://www.postgresql.org/about/news/postgresql-163-157-1412-1315-and-1219-released-2858/)

.. code-block:: console

    $ docker exec -it inyoka_postgres.<Tab> bash

    root@a789607c1d5c:/# psql -U inyoka

    \i /usr/share/postgresql/14/fix-CVE-2024-4317.sql

    \c template1
    \i /usr/share/postgresql/14/fix-CVE-2024-4317.sql

    ALTER DATABASE template0 WITH ALLOW_CONNECTIONS true;
    \c template0
    \i /usr/share/postgresql/14/fix-CVE-2024-4317.sql
    \c template1
    ALTER DATABASE template0 WITH ALLOW_CONNECTIONS false;
    exit;

✨ New features
---------------

* new management commands

  - Portal: Add management command that outputs some statistics
  - Wiki: Add management command to regenerate MetaData

🏗 Changes
----------

* Generate requirements for Python 3.12 as default
* The Docker container now use Python 3.12 which replaces Python 3.9

🔒 Security
-----------

* Update requirements (at least the dependencies ``certifi``, ``Django``, ``Jinja2``, ``requests``, ``urllib3`` include known security fixes)
* Remove deprecated Django password hashers

0.35.0 (2024-05-04)
===================

Deployment notes
----------------

#. Update requirements

✨ New features
---------------

* Use argon2 as default password hasher
* Use Django gzip middleware, so HTML gets compressed (mitigation for the BREACH attack is included in Django)

🏗 Changes
----------

* Update to Django 4.2

  - Replace pytz with zoneinfo

* Basic BDD tests for the planet


0.34.1 (2024-04-20)
===================

Deployment notes
----------------

#. Update requirements

🔒 Security
-----------
* Update ``gunicorn`` to fix a known security issue

0.34.0 (2024-04-06)
===================

Deployment notes
----------------

#. Update requirements

🏗 Changes
----------

* Add documentation for release procedure
* Update requirements (at least the dependency ``Pillow`` includes known security fixes)

🐛 Fixes
--------

* Events: Link to openstreetmap, as geohack seems to be not reachable

0.33.0 (2024-03-09)
===================

Deployment notes
----------------

#. Update requirements
#. Execute database migration

🏗 Changes
----------

* Wiki: Refactor queries for wiki page to be more efficient

🔒 Security
-----------
* Update requirements (at least the dependency ``Django`` includes known security fixes)


0.32.0 (2024-02-16)
===================

Deployment notes
----------------

#. Update requirements
#. Execute database migration

🏗 Changes
----------
* Add index for username in uppercase. This should speed-up the case-insensitive queries (at least on postgreSQL).

🔥 Removals
-----------

* in the Wiki the ``Include`` macro was removed

🐛 Fixes
--------

* Display message instead of server-error, if username was not taken during form-validation at registration, but at DB-insertion
* Strip control characters in Inyoka's markup lexer. This will fix server errors for feeds.

🔒 Security
-----------
* Update requirements (at least the dependencies ``Django`` include known security fixes)

0.31.0 (2024-01-13)
===================

Deployment notes
----------------

#. Update requirements
#. Execute database migration

🏗 Changes
----------

* pyupgrade to modernize the code base a bit
* Refactor feeds to use Django's builtin syndication framework instead of the out-of-support Werkzeug module

🔥 Removals
-----------

* Remove XMPP: XMPP was not used anymore, since it was made an optional dependency.
  The associated database migration will

  - remove not needed user settings
  - remove hidden jabber-ids for privacy, as there is no reason
    to save them anymore (previously, they could be used for
    notifications)

🐛 Fixes
--------

* Fix wiki revision rendering
* Reject NUL byte in URLs
* Fix TypeError in Service Middleware
* Return more HTTP status codes in ikhaya service instead of raising an unhandeled error
* Fix UnboundLocalError in Service Middleware, if there are not exactly two parts given via GET
* LoginForm: Always require a password


🔒 Security
-----------

* Update requirements (at least the dependencies ``Django``, ``Pillow`` and ``jinja2`` include known security fixes)


0.30.0 (2023-10-22)
===================

Deployment notes
----------------

#. Update requirements
#. Execute database migration

🏗 Changes
----------

* Added babel extractor for django templates

🔒 Security
-----------

* Update requirements (at least the dependencies ``certifi``, ``django``, ``urllib3``, ``Pillow``  include known security fixes)


0.29.0 (2023-07-21)
=====================

Deployment notes
----------------

#. Update requirements
#. Run ``python manage.py migrate``

✨ New features
---------------
* `Async markup rendering <https://github.com/inyokaproject/inyoka/pull/1256>`_

🏗 Changes
----------

* Require python 3.9
* Use default django classes for templates
* `Update celery to version 5 <https://github.com/inyokaproject/inyoka/pull/1249>`_
* `Ubuntu Distro Select: Add Ubuntu Unity, Do not allow Ubuntu GNOME for new threads <https://github.com/inyokaproject/inyoka/pull/1264/>`_

🔥 Removals
-----------

🐛 Fixes
--------

* `To delete posts in the forum, permission per forum are used instead of one global permission. The global permisson could not be configured via the webinterface <https://github.com/inyokaproject/inyoka/pull/1267>`_

🔒 Security
-----------

* Update requirements (at least the dependencies ``Pillow``, ``requests``, ``sqlparse``  include known security fixes)

0.28.0 (2022-09-11)
=====================

Deployment notes
----------------

#. Update requirements

✨ New features
---------------

* `Add task to render all wikipages, so they are all in the cache for a faster (first) retrival. <https://github.com/inyokaproject/inyoka/pull/1245>`_

🔥 Removals
-----------

* `Remove Inyoka's custom SendmailEmailBackend. Instead, use the django builtin SMTP backend.  <https://github.com/inyokaproject/inyoka/pull/1243>`_

🐛 Fixes
--------

* `Correct title and breadcumb for sent private messages <https://github.com/inyokaproject/inyoka/pull/1241>`_
* `CI: Build documentation also on PRs <https://github.com/inyokaproject/inyoka/pull/1244>`_

🔒 Security
-----------

* Update requirements (dependency-packages ``lxml`` and ``Pillow`` include known security fixes)

0.27.0 (2022-08-05)
=====================

Deployment notes
----------------

#. Update requirements
#. Adapt sentry-settings in local configuration
#. For development setups: Migrate changes from ``example_development_settings.py`` to local configuration
#. Run ``python manage.py migrate``

🏗 Changes
----------

* `Require python 3.8 <https://github.com/inyokaproject/inyoka/pull/1239>`_
* `Replace jenkins with github actions as CI <https://github.com/inyokaproject/inyoka/pull/1222>`_
* `Use django's PasswordResetView and PasswordResetConfirmView <https://github.com/inyokaproject/inyoka/pull/1135>`_
* `Add ircs as an supported protocol for InterWiki links <https://github.com/inyokaproject/inyoka/pull/1221>`_
* `Markup: Use unicode for rendering an anchor <https://github.com/inyokaproject/inyoka/pull/1226>`_

🔥 Removals
-----------

* `Wiki does not accept case insensitive urls (only lowercase) <https://github.com/inyokaproject/inyoka/commit/ede22624226c79b6ae346acc5796459e6348a1cf>`_
* `Remove global socket timeout of inyoka <https://github.com/inyokaproject/inyoka/commit/bb46af6d68facf0389b225f3905cf021555794b5>`_

🐛 Fixes
--------

* `Forum: Raise 404, if forum-slug for markread is not found <https://github.com/inyokaproject/inyoka/pull/1220>`_
* Planet, Sync: `Continue with next blog on SSLError <https://github.com/inyokaproject/inyoka/commit/254b9295f634c7d9deff782651402307582fbe80>`_, `Fix unicode error <https://github.com/inyokaproject/inyoka/commit/72bfc3fce42ab82f4e28ce1459aef4be865d6b27>`_

🔒 Security
-----------

* `Update requirements (django, django-guardian, django-filter, django-hosts, django-redis, werkzeug, django-debug-toolbar, jinja2, allure-behave, python-magic, gunicorn, lxml, pygments, urllib3, Replace raven with sentry-sdk) <https://github.com/inyokaproject/inyoka/pull/1196/>`_
