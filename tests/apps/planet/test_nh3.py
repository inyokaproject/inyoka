"""
tests.apps.planet.test_nh3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basic tests for nh3 usage.

:copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from urllib.parse import urlparse

import nh3

from inyoka.utils.test import TestCase


class TestNh(TestCase):
    def test_tags_stripped(self):
        title = """<h1 class="entry-title"><a class="entry-link" href="https://www.example.org/t/t-42/" title="t 42 veröffentlicht">t 42 veröffentlicht</a></h1>"""
        title = nh3.clean(title, tags=set())
        self.assertEqual(title, 't 42 veröffentlicht')

    def test_planet_cleaner(self):
        from inyoka.planet.tasks import planet_cleaner

        title = """<h1 class="entry-title"><a class="entry-link" href="https://www.example.org/t/t-42/" title="t 42 veröffentlicht">t 42 veröffentlicht</a></h1>"""
        title = planet_cleaner().clean(title)
        self.assertEqual(
            title,
            """<h1><a href="https://www.example.org/t/t-42/" title="t 42 veröffentlicht" rel="noopener noreferrer">t 42 veröffentlicht</a></h1>""",
        )

    def test_url_parse(self):
        o = urlparse(
            'http://docs.python.org:80/3/library/urllib.parse.html?'
            'highlight=params#url-parsing'
        )

        self.assertEqual(o.scheme, 'http')
        self.assertEqual(o.hostname, 'docs.python.org')

        o = urlparse('https://www.example.org/feed/')
        self.assertEqual(o.scheme, 'https')
        self.assertEqual(o.hostname, 'www.example.org')

        o = urlparse('https://foo@www.example.org/feed/')
        self.assertEqual(o.scheme, 'https')
        self.assertEqual(o.hostname, 'www.example.org')
