.. _utils-database:

==================
Database Utilities
==================

.. py:module:: inyoka.utils.database

.. py:currentmodule:: inyoka.utils.database

This module provides some helpers to work with the database.

.. py:data:: EXPRESSION_NODE_CALLBACKS

    This dictionary maps the operators `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `AND`
    and `OR` from django.db.models.expressions.ExpressionNode to
    the operators from :py:mod:`operator`.


.. py:class:: CannotResolve(Exception)


.. py:function:: _strip_ending_nums(string)

    If `string` contins at least one ``'-'``, the rightmost part
    after will be truncated if and only if it is an integer.


.. py:function:: find_next_increment(model, column, string[, stripdate=False, \*\*query_opts])

    Get the next incremented string based on `column` and `string`.
    This function is the port of `find_next_increment` for Django
    models.

    Example::

        find_next_increment(Article, 'slug', 'article name')


.. py:function:: get_simplified_queryset(queryset)

    Returns a QuerySet with following modifications:

     * without Aggregators
     * unused select fields
     * ``.only('id')``
     * no ``order_by``

    The resultung QuerySet can be used for efficient .count() queries.


.. py:function:: _resolve(instance, node)


.. py:function:: resolve_expression_node(instance, node)


.. py:function:: update_model(instance, **kwargs)

    Atomically update instance, setting field/value pairs from kwargs

    .. note::

        Partially copied from
        https://github.com/andymccurdy/django-tips-and-tricks/


.. py:function:: model_or_none(pk, reference)


.. py:class:: LockableObject(object)

    .. py:attribute:: lock_key_base

        Must be defined by an inherited model. Defaults to ``None``.

    .. py:method:: _get_lock_key()

        :return: The :py:attr:`lock_key_base` joined with the `id` of the referring model instance.
        :rtype: unicode

    .. py:method:: lock(request)

        Lock for 15 Minutes

    .. py:method:: unlock()

        Remove the lock started by :py:meth:`lock`.


.. py:class:: SimpleDescriptor(object)

    .. py:method:: __init__(field)

    .. py:method:: __get__(obj, owner)

    .. py:method:: __set__(obj, value)


.. py:class:: JSONField(models.TextField)

    .. py:method:: loads(s)

    .. py:method:: dumps(obj)

    .. py:method:: pre_save(obj, create)

    .. py:method:: contribute_to_class(cls, name)

    .. py:method:: south_field_triple()
