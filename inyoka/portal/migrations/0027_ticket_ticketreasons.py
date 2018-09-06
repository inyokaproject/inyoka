# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.db import migrations, models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

import inyoka.utils.database


SPAM_REASON=_(u'Spam')
OTHER_REASON=_(u'Other')


def add_ticketreason_defaults(apps, schema_editor):

    TicketReason = apps.get_model("portal", "TicketReason")

    # create the system Spam reason for posts
    TicketReason.objects.create(
        system_defined = True,
        content_type = ContentType.objects.using(db_alias).get(app_label="forum", model="post"),
        reason = SPAM_REASON
    )

    # create the system Other reason with for posts
    TicketReason.objects.create(
        system_defined = True,
        content_type = ContentType.objects.using(db_alias).get(app_label="forum", model="post"),
        reason = OTHER_REASON
    )


def migrate_old_tickets(apps, schema_editor):

    Topic = apps.get_model("forum", "Topic")
    Ticket = apps.get_model("portal", "Ticket")
    TicketReason = apps.get_model("portal", "TicketReason")

    db_alias = schema_editor.connection.alias
    topics = Topic.objects.using(db_alias).filter(reported__isnull=False).order_by('slug').all()

    for topic in topics:
        ticket = Ticket()

        ticket.content_object = topic.first_post

        ticket.reporting_user = topic.reporter
        ticket.reporting_time = datetime.utcnow()
        ticket.reporter_comment = u'Automatically migrated from old ticketing system, moved from topic to first post. Original message is: %s' % topic.reported
        ticket.reason = TicketReason.objects.get(reason=OTHER_REASON)
        if topic.report_claimed_by != None:
            ticket.owning_user = topic.report_claimed_by

        ticket.save(using=db_alias)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('portal', '0026_remove_user_forum_last_read'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(null=True, db_index=True)),
                ('reporting_time', models.DateTimeField(verbose_name='Reported at', db_index=True)),
                ('owned_time', models.DateTimeField(null=True, verbose_name='Owned at', db_index=True)),
                ('closed_time', models.DateTimeField(null=True, verbose_name='Closed at', db_index=True)),
                ('state', models.SmallIntegerField(default=0, db_index=True, verbose_name='State', choices=[(0, 'Open'), (1, 'In progress'), (2, 'Closed')])),
                ('reporter_comment', inyoka.utils.database.InyokaMarkupField(simplify=False, verbose_name='Reporter comment', force_existing=False)),
                ('owner_comment', inyoka.utils.database.InyokaMarkupField(simplify=False, null=True, verbose_name='Owner comment', force_existing=False)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('owning_user', models.ForeignKey(related_name='ticket_owning_user', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TicketReason',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.CharField(max_length=200, null=True)),
                ('system_defined', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': 'Ticket Reason',
                'verbose_name_plural': 'Ticket Reasons',
            },
        ),
        migrations.AddField(
            model_name='ticket',
            name='reason',
            field=models.ForeignKey(to='portal.TicketReason', null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='reporting_user',
            field=models.ForeignKey(related_name='ticket_reporting_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(add_ticketreason_defaults),
        migrations.RunPython(migrate_old_tickets),
    ]
