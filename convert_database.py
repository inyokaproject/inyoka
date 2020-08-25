#!/usr/bin/env python
import itertools
import os
assert 'DJANGO_SETTINGS_MODULE' in os.environ

import django
django.setup()

from django.conf import settings
from django.db import connections, models, transaction

assert 'default' in settings.DATABASES
assert 'pg' in settings.DATABASES

from django.apps import apps

# fetch defined models
all_models = list(itertools.chain(*[list(app_config.get_models()) for app_config in apps.get_app_configs()]))

# add through models
through_models = []
for model in all_models:
    for field in model._meta.get_fields():
        if field.is_relation and hasattr(field, 'through'):
            through_models.append(field.through)

# Reduce to unique models if we had a fuckup
all_models = list(set(all_models + through_models))

pg_cursor = connections['pg'].cursor()


def get_pk(model):
    for f in model._meta.get_fields():
        if getattr(f, 'primary_key', False) and isinstance(f, models.AutoField):
            return f


# no idea why this is needed:
seq_mapping = {
    'portal_user_groups_id_seq': 'portal_user_groups_id_seq1'
}

del_queries = [
    "DELETE FROM wiki_revision WHERE NOT EXISTS (SELECT 1 FROM wiki_text WHERE wiki_text.id = wiki_revision.text_id);",
    "DELETE FROM wiki_revision WHERE NOT EXISTS (SELECT 1 FROM wiki_page WHERE wiki_page.id = wiki_revision.page_id);",
    "DELETE FROM forum_post WHERE NOT EXISTS (SELECT 1 FROM forum_topic WHERE forum_topic.id = forum_post.topic_id);",
    "DELETE FROM forum_poll WHERE NOT EXISTS (SELECT 1 FROM forum_topic WHERE forum_topic.id = forum_poll.topic_id);",
    "DELETE FROM forum_polloption WHERE NOT EXISTS (SELECT 1 FROM forum_poll WHERE forum_poll.id = forum_polloption.poll_id);",
    "DELETE FROM forum_voter WHERE NOT EXISTS (SELECT 1 FROM forum_poll WHERE forum_poll.id = forum_voter.poll_id);",
    "DELETE FROM forum_voter WHERE NOT EXISTS (SELECT 1 FROM portal_user WHERE portal_user.id = forum_voter.voter_id);",
    "DELETE FROM forum_postrevision WHERE NOT EXISTS (SELECT 1 FROM forum_post WHERE forum_post.id = forum_postrevision.post_id);",
    "DELETE FROM forum_attachment WHERE NOT EXISTS (SELECT 1 FROM forum_post WHERE forum_post.id = forum_attachment.post_id);",
]

with transaction.atomic(using='pg'):
    pg_cursor.execute('SET CONSTRAINTS ALL DEFERRED')
    # created by migrations, drop to get the real ones back
    pg_cursor.execute('TRUNCATE django_content_type CASCADE')
    pg_cursor.execute('TRUNCATE auth_permission CASCADE')
    pg_cursor.execute('TRUNCATE auth_group CASCADE')
    pg_cursor.execute('TRUNCATE portal_user CASCADE')
    for model in all_models:
        print("transfering", model)
        table_name = '%s_%s' % (model._meta.app_label, model._meta.model_name.lower())
        if getattr(model._meta, 'db_table', None):
            table_name = model._meta.db_table
        pk = get_pk(model)
        # if we have a pk we can use, chunk the data to save ram
        if pk:
            existing_objects = model.objects.aggregate(max=models.Max('pk'))['max'] or 0
            start, end = 0, 1000
            while start < existing_objects:
                print(start)
                model.objects.using('pg').bulk_create(model.objects.filter(pk__gte=start, pk__lt=end))
                start = end
                end += 1000
        else:
            model.objects.using('pg').bulk_create(model.objects.all())
        # figure out current seq value and reset sequences
        max_val = model.objects.using('pg').aggregate(max=models.Max('pk'))['max'] or 0
        if pk:
            sq_name = '%s_%s_seq' % (table_name, pk.name)
            if sq_name in seq_mapping:
                sq_name = seq_mapping[sq_name]
            pg_cursor.execute("SELECT setval('%s', %%s, true)" % sq_name, [max_val + 1])

    print("Deleting broken data")
    for q in del_queries:
        pg_cursor.execute(q)
