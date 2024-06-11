#!/usr/bin/env python
"""
    inyoka.wiki.management.commands.regenerate_metadata
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Allows to regenerate the MetaData for wiki pages with a specific tested tag.

    :copyright: (c) 2007-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from django.core.management.base import BaseCommand

from inyoka.wiki.models import MetaData, Page


class Command(BaseCommand):
    help = "Allows to regenerate the MetaData for wiki pages with a specific tested tag."

    def add_arguments(self, parser):
        parser.add_argument('--tested-tag',
                            action='store',
                            dest='tested_tag',
                            help='Metadata for all wiki pages that have this tested tag will be regenerated.')

    def handle(self, *args, **options):
        to_clean = []
        for d in MetaData.objects.filter(key="getestet", value=options['tested_tag']):
            p = d.page
            print(p)
            p.update_meta()
            to_clean.append(p.name)

        Page.objects.clean_cache(to_clean)

        # drop overview pages from the cache
        Page.objects.get_by_name('Wiki/ungetestet').rev.text.remove_value_from_cache()
        Page.objects.get_by_name('Wiki/nur_getestet_bionic').rev.text.remove_value_from_cache()
