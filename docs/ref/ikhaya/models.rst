.. _ikhaya-models:

=============
Ikhaya models
=============

.. py:module:: inyoka.ikhaya.models

.. py:currentmodule:: inyoka.ikhaya.models


.. py:function:: _get_not_cached_articles(keys, cache_values)

    Return a tuple of (dates, slugs) for all keys in cache_values that are
    ``None``.


Managers
========

.. py:class:: ArticleManager(django.db.models.Manager)

    .. py:method:: get_cached(keys)

        Get some articles from the cache. `keys` must be a list with (`pub_date`,
        `slug`) pairs. Missing entries from the cache are automatically fetched
        from the database. This method should be also used for retrieving
        single objects.

        ATTENTION: All articles which are returned from this function don't
        contain any text or intro (but they will contain rendered_text and
        rendered_intro). So do NEVER save any article returned by this
        function.

    .. py:method:: get_latest_articles([category=None [, count=10]])

        Return `count` lastest articles for the category `category` or for all
        categories if None.

        :param category: Takes the slug of the category or ``None`` for all
                         categories
        :param count: maximum retrieve this many articles. Defaults to 10
        :type category: string or ``None``
        :type count: integer

    .. py:method:: get_query_set()


.. py:class:: SuggestionManager(django.db.models.Manager)

    .. py:method:: delete(ids)

        Deletes a list of suggestions with only one query and refresh the
        caches.


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

        This returns all the comments for this article

    .. py:attribute:: comment_count

    .. py:attribute:: comments_enabled

    .. py:attribute:: drafts

    .. py:attribute:: hidden()

        This returns a boolean whether this article is not visible for normal
        users.

        Articles that are not published or whose pub_date is in the
        future aren't shown for a normal user.

        :rtype: A boolean

    .. py:attribute:: icon

    .. py:attribute:: intro

    .. py:attribute:: is_xhtml

    .. py:attribute:: local_pub_datetime

    .. py:attribute:: local_updated

    .. py:data:: lock_key_base

        Defaults to: ``'ikhaya/article_lock'``

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

        Return the year/month/day part of an article url

    .. py:attribute:: subject

    .. py:attribute:: text

    .. py:attribute:: updated


    .. py:method:: delete()

        Delete the xapian document.

        Subscriptions are removed by a Django signal `pre_delete`

    .. py:method:: get_absolute_url([action='show'])

    .. py:method:: _render(text, key)

        Render a text that belongs to this Article to HTML.

    .. py:method:: save([*args [, **kwargs]])

        This increases the edit count by 1 and updates the xapian database.

    .. py:method:: _simplify(text, key)

        Remove markup of a text that belongs to this Article.

    .. py:method:: update_search()

        This updates the xapian search index.


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

        .. py:data:: app_label

            Defaults to: ``'portal'``

        .. py:data:: db_table

            Defaults to: ``'portal_event'``


.. py:class:: ArticleSearchAuthDecider(object)

    Decides whether a user can display a search result or not.


.. py:class:: IkhayaSearchAdapter(inyoka.utils.search.SearchAdapter)

    .. py:data:: type_id

        Defaults to: ``'i'``

    .. py:attribute:: auth_decider

        :py:class:`ArticleSearchAuthDecider`


    .. py:method:: extract_data(article)

    .. py:method:: get_doc_ids()

    .. py:method:: get_objects(docids)

    .. py:method:: recv(docid)

    .. py:method:: recv_multi(docids)

    .. py:method:: store_object(article [, connection=None])
