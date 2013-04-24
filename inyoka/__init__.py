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


    :copyright: (c) 2007-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
# Secure XML libraries till a python solution exists.
import defusedxml
defusedxml.defuse_stdlib()
import xml
assert xml.sax.make_parser is defusedxml.sax.make_parser
# End XML patching.
import socket
from distutils.version import LooseVersion as V
from os.path import realpath, join, dirname
from django.utils.translation import ugettext_lazy
from dulwich.repo import Repo

#: Inyoka revision present in the current mercurial working copy
INYOKA_REVISION = ugettext_lazy('unknown')


def _dummy(*args, **kwargs):
    return None


def _bootstrap():
    """Get the Inyoka version and store it."""
    # the path to the contents of the Inyoka module
    repo_path = realpath(join(dirname(__file__), '..'))

    try:
        repo = Repo(repo_path)
        tags = sorted([ref for ref in repo.get_refs() if ref.startswith('refs/tags')],
                      key=lambda obj: V(obj))
        tag = tags[-1][10:].strip()
        commit = repo.head()[:8]
        revision = {'tag': tag, 'commit': commit}
    except Exception:
        revision = {'tag': INYOKA_REVISION, 'commit': ''}

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
