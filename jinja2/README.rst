=============
Inyoka Theme
=============

This folder contains global templates that can not be assigned to one Inyoka app.
You can find app-specific templates in the respective app-folders like ``forum/jinja2``.

The next paragraphs describe how to build the static files.

Development
===========

1. Run ``npm install`` to install all node dependencies (most relevant is ``less`` to generate the CSS)
2. Run ``npm run watch`` to build all static files and watch for file changes on the CSS / JS files
   (If it does not work for you out of the box, check whether you have a package like ``inotify-tools`` installed)
3. Run ``python manage.py collectstatic --noinput --link`` in your inyoka instance
   This will create a directory ``inyoka/static-collected`` in your inyoka repository.
   These statics will be served during development.
    * ``--noinput`` will prevent a 'Are you sure?' question
    * With ``--link`` you have to only run ``collectstatic`` again, if a new file was added.

If you want to see some possible locations to improve the JavaScript run ``npm run jshint``.


Deployment
==========

1. Run ``npm ci`` to install all node dependencies (most relevant is ``less`` to generate the CSS)
2. Run ``npm run all`` to build all static files
3. Run ``python manage.py collectstatic`` in your inyoka instance
