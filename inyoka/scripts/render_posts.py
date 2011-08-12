#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    inyoka.scripts.render_posts
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import time
from django.conf import settings
settings.DATABASE_DEBUG = False
from inyoka.forum.models import post_table
from inyoka.utils.database import session
from inyoka.scripts.converter.converter import select_blocks
from inyoka.wiki.parser import RenderContext, parse


def render_posts():
    context = RenderContext(None)
    for post in select_blocks(post_table.select(), max_fails=100):
        if not post.rendered_text and not post.is_plaintext:
            text = parse(post.text, wiki_force_existing=True) \
                .render(context, 'html')
            session.execute(post_table.update(post_table.c.id == post.id, values={
                post_table.c.rendered_text: text
            }))
            session.commit()
            session.flush()
            time.sleep(2)


if __name__ == '__main__':
    render_posts()
