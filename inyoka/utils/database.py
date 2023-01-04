# -*- coding: utf-8 -*-
"""
    inyoka.utils.database
    ~~~~~~~~~~~~~~~~~~~~~

    This module provides some helpers to work with the database.

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json

from django.core.cache import cache, caches
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.signals import post_save as model_post_save_signal

from inyoka.markup.base import RenderContext, parse
from inyoka.utils.highlight import highlight_code

MAX_SLUG_INCREMENT = 999
_SLUG_INCREMENT_SUFFIXES = set(range(2, MAX_SLUG_INCREMENT + 1))


content_cache = caches['content']


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
    field = model._meta.get_field(column)
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
    filter = {'%s__startswith' % column: slug + '-'}
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
        return '/'.join((self.lock_key_base.strip('/'), str(self.id)))

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
        if value and isinstance(value, str):
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

    def pre_save(self, obj, add):
        value = obj.__dict__[self.name]
        if not isinstance(value, str):
            value = self.dumps(value)
        return value

    def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only)
        setattr(cls, self.name, SimpleDescriptor(self))


class BaseMarkupField(models.TextField):
    """
    Base Class for fields that needs to be rendered.
    """

    def __init__(self, application=None, redis_timeout=None, *args, **kwargs):
        self.application = application
        self.redis_timeout = redis_timeout
        super(BaseMarkupField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(BaseMarkupField, self).deconstruct()
        if self.application is not None:
            kwargs['application'] = self.application
        if self.redis_timeout is not None:
            kwargs['redis_timeout'] = self.redis_timeout
        return name, path, args, kwargs

    def get_redis_key(self, cls, instance, name):
        return '{application}:{model}:{id}:{field}'.format(
            application=self.application or 'portal',
            model=cls.__name__.lower(),
            id=instance.pk,
            field=name,
        )

    def contribute_to_class(self, cls, name):
        super(BaseMarkupField, self).contribute_to_class(cls, name)

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

        @property
        def field_rendered(inst_self):
            """
            Renders the content of the field.
            """
            key = self.get_redis_key(cls, inst_self, name)

            create_content = self.get_content_create_callback(inst_self, name)

            # Get the content from the cache. Creates the content if it does not
            # exist in redis, or if the cache is expired.
            return content_cache.get_or_set(key, create_content, self.redis_timeout)

        setattr(cls, 'get_{}_rendered'.format(name), staticmethod(self.get_render_method()))
        setattr(cls, '{}_rendered'.format(name), field_rendered)


class InyokaMarkupField(BaseMarkupField):
    """
    Field to save and render Inyoka markup.
    """

    def __init__(self, simplify=False, force_existing=False,
                 *args, **kwargs):
        self.simplify = simplify
        self.force_existing = force_existing
        super(InyokaMarkupField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(BaseMarkupField, self).deconstruct()
        if self.simplify is not None:
            kwargs['simplify'] = self.simplify
        if self.force_existing is not None:
            kwargs['force_existing'] = self.force_existing
        return name, path, args, kwargs

    def get_render_method(self):
        """
        Returns a callable that can be bound as staticmethod to the django model.

        This callable taks text as first argument and returns the rendered
        content.
        """
        def get_field_rendered(text, context=None):
            """
            Renders a specific text with the configuration of this field.

            This is needed to render text that is not in the database (for
            example the preview).

            The argument context has to be a RenderContext object or a
            dictonary containing additional keywordarguments to generate the
            RenderContext object.

            This method is bound to the django models as staticmethod, so it
            can also be called from the Model and not only from the instance.
            """
            if not isinstance(context, RenderContext):
                if context is None:
                    context = {}
                context = RenderContext(
                    obj=None,  # TODO: The parser shoud not be object specific
                    application=self.application,
                    simplified=self.simplify,
                    **context)

            node = parse(text, wiki_force_existing=self.force_existing)
            return node.render(context, format='html')

        return get_field_rendered

    def get_content_create_callback(self, inst_self, field_name):
        """
        Returns a callable, that renders the content.

        inst_self is an instance of a django model, which has the
        InyokaMarkupField. field_name is the name of the InyokaMarkupField.
        """

        def create_content(*args):
            """
            Calls get_render_method() with object specific arguments.

            get_render_method is a staticmethod and therefore can not use
            any value of the instance.
            """
            # Calls the method get_FIELDNAME_render_context_kwargs if the
            # django model has it.
            try:
                render_context = getattr(
                    inst_self,
                    'get_{}_render_context_kwargs'.format(field_name),
                )()
            except AttributeError:
                render_context = {}

            return self.get_render_method()(
                getattr(inst_self, field_name, ''),
                context=render_context)

        return create_content


class PygmentsField(BaseMarkupField):
    def get_render_method(self):
        def get_field_rendered(text, lang):
            """
            Renders a specific text with the configuration of this field.

            This is needed to render text that is not in the database (for
            example the preview).

            This method is bound to the django models as staticmethod, so it
            can also be called from the Model and not only from the instance.
            """
            return highlight_code(text, lang)

        return get_field_rendered

    def get_content_create_callback(self, inst_self, field_name):
        """
        Returns a callable, that renders the content.

        inst_self is an instance of a django model, which has the
        InyokaMarkupField. field_name is the name of the InyokaMarkupField.
        """

        def create_content(*args):
            """
            Calls get_render_method() with object specific arguments.

            get_render_method is a staticmethod and therefore can not use
            any value of the instance.
            """
            return self.get_render_method()(
                getattr(inst_self, field_name, ''),
                inst_self.lang)

        return create_content
