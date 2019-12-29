"""
    inyoka.wiki.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~

    Contains custom exceptions used in our wiki.


    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


class CaseSensitiveException(Exception):
    """
    Raised when a specific page is requested which does not exist, but an
    wiki page exist with another case.
    """
    def __init__(self, page, *args, **kwargs):
        self.page = page
        super(CaseSensitiveException, self).__init__(*args, **kwargs)


class CircularRedirectException(Exception):
    """
    Raised when a sequence of redirects becomes circular.
    """
