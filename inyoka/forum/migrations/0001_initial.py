import datetime

from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to='forum/attachments/temp')),
                ('name', models.CharField(max_length=255)),
                ('comment', models.TextField(null=True, blank=True)),
                ('mimetype', models.CharField(max_length=100, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.CharField(unique=True, max_length=100, db_index=True)),
                ('description', models.CharField(max_length=500, blank=True)),
                ('position', models.IntegerField(default=0, db_index=True)),
                ('post_count', models.IntegerField(default=0)),
                ('topic_count', models.IntegerField(default=0)),
                ('newtopic_default_text', models.TextField(null=True, blank=True)),
                ('user_count_posts', models.BooleanField(default=True)),
                ('force_version', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Forum',
                'verbose_name_plural': 'Forums',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=250)),
                ('start_time', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('end_time', models.DateTimeField(null=True)),
                ('multiple_votes', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250)),
                ('votes', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PollVote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'forum_voter',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.IntegerField(default=None, db_index=True)),
                ('pub_date', models.DateTimeField(default=datetime.datetime.utcnow, db_index=True)),
                ('hidden', models.BooleanField(default=False)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('rendered_text_old', models.TextField(default='', null=True, db_column='rendered_text', blank=True)),
                ('has_revision', models.BooleanField(default=False)),
                ('has_attachments', models.BooleanField(default=False)),
                ('is_plaintext', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
            },
            bases=(models.Model, inyoka.utils.database.LockableObject),
        ),
        migrations.CreateModel(
            name='PostRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('store_date', models.DateTimeField(default=datetime.datetime.utcnow)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Privilege',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('positive', models.IntegerField(default=0, null=True)),
                ('negative', models.IntegerField(default=0, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, blank=True)),
                ('slug', models.CharField(max_length=50, blank=True)),
                ('view_count', models.IntegerField(default=0)),
                ('post_count', models.IntegerField(default=0)),
                ('sticky', models.BooleanField(default=False, db_index=True)),
                ('solved', models.BooleanField(default=False)),
                ('locked', models.BooleanField(default=False)),
                ('reported', inyoka.utils.database.InyokaMarkupField(simplify=False, null=True, force_existing=False, blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('ubuntu_version', models.CharField(max_length=5, null=True, blank=True)),
                ('ubuntu_distro', models.CharField(max_length=40, null=True, blank=True)),
                ('has_poll', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Topic',
                'verbose_name_plural': 'Topics',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WelcomeMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=120)),
                ('text', inyoka.utils.database.InyokaMarkupField(simplify=False, force_existing=False)),
                ('rendered_text_old', models.TextField(db_column='rendered_text')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
