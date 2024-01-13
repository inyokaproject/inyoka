from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0011_auto_20160702_1801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='privilege',
            name='forum',
        ),
        migrations.RemoveField(
            model_name='privilege',
            name='group',
        ),
        migrations.RemoveField(
            model_name='privilege',
            name='user',
        ),
        migrations.AlterModelOptions(
            name='forum',
            options={'verbose_name': 'Forum', 'verbose_name_plural': 'Forums', 'permissions': (('delete_topic_forum', 'Can delete Topics from Forum'), ('view_forum', 'Can view Forum'), ('add_topic_forum', 'Can add Topic in Forum'), ('add_reply_forum', 'Can answer Topics in Forum'), ('sticky_forum', 'Can make Topics Sticky in Forum'), ('poll_forum', 'Can make Polls in Forum'), ('vote_forum', 'Can make Votes in Forum'), ('upload_forum', 'Can upload Attachments in Forum'), ('moderate_forum', 'Can moderate Forum'))},
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'verbose_name': 'Topic', 'verbose_name_plural': 'Topics', 'permissions': (('manage_reported_topic', 'Can manage reported Topics'),)},
        ),
        migrations.DeleteModel(
            name='Privilege',
        ),
    ]
