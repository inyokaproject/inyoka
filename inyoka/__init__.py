# -*- coding: utf-8 -*-
"""
    inyoka
    ~~~~~~

    Init file for the inyoka portal.

    :copyright: (c) 2007-2021 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
# Secure XML libraries till a python solution exists.
import defusedxml
defusedxml.defuse_stdlib()
import xml
assert xml.sax.make_parser is defusedxml.sax.make_parser
# End XML patching.


from .celery_app import app as celery_app  # noqa
import socket

# Set a global socket timeout to avoid blocking worker processes:
socket.setdefaulttimeout(10.0)

# Inyoka version is updated through bumpversion and can stay hardcoded here.
INYOKA_VERSION = "v0.24.5"
