# -*- coding: utf-8 -*-
"""
    inyoka.forum.signals
    ~~~~~~~~~~~~~~~~~~~~

    Signals for the forum.

    :copyright: (c) 2011-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.core.cache import cache
from django.db.models import Max
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from inyoka.forum.models import Forum, Post, Topic
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
    cache.delete('forum/forums/{}'.format(kwargs['instance'].slug))
    if kwargs.get('created', False):
        cache.delete('forum/slugs')


@receiver(post_delete, sender=Forum)
def post_delete_forum(sender, **kwargs):
    cache.delete('forum/forums/{}'.format(kwargs['instance'].slug))
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
def post_save_post(sender, instance, created, raw, **kwargs):
    if raw:
        return

    if created:
        # Increase post count of the author, if the forum counts posts
        if instance.topic.forum.user_count_posts:
            instance.author.post_count.incr()

        # If this is the first post of a topic, then safe it as topic.first_pots
        if instance.topic.first_post is None:
            instance.topic.first_post = instance

        # Save the post as last post of his topic
        instance.topic.last_post = instance
        instance.topic.save()

        # Increase the post count of the topic and the forum and its parents
        instance.topic.post_count.incr()
        instance.topic.forum.post_count.incr()
        for forum in instance.topic.forum.parents:
            forum.post_count.incr()

        # Update last_post of the forum and its parents
        parent_forums = [instance.topic.forum] + instance.topic.forum.parents
        (Forum.objects.filter(id__in=[forum.id for forum in parent_forums])
              .update(last_post=instance))

        # Invalidate Cache
        instance.topic.forum.invalidate_topic_cache()
        cache_keys = ['forum/forums/{}'.format(forum.slug) for forum in parent_forums]
        cache.delete_many(cache_keys)
