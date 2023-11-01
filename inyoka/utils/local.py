"""
    inyoka.utils.local
    ~~~~~~~~~~~~~~~~~~

    All kinds of request local magic.  This module provides two objects:

    `local`
        a werkzeug local object bound to the current request.

    `current_request`
        A proxy to the current active request object.

    The purpose of this module is to allow functions to access request data
    in the context of a request without explicitly passing the request object.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug import Local, LocalManager


local = Local()
local_manager = LocalManager(local)
current_request = local('request')
