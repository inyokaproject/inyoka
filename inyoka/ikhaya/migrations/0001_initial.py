# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    depends_on = (
        ('portal', '0001_initial'),
    )

    def forwards(self, orm):

        # Adding model 'Category'
        db.create_table('ikhaya_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=180)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100, blank=True)),
            ('icon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.StaticFile'], null=True, blank=True)),
        ))
        db.send_create_signal('ikhaya', ['Category'])

        # Adding model 'Article'
        db.create_table('ikhaya_article', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pub_date', self.gf('django.db.models.fields.DateField')()),
            ('pub_time', self.gf('django.db.models.fields.TimeField')()),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='article_set', to=orm['portal.User'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=180)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ikhaya.Category'])),
            ('icon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.StaticFile'], null=True, blank=True)),
            ('intro', self.gf('django.db.models.fields.TextField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('is_xhtml', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('comment_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('comments_enabled', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
        ))
        db.send_create_signal('ikhaya', ['Article'])

        # Adding unique constraint on 'Article', fields ['pub_date', 'slug']
        db.create_unique('ikhaya_article', ['pub_date', 'slug'])

        # Adding model 'Suggestion'
        db.create_table('ikhaya_suggestion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='suggestion_set', to=orm['portal.User'])),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('intro', self.gf('django.db.models.fields.TextField')()),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_suggestion_set', null=True, to=orm['portal.User'])),
        ))
        db.send_create_signal('ikhaya', ['Suggestion'])

        # Adding model 'Comment'
        db.create_table('ikhaya_comment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ikhaya.Article'], null=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('rendered_text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('ikhaya', ['Comment'])


    def backwards(self, orm):

        # Deleting model 'Category'
        db.delete_table('ikhaya_category')

        # Removing unique constraint on 'Article', fields ['pub_date', 'slug']
        db.delete_unique('ikhaya_article', ['pub_date', 'slug'])

        # Deleting model 'Article'
        db.delete_table('ikhaya_article')

        # Deleting model 'Suggestion'
        db.delete_table('ikhaya_suggestion')

        # Deleting model 'Comment'
        db.delete_table('ikhaya_comment')


    models = {
        'ikhaya.article': {
            'Meta': {'unique_together': "(('pub_date', 'slug'),)", 'object_name': 'Article'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'article_set'", 'to': "orm['portal.User']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ikhaya.Category']"}),
            'comment_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'comments_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'icon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.StaticFile']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro': ('django.db.models.fields.TextField', [], {}),
            'is_xhtml': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateField', [], {}),
            'pub_time': ('django.db.models.fields.TimeField', [], {}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'ikhaya.category': {
            'Meta': {'object_name': 'Category'},
            'icon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.StaticFile']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'blank': 'True'})
        },
        'ikhaya.comment': {
            'Meta': {'object_name': 'Comment'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ikhaya.Article']", 'null': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'rendered_text': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'ikhaya.suggestion': {
            'Meta': {'object_name': 'Suggestion'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'suggestion_set'", 'to': "orm['portal.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro': ('django.db.models.fields.TextField', [], {}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_suggestion_set'", 'null': 'True', 'to': "orm['portal.User']"}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'portal.group': {
            'Meta': {'object_name': 'Group'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'portal.staticfile': {
            'Meta': {'object_name': 'StaticFile'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
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

    complete_apps = ['ikhaya']
