import json
import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from inyoka.forum.models import Privilege, Forum
from inyoka.portal.user import Group, User

# portal permissions offsets
privileges_choices = {
    "forum.view_forum" : 1, # read
    "forum.vote_forum" : 2, # vote
    "forum.add_topic_forum" : 3, # create
    "forum.add_reply_forum" : 4, # reply
    "forum.upload_forum" : 5, # upload
    "forum.poll_forum" : 6, # create_poll
    "forum.sticky_forum" : 7, # sticky
    "forum.moderate_forum" : 8, # moderate
}


class Command(BaseCommand):
    help = "Export all forum group permissions to the specified JSON file"

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file',
            action="store",
            dest="json",
            # required=True, # would make sense, but breaks the test
            help="JSON file to write to")

    def testBit(self, int_value, offset):
        mask = 1 << offset
        return(int_value & mask) != 0

    def handle(self, **options):
        """
        Method description
        """
        
        output_file = options['json']
        if output_file is None:
            self.stderr.write(_(u"No JSON file specified, using stdout..."))
            outstream = sys.stdout
        else:
            outstream = open(output_file, 'w')
            
        all_forums = Forum.objects.all()
        
        data_list = []

        for forum in all_forums:
            forum_privileges = Privilege.objects.filter(forum_id = forum.id, negative = 0, group_id__isnull = False)
            
            data_forum = {}
            
            data_forum["id"] = forum.id
            data_forum["name"] = forum.name
            
            data_forum_groups = []
            
            for privilege in forum_privileges:
                data_group = {}
                data_group["id"] = privilege.group.id
                data_group["name"] = privilege.group.name
            
                data_perms = {}
                
                for priv in privileges_choices:
                    has_permission = self.testBit(privilege.positive, privileges_choices[priv])
                    
                    if priv in data_perms:
                        data_perms[priv] = data_perms[priv] | has_permission
                    else:
                        data_perms[priv] = has_permission
                    
                data_group["permissions"] = data_perms
                
                data_forum_groups.append(data_group)
                
            data_forum["groups"] = data_forum_groups
            
            data_list.append(data_forum)
        
        json.dump(data_list, outstream, indent=4)
