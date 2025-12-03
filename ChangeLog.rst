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

Unreleased 1.52.4 (2025-MM-DD)
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
* Update requirements


1.52.3 (2025-12-02)
===================

Deployment notes
----------------
#. Update requirements

🔒 Security
-----------
* Update requirements due to high security issue in ``Django``


1.52.2 (2025-11-05)
===================

Deployment notes
----------------
#. Update requirements

🔒 Security
-----------
* Update requirements due to high security issue in ``Django``


1.52.1 (2025-09-14)
===================

Deployment notes
----------------
#. Update requirements
#. Execute database migrations (``python manage.py migrate``)


🏗 Changes
----------
* Add Cinnamon and Ubuntu Studio to distro select in Forum


🐛 Fixes
--------
* Create a wiki index page via a database migration, if it does not exist already
* Ikhaya, NewEventForm: Fix sever error, if location-longitude or location-lattitude was missing
* Add missing translations

🔒 Security
-----------
* Update requirements (at least the dependencies ``Django``, ``pillow``  and ``requests`` include a known security fix)


1.52.0 (2025-06-01)
===================

Deployment notes
----------------

#. Update requirements
#. Execute database migrations

🏗 Changes
----------

* Reworked ``MetaFilter`` in wiki to yield more accurate results
* Use HTML ``<summary>`` and ``<details>`` instead of own JS collapse
* Remove ``python-dateutil`` as direct dependency of Inyoka (still needed by dependencies ``celery`` and ``icalendar``)
* Captcha: Fix spacing of renew button
* Modernize javascript: Use const and let, refactor & remove unused logic
* Use django 5.2 and celery 5.5

🔥 Removals
-----------

* Ikhaya: Remove assign/unassgin functionality via JavaScript (now uses only server side implementation)
* Remove ability to toggle admin links
* Remove sidebar hide functionality

🐛 Fixes
--------

* Planet, sync task: Skip blog on ``IncompleteRead``
* Forum: Dont show a dialog to prevent leaving the page, if the split-checkbox is ticked
* Use AnonymousUser for bad request template to avoid an exception
* Make ikhaya article suggestions deleteable again
* Prevent to delete blog including posts, if linked user is deleted
* Wiki: Do not require a change comment to press the cancel button (For this, the button is replaced by a link to the wiki page)

🔒 Security
-----------

* Rework captcha: the captcha image is now send via HTML (inline, base64 decoded) Instead of storing the solution into the session (for Inyoka by default a cookie), the solution is saved in the server-side cache.
* Use django's signer for the activation key (it still used sha1. Furthermore, the key had no time expiration.)
* Fix redirect of some views
* Update requirements (at least the dependency ``Django`` includes a known security fix)


1.42.2 (2025-03-07)
===================

Deployment notes
----------------

#. Update requirements
#. Execute database migrations

✨ New features
---------------
* Wiki: Update metadata and content of related pages after a edit

🏗 Changes
----------
* ``*.pot`` files are no longer in git
* Enable timezon-aware datetimes from Django
* Fix deprecation warnings related to UTC methods
* Remove private messages after specific duration. This will not affect messages in the 'archive' folder and team members.
* Event: Slug is changed for unpublished events
* Forum, Topic: Make slug unique which creates an index and fasten look ups

🔥 Removals
-----------
* Replace javascript based datetime picker with native HTML one

🐛 Fixes
--------
* Planet: Fix export
* Planet: Fix suggestion for a new blog
* Login: Allow to enter long email adress
* Events: Fix discrepancy between times displayed in forms and rendered on page

🔒 Security
-----------

* Update requirements (at least the dependencies ``Django`` and ``jinja2`` includes known security fixes)


1.42.1 (2025-02-16)
===================

🔒 Security
-----------

* Prevent to leak posts via `__service__=forum.get_new_latest_posts`


1.42.0 (2024-11-23)
===================

Deployment notes
----------------

#. Update requirements


🏗 Changes
----------

* Migrate from bump2version to bump-my-version
* Rework to use more of Django's logic for templates
* Build requirement files for all supported Python versions (for the time being: Python 3.9, 3.10, 3.11, 3.12)
* Added more tests for portal view
* Wiki sidebar: Link to a seperate wiki page to incorrect articles (before the backlink-page of templates was used)

🐛 Fixes
--------

* Calendar: Localize some missed strings in the HTML
* Documentation: Update installation requirements
* Page 'About Inyoka': Update after OSS release, fix old URLs and localize the page

🔒 Security
-----------

* Update requirements (at least the dependency ``lxml-html-clean`` includes known security fixes)


1.0.1 (2024-10-20)
==================

🏗 Changes
----------
* Add contribution guideline

🐛 Fixes
--------
* Fix domain for download-link to not point to inyokaproject.org


1.0.0 (2024-10-13)
==================

Deployment notes
----------------

#. Update requirements

🏗 Changes
----------

* Add default theme based on ubuntuusers theme to the inyoka repository
* Migrate from ``setup.py`` to ``pyproject.toml``
* Introduce ruff for code formatting
* Render ``<mark>`` for highlighted text
* Control characters are stripped from all HTTP-POST parameters
* Documentation: Now possible to use Markdown
* Documentation is now published at https://doc.inyokaproject.org/
* Use Django's view and form for change password
* Restrict user defineable font faces: Only ``[font=Arial]``, ``[font=serif]``, ``[font=sans-serif]`` and ``[font=Courier]`` are allowed
* Disallow ``<color>`` and ``<font>`` in signatures
* InyokaMarkup: Extend filtering of control characters
* InyokaMarkup: Remove empty paragraphs in generated HTML
* InyokaMarkup: Dont split up long links in HTML-markup (instead rely on CSS)
* Table of contents: Dont strip long heading text

🔥 Removals
-----------

* Remove unused javascript on register and for escaping

🐛 Fixes
--------

* Splittopic form: Fix maximum length for title of new topic
* Forum posts & Ikhaya comments can now start with a list (space is preserved)

🔒 Security
-----------

* Add ``SECURITY.md``
* Update requirements (at least the dependency ``Django`` includes known security fixes)
* Markup, Edited-/Mod boxes: Escape parameters to prevent HTML injection
* Templates: Escape more user-controllable variables to prevent HTML injections

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
