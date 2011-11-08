# -*- coding: utf-8 -*-
"""
    inyoka
    ~~~~~~

    The inyoka portal system.  The system is devided into multiple modules
    to which we refer as applications.  The name inyoka means "snake" in
    zulu and was chosen because it's a python application *cough*.

    Although the software is based on django we use different idoms and a
    non standard template engine called Jinja.  The basic application
    structure is explained below.


    Requirements
    ============

    The code is mostly tested with MySQL but should work with PostgreSQL,
    SQLite or any other database Django supports.

    Additionally Jinja 2.5 or higher is required as well as xapian for the
    full text search facilities.  For the planet application the feedparser
    library must be installed.  Additionally chardet is recommended so that
    it can better guess broken encodings of feeds.  For the pastebin, wiki and
    some other parts `pygments` 1.4 or higher must be available.
    MySQL must support InnoDB or any other transaction engine like falcon
    (untested though).  For incoming HTML data that is converted to XHTML
    we also need html5lib.
    To let the inyoka services run (required) you need also simplejson.

    We're using the recent stable django releases.

    For deployment memcached is the preferred caching system.  Otherwise use
    many threads and few processes and enable `locmem`.


    Configuration
    =============

    The default configuration the development, test and production
    configuration files should start import is in `inyoka.default_settings`.
    This file is not referenced by the application code itself which means
    that you can import it as part of the django setup without causing
    circular bootstrapping dependencies.


    Quickstart
    ==========

    To get inyoka running you have to install the dependencies and then create
    a ``development_settings.py`` in the root folder, next to the example
    settings file.  It could look like that::

        from example_development_settings import *

        DATABASE_NAME = 'inyoka'
        DATABASE_USER = 'root'
        XAPIAN_DATABASE = '/home/user/dev/inyoka/inyoka.xapdb'

    After that all you have to do before working with inyoka is sourcing the
    `init.sh` file (``source init.sh`` or ``. init.sh``).

    Then you can use the Makefile which provides comments for resetting the
    database, starting the server, building the documentation etc.  For more
    details have a look at the Makefile.


    Contents
    ========

    The following applications are part of inyoka so far:

    `portal`
        The index application.  On no subdomain and the portal page.
        Aggregates recent ikhaya posts and similar stuff.  Also shows the
        number of online users.

    `forum`
        The forum component.  It's inspired by phpBB2 which was previously
        used on the German ubuntuusers.de webpage.  Some of the functionallity
        was extended over time though.  Especially an improved notification
        system, attachments and subforums (latter new in inyoka)

    `wiki`
        Moin inspired wiki engine.  It's not yet as advanced as moin 1.7 but
        has revisioned pages and a better parser which can savely generate XML
        based output formats.  The wiki parser also has some
        BBCode elements for compatibility with the old phpBB syntax and is
        used in other components (`forum`, `ikhaya`, ...) as well.

    `planet`
        A planet planet like feed aggregator.  It has archives and santized
        input data thanks to feedparser.

    `ikhaya`
        Ikhaya is zulu for `home` and a blog application.  It's used on the
        German ubuntuusers portal for site wide annoucements and other news.
        It doesn't show up on the planet automatically, for that you have to
        add the ikhaya feed to it like for any other blog too.

    `pastebin`
        A pastebin that uses Pygments for highlighting.  It does not support
        diffing yet but allows to download pastes.


    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import socket
from os.path import realpath, join, dirname
import subprocess

#: Inyoka revision present in the current mercurial working copy
INYOKA_REVISION = 'unknown'


def _dummy(*args, **kwargs):
    return None


def _bootstrap():
    """Get the Inyoka version and store it."""
    # the path to the contents of the Inyoka module
    conts = realpath(join(dirname(__file__)))

    # get the `INYOKA_REVISION` using git subprocess.
    # TODO: once the git-ctypes port is finished switch!

    try:
        process = subprocess.Popen(['git', 'describe', '--tags'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=conts, shell=False,
                                   env=os.environ.copy())
        revision, stderro = process.communicate()
    except Exception:
        revision = INYOKA_REVISION

    revision = revision.strip()

    # This value defines the timeout for sockets in seconds.  Per default
    # python sockets do never timeout and as such we have blocking workers.
    # Socket timeouts are set globally within the whole application.
    # The value *must* be a floating point value.
    socket.setdefaulttimeout(10.0)

    # Silence logging output of openid library
    from openid import oidutil
    oidutil.log = _dummy

    return revision


INYOKA_REVISION = _bootstrap()
del _bootstrap
