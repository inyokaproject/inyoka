# -*- coding: utf-8 -*-


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ikhaya', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='suggestion',
            name='author',
            field=models.ForeignKey(related_name='suggestion_set', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='suggestion',
            name='owner',
            field=models.ForeignKey(related_name='owned_suggestion_set', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='article',
            field=models.ForeignKey(to='ikhaya.Article', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='report',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='article',
            field=models.ForeignKey(to='ikhaya.Article', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Icon', blank=True, to='portal.StaticFile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='author',
            field=models.ForeignKey(related_name='article_set', verbose_name='Author', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Category', to='ikhaya.Category'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='article',
            name='icon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Icon', blank=True, to='portal.StaticFile', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='article',
            unique_together=set([('pub_date', 'slug')]),
        ),
    ]
