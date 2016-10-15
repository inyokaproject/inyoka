.. _Inyoka: https://github.com/inyokaproject/inyoka
.. _GitHub: https://github.com/

.. _installation:

============
Installation
============

Idea
====

Inyoka_ is developed via GitHub_.
Note: You need the correct access rights to see the GitHub repository!
Documentation for git: `<http://git-scm.com/>`_

The idea for developing Inyoka is to fork the main project, do your changes in
your own repository and then add a “Pull Rquest” for the original Inyoka. A
developer should then comment your changes or will directly merge it.

Note: The changes in Inyoka will not immediately be visible on `ubuntuusers.de
<http://ubuntuusers.de/>`_

Preparation
===========

Git access
**********

If you do not have a login on GitHub_ get one so that
you can fork Inyoka and improve it.

Install Git if you have not yet:

.. code-block:: console

    $ sudo apt-get install git

Creating SSH key
****************

If you do not have a SSH key, create one:

.. code-block:: console

    $ ssh-keygen -t rsa -b 4096

You need to add your *public* key to your profile in Github under
*"Account Profile -> SSH keys -> Add SSH key"*:

.. code-block:: console

    $ cat .ssh/id_rsa.pub

Getting access to the Inyoka repository
***************************************

Then you need to contact `a developer <https://github.com/encbladexp>`_ so that
you get the correct access rights to fork the project. Simply click the "Fork"
Button on `<https://github.com/inyokaproject/inyoka>`_ to create a new
*private* Fork of this Repository.

Installation
============

First setup
***********

Before you start you need to get a local copy of your forked Inyoka project.
So open a terminal and move to a directory where you want the Inyoka files to
be stored. Then you can clone the repository:

.. code-block:: console

    $ git clone git@github.com:$GITHUBNAME/inyoka.git

``$GITHUBNAME`` is your login name on GitHub. This command will create a new
directory called *inyoka* in your current directory. So enter it:

.. code-block:: console

    $ cd inyoka

Next you need to add the upstream project for your fork and do some updates
afterwards so that you have the latest files:

.. code-block:: console

    $ git remote add upstream git@github.com:inyokaproject/inyoka.git
    $ git remote update
    $ git pull upstream staging

Package installation
********************

For compiling Inyoka and its dependencies you need a lot of developer files:

.. code-block:: console

    $  sudo apt-get install libxml2-dev libxslt1-dev libzmq-dev zlib1g-dev libjpeg-dev uuid-dev libfreetype6-dev libmysqlclient-dev build-essential redis-server libpq-dev libffi-dev nodejs-legacy

Further you need the Python 2.7 files:

.. code-block:: console

    $ sudo apt-get install python2.7
    $ sudo apt-get install python2.7-dev    #(Precise)
    $ sudo apt-get install libpython2.7-dev #(Trusty)

Further you need a recent pip and virtualenv for Python 2.7:

.. code-block:: console

    $ wget https://bootstrap.pypa.io/get-pip.py
    $ sudo python get-pip.py
    $ sudo pip install virtualenv

Finally the JavaScript package manager npm is necessary to install themes:

.. code-block:: console

    $ sudo apt-get install npm

The version of npm shipped with Ubuntu 12.04 is too old, see `these docs
<https://docs.npmjs.com/getting-started/installing-node>`_ in order to update
your version.

Actual installation
*******************
Now you can start the actual Inyoka installation:

.. code-block:: console

    $ mkdir -p ~/.venvs/
    $ virtualenv ~/.venvs/inyoka
    $ source ~/.venvs/inyoka/bin/activate
    $ pip install -r extra/requirements/development.txt

Note: You need to cd to your inyoka directory for the last command to work.

A lot of files will be downloaded and compiled. There will be some warnings 
that you can ignore. Hopefully there is not error and everything will compile 
fine.

Finally you need to edit your ``/etc/hosts`` with root privileges and add
the following line:

.. code-block:: console

    127.0.0.1       ubuntuusers.local forum.ubuntuusers.local paste.ubuntuusers.local wiki.ubuntuusers.local planet.ubuntuusers.local ikhaya.ubuntuusers.local static.ubuntuusers.local media.ubuntuusers.local

This will route all ubuntuusers.local calls in your browser to your localhost.

Note: This is only one line! Watch for line breaks!

Installing the theme
********************

Inyoka supports multiple themes, all of them are listed (among other things) on
`GitHub`__. Please refer to the specific
theme readme file in order to get installation instructions. *You will not be
able to run Inyoka without installing a theme.*

__ Inyoka_

Running Inyoka the first time
==================================

Activate Inyoka environment
***************************

For working with Inyoka you need to activate the correct environment. It will
change the PATH and the prompt a little bit:

.. code-block:: console

    $ source ~/.venvs/inyoka/bin/activate

Note: You need to do this every time you open a new terminal/shell and want to
work with Inyoka! Do not forget!

If the environment is active you'll see the entry *(inyoka)* at the
start of your prompt.

You can check if the environment is active:

.. code-block:: console

    (inyoka)$ echo $PATH

The entry ``/home/$USER/.venvs/inyoka/bin`` should appear at the beginning.

Using MySQL
***********

Even though you could use other databases than MySQL it's mostly tested with it. So
first install MySQL:

.. code-block:: console

    $ sudo apt-get install mysql-server

You will be asked for a password (maybe several times). You can leave it empty
if you want to.

Then you need to change the developer settings for the database. Rename and
edit the file *example_development_settings.py* to *development_settings.py*
in the *inyoka* directory. If you have set a password during installation of
MySQL above you need to add your password:

.. code-block:: console

    'NAME': 'ubuntuusers',
    'USER': 'root',
    'PASSWORD': '',

Further you should change the line

.. code-block:: console

    SECRET_KEY = None

to

.. code-block:: console

    SECRET_KEY = 'development-key'

To change the language, set

.. code-block:: console

    LANGUAGE_CODE = 'en-US'

to the desired value. You may also set

.. code-block:: console

    LC_ALL = 'en-US.UTF-8'

which is used for localized alphabetic sorting.

Creating test database
**********************

For testing you need to add a database in MySQL:

.. code-block:: console

    $ mysql -u root [-p]
    mysql> create database ubuntuusers;
    mysql> quit

You only need to use the ``-p`` if you have set a password in MySQL.

Next you need to add a superuser so that you gain all rights in the development
installation:

.. code-block:: console

    (inyoka)$ python manage.py migrate
    (inyoka)$ python manage.py create_superuser
    username: admin
    email: admin@localhost
    password: admin
    repeat: admin
    created superuser

Of course you can use another password, but you should keep the *admin* as
username because it will be used in some test files. It is also advisable to
use that mail adress in order to be able to test notifications, see
:ref:`testing notifications <test-notifies>`.

Note: If you want to change settings in the admin's control panel, you need to
set the mail adress to ``admin@localhost.local`` to not raise an error. The
mail adress is then automatically set back to ``admin@localhost``.

Now you can create the real test data:

.. code-block:: console

    (inyoka)$ ./make_testdata.py

Starting Inyoka
***************

Finally you can start the server the first time:

.. code-block:: console

    (inyoka)$ python manage.py runserver ubuntuusers.local:8080

In your browser open the url `<http://ubuntuusers.local:8080/>`_. You can login
with the user  *admin* and the given password above.

Before developing you should give your user full rights to everything. So click
on *Portal -> Groups"* and click on the button *"Edit"* at the group
"registered": `<http://ubuntuusers.local:8080/group/registered/edit/>`_

Check all boxes except *Not in use anymore"*. For accessing the forum select
all random forums via ``[Ctrl]`` and set all rights to *"Yes"*. Commit the
changes via the button *Send"*

You may should stop the running server via *[Ctrl-C]* and start it again before
the access rights are correct.

Working on Inyoka
=================

Environment and Server
**********************

First open a terminal, set the environment and start the server:

.. code-block:: console

    $ source ~/.venvs/inyoka/bin/activate
    (inyoka)$ python manage.py runserver ubuntuusers.local:8080

Then open another terminal, set the environment. Here you can work normally via
Git.

And now?
========

Congratulations: You have installed a local instance of Inyoka. It is time to
start hacking, read :ref:`getting-started` to learn how to submit your first
fix.
