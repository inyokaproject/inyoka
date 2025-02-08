"""
    inyoka.utils.signals
    ~~~~~~~~~~~~~~~~~~~~

    This module is wrapper module for Django's signal module
    `django.db.models.signals` as well as a Inyoka specific implementation of
    signals, e.g. for removal of `Subscriptions`.

    :copyright: (c) 2007-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from inyoka.ikhaya.models import Article, Comment
from inyoka.portal.models import Subscription


@receiver(pre_delete, sender=Article)
def remove_subscriptons(sender, **kwargs):
    """
    This signal callback-function will remove all subscriptions belonging to
    the given instance
    """
    instance = kwargs.get('instance', None)
    if instance:
        ctype = ContentType.objects.get_for_model(sender)
        Subscription.objects.filter(content_type=ctype,
                object_id=instance.id).delete()


@receiver(pre_delete, sender=Article)
def remove_comments(sender, **kwargs):
    """
    This signal callback-function will remove all comments belonging to
    the given article instance
    """
    instance = kwargs.get('instance', None)
    if instance:
        Comment.objects.filter(article=instance).delete()
