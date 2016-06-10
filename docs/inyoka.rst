.. _inyoka:

======
Inyoka
======

About
=====

The Inyoka portal system. The system is devided into multiple modules to which
we refer as applications. The name Inyoka means *snake* in `Zulu
<http://zu.wiktionary.org/wiki/snake>`_ and was chosen because it's a Python
application.

Although the software is based on Django we use different idoms and a non
standard template engine called Jinja. The basic application structure is
explained below.

Components
==========

The following applications are part of Inyoka so far:

Forum
-----

The forum component. It's inspired by `phpBB2 <http://www.phpbb.com/>`_ which
was previously used on the German ubuntuusers.de webpage. Some of the
functionallity was extended over time though. Especially an improved
notification system, attachments and subforums (latter new in Inyoka)

Ikhaya
------

Ikhaya is Zulu for `home <http://glosbe.com/zu/en/ikhaya>`_ and a blog
application. It's used on the German ubuntuusers portal for site wide
annoucements and other news. It doesn't show up on the planet automatically,
for that you have to add the ikhaya feed to it like for any other blog too.

Pastebin
--------

A pastebin that uses `Pygments <http://pygments.org/>`_ for highlighting.  It
does not support diffing yet but allows to download pastes.

Planet
------

A planet planet like feed aggregator. It has archives and santized input data
thanks to feedparser.

Portal
------

The index application. On no subdomain and the portal page. Aggregates recent
ikhaya posts and similar stuff. Also shows the number of online users.

Wiki
----

`MoinMoin <http://moinmo.in/>`_ inspired wiki engine. It's not yet as advanced
as moin 1.7 but has revisioned pages and a better parser which can savely
generate XML based output formats. The wiki parser also has some BBCode
elements for compatibility with the old phpBB syntax and is used in other
components (`forum`, `ikhaya`, ...) as well.

References
==========

.. toctree::
    :maxdepth: 2

    ref/core/index
    ref/forum/index
    ref/ikhaya/index
    ref/markup/index
    ref/middlewares/index
    ref/pastebin/index
    ref/planet/index
    ref/portal/index
    ref/utils/index
    ref/wiki/index
