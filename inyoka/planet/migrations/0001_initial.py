# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    depends_on = (
        ('portal', '0001_initial'),
    )

    def forwards(self, orm):

        # Adding model 'Blog'
        db.create_table('planet_blog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('blog_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('feed_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('icon', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('last_sync', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
        ))
        db.send_create_signal('planet', ['Blog'])

        # Adding model 'Entry'
        db.create_table('planet_entry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blog', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['planet.Blog'])),
            ('guid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('author_homepage', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('planet', ['Entry'])


    def backwards(self, orm):

        # Deleting model 'Blog'
        db.delete_table('planet_blog')

        # Deleting model 'Entry'
        db.delete_table('planet_entry')


    models = {
        'planet.blog': {
            'Meta': {'object_name': 'Blog'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blog_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'feed_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        'planet.entry': {
            'Meta': {'object_name': 'Entry'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'author_homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['planet.Blog']"}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['planet']
