from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ikhaya', '0003_auto_20151028_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=models.SlugField(help_text='Unique URL-part for the article. If not given, the slug will be generated from title.', max_length=100, verbose_name='Slug', blank=True),
        ),
    ]
