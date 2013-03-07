# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Post.author'
        db.alter_column(u'forum_post', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'], on_delete=models.PROTECT))

        # Changing field 'Post.topic'
        db.alter_column(u'forum_post', 'topic_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['forum.Topic']))

        # Changing field 'Forum.parent'
        db.alter_column(u'forum_forum', 'parent_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['forum.Forum']))

        # Changing field 'Forum.welcome_message'
        db.alter_column(u'forum_forum', 'welcome_message_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.WelcomeMessage'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Forum.last_post'
        db.alter_column(u'forum_forum', 'last_post_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'], null=True, on_delete=models.PROTECT))

        # Changing field 'Topic.forum'
        db.alter_column(u'forum_topic', 'forum_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['forum.Forum']))

        # Changing field 'Topic.first_post'
        db.alter_column(u'forum_topic', 'first_post_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['forum.Post']))

        # Changing field 'Topic.author'
        db.alter_column(u'forum_topic', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['portal.User']))

        # Changing field 'Topic.report_claimed_by'
        db.alter_column(u'forum_topic', 'report_claimed_by_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['portal.User']))

        # Changing field 'Topic.last_post'
        db.alter_column(u'forum_topic', 'last_post_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['forum.Post']))

        # Changing field 'Topic.reporter'
        db.alter_column(u'forum_topic', 'reporter_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['portal.User']))

        # Changing field 'PollVote.voter'
        db.alter_column('forum_voter', 'voter_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'], on_delete=models.PROTECT))

    def backwards(self, orm):

        # Changing field 'Post.author'
        db.alter_column(u'forum_post', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

        # Changing field 'Post.topic'
        db.alter_column(u'forum_post', 'topic_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Topic']))

        # Changing field 'Forum.parent'
        db.alter_column(u'forum_forum', 'parent_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['forum.Forum']))

        # Changing field 'Forum.welcome_message'
        db.alter_column(u'forum_forum', 'welcome_message_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.WelcomeMessage'], null=True))

        # Changing field 'Forum.last_post'
        db.alter_column(u'forum_forum', 'last_post_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'], null=True))

        # Changing field 'Topic.forum'
        db.alter_column(u'forum_topic', 'forum_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Forum']))

        # Changing field 'Topic.first_post'
        db.alter_column(u'forum_topic', 'first_post_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['forum.Post']))

        # Changing field 'Topic.author'
        db.alter_column(u'forum_topic', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

        # Changing field 'Topic.report_claimed_by'
        db.alter_column(u'forum_topic', 'report_claimed_by_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['portal.User']))

        # Changing field 'Topic.last_post'
        db.alter_column(u'forum_topic', 'last_post_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['forum.Post']))

        # Changing field 'Topic.reporter'
        db.alter_column(u'forum_topic', 'reporter_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['portal.User']))

        # Changing field 'PollVote.voter'
        db.alter_column('forum_voter', 'voter_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

    models = {
        u'forum.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'null': 'True', 'to': u"orm['forum.Post']"})
        },
        u'forum.forum': {
            'Meta': {'object_name': 'Forum'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'force_version': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_post': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Post']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'newtopic_default_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'_children'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['forum.Forum']"}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'topic_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user_count_posts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'welcome_message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.WelcomeMessage']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'forum.poll': {
            'Meta': {'object_name': 'Poll'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'multiple_votes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polls'", 'null': 'True', 'to': u"orm['forum.Topic']"})
        },
        u'forum.polloption': {
            'Meta': {'object_name': 'PollOption'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['forum.Poll']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'forum.pollvote': {
            'Meta': {'object_name': 'PollVote', 'db_table': "'forum_voter'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votings'", 'to': u"orm['forum.Poll']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.User']", 'on_delete': 'models.PROTECT'})
        },
        u'forum.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.User']", 'on_delete': 'models.PROTECT'}),
            'has_attachments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_revision': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_plaintext': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'db_index': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow', 'db_index': 'True'}),
            'rendered_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'on_delete': 'models.PROTECT', 'to': u"orm['forum.Topic']"})
        },
        u'forum.postrevision': {
            'Meta': {'object_name': 'PostRevision'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': u"orm['forum.Post']"}),
            'store_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'forum.privilege': {
            'Meta': {'object_name': 'Privilege'},
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Forum']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.Group']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'positive': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.User']", 'null': 'True'})
        },
        u'forum.topic': {
            'Meta': {'object_name': 'Topic'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'on_delete': 'models.PROTECT', 'to': u"orm['portal.User']"}),
            'first_post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['forum.Post']"}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'on_delete': 'models.PROTECT', 'to': u"orm['forum.Forum']"}),
            'has_poll': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['forum.Post']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'report_claimed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['portal.User']"}),
            'reported': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['portal.User']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'ubuntu_distro': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'forum.welcomemessage': {
            'Meta': {'object_name': 'WelcomeMessage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rendered_text': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        u'portal.group': {
            'Meta': {'object_name': 'Group'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'portal.user': {
            'Meta': {'object_name': 'User'},
            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': u"orm['portal.Group']"}),
            'aim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'gpgkey': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': u"orm['portal.Group']"}),
            'icq': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interests': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'launchpad': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'msn': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
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