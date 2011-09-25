#-*- coding: utf-8 -*-
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.db.models import Max, F
from django.db.models.signals import post_save, post_delete, pre_delete, pre_save

from inyoka.utils.database import find_next_increment
from inyoka.utils.text import slugify
from inyoka.portal.models import Subscription
from inyoka.portal.user import User
from inyoka.wiki.models import Page
from inyoka.forum.models import Forum, Topic, Post, Privilege


@receiver(pre_save, sender=Forum)
@receiver(pre_save, sender=Topic)
def slugify_models(sender, **kwargs):
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
    cache.delete('forum/forums/%s' % kwargs['instance'].slug)
    if kwargs.get('created', False):
        cache.delete('forum/slugs')


@receiver(post_delete, sender=Forum)
def post_delete_forum(sender, **kwargs):
    cache.delete('forum/forums/%s' % kwargs['instance'].slug)
    cache.delete('forum/slugs')


@receiver(post_save, sender=Topic)
def post_save_topic(sender, **kwargs):
    instance = kwargs.get('instance')
    if kwargs.get('created', False):
        Forum.objects.filter(id=instance.forum.id) \
                     .update(topic_count=F('topic_count') + 1)


@receiver(pre_delete, sender=Topic)
def pre_delete_topic(sender, **kwargs):
    instance = kwargs.get('instance')
    if not instance.forum:
        return

    ids = [p.id for p in instance.forum.parents[:-1]]
    ids.append(instance.forum_id)
    if not ids:
        return

    # set a new last_post_id because of integrity errors and
    # decrease the topic_count
    # FIXME: This might set wrong values if the parent forum has topics too
    # and isn't just a category
    last_forum_post = Post.objects.only('id') \
        .filter(forum__id__in=ids) \
        .exclude(topic=instance) \
        .aggregate(id=Max('id'))['id']
    Forum.objects.filter(id__in=ids).update(last_post=last_forum_post)

    Topic.objects.filter(id=instance.id).update(
        last_post=None,
        first_post=None)

    for post in instance.posts.all():
        post.delete()

    Forum.objects.filter(id=instance.forum.id).update(
        topic_count=F('topic_count') - 1)

    # Delete subscriptions and remove wiki page discussions
    ctype = ContentType.objects.get_for_model(Topic)
    Subscription.objects.filter(content_type=ctype, object_id=instance.id).delete()
    Page.objects.filter(topic=instance).update(topic=None)


@receiver(post_delete, sender=Topic)
def post_delete_topic(sender, **kwargs):
    cache.delete('forum/reported_topic_count')


@receiver(pre_save, sender=Post)
def pre_save_post(sender, **kwargs):
    instance = kwargs.get('instance')
    if not instance.is_plaintext:
        instance.rendered_text = instance.render_text()
    if instance.position is None:
        position = Post.objects.filter(topic=instance.topic) \
                               .aggregate(pos=Max('position'))['pos'] or 0
        instance.position = position + 1


@receiver(post_save, sender=Post)
def post_save_post(sender, **kwargs):
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
    instance = kwargs.get('instance')
    if instance.user and instance.user.id == 1:
        # anonymous user, erase cache
        cache.delete('forum/acls/anonymous')
