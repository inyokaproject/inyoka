# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Group'
        db.create_table('portal_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80)),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('permissions', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('portal', ['Group'])

        # Adding model 'User'
        db.create_table('portal_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=50)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow)),
            ('new_password_key', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('banned_until', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('avatar', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('jabber', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('icq', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
            ('msn', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('aim', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('yim', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('skype', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('wengophone', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('sip', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('signature', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('coordinates_long', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('coordinates_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('gpgkey', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('occupation', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('interests', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('launchpad', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('_settings', self.gf('django.db.models.fields.TextField')(default='(d.')),
            ('_permissions', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('forum_last_read', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('forum_read_status', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('forum_welcome', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('member_title', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('_primary_group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='primary_users_set', null=True, db_column='primary_group_id', to=orm['portal.Group'])),
        ))
        db.send_create_signal('portal', ['User'])

        # Adding M2M table for field groups on 'User'
        db.create_table('portal_user_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm['portal.user'], null=False)),
            ('group', models.ForeignKey(orm['portal.group'], null=False))
        ))
        db.create_unique('portal_user_groups', ['user_id', 'group_id'])

        # Adding model 'SessionInfo'
        db.create_table('portal_sessioninfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('last_change', self.gf('django.db.models.fields.DateTimeField')()),
            ('subject_text', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('subject_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('subject_link', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('action_link', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
        ))
        db.send_create_signal('portal', ['SessionInfo'])

        # Adding model 'PrivateMessage'
        db.create_table('portal_privatemessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('portal', ['PrivateMessage'])

        # Adding model 'PrivateMessageEntry'
        db.create_table('portal_privatemessageentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.PrivateMessage'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
            ('read', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('folder', self.gf('django.db.models.fields.SmallIntegerField')(null=True)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('portal', ['PrivateMessageEntry'])

        # Adding model 'StaticPage'
        db.create_table('portal_staticpage', (
            ('key', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=25, primary_key=True, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('portal', ['StaticPage'])

        # Adding model 'StaticFile'
        db.create_table('portal_staticfile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('is_ikhaya_icon', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('portal', ['StaticFile'])


        # Adding model 'Event'
        db.create_table('portal_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('changed', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('time', self.gf('django.db.models.fields.TimeField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('location_town', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('location_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('location_long', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('duration', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('portal', ['Event'])

        # Adding model 'SearchQueue'
        db.create_table('portal_searchqueue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('component', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('doc_id', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('portal', ['SearchQueue'])

        # Adding model 'Storage'
        db.create_table('portal_storage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('portal', ['Storage'])


    def backwards(self, orm):

        # Deleting model 'Group'
        db.delete_table('portal_group')

        # Deleting model 'User'
        db.delete_table('portal_user')

        # Removing M2M table for field groups on 'User'
        db.delete_table('portal_user_groups')

        # Deleting model 'SessionInfo'
        db.delete_table('portal_sessioninfo')

        # Deleting model 'PrivateMessage'
        db.delete_table('portal_privatemessage')

        # Deleting model 'PrivateMessageEntry'
        db.delete_table('portal_privatemessageentry')

        # Deleting model 'StaticPage'
        db.delete_table('portal_staticpage')

        # Deleting model 'StaticFile'
        db.delete_table('portal_staticfile')

        # Deleting model 'Event'
        db.delete_table('portal_event')

        # Deleting model 'SearchQueue'
        db.delete_table('portal_searchqueue')

        # Deleting model 'Storage'
        db.delete_table('portal_storage')


    models = {
        'portal.event': {
            'Meta': {'object_name': 'Event'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'duration': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'portal.group': {
            'Meta': {'object_name': 'Group'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'portal.privatemessage': {
            'Meta': {'object_name': 'PrivateMessage'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'portal.privatemessageentry': {
            'Meta': {'object_name': 'PrivateMessageEntry'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
        },
        'portal.searchqueue': {
            'Meta': {'object_name': 'SearchQueue'},
            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'portal.sessioninfo': {
            'Meta': {'object_name': 'SessionInfo'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'last_change': ('django.db.models.fields.DateTimeField', [], {}),
            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'portal.staticfile': {
            'Meta': {'object_name': 'StaticFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'portal.staticpage': {
            'Meta': {'object_name': 'StaticPage'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'portal.storage': {
            'Meta': {'object_name': 'Storage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
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
        },
    }

    complete_apps = ['portal']
