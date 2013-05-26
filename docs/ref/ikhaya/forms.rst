.. _ikhaya-forms:

============
Ikhaya forms
============

.. py:module:: inyoka.ikhaya.forms

.. py:currentmodule:: inyoka.ikhaya.forms


.. py:class:: SuggestArticleForm(django.forms.ModelForm)

    :py:class:`django.forms.ModelForm`

    .. py:method:: save(user, [commit=True])

    .. py:class:: Meta

        .. py:attribute:: fields

        .. py:attribute:: model

            :py:class:`inyoka.ikhaya.models.Suggestion`

        .. py:attribute:: widgets


.. py:class:: EditCommentForm(django.forms.Form)

    :py:class:`django.forms.Form`

    .. py:attribute:: text


.. py:class:: EditArticleForm(django.forms.ModelForm)

    :py:class:`django.forms.ModelForm`

    .. py:attribute:: author

    .. py:attribute:: pub_date

    .. py:attribute:: updated

    .. py:method:: clean_slug()

    .. py:method:: save()

    .. py:class:: Meta

        .. py:attribute:: exclude

        .. py:attribute:: model

            :py:class:`inyoka.ikhaya.models.Article`

        .. py:attribute:: widgets


.. py:class:: EditPublicArticleForm(EditArticleForm)

    :py:class:`EditArticleForm`

    .. py:class:: Meta(EditArticleForm.Meta)

        .. py:attribute:: exclude


.. py:class:: EditCategoryForm(django.forms.ModelForm)

    :py:class:`django.forms.ModelForm`

    .. py:class:: Meta

        .. py:attribute:: exclude

        .. py:attribute:: model

            :py:class:`inyoka.ikhaya.models.Category`


.. py:class:: NewEventForm(django.forms.ModelForm)

    :py:class:`django.forms.ModelForm`

    .. py:method:: clean()

    .. py:method:: save(user)

    .. py:class:: Meta

        .. py:attribute:: exclude

        .. py:attribute:: model

            :py:class:`inyoka.ikhaya.models.Event`

        .. py:attribute:: widgets


.. py:class:: EditEventForm(NewEventForm)

    :py:class:`NewEventForm`

    .. py:attribute:: visible

    .. py:class:: Meta(NewEventForm.Meta)

        .. py:attribute:: exclude
