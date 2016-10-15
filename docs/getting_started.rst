.. _getting-started:

===============
Getting Started
===============

Assuming you already have :ref:`installed <installation>` Inyoka, you can start
coding / translating / documenting etc.

Working with Git
================

Branches
********

You can check your branches via

.. code-block:: console

    (inyoka)$ git branch

The current active branch will have an asterisk at the beginning of the line.
Before starting a development in a branch you should get the newest version:

.. code-block:: console

    (inyoka)$ git pull upstream staging

Adding a new branch for your development:

.. code-block:: console

    (inyoka)$ git checkout -b fix/ticket861
    Switched to a new branch 'fix/ticket861'
    (inyoka)$ git branch
    * fix/ticket861
      staging

The ticket name can be derived from the `error tracker
<http://trac.inyokaproject.org/>`_.

You can switch to another branch via

.. code-block:: console

    (inyoka)$ git checkout staging
    Switched to branch 'staging'
    (inyoka)$ git checkout fix/ticket861
    Switched to branch 'fix/ticket861'

Note: Only change files if you are on the correct branch! You should not change
files on *staging* directly.

Comitting changes
*****************

After you have changed some files on your branch you can check your changes via

.. code-block:: console

    (inyoka)$ git status

To mark your changes for the commit and to add new files you need to do:

.. code-block:: console

    (inyoka)$ git add "ALL YOUR CHANGED AND ADDED FILES"

Check again with ``git status`` and then commit your change via

.. code-block:: console

    (inyoka)$ git commit -m "Fixes #861 -- Short description"

This will commit your changes to your local repository only.

Next you need to push the changes to your origin repository (your forked Inyoka
project):

.. code-block:: console

    (inyoka)$ git push -u origin BRANCHNAME

Add pull request
****************

Visit the `GitHub website <https://github.com/>`_ and login. Then visit your
forked Inyoka project (mostly on *https://github.com/$GITUSERNAME/inyoka*).

You should see a green button for adding the pull request from your branch to
*inyokaproject/staging*. Just do it and hope that it will be pulled by a
developer to the original Inyoka.

You do not need to add a comment in Trac, as this is automatically done. Just
remember to start your commit message with "Fixes #number".

Getting latest version on developement branch
*********************************************

.. todo::
   Shouldn't this be done *before* comitting so merging the PR is easier?

If you are developing a feature for a while, the files in the Inyoka project
may have changed by other developers. In this case you need to synchronize:

.. code-block:: console

    (inyoka)$ git checkout staging
    (inyoka)$ git pull upstream staging

This will get the latest version on your staging branch. Then you need to push
the changes on the staging branch to your origin:

.. code-block:: console

    (inyoka)$ git push origin staging

And then you can merge the changes on staging to your developement branch:

.. code-block:: console

    (inyoka)$ git checkout BRANCHNAME
    (inyoka)$ git merge staging

Testing
=======

.. _test-notifies:

Test notifications
******************

Notifications for an user with the mail adress admin@localhost can easily be
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
unit tests to ensure that you didn't mess up with anything:

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

The  Python test files start with ``test_*``. For adding new tests you usally
would copy and adapt existing test classes or methods.

Translate Inyoka
================

.. todo::
   Put more information here.

You can switch languages by changing the ``LANGUAGE_CODE`` variable in
``development_settings.py``

.. code-block:: python

    LANGUAGE_CODE = 'en_US'

To mark a string as localizable use

.. code-block:: python

    _('ENGLISH TEXT')

If you are editing a template inside an inyoka theme, use the following syntax
to mark localizable strings

.. code-block:: css

    {% trans %}AN ENGLISH TEXT{% endtrans %}

To distinguish between a singular and plural form you can use

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

.. todo::
   Fill me.

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
************

This documentation is incomplete, you can help to expand it.
