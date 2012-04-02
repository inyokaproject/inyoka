.. _ikhaya-models:

=============
Ikhaya models
=============

.. py:module:: inyoka.ikhaya.models

.. py:currentmodule:: inyoka.ikhaya.models

Managers
========

.. py:class:: ArticleManager(django.db.models.Manager)

    .. py:method:: get_cached(keys)

    .. py:method:: get_latest_articles([category=None [, count=10]])

    .. py:method:: get_query_set()


.. py:class:: SuggestionManager(django.db.models.Manager)

    .. py:method:: delete(ids)


.. py:class:: CommentManager(django.db.models.Manager)

    .. py:method:: get_latest_comments([article=None [, count=10]])


Models
======

.. py:class:: Category(django.db.models.Model)

    .. py:attribute:: icon

    .. py:attribute:: name

    .. py:attribute:: slug


    .. py:method:: get_absolute_url([action='show'])

    .. py:method:: save([*args [, **kwargs]])


    .. py:class:: Meta

        .. py:attribute:: verbose_name

        .. py:attribute:: verbose_name_plural


.. py:class:: Article(django.db.models.Model, inyoka.utils.database.LockableObject)

    .. py:attribute:: article_icon()

    .. py:attribute:: author

    .. py:attribute:: category

    .. py:attribute:: comments()

    .. py:attribute:: comment_count

    .. py:attribute:: comments_enabled

    .. py:attribute:: drafts

    .. py:attribute:: hidden()

    .. py:attribute:: icon

    .. py:attribute:: intro

    .. py:attribute:: is_xhtml

    .. py:attribute:: local_pub_datetime

    .. py:attribute:: local_updated

    .. py:attribute:: lock_key_base

    .. py:attribute:: objects

    .. py:attribute:: pub_date

    .. py:attribute:: pub_time

    .. py:attribute:: pub_datetime

    .. py:attribute:: public

    .. py:attribute:: published

    .. py:attribute:: rendered_intro()

    .. py:attribute:: rendered_text()

    .. py:attribute:: simplified_intro()

    .. py:attribute:: simplified_text()

    .. py:attribute:: slug

    .. py:attribute:: stamp()

    .. py:attribute:: subject

    .. py:attribute:: text

    .. py:attribute:: updated


    .. py:method:: delete()

    .. py:method:: get_absolute_url([action='show'])

    .. py:method:: _render(text, key)

    .. py:method:: save([*args [, **kwargs]])

    .. py:method:: _simplify(text, key)

    .. py:method:: update_search()


    .. py:class:: Meta


.. py:class:: Report(django.db.models.Model)

    .. py:attribute:: article

    .. py:attribute:: text

    .. py:attribute:: author

    .. py:attribute:: pub_date

    .. py:attribute:: deleted

    .. py:attribute:: solved

    .. py:attribute:: rendered_text


    .. py:method:: get_absolute_url([action='show'])

    .. py:method:: save([*args [, **kwargs]])


.. py:class:: Suggestion(django.db.models.Model)

    .. py:attribute:: author

    .. py:attribute:: intro

    .. py:attribute:: notes

    .. py:attribute:: objects

    .. py:attribute:: owner

    .. py:attribute:: pub_date

    .. py:attribute:: rendered_intro()

    .. py:attribute:: rendered_notes()

    .. py:attribute:: rendered_text()

    .. py:attribute:: text

    .. py:attribute:: title


    .. py:method:: get_absolute_url()


    .. py:class:: Meta

        .. py:attribute:: verbose_name

        .. py:attribute:: verbose_name_plural

.. py:class:: Comment(django.db.models.Model)

    .. py:attribute:: article

    .. py:attribute:: author

    .. py:attribute:: deleted

    .. py:attribute:: pub_date

    .. py:attribute:: objects

    .. py:attribute:: rendered_text

    .. py:attribute:: text


    .. py:method:: get_absolute_url([action='show'])

    .. py:method:: save([*args [, **kwargs]])


.. py:class:: Event(django.db.models.Model)

    .. py:attribute:: author

    .. py:attribute:: changed

    .. py:attribute:: coordinates_url()

    .. py:attribute:: created

    .. py:attribute:: date

    .. py:attribute:: description

    .. py:attribute:: enddate

    .. py:attribute:: endtime

    .. py:attribute:: location

    .. py:attribute:: location_lat

    .. py:attribute:: location_long

    .. py:attribute:: location_town

    .. py:attribute:: name

    .. py:attribute:: natural_coordinates()

    .. py:attribute:: rendered_description()

    .. py:attribute:: simple_coordinates()

    .. py:attribute:: slug

    .. py:attribute:: time

    .. py:attribute:: visible


    .. py:method:: friendly_title(with_html_link=False)

    .. py:method:: get_absolute_url([action='show'])

    .. py:method:: save([*args [, **kwargs]])


    .. py:class:: Meta

        .. py:attribute:: db_table
        .. py:attribute:: app_label


.. py:class:: ArticleSearchAuthDecider(object)


.. py:class:: IkhayaSearchAdapter(inyoka.utils.search.SearchAdapter)

    .. py:attribute:: type_id

    .. py:attribute:: auth_decider


    .. py:method:: extract_data(article)

    .. py:method:: get_doc_ids()

    .. py:method:: get_objects(docids)

    .. py:method:: recv(docid)

    .. py:method:: recv_multi(docids)

    .. py:method:: store_object(article [, connection=None])
