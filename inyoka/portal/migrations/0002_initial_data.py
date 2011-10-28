# encoding: utf-8
import datetime
from south.v2 import DataMigration

now = datetime.datetime.utcnow

DEFAULT_STORAGE_VALUES = {
    'global_message':           '',
    'max_avatar_width':         80,
    'max_avatar_height':        100,
    'max_signature_length':     400,
    'max_signature_lines':      4,
    'get_ubuntu_link':          '',
    'get_ubuntu_description':   '8.04 „Hardy Heron“',
    'blocked_hosts': '',
    'max_avatar_size':          30,
    'team_icon': '',
    'team_icon_height': 28,
    'team_icon_width': 38,
    'markup_styles': '',
    # move to forum
    'reported_topics_subscribers': '',
    # move to wiki
    'wiki_newpage_template':    u'',
    'wiki_newpage_root':        'Baustelle',
    'distri_versions':          '[' \
        '{"number":"4.10","name":"Warty Warthog","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"5.04","name":"Hoary Hedgehog","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"5.10","name":"Breezy Badger","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"6.06","name":"Dapper Drake","lts":"true","active":"false","current":"false","dev":"false"},' \
        '{"number":"6.10","name":"Edgy Eft","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"7.04","name":"Feisty Fawn","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"7.10","name":"Gutsy Gibbon","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"8.04","name":"Hardy Heron","lts":"true","active":"true","current":"false","dev":"false"},' \
        '{"number":"8.10","name":"Intrepid Ibex","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"9.04","name":"Jaunty Jackalope","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"9.10","name":"Karmic Koala","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"10.04","name":"Lucid Lynx","lts":"true","active":"true","current":"false","dev":"false"},' \
        '{"number":"10.10","name":"Maverick Meerkat","lts":"false","active":"false","current":"false","dev":"false"},' \
        '{"number":"11.04","name":"Natty Narwhal","lts":"false","active":"true","current":"false","dev":"false"},' \
        '{"number":"11.10","name":"Oneiric Ocelot","lts":"false","active":"true","current":"true","dev":"false"},' \
        '{"number":"12.04","name":"Precise Pangolin","lts":"false","active":"false","current":"false","dev":"true"}]',
}


class Migration(DataMigration):

    def forwards(self, orm):
        orm.Group.objects.get_or_create(name='Registriert', is_public=False)
        orm.User.objects.get_or_create(username='anonymous', defaults={
            'email': 'anonymous@ubuntuusers.de', 'password': '!',
            'status': 1, 'last_login': now(), 'date_joined': now(),
            'post_count': 0, '_settings': '(dp1\n.', 'forum_last_read': 0})
        orm.User.objects.get_or_create(username='ubuntuusers.de', defaults={
            'email': 'system@ubuntuusers.de', 'password': '!', 'status': 1,
            'last_login': now(), 'date_joined': now(),
            '_settings': '(dp1\n.'})

        for key,value in DEFAULT_STORAGE_VALUES.items():
            orm.Storage.objects.create(key=key, value=value)

    def backwards(self, orm):
        orm.Group.objects.filter(name='Registriert').delete()
        orm.Storage.objects.filter(key__in=DEFAULT_STORAGE_VALUES.keys()).delete()
        orm.Storage.objects.all().delete()
        orm.User.objects.filter(username__in=['ubuntuusers.de','anonymous']).delete()


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
