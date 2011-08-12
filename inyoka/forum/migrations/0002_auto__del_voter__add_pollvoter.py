# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding index on 'Post', fields ['position']
        db.create_index('forum_post', ['position'])

        # Adding index on 'Post', fields ['pub_date']
        db.create_index('forum_post', ['pub_date'])

        # Adding index on 'Forum', fields ['slug']
        db.create_index('forum_forum', ['slug'])

        # Adding index on 'Topic', fields ['slug']
        db.create_index('forum_topic', ['slug'])

        # Adding index on 'Topic', fields ['sticky']
        db.create_index('forum_topic', ['sticky'])


    def backwards(self, orm):

        # Removing index on 'Topic', fields ['sticky']
        db.delete_index('forum_topic', ['sticky'])

        # Removing index on 'Topic', fields ['slug']
        db.delete_index('forum_topic', ['slug'])

        # Removing index on 'Forum', fields ['slug']
        db.delete_index('forum_forum', ['slug'])

        # Removing index on 'Post', fields ['pub_date']
        db.delete_index('forum_post', ['pub_date'])

        # Removing index on 'Post', fields ['position']
        db.delete_index('forum_post', ['position'])


    models = {
        'forum.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'file': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Post']", 'null': 'True', 'blank': 'True'})
        },
        'forum.forum': {
            'Meta': {'object_name': 'Forum'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'force_version': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Post']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'newtopic_default_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Forum']", 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'post_count': ('django.db.models.fields.IntegerField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'topic_count': ('django.db.models.fields.IntegerField', [], {}),
            'user_count_posts': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'welcome_message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Welcomemessage']", 'null': 'True', 'blank': 'True'})
        },
        'forum.poll': {
            'Meta': {'object_name': 'Poll'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'multiple_votes': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topic']", 'null': 'True', 'blank': 'True'})
        },
        'forum.polloption': {
            'Meta': {'object_name': 'Polloption'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Poll']"}),
            'votes': ('django.db.models.fields.IntegerField', [], {})
        },
        'forum.voter': {
            'Meta': {'object_name': 'Voter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Poll']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
        },
        'forum.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
            'has_revision': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_plaintext': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'rendered_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Topic']"})
        },
        'forum.postrevision': {
            'Meta': {'object_name': 'Postrevision'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Post']"}),
            'store_date': ('django.db.models.fields.DateTimeField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'forum.privilege': {
            'Meta': {'object_name': 'Privilege'},
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Forum']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'positive': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']", 'null': 'True', 'blank': 'True'})
        },
        'forum.topic': {
            'Meta': {'object_name': 'Topic'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topics'", 'to': "orm['portal.User']"}),
            'first_post': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'topic_set'", 'null': 'True', 'to': "orm['forum.Post']"}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Forum']"}),
            'has_poll': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_post': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'topic_set2'", 'null': 'True', 'to': "orm['forum.Post']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {}),
            'report_claimed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'claimed_topics'", 'null': 'True', 'to': "orm['portal.User']"}),
            'reported': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reported_topics'", 'null': 'True', 'to': "orm['portal.User']"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'solved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ubuntu_distro': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'forum.welcomemessage': {
            'Meta': {'object_name': 'Welcomemessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rendered_text': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        'portal.group': {
            'Meta': {'object_name': 'Group'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'portal.user': {
            'Meta': {'object_name': 'User'},
            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
            '_settings': ('django.db.models.fields.TextField', [], {'default': "'(d.'"}),
            'aim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50'}),
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
            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sip': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'skype': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'wengophone': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'yim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['forum']
