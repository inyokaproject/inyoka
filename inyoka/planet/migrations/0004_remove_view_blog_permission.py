# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planet', '0003_add_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blog',
            options={'ordering': ('name',), 'verbose_name': 'Blog', 'verbose_name_plural': 'Blogs', 'permissions': (('suggest_blog', 'Can suggest Blogs'),)},
        ),
    ]
