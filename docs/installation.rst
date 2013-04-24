.. _installation:

============
Installation
============

Requirements
============

The Inyoka installation requires at least `Python 2.7 <http://python.org>`_
including their development header files. Since Inyoka should run in its own
virtual environment, you need the `Python setuptools
<http://pypi.python.org/pypi/setuptools>`_. The database in the back-end can be
any that is officially supported by :ref:`Django
<django:database-installation>`.

The code is mostly tested with MySQL but should work with PostgreSQL, SQLite or
any other database Django supports.

Additionally `Jinja 2.5 <http://jinja.pocoo.org/>`_ or higher is required as
well as `Xapian <http://xapian.org/>`_ for the full text search facilities.
For the planet application the `feedparser library
<http://code.google.com/p/feedparser/>`_ must be installed. Additionally
chardet is recommended so that it can better guess broken encodings of feeds.
For the pastebin, wiki and some other parts `Pygments 1.4
<http://pygments.org/>`_ or higher must be available. MySQL must support InnoDB
or any other transaction engine like falcon (untested though). For incoming
HTML data that is converted to XHTML we also need html5lib. To let the inyoka
services run (required) you need also `simplejson
<http://simplejson.readthedocs.org/en/latest/index.html>`_.

We're using the recent stable `Django <https://www.djangoproject.com/>`_
releases.

For deployment memcached is the preferred caching system. Otherwise use many
threads and few processes and enable `locmem`.

Building virtual environment
============================

Assuming the Inyoka project files are located so that
``~/inyoka/inyoka/__init__.py`` holds, you should create a directory
``~/venv/``. Then go the directory ``~/inyoka/`` and run
following commands:

.. code-block:: console

   $ mkdir ../venv
   $ python2 extra/make-bootstrap.py > bootstrap.py
   $ python2 bootstrap.py ../venv/
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

Now we need to tell Django about the settings file. Remember to omit the file
extension ``.py`` here.

.. code-block:: console

   $ export DJANGO_SETTINGS_MODULE="settings"

Setup
=====

The next step is the database initialization:

.. code-block:: console

   $ python manage.py syncdb
   $ python manage.py migrate
