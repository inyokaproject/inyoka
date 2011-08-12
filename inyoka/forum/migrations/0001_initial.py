# encoding: utf-8
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    depends_on = (
        ('portal', '0001_initial'),
    )

    def forwards(self, orm):

        # Adding model 'Welcomemessage'
        db.create_table('forum_welcomemessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('rendered_text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('forum', ['Welcomemessage'])

        # Adding model 'Forum'
        db.create_table('forum_forum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Forum'], null=True, blank=True)),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
            ('last_post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'], null=True, blank=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')()),
            ('topic_count', self.gf('django.db.models.fields.IntegerField')()),
            ('welcome_message', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Welcomemessage'], null=True, blank=True)),
            ('newtopic_default_text', self.gf('django.db.models.fields.TextField')(blank=True, null=True)),
            ('user_count_posts', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('force_version', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('forum', ['Forum'])

        # Adding model 'Topic'
        db.create_table('forum_topic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Forum'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('view_count', self.gf('django.db.models.fields.IntegerField')()),
            ('post_count', self.gf('django.db.models.fields.IntegerField')()),
            ('sticky', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('solved', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('locked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('reported', self.gf('django.db.models.fields.TextField')(blank=True, null=True)),
            ('reporter', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='reported_topics', null=True, to=orm['portal.User'])),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('ubuntu_version', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True, null=True)),
            ('ubuntu_distro', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True, null=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_topics', to=orm['portal.User'])),
            ('first_post', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='topic_set', null=True, to=orm['forum.Post'])),
            ('last_post', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='topic_set2', null=True, to=orm['forum.Post'])),
            ('has_poll', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('report_claimed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='claimed_topics', null=True, to=orm['portal.User'])),
        ))
        db.send_create_signal('forum', ['Topic'])

        # Adding model 'Post'
        db.create_table('forum_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Topic'])),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('rendered_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('has_revision', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_plaintext', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('forum', ['Post'])

        # Adding model 'Attachment'
        db.create_table('forum_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'], null=True, blank=True)),
            ('mimetype', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('forum', ['Attachment'])

        # Adding model 'Poll'
        db.create_table('forum_poll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Topic'], null=True, blank=True)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('multiple_votes', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('forum', ['Poll'])

        # Adding model 'Polloption'
        db.create_table('forum_polloption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Poll'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('votes', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('forum', ['Polloption'])

        # Adding model 'Postrevision'
        db.create_table('forum_postrevision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Post'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('store_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('forum', ['Postrevision'])

        # Adding model 'Privilege'
        db.create_table('forum_privilege', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.Group'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'], null=True, blank=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Forum'])),
            ('positive', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('negative', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('forum', ['Privilege'])

        # Adding model 'Voter'
        db.create_table('forum_voter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('voter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
            ('poll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['forum.Poll'])),
        ))
        db.send_create_signal('forum', ['Voter'])


    def backwards(self, orm):

        # Deleting model 'Welcomemessage'
        db.delete_table('forum_welcomemessage')

        # Deleting model 'Forum'
        db.delete_table('forum_forum')

        # Deleting model 'Topic'
        db.delete_table('forum_topic')

        # Deleting model 'Post'
        db.delete_table('forum_post')

        # Deleting model 'Attachment'
        db.delete_table('forum_attachment')

        # Deleting model 'Poll'
        db.delete_table('forum_poll')

        # Deleting model 'Polloption'
        db.delete_table('forum_polloption')

        # Deleting model 'Postrevision'
        db.delete_table('forum_postrevision')

        # Deleting model 'Privilege'
        db.delete_table('forum_privilege')

        # Deleting model 'Voter'
        db.delete_table('forum_voter')


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
            'newtopic_default_text': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Forum']", 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'post_count': ('django.db.models.fields.IntegerField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
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
        'forum.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
            'has_revision': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_plaintext': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
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
            'reported': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reported_topics'", 'null': 'True', 'to': "orm['portal.User']"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'solved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ubuntu_distro': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True', 'null': 'True'}),
            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True', 'null': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'forum.voter': {
            'Meta': {'object_name': 'Voter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Poll']"}),
            'voter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
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
