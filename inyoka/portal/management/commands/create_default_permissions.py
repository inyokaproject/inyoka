import json
import sys

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from guardian.shortcuts import assign_perm

from inyoka.forum.models import Forum
from inyoka.portal.user import Group

        
from django.conf import settings


class Command(BaseCommand):
    help = "Set default Inyoka permissions"
        

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
        
        team_group = Group.objects.get(name=settings.INYOKA_TEAM_GROUP_NAME)
        group_names = ["Projektleitung","Moderatoren","Supporter","Webteam","Ikhayateam","Serverteam","Wikiteam"]
        for group_name in group_names:
            group = Group.objects.get(name=group_name)
            
            self.stdout.write("Adding users from group %s to group %s" % (group_name, team_group.name))
            for user in group.user_set.all():
                self.stdout.write("    %s" % (user.username))
                user.groups.add(team_group)
            
        self.stdout.write("Assigning team perms")
        assign_perm("portal.send_group_privatemessage", team_group)
        
        
        group_names = ["Projektleitung","Moderatoren","Webteam"]
        for group_name in group_names:
            self.stdout.write("Assigning default perms for group %s" % (group_name))
            group = Group.objects.get(name=group_name)
            assign_perm("pastebin.change_entry", group)
            assign_perm("pastebin.delete_entry", group)

        
        group_names = ["Projektleitung","Webteam"]
        for group_name in group_names:
            group = Group.objects.get(name=group_name)
            self.stdout.write("Assigning additional perms for group %s" % (group.name))
            assign_perm("auth.add_group", group)
            assign_perm("auth.change_group", group)
            assign_perm("portal.add_user", group)
            
            assign_perm("ikhaya.add_article", group)
            assign_perm("ikhaya.add_category", group)
            assign_perm("ikhaya.add_comment", group)
            assign_perm("ikhaya.add_report", group)
            assign_perm("ikhaya.add_suggestion", group)
            assign_perm("ikhaya.change_article", group)
            assign_perm("ikhaya.change_category", group)
            assign_perm("ikhaya.change_comment", group)
            assign_perm("ikhaya.change_report", group)
            assign_perm("ikhaya.change_suggestion", group)
            assign_perm("ikhaya.delete_article", group)
            assign_perm("ikhaya.delete_category", group)
            assign_perm("ikhaya.delete_comment", group)
            assign_perm("ikhaya.delete_report", group)
            assign_perm("ikhaya.delete_suggestion", group)
            assign_perm("ikhaya.suggest_article", group)
            assign_perm("ikhaya.view_unpublished_article", group)
            assign_perm("portal.add_event", group)
            assign_perm("portal.change_event", group)
            assign_perm("portal.delete_event", group)
            assign_perm("portal.suggest_event", group)
            assign_perm("planet.add_blog", group)
            assign_perm("planet.change_blog", group)
            assign_perm("planet.delete_blog", group)
            assign_perm("planet.suggest_blog", group)
            assign_perm("planet.view_blog", group)
            assign_perm("planet.add_entry", group)
            assign_perm("planet.change_entry", group)
            assign_perm("planet.delete_entry", group)
            assign_perm("planet.hide_entry", group)
            
            assign_perm("forum.change_forum", group)
        
        
        # Permissions for all remaining teams
        
        ikhayateam = Group.objects.get(name="Ikhayateam")
        assign_perm("ikhaya.add_article", ikhayateam)
        assign_perm("ikhaya.add_category", ikhayateam)
        assign_perm("ikhaya.add_comment", ikhayateam)
        assign_perm("ikhaya.add_report", ikhayateam)
        assign_perm("ikhaya.add_suggestion", ikhayateam)
        assign_perm("ikhaya.change_article", ikhayateam)
        assign_perm("ikhaya.change_category", ikhayateam)
        assign_perm("ikhaya.change_comment", ikhayateam)
        assign_perm("ikhaya.change_report", ikhayateam)
        assign_perm("ikhaya.change_suggestion", ikhayateam)
        assign_perm("ikhaya.delete_article", ikhayateam)
        assign_perm("ikhaya.delete_category", ikhayateam)
        assign_perm("ikhaya.delete_comment", ikhayateam)
        assign_perm("ikhaya.delete_report", ikhayateam)
        assign_perm("ikhaya.delete_suggestion", ikhayateam)
        assign_perm("ikhaya.suggest_article", ikhayateam)
        assign_perm("ikhaya.view_unpublished_article", ikhayateam)
        assign_perm("portal.add_event", ikhayateam)
        assign_perm("portal.change_event", ikhayateam)
        assign_perm("portal.delete_event", ikhayateam)
        assign_perm("portal.suggest_event", ikhayateam)
        assign_perm("planet.add_blog", ikhayateam)
        assign_perm("planet.change_blog", ikhayateam)
        assign_perm("planet.delete_blog", ikhayateam)
        assign_perm("planet.suggest_blog", ikhayateam)
        assign_perm("planet.view_blog", ikhayateam)
        assign_perm("planet.add_entry", ikhayateam)
        assign_perm("planet.change_entry", ikhayateam)
        assign_perm("planet.delete_entry", ikhayateam)
        assign_perm("planet.hide_entry", ikhayateam)
        
        moderatorentl = Group.objects.get(name="Teamleitung-Moderatoren")
        assign_perm("forum.change_forum", moderatorentl)
        
        webteam = Group.objects.get(name="Webteam")
        projektleitung = Group.objects.get(name="Projektleitung")
       
        # registered global perms
        
        self.stdout.write("Assigning default perms for group registered")
        registered = Group.objects.get(name=settings.INYOKA_REGISTERED_GROUP_NAME)
        assign_perm("ikhaya.suggest_article", registered)
        assign_perm("pastebin.add_entry", registered)
        assign_perm("portal.suggest_event", registered)
        assign_perm("planet.suggest_blog", registered)

        # default forum permissions
        
        forums_public_id_list = [5,6,7,8,10,13,14,18,20,23,26,27,28,29,33,36,46,47,48,51,52,53,54,56,57,58,60,61,63,66,67,68,69,70,72,73,74,76,77,79,86,87,89,92,93,98]
        
        anonymous = Group.objects.get(name=settings.INYOKA_ANONYMOUS_GROUP_NAME)
        
        self.stdout.write("Adding permissions for anonymous to view paste entries and suggest events")
        assign_perm("pastebin.view_entry", anonymous)
        assign_perm("portal.suggest_event", anonymous)
        
        for forum_id in forums_public_id_list:
            forum = Forum.objects.get(id=forum_id)
            self.stdout.write("Adding permissions for anonymous for forum %s" % (forum.name))
            assign_perm("forum.view_forum", anonymous, forum)
        
        forums_registered_id_list = [1,5,6,7,8,10,13,14,18,20,23,26,27,28,29,33,36,46,47,48,51,52,53,54,56,57,58,60,61,62,63,66,67,68,69,70,72,73,74,76,77,79,86,87,89,90,92,93,98]
        
        for forum_id in forums_registered_id_list:
            forum = Forum.objects.get(id=forum_id)
            self.stdout.write("Adding permissions to delete topic to moderatorentl for forum %s" % (forum.name))
            assign_perm("forum.delete_topic_forum", moderatorentl, forum)
            
        for forum in Forum.objects.all():
            self.stdout.write("Adding permissions to delete topic to webteam and pl for forum %s" % (forum.name))
            assign_perm("forum.delete_topic_forum", webteam, forum)
            assign_perm("forum.delete_topic_forum", projektleitung, forum)
            
