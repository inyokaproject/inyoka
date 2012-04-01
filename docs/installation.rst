.. _installation:

============
Installation
============

Requirements
============

The Inyoka installation requires at least `Python 2.4 <http://python.org>`_
including their development header files. Since Inyoka should run in its own
virtual environment, you need the `Python setuptools
<http://pypi.python.org/pypi/setuptools>`_. The database in the back-end can be
any that is officially supported by :ref:`Django
<django:database-installation>` but we currently recommend to use MySQL.

Building virtual environment
============================

Assuming the Inyoka project files are located so that
``~/inyoka/inyoka/__init__.py`` holds, you should create a directory
``~/venv/``. Then go the directory ``~/inyoka/`` and run
following commands:

.. code-block:: console

    $ python extra/make-bootstrap.py > ../venv/bootstrap.py
    $ cd ../venv/
    $ python bootstrap.py .
    $ cd ../inyoka/
    $ . ../venv/bin/activate
    $ pip install -r extra/requirements/production.txt

This will take some time, depending on your network connection and CPU and
memory. Depending on your environment you need to install additional drivers
for you database. In case of MySQL run:

.. code-block:: console

    $ pip install MySQL-python

Configuration
=============

In the meantime we can start to configure Inyoka. Copy the file
``~/inyoka/example_development_settings.py`` to ``~/inyoka/settings.py`` and open
the new file in your favourite editor. Configure your Inyoka installation
according to your wishes. The :ref:`settings` documentation has detailed
information to all configuration directives.

Make sure that you have created the Inyoka database and the regarding user.
Check that the Inyoka database user can ``CREATE`` and ``ALTER`` tables!

Now we need to tell Django about the settings file:

.. code-block:: console

    $ export DJANGO_SETTINGS_MODULE="settings"

Setup
=====

The next step is the database initialization:

.. code-block:: console

    $ python manage.py syncdb
    $ python manage.py migrate
