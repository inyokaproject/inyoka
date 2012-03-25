diff --git a/inyoka/portal/forms.py b/inyoka/portal/forms.py
index 30b0000..d052092 100644
--- a/inyoka/portal/forms.py
+++ b/inyoka/portal/forms.py
@@ -29,13 +29,14 @@ from inyoka.utils.user import is_valid_username, normalize_username
 from inyoka.utils.dates import TIMEZONES
 from inyoka.utils.urls import href, is_safe_domain
 from inyoka.utils.forms import CaptchaField, DateTimeWidget, \
-    HiddenCaptchaField, EmailField, JabberField, validate_signature
+     HiddenCaptchaField, EmailField, JabberField, validate_signature
 from inyoka.utils.local import current_request
 from inyoka.utils.html import escape, cleanup_html
 from inyoka.utils.storage import storage
 from inyoka.utils.sessions import SurgeProtectionMixin
 from inyoka.utils.search import search as search_system
-from inyoka.portal.user import User, UserData, Group
+from inyoka.portal.user import User, UserData, Group, ProfileField, \
+     ProfileCategory
 from inyoka.portal.models import StaticPage, StaticFile
 
 #: Some constants used for ChoiceFields
@@ -312,31 +313,10 @@ class UserCPProfileForm(forms.Form):
     use_gravatar = forms.BooleanField(label=ugettext_lazy(u'Use Gravatar'), required=False)
     email = EmailField(label=ugettext_lazy(u'Email'), required=True)
     jabber = JabberField(label=ugettext_lazy(u'Jabber'), required=False)
-    icq = forms.IntegerField(label=ugettext_lazy(u'ICQ'), required=False,
-                             min_value=1, max_value=1000000000)
-    msn = forms.CharField(label=ugettext_lazy(u'MSN'), required=False)
-    aim = forms.CharField(label=ugettext_lazy(u'AIM'), required=False, max_length=25)
-    yim = forms.CharField(label=ugettext_lazy(u'Yahoo Messenger'), required=False,
-                         max_length=25)
-    skype = forms.CharField(label=ugettext_lazy(u'Skype'), required=False, max_length=25)
-    wengophone = forms.CharField(label=ugettext_lazy(u'WengoPhone'), required=False,
-                                 max_length=25)
-    sip = forms.CharField(label=ugettext_lazy(u'SIP'), required=False, max_length=25)
-    show_email = forms.BooleanField(required=False)
-    show_jabber = forms.BooleanField(required=False)
     signature = forms.CharField(widget=forms.Textarea, label=ugettext_lazy(u'Signature'),
                                required=False)
     coordinates = forms.CharField(label=ugettext_lazy(u'Coordinates (latitude, longitude)'),
                                   required=False)
-    location = forms.CharField(label=ugettext_lazy(u'Residence'), required=False, max_length=50)
-    occupation = forms.CharField(label=ugettext_lazy(u'Job'), required=False, max_length=50)
-    interests = forms.CharField(label=ugettext_lazy(u'Interests'), required=False,
-                                max_length=100)
-    website = forms.URLField(label=ugettext_lazy(u'Website'), required=False)
-    launchpad = forms.CharField(label=ugettext_lazy(u'Launchpad username'), required=False,
-                                max_length=50)
-    gpgkey = forms.RegexField('^(0x)?[0-9a-f]{8}$(?i)', label=ugettext_lazy(u'GPG key'),
-                 max_length=10, required=False)
 
     def __init__(self, *args, **kwargs):
         self.user = kwargs.pop('user')
@@ -450,6 +430,12 @@ class EditUserProfileForm(UserCPProfileForm):
         return username
 
 
+class UserCPAddProfileFieldForm(forms.Form):
+    field = forms.ModelChoiceField(label=_(u'Field'),
+                                   queryset=ProfileField.objects.all())
+    data = forms.CharField(label=_(u'Data'))
+
+
 class EditUserGroupsForm(forms.Form):
     primary_group = forms.CharField(label=ugettext_lazy(u'Primary group'), required=False,
         help_text=ugettext_lazy(u'Will be used to display the team icon'))
@@ -878,6 +864,25 @@ class ConfigurationForm(forms.Form):
         return data[key]
 
 
+class EditProfileFieldForm(forms.Form):
+    title = forms.CharField(label=_(u'Title'))
+    category = forms.ModelChoiceField(label=_(u'Category'),
+                                      queryset=ProfileCategory.objects.all(),
+                                      required=False)
+    new_category = forms.CharField(label=_(u'New Category'), required=False)
+    regex = forms.CharField(label=_(u'RegEx'), help_text=_(u'Regular '
+                            u'expression which restricts the value that users '
+                            u'can enter. Leave empty for no restriction.'),
+                            required=False)
+
+    def clean(self):
+        data = self.cleaned_data
+        if data['category'] and data['new_category']:
+            raise forms.ValidationError(_(u'Please select an existing category '
+                                          u'OR create a new one, but not both.'))
+        return data
+
+
 class EditStyleForm(forms.Form):
     styles = forms.CharField(label=ugettext_lazy(u'Styles'), widget=forms.Textarea(
                              attrs={'rows': 20}), required=False)
diff --git a/inyoka/portal/migrations/0023_auto__add_profiledata__add_profilefield.py b/inyoka/portal/migrations/0023_auto__add_profiledata__add_profilefield.py
new file mode 100644
index 0000000..d44008f
--- /dev/null
+++ b/inyoka/portal/migrations/0023_auto__add_profiledata__add_profilefield.py
@@ -0,0 +1,193 @@
+# -*- coding: utf-8 -*-
+import datetime
+from south.db import db
+from south.v2 import SchemaMigration
+from django.db import models
+
+
+class Migration(SchemaMigration):
+
+    def forwards(self, orm):
+        # Adding model 'ProfileData'
+        db.create_table('portal_profiledata', (
+            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
+            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.User'])),
+            ('profile_field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.ProfileField'])),
+            ('data', self.gf('django.db.models.fields.CharField')(max_length=255)),
+        ))
+        db.send_create_signal('portal', ['ProfileData'])
+
+        # Adding model 'ProfileField'
+        db.create_table('portal_profilefield', (
+            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
+            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
+        ))
+        db.send_create_signal('portal', ['ProfileField'])
+
+    def backwards(self, orm):
+        # Deleting model 'ProfileData'
+        db.delete_table('portal_profiledata')
+
+        # Deleting model 'ProfileField'
+        db.delete_table('portal_profilefield')
+
+    models = {
+        'contenttypes.contenttype': {
+            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
+            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
+        },
+        'portal.event': {
+            'Meta': {'object_name': 'Event'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
+            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
+            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
+            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
+            'endtime': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
+            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '56', 'blank': 'True'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
+            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.group': {
+            'Meta': {'object_name': 'Group'},
+            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
+            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.privatemessage': {
+            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'PrivateMessage'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
+            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'text': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.privatemessageentry': {
+            'Meta': {'ordering': "('_order',)", 'object_name': 'PrivateMessageEntry'},
+            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
+            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profiledata': {
+            'Meta': {'object_name': 'ProfileData'},
+            'data': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.ProfileField']"}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilefield': {
+            'Meta': {'object_name': 'ProfileField'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        },
+        'portal.searchqueue': {
+            'Meta': {'ordering': "['id']", 'object_name': 'SearchQueue'},
+            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
+            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
+        },
+        'portal.sessioninfo': {
+            'Meta': {'object_name': 'SessionInfo'},
+            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
+            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
+            'last_change': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
+            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
+            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
+        },
+        'portal.staticfile': {
+            'Meta': {'object_name': 'StaticFile'},
+            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
+            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.staticpage': {
+            'Meta': {'object_name': 'StaticPage'},
+            'content': ('django.db.models.fields.TextField', [], {}),
+            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
+        },
+        'portal.storage': {
+            'Meta': {'object_name': 'Storage'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
+            'value': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.subscription': {
+            'Meta': {'object_name': 'Subscription'},
+            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
+            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.user': {
+            'Meta': {'object_name': 'User'},
+            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
+            'aim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
+            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
+            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
+            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'gpgkey': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
+            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
+            'icq': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'interests': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'launchpad': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
+            'msn': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
+            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
+            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'profile_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['portal.ProfileField']", 'through': "orm['portal.ProfileData']", 'symmetrical': 'False'}),
+            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
+            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'sip': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'skype': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
+            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
+            'wengophone': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'yim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
+        },
+        'portal.userdata': {
+            'Meta': {'object_name': 'UserData'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        }
+    }
+
+    complete_apps = ['portal']
\ No newline at end of file
diff --git a/inyoka/portal/migrations/0024_default_profile_fields.py b/inyoka/portal/migrations/0024_default_profile_fields.py
new file mode 100644
index 0000000..86b7bd5
--- /dev/null
+++ b/inyoka/portal/migrations/0024_default_profile_fields.py
@@ -0,0 +1,188 @@
+# -*- coding: utf-8 -*-
+import datetime
+from south.db import db
+from south.v2 import DataMigration
+from django.db import models
+
+SERVICES = [u'E-Mail', u'Jabber', u'Beruf', u'Interessen', u'Webseite',
+            u'Launchpad-Name', u'GPG-Schlüssel', u'Wohnort', u'Geburtstag',
+            u'Ubuntu-Version', u'Skype', u'ICQ', u'Twitter', u'Identi.ca',
+            u'Freenode', u'Diaspora', u'Facebook', u'Last.fm', u'Libre.fm']
+class Migration(DataMigration):
+    def forwards(self, orm):
+        """Adds default profile fields.
+
+        Adds the default profile fields as decided in
+        http://forum.ubuntuusers.de/post/2764248/
+
+        """
+        for service in SERVICES:
+            field = orm.ProfileField(title=service)
+            field.save()
+
+    def backwards(self, orm):
+        for field in orm.ProfileField.objects.all():
+            if field.title in SERVICES:
+                field.delete()
+
+    models = {
+        'contenttypes.contenttype': {
+            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
+            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
+        },
+        'portal.event': {
+            'Meta': {'object_name': 'Event'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
+            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
+            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
+            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
+            'endtime': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
+            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '56', 'blank': 'True'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
+            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.group': {
+            'Meta': {'object_name': 'Group'},
+            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
+            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.privatemessage': {
+            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'PrivateMessage'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
+            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'text': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.privatemessageentry': {
+            'Meta': {'ordering': "('_order',)", 'object_name': 'PrivateMessageEntry'},
+            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
+            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profiledata': {
+            'Meta': {'object_name': 'ProfileData'},
+            'data': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.ProfileField']"}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilefield': {
+            'Meta': {'object_name': 'ProfileField'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        },
+        'portal.searchqueue': {
+            'Meta': {'ordering': "['id']", 'object_name': 'SearchQueue'},
+            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
+            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
+        },
+        'portal.sessioninfo': {
+            'Meta': {'object_name': 'SessionInfo'},
+            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
+            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
+            'last_change': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
+            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
+            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
+        },
+        'portal.staticfile': {
+            'Meta': {'object_name': 'StaticFile'},
+            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
+            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.staticpage': {
+            'Meta': {'object_name': 'StaticPage'},
+            'content': ('django.db.models.fields.TextField', [], {}),
+            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
+        },
+        'portal.storage': {
+            'Meta': {'object_name': 'Storage'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
+            'value': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.subscription': {
+            'Meta': {'object_name': 'Subscription'},
+            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
+            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.user': {
+            'Meta': {'object_name': 'User'},
+            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
+            'aim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
+            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
+            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
+            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'gpgkey': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
+            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
+            'icq': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'interests': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'launchpad': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
+            'msn': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
+            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
+            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'profile_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['portal.ProfileField']", 'through': "orm['portal.ProfileData']", 'symmetrical': 'False'}),
+            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
+            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'sip': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'skype': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
+            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
+            'wengophone': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'yim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
+        },
+        'portal.userdata': {
+            'Meta': {'object_name': 'UserData'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        }
+    }
+
+    complete_apps = ['portal']
+    symmetrical = True
diff --git a/inyoka/portal/migrations/0025_new_user_profile.py b/inyoka/portal/migrations/0025_new_user_profile.py
new file mode 100644
index 0000000..9084ed1
--- /dev/null
+++ b/inyoka/portal/migrations/0025_new_user_profile.py
@@ -0,0 +1,221 @@
+# -*- coding: utf-8 -*-
+import datetime
+import json
+from south.db import db
+from south.v2 import DataMigration
+from django.db import models
+
+SERVICES = [u'Beruf', u'Interessen', u'Webseite', u'Launchpad-Name',
+            u'GPG-Schlüssel', u'Wohnort', u'Skype', u'ICQ']
+ATTRS = {
+    u'Beruf': 'occupation',
+    u'Interessen': 'interests',
+    u'Webseite': 'website',
+    u'Launchpad-Name': 'launchpad',
+    u'GPG-Schlüssel': 'gpgkey',
+    u'Wohnort': 'location',
+    u'Skype': 'skype',
+    u'ICQ': 'icq'
+}
+
+class Migration(DataMigration):
+
+    def forwards(self, orm):
+        """Copys the old user profile to the new models."""
+        for user in orm.User.objects.all():
+            user.profile_fields.clear()
+            settings = json.loads(user.settings)
+            for field in orm.ProfileField.objects.all():
+                if field.title in SERVICES:
+                    data = getattr(user, ATTRS[field.title])
+                    if data:
+                        orm.ProfileData(user=user, profile_field=field,
+                                        data=getattr(user, ATTRS[field.title])).save()
+                if field.title == 'E-Mail' and settings.has_key('show_email') \
+                   and settings['show_email'] and user.email:
+                    orm.ProfileData(user=user, profile_field=field,
+                                    data=user.email).save()
+                if field.title == 'Jabber' and settings.has_key('show_jabber') \
+                   and settings['show_jabber'] and user.jabber:
+                    orm.ProfileData(user=user, profile_field=field,
+                                    data=user.jabber).save()
+
+
+    def backwards(self, orm):
+        for user in orm.User.objects.all():
+            for field in orm.ProfileField.objects.all():
+                if field.title in SERVICES:
+                    try:
+                        fields = orm.ProfileData.objects.filter(user=user, profile_field=field)
+                        # the old profile only supported one value per profile
+                        # field, so we might loose some data by migrating backwards
+                        if len(fields) >= 1:
+                            data = fields[0].data
+                        else:
+                            data = ''
+                    except orm.ProfileData.DoesNotExist:
+                        data = ''
+                    setattr(user, ATTRS[field.title], data)
+            user.save()
+
+    models = {
+        'contenttypes.contenttype': {
+            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
+            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
+        },
+        'portal.event': {
+            'Meta': {'object_name': 'Event'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
+            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
+            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
+            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
+            'endtime': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
+            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '56', 'blank': 'True'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
+            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.group': {
+            'Meta': {'object_name': 'Group'},
+            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
+            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.privatemessage': {
+            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'PrivateMessage'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
+            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'text': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.privatemessageentry': {
+            'Meta': {'ordering': "('_order',)", 'object_name': 'PrivateMessageEntry'},
+            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
+            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profiledata': {
+            'Meta': {'object_name': 'ProfileData'},
+            'data': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.ProfileField']"}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilefield': {
+            'Meta': {'object_name': 'ProfileField'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        },
+        'portal.searchqueue': {
+            'Meta': {'ordering': "['id']", 'object_name': 'SearchQueue'},
+            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
+            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
+        },
+        'portal.sessioninfo': {
+            'Meta': {'object_name': 'SessionInfo'},
+            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
+            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
+            'last_change': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
+            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
+            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
+        },
+        'portal.staticfile': {
+            'Meta': {'object_name': 'StaticFile'},
+            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
+            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.staticpage': {
+            'Meta': {'object_name': 'StaticPage'},
+            'content': ('django.db.models.fields.TextField', [], {}),
+            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
+        },
+        'portal.storage': {
+            'Meta': {'object_name': 'Storage'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
+            'value': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.subscription': {
+            'Meta': {'object_name': 'Subscription'},
+            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
+            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.user': {
+            'Meta': {'object_name': 'User'},
+            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
+            'aim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
+            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
+            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
+            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'gpgkey': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
+            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
+            'icq': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'interests': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'launchpad': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
+            'msn': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
+            'occupation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
+            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'profile_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['portal.ProfileField']", 'through': "orm['portal.ProfileData']", 'symmetrical': 'False'}),
+            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
+            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'sip': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'skype': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
+            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
+            'wengophone': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'yim': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
+        },
+        'portal.userdata': {
+            'Meta': {'object_name': 'UserData'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        }
+    }
+
+    complete_apps = ['portal']
+    symmetrical = True
diff --git a/inyoka/portal/migrations/0026_auto__del_field_user_interests__del_field_user_website__del_field_user.py b/inyoka/portal/migrations/0026_auto__del_field_user_interests__del_field_user_website__del_field_user.py
new file mode 100644
index 0000000..c031a26
--- /dev/null
+++ b/inyoka/portal/migrations/0026_auto__del_field_user_interests__del_field_user_website__del_field_user.py
@@ -0,0 +1,262 @@
+# -*- coding: utf-8 -*-
+import datetime
+from south.db import db
+from south.v2 import SchemaMigration
+from django.db import models
+
+
+class Migration(SchemaMigration):
+
+    def forwards(self, orm):
+        # Deleting field 'User.interests'
+        db.delete_column('portal_user', 'interests')
+
+        # Deleting field 'User.website'
+        db.delete_column('portal_user', 'website')
+
+        # Deleting field 'User.wengophone'
+        db.delete_column('portal_user', 'wengophone')
+
+        # Deleting field 'User.yim'
+        db.delete_column('portal_user', 'yim')
+
+        # Deleting field 'User.skype'
+        db.delete_column('portal_user', 'skype')
+
+        # Deleting field 'User.sip'
+        db.delete_column('portal_user', 'sip')
+
+        # Deleting field 'User.launchpad'
+        db.delete_column('portal_user', 'launchpad')
+
+        # Deleting field 'User.gpgkey'
+        db.delete_column('portal_user', 'gpgkey')
+
+        # Deleting field 'User.location'
+        db.delete_column('portal_user', 'location')
+
+        # Deleting field 'User.aim'
+        db.delete_column('portal_user', 'aim')
+
+        # Deleting field 'User.msn'
+        db.delete_column('portal_user', 'msn')
+
+        # Deleting field 'User.icq'
+        db.delete_column('portal_user', 'icq')
+
+        # Deleting field 'User.occupation'
+        db.delete_column('portal_user', 'occupation')
+
+    def backwards(self, orm):
+        # Adding field 'User.interests'
+        db.add_column('portal_user', 'interests',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.website'
+        db.add_column('portal_user', 'website',
+                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.wengophone'
+        db.add_column('portal_user', 'wengophone',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.yim'
+        db.add_column('portal_user', 'yim',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.skype'
+        db.add_column('portal_user', 'skype',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.sip'
+        db.add_column('portal_user', 'sip',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.launchpad'
+        db.add_column('portal_user', 'launchpad',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.gpgkey'
+        db.add_column('portal_user', 'gpgkey',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=8, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.location'
+        db.add_column('portal_user', 'location',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.aim'
+        db.add_column('portal_user', 'aim',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.msn'
+        db.add_column('portal_user', 'msn',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.icq'
+        db.add_column('portal_user', 'icq',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=16, blank=True),
+                      keep_default=False)
+
+        # Adding field 'User.occupation'
+        db.add_column('portal_user', 'occupation',
+                      self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True),
+                      keep_default=False)
+
+    models = {
+        'contenttypes.contenttype': {
+            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
+            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
+        },
+        'portal.event': {
+            'Meta': {'object_name': 'Event'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
+            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
+            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
+            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
+            'endtime': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
+            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '56', 'blank': 'True'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
+            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.group': {
+            'Meta': {'object_name': 'Group'},
+            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
+            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.privatemessage': {
+            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'PrivateMessage'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
+            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'text': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.privatemessageentry': {
+            'Meta': {'ordering': "('_order',)", 'object_name': 'PrivateMessageEntry'},
+            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
+            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profiledata': {
+            'Meta': {'object_name': 'ProfileData'},
+            'data': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.ProfileField']"}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilefield': {
+            'Meta': {'object_name': 'ProfileField'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        },
+        'portal.searchqueue': {
+            'Meta': {'ordering': "['id']", 'object_name': 'SearchQueue'},
+            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
+            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
+        },
+        'portal.sessioninfo': {
+            'Meta': {'object_name': 'SessionInfo'},
+            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
+            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
+            'last_change': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
+            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
+            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
+        },
+        'portal.staticfile': {
+            'Meta': {'object_name': 'StaticFile'},
+            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
+            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.staticpage': {
+            'Meta': {'object_name': 'StaticPage'},
+            'content': ('django.db.models.fields.TextField', [], {}),
+            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
+        },
+        'portal.storage': {
+            'Meta': {'object_name': 'Storage'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
+            'value': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.subscription': {
+            'Meta': {'object_name': 'Subscription'},
+            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
+            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.user': {
+            'Meta': {'object_name': 'User'},
+            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
+            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
+            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
+            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
+            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
+            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
+            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
+            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'profile_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['portal.ProfileField']", 'through': "orm['portal.ProfileData']", 'symmetrical': 'False'}),
+            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
+            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
+        },
+        'portal.userdata': {
+            'Meta': {'object_name': 'UserData'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        }
+    }
+
+    complete_apps = ['portal']
\ No newline at end of file
diff --git a/inyoka/portal/migrations/0027_auto__add_profilecategory__add_field_profilefield_category.py b/inyoka/portal/migrations/0027_auto__add_profilecategory__add_field_profilefield_category.py
new file mode 100644
index 0000000..c18785b
--- /dev/null
+++ b/inyoka/portal/migrations/0027_auto__add_profilecategory__add_field_profilefield_category.py
@@ -0,0 +1,186 @@
+# -*- coding: utf-8 -*-
+import datetime
+from south.db import db
+from south.v2 import SchemaMigration
+from django.db import models
+
+
+class Migration(SchemaMigration):
+
+    def forwards(self, orm):
+        # Adding model 'ProfileCategory'
+        db.create_table('portal_profilecategory', (
+            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
+            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
+            ('weight', self.gf('django.db.models.fields.IntegerField')(default=0)),
+            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=255)),
+        ))
+        db.send_create_signal('portal', ['ProfileCategory'])
+
+        # Adding field 'ProfileField.category'
+        db.add_column('portal_profilefield', 'category',
+                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='fields', null=True, to=orm['portal.ProfileCategory']),
+                      keep_default=False)
+
+    def backwards(self, orm):
+        # Deleting model 'ProfileCategory'
+        db.delete_table('portal_profilecategory')
+
+        # Deleting field 'ProfileField.category'
+        db.delete_column('portal_profilefield', 'category_id')
+
+    models = {
+        'contenttypes.contenttype': {
+            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
+            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
+        },
+        'portal.event': {
+            'Meta': {'object_name': 'Event'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
+            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
+            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
+            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
+            'endtime': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
+            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '56', 'blank': 'True'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
+            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.group': {
+            'Meta': {'object_name': 'Group'},
+            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
+            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.privatemessage': {
+            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'PrivateMessage'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
+            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'text': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.privatemessageentry': {
+            'Meta': {'ordering': "('_order',)", 'object_name': 'PrivateMessageEntry'},
+            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
+            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilecategory': {
+            'Meta': {'object_name': 'ProfileCategory'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.profiledata': {
+            'Meta': {'object_name': 'ProfileData'},
+            'data': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.ProfileField']"}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilefield': {
+            'Meta': {'object_name': 'ProfileField'},
+            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'fields'", 'null': 'True', 'to': "orm['portal.ProfileCategory']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        },
+        'portal.searchqueue': {
+            'Meta': {'ordering': "['id']", 'object_name': 'SearchQueue'},
+            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
+            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
+        },
+        'portal.sessioninfo': {
+            'Meta': {'object_name': 'SessionInfo'},
+            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
+            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
+            'last_change': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
+            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
+            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
+        },
+        'portal.staticfile': {
+            'Meta': {'object_name': 'StaticFile'},
+            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
+            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.staticpage': {
+            'Meta': {'object_name': 'StaticPage'},
+            'content': ('django.db.models.fields.TextField', [], {}),
+            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
+        },
+        'portal.storage': {
+            'Meta': {'object_name': 'Storage'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
+            'value': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.subscription': {
+            'Meta': {'object_name': 'Subscription'},
+            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
+            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.user': {
+            'Meta': {'object_name': 'User'},
+            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
+            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
+            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
+            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
+            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
+            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
+            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
+            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'profile_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['portal.ProfileField']", 'through': "orm['portal.ProfileData']", 'symmetrical': 'False'}),
+            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
+            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
+        },
+        'portal.userdata': {
+            'Meta': {'object_name': 'UserData'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        }
+    }
+
+    complete_apps = ['portal']
\ No newline at end of file
diff --git a/inyoka/portal/migrations/0028_auto__add_field_profilefield_regex.py b/inyoka/portal/migrations/0028_auto__add_field_profilefield_regex.py
new file mode 100644
index 0000000..073875c
--- /dev/null
+++ b/inyoka/portal/migrations/0028_auto__add_field_profilefield_regex.py
@@ -0,0 +1,175 @@
+# -*- coding: utf-8 -*-
+import datetime
+from south.db import db
+from south.v2 import SchemaMigration
+from django.db import models
+
+
+class Migration(SchemaMigration):
+
+    def forwards(self, orm):
+        # Adding field 'ProfileField.regex'
+        db.add_column('portal_profilefield', 'regex',
+                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
+                      keep_default=False)
+
+    def backwards(self, orm):
+        # Deleting field 'ProfileField.regex'
+        db.delete_column('portal_profilefield', 'regex')
+
+    models = {
+        'contenttypes.contenttype': {
+            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
+            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
+        },
+        'portal.event': {
+            'Meta': {'object_name': 'Event'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'changed': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
+            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
+            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
+            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'enddate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
+            'endtime': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'location': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
+            'location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'location_town': ('django.db.models.fields.CharField', [], {'max_length': '56', 'blank': 'True'}),
+            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
+            'time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
+            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.group': {
+            'Meta': {'object_name': 'Group'},
+            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
+            'permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.privatemessage': {
+            'Meta': {'ordering': "('-pub_date',)", 'object_name': 'PrivateMessage'},
+            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
+            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'text': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.privatemessageentry': {
+            'Meta': {'ordering': "('_order',)", 'object_name': 'PrivateMessageEntry'},
+            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'folder': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.PrivateMessage']"}),
+            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilecategory': {
+            'Meta': {'object_name': 'ProfileCategory'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
+        },
+        'portal.profiledata': {
+            'Meta': {'object_name': 'ProfileData'},
+            'data': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'profile_field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.ProfileField']"}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.profilefield': {
+            'Meta': {'object_name': 'ProfileField'},
+            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'fields'", 'null': 'True', 'to': "orm['portal.ProfileCategory']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'regex': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        },
+        'portal.searchqueue': {
+            'Meta': {'ordering': "['id']", 'object_name': 'SearchQueue'},
+            'component': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
+            'doc_id': ('django.db.models.fields.IntegerField', [], {}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
+        },
+        'portal.sessioninfo': {
+            'Meta': {'object_name': 'SessionInfo'},
+            'action': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
+            'action_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
+            'last_change': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
+            'subject_link': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
+            'subject_text': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
+            'subject_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
+        },
+        'portal.staticfile': {
+            'Meta': {'object_name': 'StaticFile'},
+            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
+            'is_ikhaya_icon': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
+        },
+        'portal.staticpage': {
+            'Meta': {'object_name': 'StaticPage'},
+            'content': ('django.db.models.fields.TextField', [], {}),
+            'key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25', 'primary_key': 'True'}),
+            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
+        },
+        'portal.storage': {
+            'Meta': {'object_name': 'Storage'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
+            'value': ('django.db.models.fields.TextField', [], {})
+        },
+        'portal.subscription': {
+            'Meta': {'object_name': 'Subscription'},
+            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
+            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
+            'ubuntu_version': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"})
+        },
+        'portal.user': {
+            'Meta': {'object_name': 'User'},
+            '_permissions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            '_primary_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'primary_users_set'", 'null': 'True', 'db_column': "'primary_group_id'", 'to': "orm['portal.Group']"}),
+            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
+            'banned_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
+            'coordinates_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'coordinates_long': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
+            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
+            'forum_last_read': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
+            'forum_read_status': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'forum_welcome': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['portal.Group']"}),
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
+            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
+            'member_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
+            'new_password_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
+            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
+            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'profile_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['portal.ProfileField']", 'through': "orm['portal.ProfileData']", 'symmetrical': 'False'}),
+            'settings': ('django.db.models.TextField', [], {'default': '{}'}),
+            'signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
+            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
+            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
+        },
+        'portal.userdata': {
+            'Meta': {'object_name': 'UserData'},
+            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
+            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
+            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['portal.User']"}),
+            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
+        }
+    }
+
+    complete_apps = ['portal']
\ No newline at end of file
diff --git a/inyoka/portal/templates/portal/configuration.html b/inyoka/portal/templates/portal/configuration.html
index 63e3559..eb0d748 100644
--- a/inyoka/portal/templates/portal/configuration.html
+++ b/inyoka/portal/templates/portal/configuration.html
@@ -1,6 +1,6 @@
 {#
-    templates.admin.configuration
-    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
+    portal/configuration.html
+    ~~~~~~~~~~~~~~~~~~~~~~~~~
 
     On this page the administrator can set general configuration values.
 
@@ -75,6 +75,34 @@
     </tbody>
   </table>
   {{ form.distri_versions }}
+  <h3>{%- trans -%}Profile fields{%- endtrans -%}</h3>
+  {% if profile_fields %}
+    <table>
+      <thead>
+        <tr>
+          <th>{% trans %}Title{% endtrans %}</th>
+          <th>{% trans %}Category{% endtrans %}</th>
+          <th></th>
+        </tr>
+      </thead>
+      <tbody>
+        {% for field in profile_fields %}
+          <tr>
+            <td>{{ field.title|e }}</td>
+            <td>{{ field.category.title|e }}</td>
+            <td><a href="{{ href('portal', 'config', 'profile_field', field.id) }}">Edit</a></td>
+          </tr>
+        {% endfor %}
+      </tbody>
+      <tfoot>
+        <td colspan="3">
+          <a href="{{ href('portal', 'config', 'profile_field', 'new') }}">
+            {%- trans -%}Add{%- endtrans -%}
+          </a>
+        </td>
+      </tfoot>
+    </table>
+  {% endif %}
   <p>
     <input type="submit" value="{% trans %}Submit{% endtrans %}" />
   </p>
diff --git a/inyoka/portal/templates/portal/index.html b/inyoka/portal/templates/portal/index.html
index 2e5907a..5a08a76 100644
--- a/inyoka/portal/templates/portal/index.html
+++ b/inyoka/portal/templates/portal/index.html
@@ -2,9 +2,9 @@
     portal/index.html
     ~~~~~~~~~~~~~~~~~
 
-    This is ubuntuusers' main page that provides links to quite many pages.
+    This is the frontpage which provides links to quite many pages.
 
-    It also displays some of the latest ikhaya messages.
+    It also displays some of the latest news.
 
     :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
     :license: GNU GPL, see LICENSE for more details.
diff --git a/inyoka/portal/templates/portal/profile.html b/inyoka/portal/templates/portal/profile.html
index abe433b..8d1aff9 100644
--- a/inyoka/portal/templates/portal/profile.html
+++ b/inyoka/portal/templates/portal/profile.html
@@ -27,27 +27,61 @@
   {{ href('portal', 'user', user.username, do)|e }}
 {% endmacro %}
 
+{% block tabbar %}
+  <ul>
+    <li>
+      <a href="{{ user|url }}"{% if not category %}class="active"{% endif %}>
+        General
+      </a>
+    </li>
+    {% for cat in categories %}
+      <li>
+        <a href="{{ user|url(category=cat) }}"{% if cat == category %}class="active"{% endif %}>
+          {{ cat.title|e }}
+        </a>
+      </li>
+    {% endfor %}
+    {% if wikipage %}
+      <li>
+        <a href="{{ href('wiki', 'Benutzer', user.username|e) }}">
+          {% trans %}Wikipage{% endtrans %}
+        </a>
+      </li>
+    {% endif %}
+    {%- if request.user.can('user_edit') %}
+      <li>
+        <a href="{{ href('portal', 'user', user.username, 'edit') }}"
+           class="admin_link">
+          {% trans %}Edit{% endtrans %}
+        </a>
+      </li>
+    {%- endif %}
+    {%- if request.user.can('subscribe_to_users') -%}
+      <li>
+        {%- if is_subscribed %}
+          <a href="{{ generate_subscription_link(do='unsubscribe') }}"
+             class="action action_subscribe subscribe_user admin_link">
+            {% trans %}Don’t watch anymore{% endtrans %}
+          </a>
+        {%- else %}
+          <a href="{{ generate_subscription_link() }}"
+             class="action action_subscribe subscribe_user admin_link">
+            {% trans %}Watch{% endtrans %}
+          </a>
+        {%- endif -%}
+      </li>
+    {%- endif %}
+  </ul>
+{% endblock %}
+
 {% block portal_content %}
-  <h3>{{ user.username|e }}
-  {%- if request.user.can('user_edit') %}
-    <a href="{{ href('portal', 'user', user.username, 'edit') }}" class="admin_link"><img
-      src="{{ href('static', 'img/ikhaya/category_edit.png') }}" alt="{% trans %}Edit user{% endtrans %}" title="{% trans %}Edit user{% endtrans %}" /></a>
-  {%- endif %}
-  {%- if request.user.can('subscribe_to_users') -%}
-    {%- if is_subscribed %}
-      <a href="{{ generate_subscription_link(do='unsubscribe') }}" class="action action_subscribe subscribe_user admin link"><img
-      src="{{ href('static', 'img/forum/subscribe.png') }}" alt="{% trans %}Don’t watch anymore{% endtrans %}" title="{% trans %}Don’t watch anymore{% endtrans %}" /></a>
-    {%- else %}
-      <a href="{{ generate_subscription_link() }}" class="action action_subscribe subscribe_user admin_link"><img
-      src="{{ href('static', 'img/forum/subscribe.png') }}" alt="{% trans %}Watch{% endtrans %}" title="{% trans %}Watch{% endtrans %}" /></a>
-    {%- endif -%}
-  {%- endif %}
-  </h3>
+  <h3>{{ user.username|e }}</h3>
   {%- if user in (User.objects.get_system_user(), User.objects.get_anonymous_user()) %}
     {% trans name=user.username|e %}{{ name }} is a system user.{% endtrans %}
   {%- elif user.is_deleted or user.is_banned %}
     {% trans name=user.username|e %}{{ name }} is not available.{% endtrans %}
   {%- else %}
+    <!--
     <table class="userinfo admin_link_hover">
       <tr>
         <th>{% trans %}Name{% endtrans %}</th>
@@ -62,25 +96,6 @@
         {{ show_item('email') }}
       </tr>
       <tr>
-        <th>{% trans %}Website{% endtrans %}</th>
-        <td>
-          {%- if user.website -%}
-            <a href="{{ user.website|e }}">{{ user.website|e }}</a>
-          {%- else -%}
-            –
-          {%- endif -%}
-        </td>
-      </tr>
-      <tr>
-        <th>{% trans %}Launchpad username{% endtrans %}</th>
-        <td>
-          {%- if user.launchpad -%}
-            <a href="{{ user.launchpad_url|e }}">{{ user.launchpad|e }}</a>
-          {%- else -%}
-            –
-          {% endif %}
-        </td>
-      <tr>
         <th>{% trans %}Member since{% endtrans %}</th>
         <td>{{ user.date_joined|datetimeformat }}</td>
       </tr>
@@ -92,58 +107,6 @@
         </td>
       </tr>
       <tr>
-        <th>{% trans %}GPG key{% endtrans %}</th>
-        <td>{% if user.gpgkey %}0x{{ user.gpgkey|e }}{% else %}–{% endif %}</td>
-      </tr>
-      <tr>
-        <th>{% trans %}Residence{% endtrans %}</th>
-        <th>{% trans %}Job{% endtrans %}</th>
-        <th>{% trans %}Interests{% endtrans %}</th>
-      </tr>
-      <tr>
-        <td>{{ user.location|e or '–' }}</td>
-        <td>{{ user.occupation|e or '–' }}</td>
-        <td>{{ user.interests|e or '–' }}</td>
-      </tr>
-      <tr>
-        <th>{% trans %}MSN{% endtrans %}</th>
-        <th>{% trans %}ICQ{% endtrans %}</th>
-        <th>{% trans %}AIM{% endtrans %}</th>
-      </tr>
-      <tr>
-        <td>{{ user.msn|e or '–' }}</td>
-        <td>{{ user.icq|e or '–' }}</td>
-        <td>{{ user.aim|e or '–' }}</td>
-      </tr>
-      <tr>
-        <th>{% trans %}Yahoo Messenger{% endtrans %}</th>
-        <th>{% trans %}Skype{% endtrans %}</th>
-        <th>{% trans %}WengoPhone{% endtrans %}</th>
-      </tr>
-      <tr>
-        <td>{{ user.yim|e or '–' }}</td>
-        <td>{{ user.skype|e or '–' }}</td>
-        <td>{{ user.wengophone|e or '–' }}</td>
-      </tr>
-      <tr>
-        <th>{% trans %}SIP{% endtrans %}</th>
-        <th>{% trans %}Jabber{% endtrans %}</th>
-        <th>{% trans %}Contact{% endtrans %}</th>
-      </tr>
-      <tr>
-        <td>{{ user.sip|e or '–' }}</td>
-        {% if user.jabber and user.settings['show_jabber'] -%}
-        <td><a href="{{ user.jabber_url|e }}">{{ user.jabber|e }}</a></td>
-        {%- elif user.jabber and REQUEST.user.can('user_edit') -%}
-        <td class="hidden"><a href="{{ user.jabber_url|e }}">{{ user.jabber|e }}</a></td>
-        {%- else -%}
-        <td>–</td>
-        {%- endif -%}
-        <td>
-          <a href="{{ user|url('privmsg') }}">{% trans %}Private message{% endtrans %}</a>
-        </td>
-      </tr>
-      <tr>
         <th colspan="3">{% trans %}Group memberships{% endtrans %}
           {% if REQUEST.user.can('user_edit') %}
           <a href="{{ href('portal', 'user', user.username, 'edit', 'groups') }}" class="admin_link"><img src="{{ href('static', 'img/ikhaya/category_edit.png') }}"></a>
@@ -162,11 +125,17 @@
         </td>
       </tr>
     </table>
+    -->
+    <div class="userprofile_fields">
+      {% for data in profile_data %}
+        <div class="field">
+          <div class="field_left"></div>
+          <div class="field_right">
+            <div class="title">{{ data.profile_field.title|e }}</div>
+            <p>{{ data.data|e }}</p>
+          </div>
+        </div>
+      {% endfor %}
+    </div>
   {% endif %}
-  {%- if wikipage %}
-    {{ wikipage }}
-    <p>
-      (<a href="{{ href('wiki', SETTINGS.WIKI_USER_BASE, user.username|e, action='edit') }}">{% trans %}edit{% endtrans %}</a>)
-    </p>
-  {%- endif %}
 {% endblock %}
diff --git a/inyoka/portal/templates/portal/profile_field_edit.html b/inyoka/portal/templates/portal/profile_field_edit.html
new file mode 100644
index 0000000..6a8370d
--- /dev/null
+++ b/inyoka/portal/templates/portal/profile_field_edit.html
@@ -0,0 +1,30 @@
+{#
+    portal/profile_field_edit.html
+    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
+
+    Administrationpage to edit user profile fields.
+
+#}
+{% extends 'portal/overall.html' %}
+{% from 'macros.html' import render_form %}
+
+{%- do BREADCRUMB.append(_('Profile field'), href('portal', 'config', 'profile_field', field.id or 'new'), True) %}
+{%- do BREADCRUMB.append(_('Configuration'), href('portal', 'config'), True) %}
+
+{% block content %}
+  <h3>
+    {% if field %}
+      {%- trans field=field.title -%}Edit profile field “{{ field }}”{%- endtrans -%}
+    {% else %}
+      {%- trans -%}New profile field{%- endtrans -%}
+    {% endif %}
+  </h3>
+  {{ form.errors.__all__ }}
+  <form method="post">
+    {{ render_form(form, ['title', 'regex', 'category', 'new_category']) }}
+    <input type="submit" value="{% trans %}Submit{% endtrans %}" />
+    {% if field %}
+      <input type="submit" name="delete" value="{% trans %}Delete{% endtrans %}" />
+    {% endif %}
+  </form>
+{% endblock %}
diff --git a/inyoka/portal/templates/portal/usercp/add_field.html b/inyoka/portal/templates/portal/usercp/add_field.html
new file mode 100644
index 0000000..fe84058
--- /dev/null
+++ b/inyoka/portal/templates/portal/usercp/add_field.html
@@ -0,0 +1,25 @@
+{#
+    portal/usercp/add_field.html
+    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
+
+    Users with disabled JavaScript can add profile fields here.
+
+    :copyright: (c) 2007-2011 by the Inyoka Team, see AUTHORS for more details.
+    :license: GNU GPL, see LICENSE for more details.
+#}
+
+{% extends 'portal/usercp/overall.html' %}
+
+{% from 'macros.html' import render_form %}
+
+{% do BREADCRUMB.append(_('Profile field'), href('portal', 'usercp', 'profile', 'add_field'), True) %}
+{% do BREADCRUMB.append(_('Profile'), href('portal', 'usercp', 'profile')) %}
+{% set selected = 'profile' %}
+
+{% block portal_content %}
+  <form enctype="multipart/form-data" method="post" action="">
+    <h3>{% trans %}Add profile field{% endtrans %}</h3>
+    {{ render_form(form, ['field', 'data']) }}
+    <input type="submit" value="{% trans %}Submit{% endtrans %}" />
+  </form>
+{% endblock %}
diff --git a/inyoka/portal/templates/portal/usercp/profile.html b/inyoka/portal/templates/portal/usercp/profile.html
index 2bf79c2..6f7ad50 100644
--- a/inyoka/portal/templates/portal/usercp/profile.html
+++ b/inyoka/portal/templates/portal/usercp/profile.html
@@ -1,8 +1,8 @@
 {#
-    portal/usercp/settings.html
-    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
+    portal/usercp/profile.html
+    ~~~~~~~~~~~~~~~~~~~~~~~~~~
 
-    This page shows the user control panel settings page.
+    This page shows the user the configuration of his profile.
 
     :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
     :license: GNU GPL, see LICENSE for more details.
@@ -31,7 +31,6 @@
       </dd>
       {%- endif %}
       {%- if form.errors.avatar %}<dd>{{ form.errors.avatar }}</dd>{% endif %}
-      <hr style="clear: both;" />
       <dt>{% trans %}Gravatar:{% endtrans %}</dt>
       {% if user.settings.use_gravatar %}
       <dd><img class="usercp_avatar" src="{{ user.gravatar_url }}" alt="Gravatar" /></dd>
@@ -45,28 +44,53 @@
     <dl>
       <dd>
         <p class="note">{% trans -%}
-          By default, the email and jabber addresses are not displayed in your public profile. To publish them, you need to check the “show in profile“ box.
+          The email and jabber addresses are not displayed in your public profile.
+          If you want to make them public, add them to your public information.
         {%- endtrans %}</p>
       </dd>
-      {% for item in ['email', 'jabber', 'icq', 'msn', 'aim', 'yim', 'skype', 'wengophone', 'sip'] %}
+      {% for item in ['email', 'jabber'] %}
         <dt>
           <label for="{{ form[item].auto_id }}">{{ form[item].label }}</label>
         </dt>
-        <dd>{{ form[item] }}
-          {%- if item in ['email', 'jabber'] %}
-            <span class="note">{{ form['show_' + item] }}
-              <label for="id_show_{{ item }}">{% trans %}Show in profile{% endtrans %}</label>
-            </span>
-          {%- endif -%}
-        </dd>
+        <dd>{{ form[item] }}</dd>
         {%- if form.errors[item] %}<dd>{{ form.errors[item] }}</dd>{% endif %}
       {% endfor %}
     </dl>
-    <h3>{% trans %}Miscellaneous settings{% endtrans %}</h3>
-    {{ render_form(form, ['occupation', 'interests', 'website',
-                          'launchpad', 'gpgkey']) }}
+    <h3>{% trans %}Public information{% endtrans %}</h3>
+    <p class="note">{%- trans -%}You can customize your <em>public</em> profile with the fields below.{%- endtrans -%}</p>
+    <table id="profile_fields">
+      <thead>
+        <tr>
+          <td class="field">{% trans %}Field{% endtrans %}</td>
+          <td class="data">{% trans %}Data{% endtrans %}</td>
+          <td class="delete"></td>
+        </tr>
+      </thead>
+      <tbody>
+        {% for data in profile_data %}
+          <tr>
+            <td>{{ data.profile_field.title }}</td>
+            <td>
+              <input type="text" value="{{ data.data }}"
+                     name="profile_field_{{ loop.index0 }}.{{ data.profile_field.id }}" />
+              </td>
+            <td>
+              <a class="delete"
+                 href="{{ href('portal', 'usercp', 'profile', 'delete_field', data.id) }}">Delete</a></td>
+          </tr>
+        {% endfor %}
+      </tbody>
+      <tfoot>
+        <tr>
+          <td colspan="3" class="add">
+            <a id="add_profile_field"
+               href="{{ href('portal', 'usercp', 'profile', 'add_field') }}">Add a field</a>
+          </td>
+        </tr>
+      </tfoot>
+    </table>
     <h4>{% trans %}Geographical location{% endtrans %}</h4>
-    {{ render_form(form, ['location', 'coordinates']) }}
+    {{ render_form(form, ['coordinates']) }}
     <h3>{% trans %}OpenIDs{% endtrans %}</h3>
     <p>
       {% if openids %}
@@ -139,4 +163,51 @@
 
     /*]]>*/
   </script>
+  <script type="text/javascript">
+    /*<![CDATA[*/
+    $('#add_profile_field').click(function() {
+      $('#profile_fields tbody')
+      .append($('<tr>')
+        .append($('<td>')
+          .append($('<select>')
+          )
+        )
+        .append($('<td>')
+          .append($('<input>')
+            .attr('type', 'text')
+          )
+        )
+        .append($('<td>')
+          .append($('<a>')
+            .attr('class', 'delete')
+            .text('Delete')
+            .click(function() {
+              $(this).parent().parent().remove();
+            })
+          )
+        )
+      )
+
+      var profile_fields = eval('({{ profile_fields }})');
+      var select = $('#profile_fields tbody tr:last td select')
+      select.append($('<option>'));
+      for (i in profile_fields) {
+        select.append($('<option>')
+          .attr('value', profile_fields[i].id)
+          .text(profile_fields[i].title)
+        );
+      }
+      select.change(function() {
+        var row = select.parent().parent()
+        var name = 'profile_field_' + row.index() + '.' + select.val();
+        row.find('input').attr('name', name);
+      });
+      return false;
+    });
+    $('.delete').click(function() {
+      $(this).parent().parent().remove();
+      return false;
+    });
+    /*]]>*/
+  </script>
 {% endblock %}
diff --git a/inyoka/portal/urls.py b/inyoka/portal/urls.py
index 8242bed..74a8b9c 100644
--- a/inyoka/portal/urls.py
+++ b/inyoka/portal/urls.py
@@ -20,6 +20,7 @@ urlpatterns = patterns('inyoka.portal.views',
     (r'^users/(?P<page>\d+)/$', 'memberlist'),
     (r'^user/new/$', 'user_new'),
     (r'^user/(?P<username>[^/]+)/$', 'profile'),
+    (r'^user/(?P<username>[^/]+)/c/(?P<category>[^/]+)/$', 'profile'),
     (r'^user/(?P<username>[^/]+)/subscribe/$', 'subscribe_user'),
     (r'^user/(?P<username>[^/]+)/unsubscribe/$', 'unsubscribe_user'),
     (r'^user/(?P<username>[^/]+)/edit/$', 'user_edit'),
@@ -41,6 +42,8 @@ urlpatterns = patterns('inyoka.portal.views',
     (r'^usercp/$', 'usercp'),
     (r'^usercp/settings/$', 'usercp_settings'),
     (r'^usercp/profile/$', 'usercp_profile'),
+    (r'^usercp/profile/add_field/$', 'usercp_add_profile_field'),
+    (r'^usercp/profile/delete_field/(?P<field_id>\d+)/$', 'usercp_delete_profile_field'),
     (r'^usercp/password/$', 'usercp_password'),
     (r'^usercp/subscriptions/$', 'usercp_subscriptions'),
     (r'^usercp/subscriptions/(?P<page>\d+)/$', 'usercp_subscriptions'),
@@ -72,6 +75,8 @@ urlpatterns = patterns('inyoka.portal.views',
     (r'^opensearch/(?P<app>[a-z]+)/$', 'open_search'),
     (r'^openid/(.*)', 'openid_consumer'),
     (r'^config/$', 'config'),
+    (r'^config/profile_field/new/$', 'profile_field_edit'),
+    (r'^config/profile_field/(?P<field_id>\d+)/$', 'profile_field_edit'),
     (r'^styles/$', 'styles'),
     # shortcuts
     (r'^ikhaya/(\d+)/$', 'ikhaya_redirect'),
diff --git a/inyoka/portal/user.py b/inyoka/portal/user.py
index b8d07e6..108730d 100644
--- a/inyoka/portal/user.py
+++ b/inyoka/portal/user.py
@@ -20,6 +20,7 @@ from StringIO import StringIO
 from django.conf import settings
 from django.core.cache import cache
 from django.db import models
+from django.template.defaultfilters import slugify
 from django.utils.translation import ugettext_lazy, ugettext as _
 
 from inyoka.utils import encode_confirm_data, classproperty
@@ -162,6 +163,8 @@ def deactivate_user(user):
     except WikiPage.DoesNotExist:
         pass
 
+    # TODO: user.status = 3 equals "user.is_deleted", i dont get the following
+    # lines (see also line 550)
     user.status = 3
     if not user.is_banned:
         user.email = 'user%d@ubuntuusers.de.invalid' % user.id
@@ -169,10 +172,8 @@ def deactivate_user(user):
     user.groups.remove(*user.groups.all())
     user.avatar = user.coordinates_long = user.coordinates_lat = \
         user.new_password_key = user._primary_group = None
-    user.icq = user.jabber = user.msn = user.aim = user.yim = user.skype = \
-        user.wengophone = user.sip = user.location = user.signature = \
-        user.gpgkey = user.location = user.occupation = user.interests = \
-        user.website = user.launchpad = user.member_title = ''
+    user.jabber = user.signature = user.member_title = ''
+    user.profile_fields.clear()
     user.save()
 
 
@@ -482,6 +483,31 @@ class UserManager(models.Manager):
         return _SYSTEM_USER
 
 
+class ProfileCategory(models.Model):
+    """Category for the profile fields."""
+    title = models.CharField(_(u'Title'), max_length=255)
+    weight = models.IntegerField(_(u'Weight'), default=0)
+    slug = models.SlugField(max_length=255, unique=True)
+
+    def __unicode__(self):
+        return self.title
+
+    def save(self, *args, **kwargs):
+        if not self.id:
+            self.slug = slugify(self.title)
+        super(ProfileCategory, self).save(*args, **kwargs)
+
+class ProfileField(models.Model):
+    """Contains the profile fields which are available for the users."""
+    title = models.CharField(max_length=255)
+    category = models.ForeignKey(ProfileCategory, related_name='fields',
+                                 blank=True, null=True)
+    regex = models.CharField(max_length=255, blank=True, null=True)
+
+    def __unicode__(self):
+        return self.title
+
+
 class User(models.Model):
     """User model that contains all informations about an user."""
     objects = UserManager()
@@ -506,26 +532,14 @@ class User(models.Model):
     banned_until = models.DateTimeField(ugettext_lazy(u'Banned until'), null=True)
 
     # profile attributes
+    profile_fields = models.ManyToManyField(ProfileField, through='ProfileData')
     post_count = models.IntegerField(ugettext_lazy(u'Posts'), default=0)
     avatar = models.ImageField(ugettext_lazy(u'Avatar'), upload_to='portal/avatars',
                                blank=True, null=True)
     jabber = models.CharField(ugettext_lazy(u'Jabber'), max_length=200, blank=True)
-    icq = models.CharField(ugettext_lazy(u'ICQ'), max_length=16, blank=True)
-    msn = models.CharField(ugettext_lazy(u'MSN'), max_length=200, blank=True)
-    aim = models.CharField(ugettext_lazy(u'AIM'), max_length=200, blank=True)
-    yim = models.CharField(ugettext_lazy(u'Yahoo Messenger'), max_length=200, blank=True)
-    skype = models.CharField(ugettext_lazy(u'Skype'), max_length=200, blank=True)
-    wengophone = models.CharField(ugettext_lazy(u'WengoPhone'), max_length=200, blank=True)
-    sip = models.CharField('SIP', max_length=200, blank=True)
     signature = models.TextField(ugettext_lazy(u'Signature'), blank=True)
     coordinates_long = models.FloatField(ugettext_lazy(u'Coordinates (longitude)'), blank=True, null=True)
     coordinates_lat = models.FloatField(ugettext_lazy(u'Coordinates (latitude)'), blank=True, null=True)
-    location = models.CharField(ugettext_lazy(u'Residence'), max_length=200, blank=True)
-    gpgkey = models.CharField(ugettext_lazy(u'GPG key'), max_length=8, blank=True)
-    occupation = models.CharField(ugettext_lazy(u'Job'), max_length=200, blank=True)
-    interests = models.CharField(ugettext_lazy(u'Interests'), max_length=200, blank=True)
-    website = models.URLField(ugettext_lazy(u'Website'), blank=True)
-    launchpad = models.CharField(ugettext_lazy(u'Launchpad username'), max_length=50, blank=True)
     settings = JSONField(ugettext_lazy(u'Settings'), default={})
     _permissions = models.IntegerField(ugettext_lazy(u'Privileges'), default=0)
 
@@ -546,6 +560,9 @@ class User(models.Model):
                                        blank=True, null=True,
                                        db_column='primary_group_id')
 
+    def __unicode__(self):
+        return self.username
+
     def save(self, *args, **kwargs):
         """
         Save method that dumps `self.settings` before and cleanup
@@ -555,9 +572,6 @@ class User(models.Model):
         cache.delete('portal/user/%s/signature' % self.id)
         cache.delete('portal/user/%s' % self.id)
 
-    def __unicode__(self):
-        return self.username
-
     is_anonymous = property(lambda x: x.username == settings.INYOKA_ANONYMOUS_USER)
     is_authenticated = property(lambda x: not x.is_anonymous)
     is_active = property(lambda x: x.status == 1)
@@ -730,8 +744,10 @@ class User(models.Model):
             os.remove(fn)
         self.avatar = None
 
-    def get_absolute_url(self, action='show', *args):
+    def get_absolute_url(self, action='show', category=None, *args):
         if action == 'show':
+            if category:
+                return href('portal', 'user', self.urlsafe_username, 'c', category.slug)
             return href('portal', 'user', self.urlsafe_username)
         elif action == 'privmsg':
             return href('portal', 'privmsg', 'new',
@@ -771,6 +787,17 @@ class User(models.Model):
         return cls.objects.get_anonymous_user()
 
 
+class ProfileData(models.Model):
+    """Intermediary between Profile and User.
+
+    Stores the data a user enters for a profile.
+
+    """
+    user = models.ForeignKey(User)
+    profile_field = models.ForeignKey(ProfileField)
+    data = models.CharField(max_length=255)
+
+
 class UserData(models.Model):
     user = models.ForeignKey(User)
     key = models.CharField(max_length=255)
diff --git a/inyoka/portal/views.py b/inyoka/portal/views.py
index 72d785b..ae18980 100644
--- a/inyoka/portal/views.py
+++ b/inyoka/portal/views.py
@@ -11,10 +11,12 @@
     :license: GNU GPL, see LICENSE for more details.
 """
 import binascii
+from datetime import datetime, date, timedelta
+import json
+from PIL import Image
 import pytz
+import re
 import time
-from PIL import Image
-from datetime import datetime, date, timedelta
 
 from django import forms
 from django.conf import settings
@@ -39,10 +41,11 @@ from inyoka.utils.dates import DEFAULT_TIMEZONE, \
 from inyoka.utils.http import templated, HttpResponse, \
      PageNotFound, does_not_exist_is_404, HttpResponseRedirect
 from inyoka.utils.sessions import get_sessions, make_permanent, \
-    get_user_record, test_session_cookie
+     get_user_record, test_session_cookie
 from inyoka.utils.urls import href, url_for, is_safe_domain
 from inyoka.utils.html import escape
 from inyoka.utils.flashing import flash
+from inyoka.utils.flash_confirmation import confirm_action
 from inyoka.utils.sortable import Sortable
 from inyoka.utils.pagination import Pagination
 from inyoka.utils.notification import send_notification
@@ -66,13 +69,15 @@ from inyoka.portal.forms import LoginForm, SearchForm, RegisterForm, \
      OpenIDConnectForm, EditUserProfileForm, EditUserGroupsForm, \
      EditStaticPageForm, EditFileForm, ConfigurationForm, EditStyleForm, \
      EditUserPrivilegesForm, EditUserPasswordForm, EditUserStatusForm, \
-     CreateUserForm, UserMailForm, EditGroupForm, CreateGroupForm
+     CreateUserForm, UserMailForm, EditGroupForm, CreateGroupForm, \
+     EditProfileFieldForm, UserCPAddProfileFieldForm
 from inyoka.portal.models import StaticPage, PrivateMessage, Subscription, \
      PrivateMessageEntry, PRIVMSG_FOLDERS, StaticFile
 from inyoka.portal.user import User, Group, UserBanned, UserData, \
-    deactivate_user, reactivate_user, set_new_email, \
-    send_new_email_confirmation, reset_email, send_activation_mail, \
-    send_new_user_password, PERMISSION_NAMES
+     deactivate_user, reactivate_user, set_new_email, \
+     send_new_email_confirmation, reset_email, send_activation_mail, \
+     send_new_user_password, PERMISSION_NAMES, ProfileField, ProfileData, \
+     ProfileCategory
 from inyoka.portal.utils import check_login, calendar_entries_for_month, \
      require_permission, google_calendarize, UBUNTU_VERSIONS, UbuntuVersionList
 from inyoka.portal.filters import SubscriptionFilter
@@ -511,7 +516,7 @@ def search(request):
 
 @check_login(message=_(u'You need to be logged in to view a user profile.'))
 @templated('portal/profile.html')
-def profile(request, username):
+def profile(request, username, category=None):
     """Show the user profile if the user is logged in."""
 
     user = User.objects.get(username)
@@ -529,6 +534,7 @@ def profile(request, username):
         content = wikipage.rev.rendered_text
     except WikiPage.DoesNotExist:
         content = u''
+
     if request.user.can('group_edit') or request.user.can('user_edit'):
         groups = user.groups.all()
     else:
@@ -536,13 +542,29 @@ def profile(request, username):
 
     subscribed = Subscription.objects.user_subscribed(request.user, user)
 
+    categories = ProfileCategory.objects.order_by('weight').all()
+    profile_data = ProfileData.objects.filter(user=user)
+    if not category:
+        profile_data = profile_data.filter(profile_field__category=None)
+        profile_category = None
+    else:
+        try:
+            profile_category = categories.get(slug=category)
+        except ProfileCategory.DoesNotExist:
+            raise PageNotFound()
+        profile_data = profile_data.filter(profile_field__category=profile_category)
+    profile_data = profile_data.order_by('profile_field__title').all()
+
     return {
-        'user':          user,
-        'groups':        groups,
-        'wikipage':      content,
-        'User':          User,
+        'user': user,
+        'groups': groups,
+        'wikipage': content,
+        'User': User,
         'is_subscribed': subscribed,
-        'request':       request
+        'request': request,
+        'profile_data': profile_data,
+        'categories': categories,
+        'category': profile_category,
     }
 
 
@@ -630,17 +652,29 @@ def usercp(request):
 @check_login(message=_(u'You need to be logged in to change your profile'))
 @templated('portal/usercp/profile.html')
 def usercp_profile(request):
-    """User control panel view for changing the user's profile"""
+    """User control panel view for changing the user's profile."""
     user = request.user
     if request.method == 'POST':
         form = UserCPProfileForm(request.POST, request.FILES, user=user)
         if form.is_valid():
             data = form.cleaned_data
-            for key in ('jabber', 'icq', 'msn', 'aim', 'yim',
-                        'skype', 'wengophone', 'sip',
-                        'signature', 'location', 'occupation',
-                        'interests', 'website', 'gpgkey',
-                        'launchpad'):
+            user.profile_fields.clear()
+            for key in request.POST.keys():
+                if key.startswith('profile_field_') and request.POST[key]:
+                    field_id = int(key.partition('.')[2])
+                    field = ProfileField.objects.get(id=field_id)
+                    value = request.POST[key]
+                    if field.regex and not re.match(field.regex, value):
+                        flash(_(u'The value for the profile field %(field)s '
+                                u'could not be saved, it was invalid.') % {
+                                    'field': field.title
+                                }, False)
+                        continue
+                    field_data = ProfileData(user=user, profile_field=field,
+                                             data=value)
+                    field_data.save()
+
+            for key in ('jabber', 'signature'):
                 setattr(user, key, data[key] or '')
             if data['email'] != user.email:
                 send_new_email_confirmation(user, data['email'])
@@ -669,7 +703,7 @@ def usercp_profile(request):
                         'The used file format is not supported, please choose '
                         'another one for your avatar.')).messages
 
-            for key in ('show_email', 'show_jabber', 'use_gravatar'):
+            for key in ('use_gravatar',):
                 user.settings[key] = data[key]
             user.save()
 
@@ -702,18 +736,69 @@ def usercp_profile(request):
     storage_keys = storage.get_many(('max_avatar_width',
         'max_avatar_height', 'max_avatar_size', 'max_signature_length'))
 
+    profile_fields = json.dumps([{'id': field.id, 'title': field.title} for field in ProfileField.objects.order_by('title').all()])
+    return {
+        'form': form,
+        'user': request.user,
+        'gmaps_apikey': settings.GOOGLE_MAPS_APIKEY,
+        'max_avatar_width': storage_keys.get('max_avatar_width', -1),
+        'max_avatar_height': storage_keys.get('max_avatar_height', -1),
+        'max_avatar_size': storage_keys.get('max_avatar_size', -1),
+        'max_sig_length': storage_keys.get('max_signature_length'),
+        'openids': UserData.objects.filter(user=user, key='openid'),
+        'profile_fields': profile_fields,
+        'profile_data': ProfileData.objects.filter(user=user).order_by('profile_field__title'),
+    }
+
+
+@check_login(message=_(u'You need to be logged in to change your profile'))
+@templated('portal/usercp/add_field.html')
+def usercp_add_profile_field(request):
+    """View to add a profile field.
+
+    Only used as fallback if the user disabled JavaScript.
+
+    """
+    user = request.user
+    if request.method == 'POST':
+        form = UserCPAddProfileFieldForm(request.POST)
+        if form.is_valid():
+            data = form.cleaned_data
+            field_data = ProfileData(user=user, profile_field=data['field'],
+                                     data=data['data'])
+            field_data.save()
+            flash(_(u'The profile field was added successfully.'), True)
+            return HttpResponseRedirect(href('portal', 'usercp', 'profile'))
+        else:
+            flash(_(u'Errors occurred, please fix them.'), False)
+    else:
+        form = UserCPAddProfileFieldForm()
     return {
-        'form':                 form,
-        'user':                 request.user,
-        'gmaps_apikey':         settings.GOOGLE_MAPS_APIKEY,
-        'max_avatar_width':     storage_keys.get('max_avatar_width', -1),
-        'max_avatar_height':    storage_keys.get('max_avatar_height', -1),
-        'max_avatar_size':      storage_keys.get('max_avatar_size', -1),
-        'max_sig_length':       storage_keys.get('max_signature_length'),
-        'openids':              UserData.objects.filter(user=user, key='openid'),
+        'form': form,
     }
 
 
+@check_login(message=_(u'You need to be logged in to change your profile'))
+@confirm_action(message=_(u'Du you want to remove the profile field?'),
+                confirm=_(u'Delete'), cancel=_(u'Cancel'))
+def usercp_delete_profile_field(request, field_id):
+    """View to delete a profile field.
+
+    Only used as fallback if the user disabled JavaScript.
+
+    """
+    user = request.user
+    # filter by user to prevent deleting other users profile fields
+    try:
+        data = ProfileData.objects.filter(user=user).get(id=field_id)
+    except ProfileData.DoesNotExist:
+        raise PageNotFound()
+    data.delete()
+
+    flash(_(u'The profile field was deleted successfully.'), True)
+    return HttpResponseRedirect(href('portal', 'usercp', 'profile'))
+
+
 @check_login(message=_(u'You need to be logged in to change your settings.'))
 @templated('portal/usercp/settings.html')
 def usercp_settings(request):
@@ -946,10 +1031,7 @@ def user_edit_profile(request, username):
             lat = data.get('coordinates_lat', None)
             long = data.get('coordinates_long', None)
             data['coordinates'] = '%s, %s' % (lat, long) if lat and long else ''
-            for key in ('website', 'interests', 'location', 'jabber', 'icq',
-                         'msn', 'aim', 'yim', 'signature', 'coordinates',
-                         'gpgkey', 'email', 'skype', 'sip', 'wengophone',
-                         'launchpad', 'member_title', 'username'):
+            for key in ('signature', 'coordinates', 'email', 'member_title'):
                 setattr(user, key, data[key] or '')
             if data['delete_avatar']:
                 user.delete_avatar()
@@ -2082,9 +2164,59 @@ def config(request):
         'form': form,
         'team_icon_url': team_icon and href('media', team_icon) or None,
         'versions': list(sorted(UbuntuVersionList())),
+        'profile_fields': ProfileField.objects.order_by('title').all(),
+        'profile_categories': ProfileCategory.objects.order_by('weight').all(),
     }
 
 
+@require_permission('configuration_edit')
+@templated('portal/profile_field_edit.html')
+def profile_field_edit(request, field_id=None):
+    if not field_id:
+        field = None
+    else:
+        field = ProfileField.objects.get(id=field_id)
+
+    if request.method == 'POST':
+        form = EditProfileFieldForm(request.POST, request.FILES)
+        if form.is_valid():
+            data = form.cleaned_data
+            if field and request.POST.get('delete'):
+                category = field.category
+                field.delete()
+                if not category.fields.all():
+                    category.delete()
+            else:
+                if not field:
+                    field = ProfileField()
+                old_category = field.category
+                if data['category']:
+                    field.category = data['category']
+                elif data['new_category']:
+                    category = ProfileCategory(title=data['new_category'])
+                    category.save()
+                    field.category = category
+                field.title = data['title']
+                field.regex = data['regex']
+                field.save()
+                if old_category and not old_category.fields.all():
+                    old_category.delete()
+            return HttpResponseRedirect(href('portal', 'config'))
+    else:
+        if field:
+            form = EditProfileFieldForm(initial={
+                'title': field.title,
+                'category': field.category,
+                'regex': field.regex,
+            })
+        else:
+            form = EditProfileFieldForm()
+
+    return {
+        'field': field,
+        'form': form,
+    }
+
 @templated('portal/static_page.html')
 def static_page(request, page):
     """Renders static pages"""
diff --git a/inyoka/static/style/portal.less b/inyoka/static/style/portal.less
index cee344c..0fcedb8 100644
--- a/inyoka/static/style/portal.less
+++ b/inyoka/static/style/portal.less
@@ -13,6 +13,17 @@ form.usercp_form {
   ul {
     list-style: none;
   }
+  #profile_fields {
+    .field {
+      width: 150px;
+    }
+    .delete {
+      width: 75px;
+    }
+    select {
+      width: 100%;
+    }
+  }
 }
 img.cat {
   float: right;
@@ -222,6 +233,36 @@ div.usercp_control {
     }
   }
 }
+div.userprofile_fields {
+  text-align: left;
+  vertical-align: middle;
+  .field {
+    display: inline-block;
+    height: 100px;
+    border: 1px solid #BBBBBB;
+    .rounded;
+    overflow: hidden;
+    margin: 5px;
+  }
+  .field_left {
+    float: left;
+    width: 100px;
+    height: 100%;
+    background-color: #F4F4F4;
+    border-right: 1px solid #DDDDDD;
+  }
+  .field_right {
+    float: left;
+    width: 200px;
+    height: 100%;
+    padding: 0 5px;
+    .title {
+      font-weight: bold;
+      border-bottom: 1px solid #BBBBBB;
+      padding: 2px;
+    }
+  }
+}
 img.usercp_avatar {
   float: right;
   padding-bottom: 20px;
diff --git a/make_testdata.py b/make_testdata.py
index 24c42bd..43f9a38 100755
--- a/make_testdata.py
+++ b/make_testdata.py
@@ -153,13 +153,7 @@ def make_users():
         u.groups = list(set(choice(groups) for _ in xrange(randint(0, 5))))
         u.post_count = randint(0, 1000)
         u.jabber = '%s@%s.local' % (word(markup=False), word(markup=False))
-        u.icq = word(markup=False)[:16]
-        u.msn = word(markup=False)
-        u.aim = word(markup=False)
         u.signature = words()
-        u.occupation = word(markup=False)
-        u.interests = word(markup=False)
-        u.website = u'http://%s.de' % word(markup=False)
         if not randint(0, 3):
             u.status = 0
         u.save()
