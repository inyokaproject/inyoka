# -*- coding: utf-8 -*-
"""
    inyoka.utils.database
    ~~~~~~~~~~~~~~~~~~~~~

    This module provides some helpers to work with the database.

    :copyright: (c) 2007-2015 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
import operator

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.expressions import F, ExpressionNode
from django.db.models.signals import post_save as model_post_save_signal
from django.core.cache import get_cache

from inyoka.markup import parse, RenderContext


EXPRESSION_NODE_CALLBACKS = {
    ExpressionNode.ADD: operator.add,
    ExpressionNode.SUB: operator.sub,
    ExpressionNode.MUL: operator.mul,
    ExpressionNode.DIV: operator.div,
    ExpressionNode.MOD: operator.mod,
    ExpressionNode.BITAND: operator.and_,
    ExpressionNode.BITOR: operator.or_,
}


MAX_SLUG_INCREMENT = 999
_SLUG_INCREMENT_SUFFIXES = set(range(2, MAX_SLUG_INCREMENT + 1))


content_cache = get_cache('content')


class CannotResolve(Exception):
    pass


def _strip_ending_nums(string):
    if '-' in string and string.rsplit('-', 1)[-1].isdigit():
        return string.rsplit('-', 1)[0]
    return string


def find_next_increment(model, column, string, **query_opts):
    """Get the next incremented string based on `column` and `string`.

    Example::

        find_next_increment(Article, 'slug', 'article name')
    """
    field = model._meta.get_field_by_name(column)[0]
    max_length = field.max_length if hasattr(field, 'max_length') else None
    # We are pretty defensive here and make sure we always have 4 characters
    # left, to be able to append up to 999 slugs (-1 ... -999)
    counter_length = len(str(MAX_SLUG_INCREMENT)) + 1
    assert max_length is None or max_length > counter_length
    slug = string[:max_length - counter_length] if max_length is not None else string
    filter = {column: slug}
    filter.update(query_opts)
    if not model.objects.filter(**filter).exists():
        return slug
    filter = {'%s__startswith' % column: slug + u'-'}
    filter.update(query_opts)
    existing = model.objects.filter(**filter).values_list(column, flat=True)
    # strip of the common prefix
    prefix_len = len(slug) + 1
    slug_numbers = [s[prefix_len:] for s in existing]
    # find the next free slug number
    slug_numbers = {int(i) for i in slug_numbers if i.isdigit()}
    unused_numbers = _SLUG_INCREMENT_SUFFIXES - slug_numbers
    if unused_numbers:
        num = min(unused_numbers)
    elif max_length is None:
        num = max(slug_numbers) + 1
    else:
        raise RuntimeError(
            "No suitable slug increment for %s found. No unused increment "
            "or max_length not None." % slug
        )
    return '{0}-{1}'.format(slug, num)


def get_simplified_queryset(queryset):
    """Returns a QuerySet with following modifications:

     * without Aggregators
     * unused select fields
     * .only('id')
     * no order_by

    The resultung QuerySet can be used for efficient .count() queries.
    """
    cqry = queryset._clone().only('id')
    cqry.query.clear_select_fields()
    cqry.query.clear_ordering(True)
    cqry.query.clear_limits()
    cqry.query.select_for_update = False
    cqry.query.select_related = False
    cqry.query.related_select_cols = []
    cqry.query.related_select_fields = []
    return cqry


def _resolve(instance, node):
    if isinstance(node, F):
        return getattr(instance, node.name)
    elif isinstance(node, ExpressionNode):
        return _resolve(instance, node)
    return node


def resolve_expression_node(instance, node):
    op = EXPRESSION_NODE_CALLBACKS.get(node.connector, None)
    if not op:
        raise CannotResolve
    runner = _resolve(instance, node.children[0])
    for n in node.children[1:]:
        runner = op(runner, _resolve(instance, n))
    return runner


# Partially copied from
# https://github.com/andymccurdy/django-tips-and-tricks/
def update_model(instance, **kwargs):
    """Atomically update instance, setting field/value pairs from kwargs"""
    if not instance:
        return []

    instances = instance if isinstance(instance, (set, list, tuple)) else [instance]

    query_kwargs = kwargs.copy()
    for instance in instances:
        # fields that use auto_now=True should be updated corrected, too!
        for field in instance._meta.fields:
            exists = hasattr(field, 'auto_now')
            if exists and field.auto_now and field.name not in kwargs:
                kwargs[field.name] = field.pre_save(instance, False)
            if field.name in kwargs and isinstance(field, JSONField):
                query_kwargs[field.name] = field.dumps(kwargs[field.name])

    manager = instances[0].__class__._default_manager
    if len(instances) == 1:
        qset = manager.filter(pk=instances[0].pk)
    else:
        qset = manager.filter(pk__in=[i.pk for i in instances])
    rows_affected = qset.update(**query_kwargs)

    # apply the updated args to the instance to mimic the change
    # note that these might slightly differ from the true database values
    # as the DB could have been updated by another thread. callers should
    # retrieve a new copy of the object if up-to-date values are required
    for k, v in kwargs.iteritems():
        if isinstance(v, ExpressionNode):
            v = resolve_expression_node(instance, v)
        for instance in instances:
            setattr(instance, k, v)

    return rows_affected


def model_or_none(pk, reference):
    if not reference or pk == reference.pk:
        return None
    try:
        return reference.__class__.objects.get(pk=pk)
    except reference.DoesNotExist:
        return None


class LockableObject(object):

    #: Must be defined by an inherited model.
    lock_key_base = None

    def _get_lock_key(self):
        return u'/'.join((self.lock_key_base.strip('/'), unicode(self.id)))

    def lock(self, request):
        """Lock for 15 Minutes"""
        existing = cache.get(self._get_lock_key())
        if existing is None and self.id:
            cache.set(self._get_lock_key(), request.user.username, 900)
        if existing is not None and existing != request.user.username:
            return existing
        return False

    def unlock(self):
        cache.delete(self._get_lock_key())


class SimpleDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, owner):
        value = obj.__dict__[self.field.name]
        # we don't try to deserialize empty strings
        if value and isinstance(value, basestring):
            value = self.field.loads(value)
            obj.__dict__[self.field.name] = value
        return value

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = value


class JSONField(models.TextField):
    def loads(self, s):
        return json.loads(s)

    def dumps(self, obj):
        return json.dumps(obj, cls=DjangoJSONEncoder)

    def pre_save(self, obj, create):
        value = obj.__dict__[self.name]
        if not isinstance(value, basestring):
            value = self.dumps(value)
        return value

    def contribute_to_class(self, cls, name):
        super(JSONField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, SimpleDescriptor(self))

    def south_field_triple(self):
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return 'django.db.models.TextField', args, kwargs


class InyokaMarkupField(models.TextField):
    """
    Field to save and render Inyoka markup.
    """

    def __init__(self, application=None, simplify=False, force_existing=False,
                 redis_timeout=None, *args, **kwargs):
        self.application = application
        self.simplify = simplify
        self.force_existing = force_existing
        self.redis_timeout = None
        super(InyokaMarkupField, self).__init__(*args, **kwargs)

    def get_redis_key(self, cls, instance, name):
        return '{application}:{model}:{id}:{field}'.format(
            application=self.application or 'portal',
            model=cls.__name__.lower(),
            id=instance.pk,
            field=name,
        )

    def contribute_to_class(self, cls, name):
        super(InyokaMarkupField, self).contribute_to_class(cls, name)

        # Register to the post_save signal, to delete the redis cache if the
        # content changes
        def delete_cache_receiver(sender, instance, created, **kwargs):
            if not created:
                key = self.get_redis_key(cls, instance, name)
                content_cache.delete(key)

        model_post_save_signal.connect(
            delete_cache_receiver,
            sender=cls,
            weak=False,
            dispatch_uid="{cls}{field}".format(
                cls=cls.__name__,
                field=name,
            )
        )

        def render_method(text):
            """
            Renders a specific text with the configuration of this field.

            This is needed to render text that is not in the database (for
            example the preview).
            """
            context = RenderContext(
                obj=None,  # TODO: The parser shoud not be object specific
                application=self.application,
                simplified=self.simplify,
            )
            node = parse(text, wiki_force_existing=self.force_existing)
            return node.render(context, format='html')

        @property
        def render(inst_self):
            """
            Renders the content of the field.
            """
            key = self.get_redis_key(cls, inst_self, name)

            def create_content(*args):
                return render_method(getattr(inst_self, name, ''))

            # Get the content from the cache. Creates the content if it does not
            # exist in redis, or if the cache expired.
            return content_cache.get_or_set(key, create_content, self.redis_timeout)

        setattr(cls, '{}_rendered'.format(name), render)
        setattr(cls, 'get_{}_rendered'.format(name), staticmethod(render_method))


    def south_field_triple(self):
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)
        return 'django.db.models.TextField', args, kwargs
