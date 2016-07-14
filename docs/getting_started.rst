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
forked Inyoka project (mostly on `https://github.com/$GITUSERNAME/inyoka`_).

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

Notifications for an user which mail adress admin@localhost can easily be
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

Before adding a pull request or before committing at all you should run all
unit tests so that you see that you don't have broken anything:

.. code-block:: console

    (inyoka)$ ./tests/runtests.sh --settings tests.settings.sqlite

You can just run some specific tests:

.. code-block:: console

    (inyoka)$ ./tests/runtests.sh --settings tests.settings.sqlite
    tests.apps.ikhaya.test_forms

where ``tests.apps.ikhaya.test_forms`` is the directory structure
``tests/apps/ikhaya/test_forms``.

Add tests
*********

If you have changed or added some Python files you should add some unit tests
as well for the classes. You'll find the tests under ``tests/apps/$APPNAME/``.

The  Python test files start with ``test_*``. For adding new tests you can
mostly open a file and copying other test classes or test methods.

Translate Inyoka
================

.. todo::
   Put more information here.

Every component of Inyoka has its own translation file. You can switch
languages by changing the ``LANGUAGE_CODE`` variable in
``development_settings.py``

.. code-block:: console

    LANGUAGE_CODE = 'en'

Template syntax:

.. code-block:: console

    {% trans %}ENGLISH TEXT{% endtrans %}

After changing the above code, you also need to change the string in the
corresponding ``*.po`` file. (e. g.
``inyoka/wiki/locale/de_DE/LC_MESSAGES/django.po``) Afterwards you have to run
the following command to generate the ``*.pot`` file.

.. code-block:: console

    (inyoka) $ python manage.py makemessages

Compile the corresponding ``*.mo`` files

.. code-block:: console

    (inyoka)$ python manage.py compilemessages

Restart server to test.

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

Documentating
*************

This documentation is incomplete, you can help by expanding it.
