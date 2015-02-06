# -*- coding: utf-8 -*-
import datetime
import os
import os.path as path
import re
import shutil

from django.conf import settings
from django.db import models
from south.db import db
from south.v2 import DataMigration

_new_path_re = re.compile('forum/attachments/\d{2}/\d{2}/')
_attachment_max_length = 100

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        if not os.path.exists(path.join(settings.MEDIA_ROOT, 'forum/attachments_migrate')):
            if os.path.exists(path.join(settings.MEDIA_ROOT, 'forum/attachments')):
                shutil.move(path.join(settings.MEDIA_ROOT, 'forum/attachments'),
                            path.join(settings.MEDIA_ROOT, 'forum/attachments_migrate'))
            # prepare the new folderstructure:
            for i in range(61):
                for j in range(54):
                    p = path.join(settings.MEDIA_ROOT, 'forum/attachments/{0:02d}/{1:02d}'.format(i,j))
                    if not path.exists(p):
                        os.makedirs(p)
        Attachment = orm['forum.attachment']
        second = 0
        kw = 0
        for attachment in Attachment.objects.all():
            new_path = 'forum/attachments/{0:02d}/{1:02d}/'.format(second, kw)
            if _new_path_re.match(attachment.file.name):
                continue
            old_path = attachment.file.name.replace('/attachments/', '/attachments_migrate/')
            if not attachment.post_id: # ignore temp attachments
                continue
            if not path.exists(path.join(settings.MEDIA_ROOT, old_path)):
                print "skipping", attachment.file.name
                continue
            old_name = old_path.split('/')[-1]
            new_path = path.join(new_path, u'%d-%s' % (attachment.post_id, old_name))
            if len(new_path) > _attachment_max_length:
                data = new_path.rsplit('.', 1)
                if len(data) == 2:
                    p, ext = data
                    new_path = p[:_attachment_max_length - 1 - len(ext)] + '.' + ext
                else:
                    new_path = data[0][:_attachment_max_length]
            try:
                shutil.move(path.join(settings.MEDIA_ROOT, old_path),
                            path.join(settings.MEDIA_ROOT, new_path))
            except Exception as e:
                print "%s -> %s %s" % (old_path, new_path, e)
            Attachment.objects.filter(pk=attachment.pk).update(file=new_path)
            if second == 60:
                kw = (kw + 1) % 54
            second = (second + 1) % 61


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'forum.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'null': 'True', 'to': "orm['forum.Post']"})
        },
        'forum.forum': {
            'Meta': {'object_name': 'Forum'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'force_version': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Post']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'newtopic_default_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_children'", 'null': 'True', 'to': "orm['forum.Forum']"}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'topic_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user_count_posts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'welcome_message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.WelcomeMessage']", 'null': 'True', 'blank': 'True'})
        },
        'forum.poll': {
            'Meta': {'object_name': 'Poll'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'multiple_votes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polls'", 'null': 'True', 'to': "orm['forum.Topic']"})
        },
        'forum.polloption': {
            'Meta': {'object_name': 'PollOption'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['forum.Poll']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'forum.pollvote': {
            'Meta': {'object_name': 'PollVote', 'db_table': "'forum_voter'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votings'", 'to': "orm['forum.Poll']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
        },
        'forum.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
            'has_attachments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_revision': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_plaintext': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'db_index': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow', 'db_index': 'True'}),
            'rendered_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['forum.Topic']"})
        },
        'forum.postrevision': {
            'Meta': {'object_name': 'PostRevision'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['forum.Post']"}),
            'store_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'forum.privilege': {
            'Meta': {'object_name': 'Privilege'},
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Forum']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.Group']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'positive': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']", 'null': 'True'})
        },
        'forum.topic': {
            'Meta': {'object_name': 'Topic'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['portal.User']"}),
            'first_post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['forum.Post']"}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': "orm['forum.Forum']"}),
            'has_poll': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['forum.Post']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'report_claimed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['portal.User']"}),
            'reported': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['portal.User']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'ubuntu_distro': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'forum.welcomemessage': {
            'Meta': {'object_name': 'WelcomeMessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rendered_text': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        'portal.group': {
            'Meta': {'object_name': 'Group'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'portal.user': {
            'Meta': {'object_name': 'User'},
            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
            'aim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'gpgkey': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
            'icq': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interests': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'launchpad': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'msn': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sip': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'skype': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'wengophone': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'yim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['forum']
    symmetrical = True
