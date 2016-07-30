import json
import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from inyoka.portal.user import Group


# portal permissions offsets, 17 is unused
permission_choices = {
    1 : "ikhaya.change_article", # article_edit
    2 : "ikhaya.change_category", # category_edit
    3 : "portal.change_event", # event_edit
    4 : "ikhaya.change_comment", # comment_edit
    5 : "planet.change_blog", # blog_edit
    6 : "portal.change_storage", # configuration_edit
    7 : "portal.change_staticpage", # static_page_edit
    8 : "portal.change_staticpage", # markup_css_edit
    9 : "portal.change_staticfile", # static_file_edit
    10 : "portal.change_user", # user_edit
    11 : "portal.change_user", # group_edit
    12 : "portal.send_group_privatemessage", # send_group_pm
    13 : "forum.change_forum", # forum_edit
    14 : "forum.manage_reported_topic", # manage_topics
    15 : "forum.delete_topic_forum", # delete_topic
    16 : "ikhaya.view_unpublished_article", # article_read
    18 : "pastebin.change_entry", # manage_pastebin
    19 : "portal.subscribe_user" # subscribe_to_users
}


class Command(BaseCommand):
    help = "Export all portal group permissions to the specified JSON file"

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
        
        all_groups = Group.objects.all()
        
        data_list = []

        for group in all_groups:
            data_group = {}
            
            data_group["id"] = group.id
            data_group["name"] = group.name
            
            data_group_perms = {}
            
            for offset,permission_name in permission_choices.items():
                has_permission = self.testBit(group.permissions, offset)
                
                #self.stdout.write("%s : %s" % (group.name, permission_name))
                
                if permission_name in data_group_perms:
                    data_group_perms[permission_name] = data_group_perms[permission_name] | has_permission
                    #self.stdout.write("Duplicate permission: %s" % (permission_name))
                else:
                    data_group_perms[permission_name] = has_permission
                
            data_group["permissions"] = data_group_perms
            
            data_list.append(data_group)
        
        json.dump(data_list, outstream, indent=4)
