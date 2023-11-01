import datetime

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import inyoka.portal.user
import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('username', models.CharField(unique=True, max_length=30, verbose_name='Username', db_index=True)),
                ('email', models.EmailField(unique=True, max_length=50, verbose_name='Email address', db_index=True)),
                ('status', models.IntegerField(default=0, verbose_name='Activation status', choices=[(0, 'not yet activated'), (1, 'active'), (2, 'banned'), (3, 'deleted himself')])),
                ('date_joined', models.DateTimeField(default=datetime.datetime.utcnow, verbose_name='Member since')),
                ('banned_until', models.DateTimeField(help_text='leave empty to ban permanent', null=True, verbose_name='Banned until', blank=True)),
                ('post_count', models.IntegerField(default=0, verbose_name='Posts')),
                ('avatar', models.ImageField(upload_to=inyoka.portal.user.upload_to_avatar, null=True, verbose_name='Avatar', blank=True)),
                ('jabber', models.CharField(max_length=200, verbose_name='Jabber', blank=True)),
                ('icq', models.CharField(max_length=16, verbose_name='ICQ', blank=True)),
                ('msn', models.CharField(max_length=200, verbose_name='MSN', blank=True)),
                ('aim', models.CharField(max_length=200, verbose_name='AIM', blank=True)),
                ('yim', models.CharField(max_length=200, verbose_name='Yahoo Messenger', blank=True)),
                ('skype', models.CharField(max_length=200, verbose_name='Skype', blank=True)),
                ('wengophone', models.CharField(max_length=200, verbose_name='WengoPhone', blank=True)),
                ('sip', models.CharField(max_length=200, verbose_name='SIP', blank=True)),
                ('signature', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Signature', force_existing=False, blank=True)),
                ('coordinates_long', models.FloatField(null=True, verbose_name='Coordinates (longitude)', blank=True)),
                ('coordinates_lat', models.FloatField(null=True, verbose_name='Coordinates (latitude)', blank=True)),
                ('location', models.CharField(max_length=200, verbose_name='Residence', blank=True)),
                ('gpgkey', models.CharField(max_length=255, verbose_name='GPG key', blank=True)),
                ('occupation', models.CharField(max_length=200, verbose_name='Job', blank=True)),
                ('interests', models.CharField(max_length=200, verbose_name='Interests', blank=True)),
                ('website', models.URLField(verbose_name='Website', blank=True)),
                ('launchpad', models.CharField(max_length=50, verbose_name='Launchpad username', blank=True)),
                ('settings', inyoka.utils.database.JSONField(default={}, verbose_name='Settings')),
                ('_permissions', models.IntegerField(default=0, verbose_name='Privileges')),
                ('forum_last_read', models.IntegerField(default=0, verbose_name='Last read post', blank=True)),
                ('forum_read_status', models.TextField(verbose_name='Read posts', blank=True)),
                ('forum_welcome', models.TextField(verbose_name='Read welcome message', blank=True)),
                ('member_title', models.CharField(max_length=200, null=True, verbose_name='Team affiliation / Member title', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True, max_length=100)),
                ('changed', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('date', models.DateField(db_index=True)),
                ('time', models.TimeField(null=True, blank=True)),
                ('enddate', models.DateField(null=True, blank=True)),
                ('endtime', models.TimeField(null=True, blank=True)),
                ('description', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False, blank=True)),
                ('location', models.CharField(max_length=128, blank=True)),
                ('location_town', models.CharField(max_length=56, blank=True)),
                ('location_lat', models.FloatField(null=True, verbose_name='Degree of latitude', blank=True)),
                ('location_long', models.FloatField(null=True, verbose_name='Degree of longitude', blank=True)),
                ('visible', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'portal_event',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(db_index=True, unique=True, max_length=80, verbose_name='Group name', error_messages={'unique': 'This group name is already taken. Please choose another one.'})),
                ('is_public', models.BooleanField(default=False, help_text='Will be shown in the group overview and the user profile', verbose_name='Public profile')),
                ('permissions', models.IntegerField(default=0, verbose_name='Privileges')),
                ('icon', models.ImageField(upload_to='portal/team_icons', null=True, verbose_name='Team icon', blank=True)),
            ],
            options={
                'verbose_name': 'Usergroup',
                'verbose_name_plural': 'Usergroups',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=255, verbose_name='Title')),
                ('pub_date', models.DateTimeField(verbose_name='Date')),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Text', force_existing=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-pub_date',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PrivateMessageEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('read', models.BooleanField(default=False, verbose_name='Read')),
                ('folder', models.SmallIntegerField(null=True, verbose_name='Folder', choices=[(0, 'sent'), (1, 'inbox'), (2, 'trash'), (3, 'archive')])),
                ('message', models.ForeignKey(to='portal.PrivateMessage', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SessionInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=200, db_index=True)),
                ('last_change', models.DateTimeField(db_index=True)),
                ('subject_text', models.CharField(max_length=100, null=True)),
                ('subject_type', models.CharField(max_length=20)),
                ('subject_link', models.CharField(max_length=200, null=True)),
                ('action', models.CharField(max_length=500)),
                ('action_link', models.CharField(max_length=200, null=True)),
                ('category', models.CharField(max_length=200, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StaticFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(unique=True, max_length=100, verbose_name='Identifier', db_index=True)),
                ('file', models.FileField(upload_to='portal/files', verbose_name='File')),
                ('is_ikhaya_icon', models.BooleanField(default=False, help_text='Choose this if the file should appear as a article or category icon possibility', verbose_name='Is Ikhaya icon')),
            ],
            options={
                'verbose_name': 'Static file',
                'verbose_name_plural': 'Static files',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StaticPage',
            fields=[
                ('key', models.SlugField(primary_key=True, serialize=False, max_length=25, help_text='Will be used to generate the URL. Cannot be changed later.', unique=True, verbose_name='Key')),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('content', inyoka.utils.database.InyokaMarkupField(help_text='Inyoka syntax required.', simplify=False, verbose_name='Content', force_existing=False)),
            ],
            options={
                'verbose_name': 'Static page',
                'verbose_name_plural': 'Static pages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=200, db_index=True)),
                ('value', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notified', models.BooleanField(default=False, verbose_name='User was already notified')),
                ('ubuntu_version', models.CharField(max_length=5, null=True)),
                ('object_id', models.PositiveIntegerField(null=True, db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', null=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('content_rendered_old', models.TextField(db_column='content_rendered')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterOrderWithRespectTo(
            name='privatemessageentry',
            order_with_respect_to='message',
        ),
        migrations.AddField(
            model_name='user',
            name='_primary_group',
            field=models.ForeignKey(related_name='primary_users_set', db_column='primary_group_id', blank=True, to='portal.Group', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_name='user_set', verbose_name='Groups', to='portal.Group', blank=True),
            preserve_default=True,
        ),
    ]
