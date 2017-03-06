.. _getting-started:

===============
Getting Started
===============

Assuming you already have :ref:`installed <installation>` Inyoka, you can start
working on it. You need to know how to work with Git. `Pro Git<https://git-scm.com/book/en/v2>`_
is a good ressource to learn Git. And see the
`GitHub Help 'Creating a pull request'<https://help.github.com/articles/creating-a-pull-request/>`_
to create pull requests.

The base development branch is ``staging`` and all new development branches
should be based from that branch. ``master`` is always the latest stable release
which is also running on ubuntuusers.de.

Testing
=======

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

   After changing a @task function, you need to restart the celery server.

.. todo::

   How to test jabber notifications?

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

Translate Inyoka
================

Every component of Inyoka has its own translation file. You can switch
languages by changing the ``LANGUAGE_CODE`` variable in
``development_settings.py``

.. code-block:: python

    LANGUAGE_CODE = 'en-us'

To mark a string as localizable use:

.. code-block:: python

     _('ENGLISH TEXT')

If you are editing a template inside an inyoka theme, use the following syntax
to mark localizable strings:

.. code-block:: css

    {% trans %}AN ENGLISH TEXT{% endtrans %}

To distinguish between a singular and plural form you can use:

.. code-block:: css

    {% trans count=VAR %}AN ENGLISH TEXT{% pluralize %}SOME ENGLISH TEXTS{% endtrans %}

where VAR is the deciding variable. You can also use variables in localizable
strings as

.. code-block:: css

    {% trans count=VAR %}AN ENGLISH TEXT{% pluralize %}THERE ARE {{ count }}} ENGLISH TEXTS{% endtrans %}

After applying these changes, run the following command to generate the
``*.pot`` files (translation templates) and automatically add the new strings
to existing ``*.po`` files.

.. code-block:: console

    (inyoka) $ python manage.py makemessages

.. note::

    Each component of Inyoka has its own translation file

To add a new language, you need to create the sub directory
``ll_CC/LC_MESSAGES`` inside the ``locale`` folder of a component (e.g.
``inyoka/wiki/locale/de_DE/LC_MESSAGES``). Copy the ``django.pot`` file to this
directory and rename it to ``django.po``.

Do the translation using the ``*.po`` files (e.g.
``inyoka/wiki/locale/de_DE/LC_MESSAGES/django.po``). Afterwards run the
following command to compile the corresponding ``*.mo`` files (binary
translation files)

.. code-block:: console

    (inyoka)$ python manage.py compilemessages

Restart the server to test.

Test someone's Pull Request
===========================

See the GitHub Documentation on `How to checkot Pull Requests locally <https://help.github.com/articles/checking-out-pull-requests-locally/>`_

Styles
======

Inyoka uses `less <http://lesscss.org/>`_ for creating css files. Run

.. code-block:: console

    (inyoka)$ ./node_modules/grunt-cli/bin/grunt watch

in your theme's base directory to automatically generate the ``.css`` files.
For more information read the theme documentation.

Documentation
=============

Installation
************

In order to create or update the documentation (yes, *this* documentation), simply run:

.. code-block:: console

    (inyoka)$ make -C docs html

Contributing
*************

This documentation is incomplete, you can help to expand it.
