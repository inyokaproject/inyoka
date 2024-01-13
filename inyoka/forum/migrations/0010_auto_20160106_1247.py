import django.db.models.deletion
from django.db import migrations, models

import inyoka.utils.database


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0009_auto_20160106_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forum',
            name='description',
            field=models.CharField(max_length=500, verbose_name='Description', blank=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='force_version',
            field=models.BooleanField(default=False, verbose_name='Force version'),
        ),
        migrations.AlterField(
            model_name='forum',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='forum',
            name='newtopic_default_text',
            field=models.TextField(null=True, verbose_name='Default text for new topics', blank=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='parent',
            field=models.ForeignKey(related_name='_children', on_delete=django.db.models.deletion.PROTECT, verbose_name='Parent forum', blank=True, to='forum.Forum', null=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='position',
            field=models.IntegerField(default=0, verbose_name='Position', db_index=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='slug',
            field=models.SlugField(unique=True, max_length=100, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='forum',
            name='support_group',
            field=models.ForeignKey(related_name='forums', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Support group', blank=True, to='portal.Group', null=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='user_count_posts',
            field=models.BooleanField(default=True, help_text='If not set then posts of users in this forum are ignored in the post counter of the user.', verbose_name='Count user posts'),
        ),
        migrations.AlterField(
            model_name='forum',
            name='welcome_text',
            field=inyoka.utils.database.InyokaMarkupField(simplify=False, null=True, verbose_name='Welcome text', force_existing=False, blank=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='welcome_title',
            field=models.CharField(max_length=120, null=True, verbose_name='Welcome title', blank=True),
        ),
    ]
