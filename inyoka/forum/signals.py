# -*- coding: utf-8 -*-
"""
    inyoka.forum.signals
    ~~~~~~~~~~~~~~~~~~~~

    Signals for the forum.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.cache import cache
from django.db.models import F, Max
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from inyoka.forum.models import Forum, Post, Privilege, Topic
from inyoka.utils.database import find_next_increment
from inyoka.utils.text import slugify


@receiver(pre_save, sender=Forum)
@receiver(pre_save, sender=Topic)
def slugify_models(sender, **kwargs):
    if kwargs['raw']:
        return
    instance = kwargs.get('instance')
    if instance and not instance.slug:
        if isinstance(instance, Forum):
            instance.slug = find_next_increment(Forum, 'slug',
                slugify(instance.name))
        elif isinstance(instance, Topic):
            instance.slug = find_next_increment(Topic, 'slug',
                slugify(instance.title))


@receiver(post_save, sender=Forum)
def post_save_forum(sender, **kwargs):
    if kwargs['raw']:
        return
    cache.delete('forum/forums/%s' % kwargs['instance'].slug)
    if kwargs.get('created', False):
        cache.delete('forum/slugs')


@receiver(post_delete, sender=Forum)
def post_delete_forum(sender, **kwargs):
    cache.delete('forum/forums/%s' % kwargs['instance'].slug)
    cache.delete('forum/slugs')


@receiver(post_save, sender=Topic)
def post_save_topic(sender, **kwargs):
    if kwargs['raw']:
        return
    instance = kwargs.get('instance')
    if kwargs.get('created', False):
        instance.forum.topic_count.incr()


@receiver(post_delete, sender=Topic)
def post_delete_topic(sender, **kwargs):
    cache.delete('forum/reported_topic_count')


@receiver(pre_save, sender=Post)
def pre_save_post(sender, **kwargs):
    if kwargs['raw']:
        return
    instance = kwargs.get('instance')
    if instance.position is None:
        position = Post.objects.filter(topic=instance.topic) \
                               .aggregate(pos=Max('position'))['pos'] or 0
        instance.position = position + 1


@receiver(post_save, sender=Post)
def post_save_post(sender, **kwargs):
    if kwargs['raw']:
        return
    instance = kwargs.get('instance')
    created = kwargs.get('created', False)

    if created:
        if instance.topic.forum.user_count_posts:
            instance.author.post_count.incr()

        values = {'last_post': instance}

        if instance.topic.first_post is None:
            instance.topic.first_post = instance
            instance.topic.save()

        Topic.objects.filter(pk=instance.topic.pk).update(**values)
        instance.topic.post_count.incr()
        # refetch the topic instance since we use it later on
        instance.topic = Topic.objects.get(pk=instance.topic.pk)

        parent_ids = list(p.id for p in instance.topic.forum.parents)
        parent_ids.append(instance.topic.forum.id)
        instance.topic.forum.post_count.incr()
        for forum in instance.topic.forum.parents:
            forum.post_count.incr()
        Forum.objects.filter(id__in=parent_ids).update(last_post=instance)
        instance.topic.forum.invalidate_topic_cache()


@receiver(post_save, sender=Privilege)
@receiver(post_delete, sender=Privilege)
def clear_anonymous_privilege_cache(sender, **kwargs):
    if kwargs.get('raw'):
        return
    instance = kwargs.get('instance')
    if instance.user and instance.user.id == 1:
        # anonymous user, erase cache
        cache.delete('forum/acls/anonymous')
