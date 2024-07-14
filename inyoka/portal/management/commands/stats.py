"""
    inyoka.portal.management.commands.stats
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file that outputs some statistics about the portal.
    In some time in the future, these should be converted to a proper view.

    :copyright: (c) 2011-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import TruncYear

from inyoka.portal.user import User


class Command(BaseCommand):
    help = "Outputs some statistics about the portal"

    def last_logins_grouped_by_year(self):
        query = (User.objects.annotate(year=TruncYear('last_login')).values('year')
                 .annotate(c=Count('id')).values('year', 'c').order_by('year'))

        for e in query:
            print(e['year'], e['c'])

    def handle(self, **options):
        self.last_logins_grouped_by_year()
