"""
inyoka.planet.tasks
~~~~~~~~~~~~~~~~~~~

The ``sync`` function should be called periodically to check for new
articles.  It checks whether the last synchronization of a blog is more
than ``PLANET_SYNC_TIME`` ago and updates them.

It'd be ideal if ``sync`` was called every 30 minutes.
See the entry with `'task': 'inyoka.planet.tasks.sync'` in
settings,CELERYBEAT_SCHEDULE to see the time interval.


:copyright: (c) 2007-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import socket
import ssl
import urllib
from copy import deepcopy
from datetime import datetime, timezone
from http.client import IncompleteRead
from urllib.parse import urlparse

import feedparser
import nh3
from celery import shared_task
from django.utils import timezone as dj_timezone
from django.utils.encoding import force_str

from inyoka.planet.models import Blog, Entry
from inyoka.utils.html import cleanup_html
from inyoka.utils.logger import logger


def planet_cleaner():
    planet_tags = deepcopy(nh3.ALLOWED_TAGS)
    planet_tags.add('section')
    planet_tags.add('audio')
    planet_tags.add('source')
    planet_tags.add('video')
    planet_tags.add('track')

    planet_attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    planet_attributes['a'].add('title')

    planet_attributes = planet_attributes | {
        'audio': {'src', 'controls', 'controlslist'},
        'abbr': {'title'},
        'dfn': {'id'},
        'time': {'datetime'},
        'track': {'default', 'kind', 'src', 'srclang'},
        'source': {'src', 'type'},
        'video': {'src', 'controls', 'poster', 'controlslist'},
    }

    def planet_attribute_filter(tag, attr, value):
        blog_domains = Blog.objects.filter(active=True).values_list(
            'blog_url', flat=True
        )
        blog_domains = {urlparse(b).hostname for b in blog_domains}

        if (
            (tag == 'audio' and attr == 'src')
            or (tag == 'img' and attr == 'src')
            or (tag == 'source' and attr == 'src')
            or (tag == 'track' and attr == 'src')
            or (tag == 'video' and attr == 'src')
            or (tag == 'video' and attr == 'poster')
        ):
            domain = urlparse(value).hostname
            if domain not in blog_domains:
                return None

        return value

    return nh3.Cleaner(
        tags=planet_tags,
        attributes=planet_attributes,
        attribute_filter=planet_attribute_filter,
        url_schemes={'http', 'https', 'mailto'},
    )


# set a default timeout. Otherwise, fetching some feeds might cause the script
# to block forever
socket.setdefaulttimeout(20.0)


@shared_task
def sync():
    _sync()


def _sync():
    """
    Performs a synchronization. Articles that are already synchronized aren't
    touched anymore.
    """
    for blog in Blog.objects.filter(active=True):
        logger.debug('syncing blog %s' % blog.name)
        # parse the feed. feedparser.parse will never give an exception
        # but the bozo bit might be defined.

        try:
            feed = feedparser.parse(blog.feed_url)
        except (
            LookupError,
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            ssl.SSLError,
            IncompleteRead,
        ) as e:
            logger.debug('%s on %s' % (repr(e), blog.feed_url))
            continue

        blog_author = feed.get('author') or blog.name
        blog_author_detail = feed.get('author_detail')

        for entry in feed.entries:
            # get the guid. either the id if specified, otherwise the link.
            # if none is available we skip the entry.
            guid = entry.get('id') or entry.get('link')
            if not guid:
                logger.debug(' no guid found, skipping')
                continue

            try:
                old_entry = Entry.objects.get(guid=guid)
            except Entry.DoesNotExist:
                old_entry = None

            # get title, url and text. skip if no title or no text is
            # given. if the link is missing we use the blog link.

            if not entry.get('title_detail'):
                logger.debug(' no title found for %r, skipping' % guid)
                continue

            title = entry.title_detail.get('value') or ''
            title = nh3.clean(title, tags=set())

            url = entry.get('link') or blog.blog_url

            text = (
                'content' in entry and entry.content[0] or entry.get('summary_detail')
            )

            text = cleanup_html(text.get('value'), planet_cleaner())

            if not text:
                logger.debug('no text found for %r, skipping' % guid)
                continue

            # get the pub date and updated date. This is rather complex
            # because different feeds do different stuff
            pub_date = (
                entry.get('published_parsed')
                or entry.get('created_parsed')
                or entry.get('date_parsed')
            )
            updated = entry.get('updated_parsed') or pub_date
            pub_date = pub_date or updated

            # if we don't have a pub_date we skip.
            if not pub_date:
                logger.debug(' no pub_date for %r found, skipping' % guid)
                continue

            # convert the time tuples to datetime objects.
            pub_date = datetime(*pub_date[:6], tzinfo=timezone.utc)
            updated = datetime(*updated[:6], tzinfo=timezone.utc)

            # get the blog author or fall back to blog default.
            author = entry.get('author') or blog_author
            author_detail = entry.get('author_detail') or blog_author_detail
            if not author and author_detail:
                author = author_detail.get('name')
            if not author:
                logger.debug(' no author for entry %r found, skipping' % guid)
            author_homepage = author_detail and author_detail.get('href') or url

            # create a new entry object based on the data collected or
            # update the old one.
            entry = old_entry or Entry()
            for n in (
                'blog',
                'guid',
                'title',
                'url',
                'text',
                'pub_date',
                'updated',
                'author',
                'author_homepage',
            ):
                try:
                    max_length = entry._meta.get_field(n).max_length
                except AttributeError:
                    max_length = None
                if isinstance(locals()[n], str):
                    setattr(entry, n, force_str(locals()[n][:max_length]))
                else:
                    setattr(entry, n, locals()[n])

            entry.save()

        blog.last_sync = dj_timezone.now()
        blog.save()
