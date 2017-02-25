import json
import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from guardian.shortcuts import assign_perm

from inyoka.forum.models import Forum
from inyoka.portal.user import Group



class Command(BaseCommand):
    help = "Set default Inyoka permissions for anonymous"
        

    def handle(self, **options):
        """
        Method description
        """


        # delete no longer needed groups
        
        delete_groups = ["Autor des Monats","no-hinterzimmer","no-lounge","no-unstable","no-wiki","UWR-Team","Vereinsvorsitz"]
         
        for group_name in delete_groups:
            self.stdout.write("Deleting %s" % (group_name))
            Group.objects.filter(name=group_name).delete()
            
            
        # add some new permissions
        
        group_names = ["Projektleitung","Moderatoren","Webteam"]
        for group_name in group_names:
            self.stdout.write("Assigning default perms for group %s" % (group_name))
            group = Group.objects.get(name=group_name)
            assign_perm("pastebin.change_entry", group)


        # default forum permissions
        
        forum_id_list = [5,6,7,8,10,13,14,18,20,23,26,27,28,29,33,36,46,47,48,51,52,53,54,56,57,58,60,61,63,66,67,68,69,70,72,73,74,76,77,79,86,87,89,92,93,98]
        anonymous = Group.objects.get(name="anonymous")
        
        for forum_id in forum_id_list:
            forum = Forum.objects.get(id=forum_id)
            self.stdout.write("Adding permissions for anonymous for forum %s" % (forum.name))
            assign_perm("forum.view_forum", anonymous, forum)
            
        
