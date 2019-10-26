# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='author',
            field=models.ForeignKey(related_name='topics', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='topic',
            name='first_post',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='forum.Post', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='topic',
            name='forum',
            field=models.ForeignKey(related_name='topics', on_delete=django.db.models.deletion.PROTECT, to='forum.Forum'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='topic',
            name='last_post',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='forum.Post', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='topic',
            name='report_claimed_by',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='topic',
            name='reporter',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='privilege',
            name='forum',
            field=models.ForeignKey(to='forum.Forum'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='privilege',
            name='group',
            field=models.ForeignKey(to='portal.Group', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='privilege',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='postrevision',
            name='post',
            field=models.ForeignKey(related_name='revisions', to='forum.Post'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='post',
            name='topic',
            field=models.ForeignKey(related_name='posts', on_delete=django.db.models.deletion.PROTECT, to='forum.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pollvote',
            name='poll',
            field=models.ForeignKey(related_name='votings', to='forum.Poll'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pollvote',
            name='voter',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='polloption',
            name='poll',
            field=models.ForeignKey(related_name='options', to='forum.Poll'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poll',
            name='topic',
            field=models.ForeignKey(related_name='polls', to='forum.Topic', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forum',
            name='last_post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='forum.Post', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forum',
            name='parent',
            field=models.ForeignKey(related_name='_children', on_delete=django.db.models.deletion.PROTECT, to='forum.Forum', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forum',
            name='welcome_message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='forum.WelcomeMessage', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='post',
            field=models.ForeignKey(related_name='attachments', to='forum.Post', null=True),
            preserve_default=True,
        ),
    ]
