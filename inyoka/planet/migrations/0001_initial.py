from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40, verbose_name='Name of the blog')),
                ('description', models.TextField(null=True, verbose_name='Description', blank=True)),
                ('blog_url', models.URLField(verbose_name='URL of the blog')),
                ('feed_url', models.URLField(verbose_name='URL of the feed')),
                ('icon', models.ImageField(upload_to='planet/icons', verbose_name='Icon', blank=True)),
                ('last_sync', models.DateTimeField(null=True, blank=True)),
                ('active', models.BooleanField(default=True, verbose_name='Index the blog')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Blog',
                'verbose_name_plural': 'Blogs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('guid', models.CharField(unique=True, max_length=200, db_index=True)),
                ('title', models.CharField(max_length=140)),
                ('url', models.URLField()),
                ('text', models.TextField()),
                ('pub_date', models.DateTimeField(db_index=True)),
                ('updated', models.DateTimeField(db_index=True)),
                ('author', models.CharField(max_length=50)),
                ('author_homepage', models.URLField(null=True, blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('blog', models.ForeignKey(to='planet.Blog', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-pub_date',),
                'get_latest_by': 'pub_date',
                'verbose_name': 'Entry',
                'verbose_name_plural': 'Entries',
            },
            bases=(models.Model,),
        ),
    ]
