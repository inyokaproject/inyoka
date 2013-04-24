.. _utils-forms:

==============
Form Utilities
==============

.. py:module:: inyoka.utils.forms

.. py:currentmodule:: inyoka.utils.forms

This model contains extensions to the Django forms like special form
fields or validators.


.. py:function:: clear_surge_protection(request, form)

    Clean errors in parent form so that submitting inherited forms don't
    raise any errors.

    This function also cleanup the surge surge protection timer so that we
    get no nasty hickups by just submitting an inherited form and sending
    the whole form afterwards.


.. py:function:: validate_empty_text(value)

    :raise: Raises a :py:exc:`django.forms.ValidationError` if `value` is
        empty after removing leading and trailing white spaces.


.. py:function:: validate_signature(signature)

    Parse a signature and check if it's valid.

    :raise: Raises a :py:exc:`django.forms.ValidationError` if any of the
        following applies to `signaure`:

         * The signature is too long
         * The signature has too many lines
         * The signature has too many nested elements


.. py:class:: MultiField(forms.Field)

    This field validates a bunch of values using zero, one or more fields.
    If the value is just one string, a list is created.

    .. py:attribute:: widget

        A :py:class:`django.forms.SelectMultiple`

    .. py:method:: __init__([fields=(), \*args, \*\*kwargs])

    .. py:method:: clean(value)

        Validates that the value is a list or a tuple.


.. py:class:: UserField(forms.CharField)

    Allows to enter a username as text and validates if the given user
    exists.

    .. py:method:: prepare_value(data)

    .. py:method:: to_python(value)

        :raise: Raises a :py:exc:`django.forms.ValidationError` if no user was found.


.. py:class:: CaptchaWidget(Input)

    .. py:attribute:: input_type

        Defaults to ``'text'``

    .. py:method:: render(name, value[, attrs=None])


.. py:class:: DateTimeWidget(Input)

    .. py:attribute:: input_type

        Defaults to ``'text'``

    .. py:attribute:: value_type

        Defaults to ``'datetime'``

    .. py:method:: render(name, value[, attrs=None])


.. py:class:: DateWidget(DateTimeWidget)

    .. py:attribute:: input_type

        Defaults to ``'text'``

    .. py:attribute:: value_type

        Defaults to ``'date'``


.. py:class:: TimeWidget(DateTimeWidget)

    .. py:attribute:: input_type

        Defaults to ``'text'``

    .. py:attribute:: value_type

        Defaults to ``'time'``


.. py:class:: DateTimeField(forms.DateTimeField)

    .. py:attribute:: widget

        A :py:class:`DateTimeWidget`.

    .. py:method:: prepare_value(data)

    .. py:method:: clean(value)


.. py:class:: CaptchaField(forms.Field)

    .. py:attribute:: widget

        A :py:class:`CaptchaWidget`.

    .. py:method:: __init__([only_anonymous=False, \*args, \*\*kwargs])

    .. py:method:: clean(value)


.. py:class:: StrippedCharField(forms.CharField)

    .. py:attribute:: default_validators

        Defaults to a list containing only :py:func:`validate_empty_text`.


.. py:class:: HiddenCaptchaField(forms.Field)

    .. py:attribute:: widget

        A :py:class:`django.forms.HiddenInput`.

    .. py:method:: clean(value)


.. py:class:: EmailField(forms.CharField)

    .. py:method:: clean(value)


.. py:class:: JabberField(forms.CharField)

    .. py:method:: clean(value)


.. py:class:: SlugField(forms.CharField)

    .. py:method:: clean(value)
