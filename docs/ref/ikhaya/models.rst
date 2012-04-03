.. _ikhaya-models:

=============
Ikhaya models
=============

.. py:module:: inyoka.ikhaya.models

.. py:currentmodule:: inyoka.ikhaya.models


.. py:function:: _get_not_cached_articles(keys, cache_values)

    Return a tuple of (dates, slugs) for all keys in cache_values that are
    ``None``.

    :rtype: tuple


Managers
========

.. py:class:: ArticleManager(django.db.models.Manager)

    :py:class:`django.db.models.Manager`

    .. py:method:: __init__([public=True, all=False])

    .. py:method:: get_cached(keys)

        Get some articles from the cache. `keys` must be a list with (`pub_date`,
        `slug`) pairs. Missing entries from the cache are automatically fetched
        from the database. This method should be also used for retrieving
        single objects.

        ATTENTION: All articles which are returned from this function don't
        contain any text or intro (but they will contain rendered_text and
        rendered_intro). So do NEVER save any article returned by this
        function.

    .. py:method:: get_latest_articles([category=None, count=10])

        Return `count` lastest articles for the category `category` or for all
        categories if None.

        :param category: Takes the slug of the category or ``None`` for all
                         categories
        :param count: maximum retrieve this many articles. Defaults to 10
        :type category: string or ``None``
        :type count: int

    .. py:method:: get_query_set()


.. py:class:: SuggestionManager(django.db.models.Manager)

    :py:class:`django.db.models.Manager`

    .. py:method:: delete(ids)

        Deletes a list of suggestions with only one query and refresh the
        caches.


.. py:class:: CommentManager(django.db.models.Manager)

    :py:class:`django.db.models.Manager`

    .. py:method:: get_latest_comments([article=None, count=10])


Models
======

.. py:class:: Category(django.db.models.Model)

    :py:class:`django.db.models.Model`

    .. py:attribute:: icon

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.models.StaticFile` record.

    .. py:attribute:: name

        This :py:class:`django.db.models.CharField` holds the displayed name
        of the :py:class:`Category`.

    .. py:attribute:: slug

        The slug for this category that is used for links etc. An instance of
        :py:class:`django.db.models.CharField`


    .. py:method:: get_absolute_url([action='show'])

        Retrieve the absolute URL for this category.

        :param string action: Either of ``'edit'`` or ``'show'``.
        :return: The URL to the category that either links to the display view
                 or the edit form.

    .. py:method:: save([\*args, \*\*kwargs])


    .. py:class:: Meta

        .. py:attribute:: verbose_name

        .. py:attribute:: verbose_name_plural


.. py:class:: Article(django.db.models.Model, inyoka.utils.database.LockableObject)

    :py:class:`django.db.models.Model`
    :py:class:`inyoka.utils.database.LockableObject`

    .. py:attribute:: article_icon

        Property returning either :py:attr:`icon` or :py:attr:`Category.icon`

    .. py:attribute:: author

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.user.User` record.

    .. py:attribute:: category

        A :py:class:`~django.db.models.ForeignKey` to an
        :py:class:`Category` record.

    .. py:attribute:: comments

        Property that returns all the comments for this article.
        :rtype: :py:class:`django.db.models.query.QuerySet`

    .. py:attribute:: comment_count

        :py:class:`django.db.models.IntegerField`

    .. py:attribute:: comments_enabled

        :py:class:`django.db.models.BooleanField`

    .. py:attribute:: drafts

        An :py:class:`ArticleManager` with ``public=False``

    .. py:attribute:: hidden

        Property that returns a boolean whether this article is *not* visible
        for normal users.

        Articles that are not published or whose pub_date is in the
        future aren't shown for a normal user.

        :rtype: A boolean

    .. py:attribute:: icon

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.models.StaticFile` record.

    .. py:attribute:: intro

        :py:class:`django.db.models.TextField`

    .. py:attribute:: is_xhtml

        :py:class:`django.db.models.BooleanField`

    .. py:attribute:: local_pub_datetime

        Property

    .. py:attribute:: local_updated

        Property

    .. py:data:: lock_key_base

        Defaults to: ``'ikhaya/article_lock'``

    .. py:attribute:: objects

        An :py:class:`ArticleManager` with ``all=True``

    .. py:attribute:: pub_date

        :py:class:`django.db.models.DateField`

    .. py:attribute:: pub_time

        :py:class:`django.db.models.TimeField`

    .. py:attribute:: pub_datetime

        ``@deferred``

    .. py:attribute:: public

        :py:class:`django.db.models.BooleanField`

    .. py:attribute:: published

        An :py:class:`ArticleManager` with ``public=True``

    .. py:attribute:: rendered_intro

        Property returning the rendered content of :py:attr:`intro`.

    .. py:attribute:: rendered_text

        Property returning the rendered content of :py:attr:`text`.

    .. py:attribute:: simplified_intro

        Property returning the rendered content of :py:attr:`intro` w/o HTML
        tags.

    .. py:attribute:: simplified_text

        Property returning the rendered content of :py:attr:`text` w/o HTML
        tags.

    .. py:attribute:: slug

        :py:class:`django.db.models.SlugField`

    .. py:attribute:: stamp

        Property returning the year/month/day part of an article URL.

    .. py:attribute:: subject

        :py:class:`django.db.models.CharField`

    .. py:attribute:: text

        :py:class:`django.db.models.TextField`

    .. py:attribute:: updated

        :py:class:`django.db.models.DateTimeField`


    .. py:method:: delete()

        Delete the Xapian document.

        Subscriptions are removed by a Django signal `pre_delete`

    .. py:method:: get_absolute_url([action='show'])

        Retrieve the absolute URL for this article.

        :param string action: Either of ``'comments'``, ``'delete'``,
            ``'edit'``, ``'id'``, ``'last_comment'``, ``'report_new'``,
            ``'reports'``, ``'show'``, ``'subscribe'`` or ``'unsubscribe'``.
        :return: The URL to the article for the given action.

    .. py:method:: _render(text)

        Render `text` to HTML. The
        :py:attr:`~inyoka.wiki.parser.RenderContext.application` parameter for
        the :py:class:`~inyoka.wiki.parser.RenderContext` is set to
        ``'ikhaya'``.

    .. py:method:: save([\*args, \*\*kwargs])

        Save the instance and updates the Xapian database.

    .. py:method:: _simplify(text)

        Remove HTML tags from `text`.

    .. py:method:: update_search()

        This updates the Xapian search index.


    .. py:class:: Meta

        .. py:attribute:: ordering

            Defaults to: ``['-pub_date', '-pub_time', 'author']``

        .. py:attribute:: verbose_name

        .. py:attribute:: verbose_name_plural

        .. py:attribute:: unique_together

            Defaults to: ``('pub_date', 'slug')``


.. py:class:: Report(django.db.models.Model)

    :py:class:`django.db.models.Model`

    .. py:attribute:: article

        A :py:class:`~django.db.models.ForeignKey` to an :py:class:`Article`
        record.

    .. py:attribute:: author

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.user.User` record.

    .. py:attribute:: deleted

        :py:class:`django.db.models.BooleanField`

    .. py:attribute:: pub_date

        :py:class:`django.db.models.DateTimeField`

    .. py:attribute:: rendered_text

        :py:class:`django.db.models.TextField`

    .. py:attribute:: solved

        :py:class:`django.db.models.BooleanField`

    .. py:attribute:: text

        :py:class:`django.db.models.TextField`


    .. py:method:: get_absolute_url([action='show'])

        Retrieve the absolute URL for this report.

        :param string action: Either of ``'hide'``, ``'restore'``, ``'show'``,
            ``'solve'`` or ``'unsolve'``.
        :return: The URL to the report for the given action.

    .. py:method:: save([\*args, \*\*kwargs])


.. py:class:: Suggestion(django.db.models.Model)

    :py:class:`django.db.models.Model`

    .. py:attribute:: author

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.user.User` record.

    .. py:attribute:: intro

        :py:class:`django.db.models.TextField`

    .. py:attribute:: notes

        :py:class:`django.db.models.TextField`

    .. py:attribute:: objects

        An :py:class:`SuggestionManager`

    .. py:attribute:: owner

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.user.User` record.

    .. py:attribute:: pub_date

        :py:class:`django.db.models.DateTimeField`

    .. py:attribute:: rendered_intro()

        Parses the :py:attr:`intro` and compiles it to HTML. The content is
        written to the cache and returned.

    .. py:attribute:: rendered_notes()

        Parses the :py:attr:`notes` and compiles it to HTML. The content is
        written to the cache and returned.

    .. py:attribute:: rendered_text()

        Parses the :py:attr:`text` and compiles it to HTML. The content is
        written to the cache and returned.

    .. py:attribute:: text

        :py:class:`django.db.models.TextField`

    .. py:attribute:: title

        :py:class:`django.db.models.CharField`


    .. py:method:: get_absolute_url()

        Retrieve the absolute URL for this report.


    .. py:class:: Meta

        .. py:attribute:: verbose_name

        .. py:attribute:: verbose_name_plural

.. py:class:: Comment(django.db.models.Model)

    :py:class:`django.db.models.Model`

    .. py:attribute:: article

        A :py:class:`~django.db.models.ForeignKey` to an
        :py:class:`Article` record.

    .. py:attribute:: author

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.user.User` record.

    .. py:attribute:: deleted

        :py:class:`django.db.models.BooleanField`

    .. py:attribute:: pub_date

        :py:class:`django.db.models.DateTimeField`

    .. py:attribute:: objects

        An :py:class:`CommentManager`

    .. py:attribute:: rendered_text

        :py:class:`django.db.models.TextField`

    .. py:attribute:: text

        :py:class:`django.db.models.TextField`


    .. py:method:: get_absolute_url([action='show'])

        Retrieve the absolute URL for this comment.

        :param string action: Either of ``'edit'``, ``'hide'``, ``'restore'``
            or ``'show'``.
        :return: The URL to the comment for the given action.

    .. py:method:: save([\*args, \*\*kwargs])


.. py:class:: Event(django.db.models.Model)

    :py:class:`django.db.models.Model`

    .. py:attribute:: author

        A :py:class:`~django.db.models.ForeignKey` to a
        :py:class:`~inyoka.portal.user.User` record.

    .. py:attribute:: changed

        :py:class:`django.db.models.DateTimeField`

    .. py:attribute:: coordinates_url

        Property.
        
        Creates the URL to the location using the `GeoHack
        <https://wiki.toolserver.org/view/GeoHack>`_ tool.

        .. seealso:: :py:attr:`natural_coordinates`, :py:attr:`simple_coordinates`

    .. py:attribute:: created

        :py:class:`django.db.models.DateTimeField`

    .. py:attribute:: date

        :py:class:`django.db.models.DateField`

    .. py:attribute:: description

        :py:class:`django.db.models.TextField`

    .. py:attribute:: enddate

        :py:class:`django.db.models.DateField`

    .. py:attribute:: endtime

        :py:class:`django.db.models.TimeField`

    .. py:attribute:: location

        :py:class:`django.db.models.CharField`

    .. py:attribute:: location_lat

        :py:class:`django.db.models.FloatField`

    .. py:attribute:: location_long

        :py:class:`django.db.models.FloatField`

    .. py:attribute:: location_town

        :py:class:`django.db.models.CharField`

    .. py:attribute:: name

        :py:class:`django.db.models.CharField`

    .. py:attribute:: natural_coordinates

        Property.
        
        Format the coordinates :py:attr:`location_lat` and
        :py:attr:`location_long` as ``'52.5005° N, 13.3988° O'``

        .. seealso:: :py:attr:`coordinates_url`, :py:attr:`simple_coordinates`

    .. py:attribute:: rendered_description()

    .. py:attribute:: simple_coordinates()

        Property.
        
        Format the coordinates :py:attr:`location_lat` and
        :py:attr:`location_long` as ``'52.5005;13.3988'``

        .. seealso:: :py:attr:`coordinates_url`, :py:attr:`natural_coordinates`

    .. py:attribute:: slug

        :py:class:`django.db.models.SlugField`

    .. py:attribute:: time

        :py:class:`django.db.models.TimeField`

    .. py:attribute:: visible

        :py:class:`django.db.models.BooleanField`


    .. py:method:: friendly_title(with_html_link=False)

    .. py:method:: get_absolute_url([action='show'])

        Retrieve the absolute URL for this comment.

        :param string action: Either of ``'copy'``, ``'edit'``, ``'delete'``,
            ``'new'`` or ``'show'``.
        :return: The URL to the comment for the given action.

    .. py:method:: save([\*args, \*\*kwargs])


    .. py:class:: Meta

        .. py:data:: app_label

            Defaults to: ``'portal'``

        .. py:data:: db_table

            Defaults to: ``'portal_event'``


.. py:class:: ArticleSearchAuthDecider(object)

    Decides whether a user can display a search result or not.

    .. py:method:: __init__(user)

    .. py:method:: __call__(auth)


.. py:class:: IkhayaSearchAdapter(inyoka.utils.search.SearchAdapter)

    :py:class:`inyoka.utils.search.SearchAdapter`

    .. py:data:: type_id

        Defaults to: ``'i'``

    .. py:attribute:: auth_decider

        :py:class:`ArticleSearchAuthDecider`


    .. py:method:: extract_data(article)

    .. py:method:: get_doc_ids()

    .. py:method:: get_objects(docids)

    .. py:method:: recv(docid)

    .. py:method:: recv_multi(docids)

    .. py:method:: store_object(article[, connection=None])
