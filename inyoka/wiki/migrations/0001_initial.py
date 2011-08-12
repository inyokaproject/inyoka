# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    depends_on = (
        ('portal', '0001_initial'),
        ('forum', '0001_initial'),
    )

    def forwards(self, orm):

        # Adding model 'Text'
        db.create_table('wiki_text', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=40)),
            ('html_render_instructions', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('wiki', ['Text'])

        # Adding model 'Page'
        db.create_table('wiki_page', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('topic_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal('wiki', ['Page'])

        # Adding model 'Attachment'
        db.create_table('wiki_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('wiki', ['Attachment'])

        # Adding model 'Revision'
        db.create_table('wiki_revision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['wiki.Page'])),
            ('text', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['wiki.Text'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='wiki_revisions', null=True, to=orm['portal.User'])),
            ('change_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('remote_addr', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('attachment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Attachment'], null=True, blank=True)),
        ))
        db.send_create_signal('wiki', ['Revision'])

        # Adding model 'MetaData'
        db.create_table('wiki_metadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Page'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=512)),
        ))
        db.send_create_signal('wiki', ['MetaData'])


    def backwards(self, orm):

        # Deleting model 'Text'
        db.delete_table('wiki_text')

        # Deleting model 'Page'
        db.delete_table('wiki_page')

        # Deleting model 'Attachment'
        db.delete_table('wiki_attachment')

        # Deleting model 'Revision'
        db.delete_table('wiki_revision')

        # Deleting model 'MetaData'
        db.delete_table('wiki_metadata')


    models = {
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
        },
        'wiki.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'wiki.metadata': {
            'Meta': {'object_name': 'MetaData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Page']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'wiki.page': {
            'Meta': {'object_name': 'Page'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'topic_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'wiki.revision': {
            'Meta': {'object_name': 'Revision'},
            'attachment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Attachment']", 'null': 'True', 'blank': 'True'}),
            'change_date': ('django.db.models.fields.DateTimeField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['wiki.Page']"}),
            'remote_addr': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'text': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['wiki.Text']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wiki_revisions'", 'null': 'True', 'to': "orm['portal.User']"})
        },
        'wiki.text': {
            'Meta': {'object_name': 'Text'},
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'html_render_instructions': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['wiki']
