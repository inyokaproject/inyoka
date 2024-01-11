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


0.31.0 (2024-01-XX)
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
