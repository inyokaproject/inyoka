# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Category.icon'
        db.alter_column(u'ikhaya_category', 'icon_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.StaticFile'], null=True, on_delete=models.SET_NULL))

        # Changing field 'Report.author'
        db.alter_column(u'ikhaya_report', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'], on_delete=models.PROTECT))

        # Changing field 'Suggestion.author'
        db.alter_column(u'ikhaya_suggestion', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['portal.User']))

        # Changing field 'Suggestion.owner'
        db.alter_column(u'ikhaya_suggestion', 'owner_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['portal.User']))

        # Changing field 'Comment.author'
        db.alter_column(u'ikhaya_comment', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'], on_delete=models.PROTECT))

        # Changing field 'Comment.article'
        db.alter_column(u'ikhaya_comment', 'article_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ikhaya.Article'], null=True, on_delete=models.PROTECT))

        # Changing field 'Article.category'
        db.alter_column(u'ikhaya_article', 'category_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ikhaya.Category'], on_delete=models.PROTECT))

        # Changing field 'Article.author'
        db.alter_column(u'ikhaya_article', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(on_delete=models.PROTECT, to=orm['portal.User']))

        # Changing field 'Article.icon'
        db.alter_column(u'ikhaya_article', 'icon_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.StaticFile'], null=True, on_delete=models.SET_NULL))

    def backwards(self, orm):

        # Changing field 'Category.icon'
        db.alter_column(u'ikhaya_category', 'icon_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.StaticFile'], null=True))

        # Changing field 'Report.author'
        db.alter_column(u'ikhaya_report', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

        # Changing field 'Suggestion.author'
        db.alter_column(u'ikhaya_suggestion', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

        # Changing field 'Suggestion.owner'
        db.alter_column(u'ikhaya_suggestion', 'owner_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['portal.User']))

        # Changing field 'Comment.author'
        db.alter_column(u'ikhaya_comment', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

        # Changing field 'Comment.article'
        db.alter_column(u'ikhaya_comment', 'article_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ikhaya.Article'], null=True))

        # Changing field 'Article.category'
        db.alter_column(u'ikhaya_article', 'category_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ikhaya.Category']))

        # Changing field 'Article.author'
        db.alter_column(u'ikhaya_article', 'author_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User']))

        # Changing field 'Article.icon'
        db.alter_column(u'ikhaya_article', 'icon_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.StaticFile'], null=True))

    models = {
        u'ikhaya.article': {
            'Meta': {'ordering': "['-pub_date', '-pub_time', 'author']", 'unique_together': "(('pub_date', 'slug'),)", 'object_name': 'Article'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'article_set'", 'on_delete': 'models.PROTECT', 'to': u"orm['portal.User']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ikhaya.Category']", 'on_delete': 'models.PROTECT'}),
            'comment_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'comments_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'icon': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.StaticFile']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro': ('django.db.models.fields.TextField', [], {}),
            'is_xhtml': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pub_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'pub_time': ('django.db.models.fields.TimeField', [], {}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'ikhaya.category': {
            'Meta': {'object_name': 'Category'},
            'icon': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.StaticFile']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'slug': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '100', 'blank': 'True'})
        },
        u'ikhaya.comment': {
            'Meta': {'object_name': 'Comment'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ikhaya.Article']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.User']", 'on_delete': 'models.PROTECT'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'rendered_text': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'ikhaya.report': {
            'Meta': {'object_name': 'Report'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ikhaya.Article']", 'null': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.User']", 'on_delete': 'models.PROTECT'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'rendered_text': ('django.db.models.fields.TextField', [], {}),
            'solved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'ikhaya.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestion_set'", 'on_delete': 'models.PROTECT', 'to': u"orm['portal.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro': ('django.db.models.fields.TextField', [], {}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_suggestion_set'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['portal.User']"}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'portal.group': {
            'Meta': {'object_name': 'Group'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'portal.staticfile': {
            'Meta': {'object_name': 'StaticFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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

    complete_apps = ['ikhaya']