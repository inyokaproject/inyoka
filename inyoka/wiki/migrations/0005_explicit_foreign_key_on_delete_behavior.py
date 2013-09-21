# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Revision.text'
        db.alter_column(u'wiki_revision', 'text_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['wiki.Text']))

        # Changing field 'Revision.user'
        db.alter_column(u'wiki_revision', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['portal.User']))

        # Changing field 'Revision.page'
        db.alter_column(u'wiki_revision', 'page_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['wiki.Page']))

        # Changing field 'Revision.attachment'
        db.alter_column(u'wiki_revision', 'attachment_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Attachment'], null=True, on_delete=models.PROTECT))

        # Changing field 'Page.topic'
        db.alter_column(u'wiki_page', 'topic_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Topic'], null=True, on_delete=models.PROTECT))

        # Changing field 'Page.last_rev'
        db.alter_column(u'wiki_page', 'last_rev_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.PROTECT, to=orm['wiki.Revision']))

    def backwards(self, orm):

        # Changing field 'Revision.text'
        db.alter_column(u'wiki_revision', 'text_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Text']))

        # Changing field 'Revision.user'
        db.alter_column(u'wiki_revision', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['portal.User']))

        # Changing field 'Revision.page'
        db.alter_column(u'wiki_revision', 'page_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Page']))

        # Changing field 'Revision.attachment'
        db.alter_column(u'wiki_revision', 'attachment_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Attachment'], null=True))

        # Changing field 'Page.topic'
        db.alter_column(u'wiki_page', 'topic_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Topic'], null=True))

        # Changing field 'Page.last_rev'
        db.alter_column(u'wiki_page', 'last_rev_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['wiki.Revision']))

    models = {
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
        },
        u'wiki.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'wiki.metadata': {
            'Meta': {'object_name': 'MetaData'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wiki.Page']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '512', 'db_index': 'True'})
        },
        u'wiki.page': {
            'Meta': {'ordering': "['name']", 'object_name': 'Page'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_rev': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['wiki.Revision']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['forum.Topic']", 'null': 'True', 'on_delete': 'models.PROTECT'})
        },
        u'wiki.revision': {
            'Meta': {'ordering': "['-change_date']", 'object_name': 'Revision'},
            'attachment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wiki.Attachment']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'change_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'on_delete': 'models.PROTECT', 'to': u"orm['wiki.Page']"}),
            'remote_addr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'text': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'on_delete': 'models.PROTECT', 'to': u"orm['wiki.Text']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wiki_revisions'", 'null': 'True', 'on_delete': 'models.PROTECT', 'to': u"orm['portal.User']"})
        },
        u'wiki.text': {
            'Meta': {'object_name': 'Text'},
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40', 'db_index': 'True'}),
            'html_render_instructions': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['wiki']