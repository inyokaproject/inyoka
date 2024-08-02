========================
Inyoka Theme
========================

.. image:: https://github.com/inyokaproject/theme-inyoka/actions/workflows/test.yml/badge.svg
    :target: https://github.com/inyokaproject/theme-inyoka/actions/workflows/test.yml
    :alt: Inyoka Theme CI

Installation
============

On development systems:
-----------------------

1. Run ``git clone git@github.com:inyokaproject/theme-inyoka.git`` next to
   the cloned Inyoka repository. (Basically, it doesn't matter were you clone
   the theme repository, but for support reasons it might be better to use the
   same base folder like for Inyoka). After cloning the file-structure should
   look like::

        $ tree -L 1
        .
        ├── inyoka
        ├── theme-inyoka
        └── maybe another-theme

2. Switch into the repository: ``cd theme-ubuntusers``
3. Activate source ``source ~/.venvs/inyoka/bin/activate``
4. Install as a development package: ``pip install -e .``
5. Run ``npm install`` to install all node dependencies (most relevant is ``less`` to generate the CSS)
6. Run ``npm run watch`` to build all static files and watch for file changes on the CSS / JS files
   (If it does not work for you out of the box, check whether you have a package like ``inotify-tools`` installed)
7. Let Django know about the theme. Add ``'inyoka_theme_inyoka'`` to the
   ``INSTALLED_APPS`` in ``inyoka/development_settings.py``::

       INSTALLED_APPS = INSTALLED_APPS + (
           'inyoka_theme_inyoka',
       )
9. Run ``python manage.py collectstatic --noinput --link`` in your inyoka instance
   This will create a directory ``inyoka/static-collected`` in your inyoka repository. The directory
   contains links to the found static files in the theme repository. These statics will be served during development.
    * ``--noinput`` will prevent a 'Are you sure?' question
    * With ``--link`` you have to only run ``collectstatic`` again, if a new file was added
 
If you want to see some possible locations to improve the JavaScript run ``npm run jshint``.

On Production
-------------

1. Run ``pip install -U "git+ssh://git@github.com:inyokaproject/theme-inyoka.git@staging#egg=inyoka-theme-inyoka"``

Deployment
----------

1. Run ``npm install`` to install all node dependencies (most relevant is ``less`` to generate the CSS)
2. Run ``npm run all`` to build all static files
3. Run ``python manage.py collectstatic`` in your inyoka instance
