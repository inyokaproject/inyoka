from django.core.management.base import NoArgsCommand
from inyoka.utils.search import search as search_system, autodiscover
autodiscover()


class Command(NoArgsCommand):
    help = "Reindexes everything into elasticsearch"

    def handle_noargs(self, **options):
        search_system.reindex()
