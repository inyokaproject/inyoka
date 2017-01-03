import json
import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from guardian.shortcuts import assign_perm

from inyoka.forum.models import Forum
from inyoka.portal.user import Group


# portal permissions offsets, 17 is unused
permission_portal = {
    "ikhaya.change_article" : 1, # article_edit
    "ikhaya.change_category" : 2, # category_edit
    "portal.change_event" : 3, # event_edit
    "ikhaya.change_comment" : 4, # comment_edit
    "planet.change_blog" : 5, # blog_edit
    "portal.change_storage" : 6, # configuration_edit
    "portal.change_staticpage" : 7, # static_page_edit
    "portal.change_staticpage" : 8, # markup_css_edit
    "portal.change_staticfile" : 9, # static_file_edit
    "portal.change_user" : 10, # user_edit
    "auth.change_group" : 11, # group_edit
    "portal.send_group_privatemessage" : 12, # send_group_pm
    "forum.change_forum" : 13, # forum_edit
    "forum.manage_reported_topic" : 14, # manage_topics
    "forum.delete_topic_forum" : 15, # delete_topic
    "ikhaya.view_unpublished_article" : 16, # article_read
    "pastebin.change_entry" : 18, # manage_pastebin
    "portal.subscribe_user" : 19 # subscribe_to_users
}


# forum permissions offsets
privileges_forum = {
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
    help = "Import all old Inyoka permissions from the specified JSON files"

    def add_arguments(self, parser):
        parser.add_argument('--file_portal',
            action="store",
            dest="portal_perms",
            # required=True, # would make sense, but breaks the test
            help="JSON file to read from for portal permissions")
        parser.add_argument('--file_forum',
            action="store",
            dest="forum_perms",
            # required=True, # would make sense, but breaks the test
            help="JSON file to read from for forum permissions")
        

    def handle(self, **options):
        """
        Method description
        """
        
        file_portal = open(options['portal_perms'])
        file_forum = open(options['forum_perms'])
        
        # portal permissions
        
        data_portal = json.load(file_portal)
        
        for group_perms in data_portal:
            group = Group.objects.get(id=group_perms["id"])
            self.stdout.write("%s" % (group.name))

            perms = group_perms["permissions"]
            
            for key,value in perms.items():
                if value:
                    self.stdout.write("    %s" % (key))
                    assign_perm(key, group)

        # forum permissions

        data_forum = json.load(file_forum)
        
        for forum_perms in data_forum:
            forum = Forum.objects.get(id=forum_perms["id"])
            
            self.stdout.write("%s" % (forum.name))
            
            for group_perms in forum_perms["groups"]:
                group = Group.objects.get(id=group_perms["id"])
                
                self.stdout.write("    %s" % (group.name))
                
                perms = group_perms["permissions"]
            
                for key,value in perms.items():
                    if value:
                        self.stdout.write("        %s" % (key))
                        assign_perm(key, group, forum)
