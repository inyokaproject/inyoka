.. _general:

Inyoka
======

**If possible, please read the**
`pretty version (select the newest build, download the artifact 'Inyoka_Documentation') <https://github.com/inyokaproject/inyoka/actions?query=branch%3Astaging>`_.


The Inyoka portal system is divided into multiple modules to which we
refer as applications. The name Inyoka means “snake” in
`zulu <http://zu.wiktionary.org/wiki/snake>`_ and was chosen because
it’s a Python application 🤓.

Although the software is based on `Django <https://www.djangoproject.com/>`_,
it uses (sometimes and mostly for legacy reasons) different idioms and the non
standard template engine `Jinja <https://palletsprojects.com/p/jinja/>`_.
The basic application structure is explained below.

Build states
------------

Master |Build Status Master|   Staging |Build Status Staging|   Testing |Build Status Testing|

Requirements
------------

We’re using the recent LTS Django releases. Django and all
python-requirements can be installed with ``pip``.

The code is mostly tested with the database PostgreSQL. Theoretically,
most functions should work with SQLite or any other database Django
supports. The preferred caching system is redis.

Installation & Configuration
----------------------------

See :ref:`installation` and :ref:`getting-started`.

Applications of Inyoka
----------------------

The following applications are part of Inyoka so far:

`portal`
   The index application. It resides on no subdomain and is
   the portal page. It aggregates for example the recent ikhaya posts.

`forum`
   The forum component. It’s inspired by
   `phpBB2 <http://www.phpbb.com/>`_ which was previously used on the
   German ubuntuusers.de webpage. Some of the functionality was extended
   over time though. Especially an improved notification system,
   attachments and subforums.

`wiki`
   `MoinMoin <http://moinmo.in/>`_ inspired wiki engine. It’s
   not as advanced as moin but has revisioned pages and a parser which
   can safely generate XML based output formats. The wiki parser also
   has some BBCode elements for compatibility with the old phpBB syntax
   and is used in other components (``forum``, ``ikhaya``, …) as well.

`planet`
   A planet like feed aggregator. It archives and sanitizes
   input data thanks to feedparser.

`ikhaya`
   Ikhaya is zulu for
   `home <http://glosbe.com/zu/en/ikhaya>`_ and a blog application.
   It’s used on the German ubuntuusers portal for site wide
   announcements and other news. It doesn’t show up on the planet
   automatically, for that you have to add the ikhaya feed to it like
   any other blog.

`pastebin`
   A pastebin that uses `Pygments <http://pygments.org/>`_
   for highlighting. It does not support diffing yet but allows to
   download pastes.

.. |Build Status Master| image:: https://github.com/inyokaproject/inyoka/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/inyokaproject/inyoka/actions/workflows/test.yml?query=branch%3Amaster
.. |Build Status Staging| image:: https://github.com/inyokaproject/inyoka/actions/workflows/test.yml/badge.svg?branch=staging
   :target: https://github.com/inyokaproject/inyoka/actions/workflows/test.yml?query=branch%3Astaging
.. |Build Status Testing| image:: https://github.com/inyokaproject/inyoka/actions/workflows/test.yml/badge.svg?branch=testing
   :target: https://github.com/inyokaproject/inyoka/actions/workflows/test.yml?query=branch%3Atesting
