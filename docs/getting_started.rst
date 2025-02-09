.. _getting-started:

===============
Getting Started
===============

Assuming you already have :ref:`installed <installation>` Inyoka, you can start
working on it. You need to know how to work with Git. `Pro Git <https://git-scm.com/book/en/v2>`_
is a good resource to learn Git. And see the
`GitHub Help 'Creating a pull request' <https://help.github.com/articles/creating-a-pull-request/>`_
to create pull requests.

The base development branch is ``staging`` and all new development branches
should be based from that branch. ``master`` is always the latest stable release
which is also running on ubuntuusers.de.

Tests
=====

Run tests
*********

Before adding a pull request or even committing you should run all
unit tests to ensure that you didn't break anything:

.. code-block:: console

    (inyoka)$ ./tests/runtests.sh --settings tests.settings.sqlite

You can just run some specific tests:

.. code-block:: console

    (inyoka)$ ./tests/runtests.sh --settings tests.settings.sqlite tests.apps.ikhaya.test_forms

where ``tests.apps.ikhaya.test_forms`` is the directory structure
``tests/apps/ikhaya/test_forms``.

Add tests
*********

If you have changed or added some Python files you should add some unit tests
as well for the classes. You'll find the tests under ``tests/apps/$APPNAME/``.

The Python test files start with ``test_*``. For adding new tests you usually
copy and adapt existing test classes and methods.

.. _test-notifies:

Test notifications
******************

Notifications for an user with the email address ``admin@localhost`` can easily be
tested by starting celery:

.. code-block:: console

   (inyoka)$ export DJANGO_SETTINGS_MODULE=development_settings
   (inyoka)$ celery -A inyoka worker -B -l DEBUG

Among other things you will see the notification mails for the admin user.

.. note::

   After changing a ``@task`` function, you need to restart the celery server.


BDD-Integration Tests
*********************

To cover the functionality between different modules there are BDD-Style integration tests at ``tests/bdd/``.

To run them you need to have Chromium installed on your system. Other browsers could be supported. But their usage
still needs to be implemented and documented (If you are looking for a task feel free).


.. code-block:: console

    (inyoka)$ export DJANGO_SETTINGS_MODULE='tests.bdd.bdd_settings'
    (inyoka)$ python manage.py behave

If you don't want to use the export of the settings you may also run

.. code-block:: console

    (inyoka)$ python manage.py behave --settings tests.bdd.settings.general


Code style
==========

The project uses `ruff <https://docs.astral.sh/ruff/>`_ to run code quality checks
on Inyoka's code base. Start the linter as follows from the project's root directory:

.. code-block:: console

    (inyoka)$ ruff check

Most style violations should be directly fixable via the ``--fix`` option.

Translate Inyoka
================

Every component of Inyoka has its own translation file. You can switch
languages by changing the ``LANGUAGE_CODE`` variable in
``development_settings.py``

.. code-block:: python

    LANGUAGE_CODE = 'en-us'

Define a translation key
************************

To mark a string as localizable use:

.. code-block:: python

     _('ENGLISH TEXT')

If you are editing a template inside an inyoka theme, use the following syntax
to mark localizable strings:

.. code-block:: jinja

    {% trans %}AN ENGLISH TEXT{% endtrans %}

To distinguish between a singular and plural form you can use:

.. code-block:: jinja

    {% trans count=VAR %}AN ENGLISH TEXT{% pluralize %}SOME ENGLISH TEXTS{% endtrans %}

where VAR is the deciding variable. You can also use variables in localizable
strings as

.. code-block:: jinja

    {% trans count=VAR %}AN ENGLISH TEXT{% pluralize %}THERE ARE {{ count }}} ENGLISH TEXTS{% endtrans %}

After applying these changes, run the following command to generate the
``*.pot`` files (translation templates) and automatically add the new strings
to existing ``*.po`` files.

.. code-block:: console

    (inyoka) $ python manage.py makemessages

.. note::

    Each component of Inyoka has its own translation file

Add a new translation
*********************

Inyoka is translated on `transifex <https://www.transifex.com/inyokaproject/inyoka/dashboard/>`_. To upload
new translations to transfix `configure first the client <https://github.com/transifex/cli>`_
(We recommended to download the binary manually or use docker).
Afterwards, run:

.. code-block:: console

    (inyoka) $ tx push -s

You have two ways to do the translations.

1. Locally
    Do the translation using the ``*.po`` files (for example ``inyoka/wiki/locale/de_DE/LC_MESSAGES/django.po``)
    and upload them afterwards with:

    .. code-block:: console

        (inyoka) $ tx push -t

2. On transifex
    Do the translation for the untranslated strings on
    `transifex <https://www.transifex.com/inyokaproject/inyoka/dashboard/>`_. Afterwards you download
    the changes using:

    .. code-block:: console

        (inyoka) $ tx pull

If the translations are done, run the following command to compile the corresponding ``*.mo`` files (binary
translation files)

.. code-block:: console

    (inyoka)$ python manage.py compilemessages

and restart the server for testing.

It is recommended to add the ``*.mo`` files in a seperate commit, because they cannot
be merged by git. In case of a merge conflict, the commit can be dropped, the ``*.po`` files merged
and the ``*.mo`` files compiled again.

Add a new language
******************

The fastest way to add a new language is to add it to the transifex project and than
download it with:

.. code-block:: console

    (inyoka) $ tx pull -a

If you prefer to do it manually, you need to create the sub directory
``ll_CC/LC_MESSAGES`` inside the ``locale`` folder of a component (for example
``inyoka/wiki/locale/de_DE/LC_MESSAGES``). Copy the ``django.pot`` file to this
directory and rename it to ``django.po``.


Test someone's Pull Request
===========================

See the GitHub Documentation on `How to checkout Pull Requests locally <https://help.github.com/articles/checking-out-pull-requests-locally/>`_

Styles
======

Inyoka uses `less <http://lesscss.org/>`_ for creating css files. Run

.. code-block:: console

    (inyoka)$ npm run watch

in your theme's base directory to automatically generate the ``.css`` files.
For more information read the theme documentation.

Documentation
=============

Creation
********

In order to create or update the documentation (yes, *this* documentation), simply run:

.. code-block:: console

    (inyoka)$ make -C docs html

Contributing
*************

This documentation is incomplete, you can help to expand it.
