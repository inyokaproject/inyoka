# Inyoka

The inyoka portal system is divided into multiple modules
to which we refer as applications. The name inyoka means “snake” in
zulu and was chosen because it's a python application 🤓.

Although the software is based on django, it uses (sometimes, mostly for legacy reasons)
different idioms and the non standard template engine Jinja. The basic
application structure is explained below.

## Build states

Master&nbsp;[![Build Status Master](https://ci.ubuntu-de.org/buildStatus/icon?job=inyokaproject-github/inyoka/master)](https://ci.ubuntu-de.org/job/inyokaproject-github/inyoka/master) &emsp;
Staging&nbsp;[![Build Status Staging](https://ci.ubuntu-de.org/buildStatus/icon?job=inyokaproject-github/inyoka/staging)](https://ci.ubuntu-de.org/job/inyokaproject-github/inyoka/staging) &emsp;
Testing&nbsp;[![Build Status Testing](https://ci.ubuntu-de.org/buildStatus/icon?job=inyokaproject-github/inyoka/testing)](https://ci.ubuntu-de.org/job/inyokaproject-github/inyoka/testing)

## Requirements

We're using the recent LTS django releases. Django and all python-requirements
can be installed with `pip`.

The code is mostly tested with the database PostgreSQL but should work with SQLite or
any other database Django supports. The preferred caching system is redis.

## Installation & Configuration

See in the documentation the files “installation” and “getting_started”.

## Applications of Inyoka

The following applications are part of inyoka so far:

 * `portal` The index application. It resides on no subdomain and is the portal page.
    It aggregates for example the recent ikhaya posts.

 * `forum`
    The forum component. It's inspired by phpBB2 which was previously
    used on the German ubuntuusers.de webpage. Some of the functionality
    was extended over time though. Especially an improved notification
    system, attachments and subforums.

 * `wiki`
    Moin inspired wiki engine. It's not as advanced as moin but
    has revisioned pages and a parser which can safely generate XML
    based output formats. The wiki parser also has some
    BBCode elements for compatibility with the old phpBB syntax and is
    used in other components (`forum`, `ikhaya`, …) as well.

 * `planet`
    A planet like feed aggregator. It has archives and sanitized
    input data thanks to feedparser.

 * `ikhaya`
    Ikhaya is zulu for `home` and a blog application. It's used on the
    German ubuntuusers portal for site wide announcements and other news.
    It doesn't show up on the planet automatically, for that you have to
    add the ikhaya feed to it like any other blog.

 * `pastebin`
    A pastebin that uses Pygments for highlighting. It does not support
    diffing yet but allows to download pastes.
