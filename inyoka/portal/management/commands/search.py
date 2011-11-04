from optparse import make_option
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Search for something"

    option_list = BaseCommand.option_list + (
        make_option('-i', '--indices', action='store',
                    default=None, dest='indices'),
    )

    def handle(self, *args, **options):
        from inyoka.utils.search import search as search_system
        indices = filter(None, (options.get('indices', ) or '').split(','))
        result = search_system.search(u' '.join(*args), search_system.get_indices(*indices))
        print "Hits Total: %s" % result.total
        print "Hits: \n\n%s" % result.hits
