.. _Inyoka: https://github.com/inyokaproject/inyoka
.. _GitHub: https://github.com/

.. _installation:

============
Installation
============

Idea
====

Inyoka_ is developed via GitHub_.
You need the correct access rights to see the GitHub repository!
You can find a documentation on how to use Git here: `<http://git-scm.com/>`_

The idea for developing Inyoka is to fork the main project, do your changes in
your own branch in your repository and then open a “Pull Request” for the original
Inyoka-repository. A developer will then review your changes or will directly merge it.

The changes in Inyoka will not immediately be visible on `ubuntuusers.de
<http://ubuntuusers.de/>`_

Preparation
===========

Getting access to the Inyoka repository
***************************************

You need to contact a team member who will give you access rights to fork the project.
After that, simply fork the `<https://github.com/inyokaproject/inyoka>`_ repository
to create a new *private* fork of this repository.

Installation
============

Package installation
********************

For using Inyoka and its dependencies you need a lot of python and developer files:

.. code-block:: console

    $  sudo apt-get install git nodejs-legacy libxml2-dev libxslt1-dev libzmq-dev zlib1g-dev libjpeg-dev uuid-dev libfreetype6-dev libpq-dev build-essential libpq-dev libffi-dev python3-dev

You also need the JavaScript package manager npm:

.. code-block:: console

    $ sudo apt-get install npm


Inyoka installation
*******************

Now you can start the installation of inyoka:

.. code-block:: console

    $ mkdir -p ~/.venvs/
    $ python -m venv ~/.venvs/inyoka
    $ source ~/.venvs/inyoka/bin/activate
    $ cd to/my/inyoka-repo # replace with correct path
    $ pip install -r extra/requirements/development.txt

The last command downloads and installs all needed libraries via pip.

.. note::
   ``development.txt`` and ``production.txt`` are just symlinks to the
   environment used on ubuntuusers.de. Please check, if you have another
   python version installed and need to use another requirements file. All
   available requirements files can be found in ``extra/requirements/``.

   If you are interested in how these files are generated, see :ref:`packagemanagement`.

Once the requirements are installed, you can run *optionally*

::

   $ pip-sync extra/requirements/development.txt

``pip-sync`` has the benefit of removing all unneeded packages from the virtualenv.
``pip`` will leave f.e. old dropped dependencies in the virtualenv. This is especially
relevant, if you have an old virtualenv and update the packages in it regularly.

At the end you need to edit your ``/etc/hosts`` with root privileges and add
the following line:

.. code-block:: console

    127.0.0.1       ubuntuusers.local forum.ubuntuusers.local paste.ubuntuusers.local wiki.ubuntuusers.local planet.ubuntuusers.local ikhaya.ubuntuusers.local static.ubuntuusers.local media.ubuntuusers.local

This will route all ubuntuusers.local calls in your browser to your localhost.

Installing the theme
********************

Inyoka supports multiple themes, all of them are listed (among other things) on
`GitHub`__. Please refer to the specific
theme `README` file in order to get installation instructions. You will not be
able to run Inyoka without installing a theme!

__ Inyoka_

Working with Inyoka the first time
==================================

Activate Inyoka environment
***************************

To work on Inyoka you need to activate the virtual environment. It will
change the PATH and the prompt:

.. code-block:: console

    $ source ~/.venvs/inyoka/bin/activate

..  note::
    You need to do this every time you open a new terminal/shell and want to
    work on Inyoka!

If the environment is active you'll see the entry *(inyoka)* at the
start of your prompt.

You can check if the environment is active:

.. code-block:: console

    (inyoka)$ echo $PATH

The entry ``/home/$USER/.venvs/inyoka/bin`` should appear at the beginning.

Preparing the database
**********************

Inyoka supports only PostgreSQL as database, all other databases supported by django are
without any support! Inyoka also needs a running redis server.

.. code-block:: console

    $ sudo apt-get install postgresql redis-server

Next, you need a ``development_settings.py`` file which can be copied from
the example file:

.. code-block:: console

    $ cp example_development_settings.py development_settings.py

If you have set a database password during installation you need to specify
the password:

.. code-block:: console

    'NAME': 'ubuntuusers',
    'USER': 'root',
    'PASSWORD': '',

Further you need to set a ``SECRET_KEY`` with a string, like this:

.. code-block:: console

    SECRET_KEY = 'development-key'

To switch between the supported languages you have to add another setting.
Currently available languages are ``en-us`` and ``de-de``.

.. code-block:: console

    LANGUAGE_CODE= 'de-de'

Creating test database
**********************

You need to add a database in PostgreSQL:

.. code-block:: console

    $ sudo -i -u postgres
    $ createuser -P inyoka
    $ createdb -O inyoka inyoka

Next you need to add a superuser so that you gain all rights in the development
installation of Inyoka:

.. code-block:: console

   (inyoka)$  python manage.py migrate
   (inyoka)$  python manage.py create_superuser
   username: admin
   email: admin@localhost
   password: admin
   repeat: admin
   created superuser

You can also use another password, but you should keep the *admin* username
because it will be used in some test files. It is also advisable to
use that mail address in order to be able to test notifications, see
:ref:`testing notifications <test-notifies>`.

.. note::
   If you want to change settings in the admin's control panel, you need to
   set the email address to ``admin@localhost.local`` to not raise an error. The
   email address is then automatically set back to ``admin@localhost``.

Now you can create the real test data:

.. code-block:: console

    (inyoka)$ ./make_testdata.py

Starting Inyoka
***************

Finally you can start the server the first time:

.. code-block:: console

    (inyoka)$ python manage.py runserver ubuntuusers.local:8080

Open the url `<http://ubuntuusers.local:8080/>`_ in your browser. You can login
with the user *admin* and the given password above.

And now?
========

Congratulations: You have installed a local instance of Inyoka. It is time to
start hacking, read :ref:`getting-started` to learn how to submit your first
fix.
