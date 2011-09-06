from optparse import make_option
from django.core.management.base import BaseCommand
from inyoka.utils.search import search as search_system, autodiscover
autodiscover()


class Command(BaseCommand):
    help = "Reindexes everything into elasticsearch"

    option_list = BaseCommand.option_list + (
        make_option('-i', '--index', action='store',
                    dest='index', default=None),
    )

    def handle(self, *args, **options):
        search_system.reindex(options['index'])
