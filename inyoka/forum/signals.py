# -*- coding: utf-8 -*-
"""
    inyoka.forum.signals
    ~~~~~~~~~~~~~~~~~~~~

    Signals for the forum.

    :copyright: (c) 2011-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from django.dispatch import receiver
from django.db.models import F, Max
from django.core.cache import cache
from django.db.models.signals import pre_save, post_save, post_delete

from inyoka.utils.text import slugify
from inyoka.portal.user import User
from inyoka.forum.models import Post, Topic, Forum, Privilege
from inyoka.utils.database import find_next_increment


@receiver(pre_save, sender=Forum)
@receiver(pre_save, sender=Topic)
def slugify_models(sender, **kwargs):
    if kwargs['raw']: return
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
    if kwargs['raw']: return
    cache.delete('forum/forums/%s' % kwargs['instance'].slug)
    if kwargs.get('created', False):
        cache.delete('forum/slugs')


@receiver(post_delete, sender=Forum)
def post_delete_forum(sender, **kwargs):
    cache.delete('forum/forums/%s' % kwargs['instance'].slug)
    cache.delete('forum/slugs')


@receiver(post_save, sender=Topic)
def post_save_topic(sender, **kwargs):
    if kwargs['raw']: return
    instance = kwargs.get('instance')
    if kwargs.get('created', False):
        Forum.objects.filter(id=instance.forum.id) \
                     .update(topic_count=F('topic_count') + 1)


@receiver(post_delete, sender=Topic)
def post_delete_topic(sender, **kwargs):
    kwargs['instance'].reindex()
    cache.delete('forum/reported_topic_count')


@receiver(pre_save, sender=Post)
def pre_save_post(sender, **kwargs):
    if kwargs['raw']: return
    instance = kwargs.get('instance')
    if not instance.is_plaintext:
        instance.rendered_text = instance.render_text()
    if instance.position is None:
        position = Post.objects.filter(topic=instance.topic) \
                               .aggregate(pos=Max('position'))['pos'] or 0
        instance.position = position + 1


@receiver(post_save, sender=Post)
def post_save_post(sender, **kwargs):
    if kwargs['raw']: return
    instance = kwargs.get('instance')
    created = kwargs.get('created', False)

    if created:
        if instance.topic.forum.user_count_posts:
            User.objects.filter(id=instance.author.id) \
                        .update(post_count=F('post_count') + 1)
            cache.delete('portal/user/%d' % instance.author.id)

        values = {'post_count': F('post_count') + 1,
                  'last_post': instance}

        if instance.topic.first_post is None:
            instance.topic.first_post = instance
            instance.topic.save()

        Topic.objects.filter(pk=instance.topic.pk).update(**values)
        # refetch the topic instance since we use it later on
        instance.topic = Topic.objects.get(pk=instance.topic.pk)

        parent_ids = list(p.id for p in instance.topic.forum.parents)
        parent_ids.append(instance.topic.forum.id)
        Forum.objects.filter(id__in=parent_ids).update(
            post_count=F('post_count') + 1,
            last_post=instance)
        instance.topic.forum.invalidate_topic_cache()


@receiver(post_save, sender=Privilege)
@receiver(post_delete, sender=Privilege)
def clear_anonymous_privilege_cache(sender, **kwargs):
    if kwargs.get('raw'): return
    instance = kwargs.get('instance')
    if instance.user and instance.user.id == 1:
        # anonymous user, erase cache
        cache.delete('forum/acls/anonymous')
