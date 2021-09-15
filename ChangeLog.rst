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


Unreleased 0.27.0 (2021-MM-DD)
=====================

✨ New features
---------------

🏗 Changes
----------

* `Replace jenkins with github actions as CI <https://github.com/inyokaproject/inyoka/pull/1222>`_
* `Use django's PasswordResetView and PasswordResetConfirmView <https://github.com/inyokaproject/inyoka/pull/1135>`_
* `Add ircs as an supported protocol for InterWiki links <https://github.com/inyokaproject/inyoka/pull/1221>`_
* `Markup: Use unicode for rendering an anchor <https://github.com/inyokaproject/inyoka/pull/1226>`_

🗑 Deprecations
--------------

🔥 Removals
-----------

* `Wiki does not accept case insensitive urls (only lowercase) <https://github.com/inyokaproject/inyoka/commit/ede22624226c79b6ae346acc5796459e6348a1cf>`_
* `Remove global socket timeout of inyoka <https://github.com/inyokaproject/inyoka/commit/bb46af6d68facf0389b225f3905cf021555794b5>`_

🐛 Fixes
--------

* `Forum: Raise 404, if forum-slug for markread is not found <https://github.com/inyokaproject/inyoka/pull/1220>`_

🔒 Security
-----------

* `Update requirements (django, django-guardian, django-filter, django-hosts, django-redis, werkzeug, django-debug-toolbar, jinja2, allure-behave, python-magic, gunicorn, lxml, pygments, urllib3, Replace raven with sentry-sdk) <https://github.com/inyokaproject/inyoka/pull/1196/>`_
