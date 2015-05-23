.. _installation:

============
Installation
============

Idea
====

Inyoka is developed via `GitHub
<https://github.com/inyokaproject/inyoka>`_.  Note: You need the correct
access rights to see the GitHub repository!  Documentation for git:
`<http://git-scm.com/>`_

The idea for developing Inyoka is to fork the main project, do your
changes in your own repository and then add a “Pull Rquest” for the
original Inyoka. A developer should then comment your changes or will
directly merge it.

Note: The changes in Inyoka will not immediately be visible on
`ubuntuusers.de <http://ubuntuusers.de/>`_


Preparation
===========

Git access
**********

If you do not have a login on `GitHub <https://github.com/>`_ get one so
that you can fork Inyoka and improve it.

If you do not have Git installed install it:

.. code-block:: console

  $ sudo apt-get install git

Creating SSH key
****************

If you do not have a SSH key, create one:

.. code-block:: console

  $ ssh-keygen -t rsa -b 4096

Then you need to add your *public* key to your profile in Git under
*"Account Profile -> SSH keys -> Add SSH key"*:

.. code-block:: console

  $ cat .ssh/id_rsa.pub

Getting access to the Inyoka repository
***************************************

Then you need to write to `a developer <https://github.com/encbladexp>`_
so that you get the correct access rights to fork the project.  Simply
klick the "Fork" Button on `<https://github.com/inyokaproject/inyoka>`_ to
create a new *private* Fork of this Repository.


Installation
============

First setup
***********

Before  you start you need to get a local copy of your forked Inyoka
project. So open a terminal and move to a directory where you want the
Inyoka files to be stored. Then you can clone the repository:

.. code-block:: console

  $ git clone git@github.com:$GITNAME/inyoka.git

``$GITNAME``  is your login name on GitHub. This command will create a
new directory  called *inyoka* in your current directory. So go to it:

.. code-block:: console

  $ cd inyoka

Next you need to add the upstream project for your fork and do some update
afterwards so that you have the latest files:

.. code-block:: console

  $ git remote add upstream git@github.com:inyokaproject/inyoka.git
  $ git remote update
  $ git pull upstream staging

Package installation
********************

For compiling Inyoka and its dependencies you need a lot of developer
files:

.. code-block:: console

  $  sudo apt-get install libxml2-dev libxslt1-dev
  libzmq-dev zlib1g-dev libjpeg-dev uuid-dev libfreetype6-dev
  libmysqlclient-dev build-essential libmemcached-dev

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

Finally for installing themes npm, a package manager for javascript, is
needed:

.. code-block:: console

  $ sudo apt-get install npm

The version of npm shipped on Ubuntu 12.04 is too old, see `these docs
<https://docs.npmjs.com/getting-started/installing-node>`_ in order to
update your version.

Adding links (Ubuntu only)
**************************

Inyoka  needs the program '''virtualenv''' and expects the version 2.7. In
Ubuntu the installed binary does not have the version tag in the name.  So
you need to add a softlink:

.. code-block:: console

  $ cd /usr/bin/
  $ sudo ln -s virtualenv virtualenv-2.7

Actual instalallation
*********************
Next you can start the actual Inyoka installation:

.. code-block:: console

  $ mkdir -p ~/.venvs/inyoka
  $ virtualenv-2.7 ~/.venvs/inyoka
  $ ~/.venvs/inyoka/bin/pip install -r extra/requirements/test.txt

A lot of files will be downloaded and compiled. Further there will be
some warnings that you can ignore. Hopefully there is not error and
everything will compile fine.

At the end you need to edit your *etc/hosts* with root privilegies
and add the following line:

.. code-block::

  127.0.0.1       ubuntuusers.local forum.ubuntuusers.local
      paste.ubuntuusers.local   wiki.ubuntuusers.local
      planet.ubuntuusers.local  ikhaya.ubuntuusers.local
      static.ubuntuusers.local  media.ubuntuusers.local

This will route all ubuntuusers.local calls in your browser to your
localhost.

Note: This is only one line! Watch for linebreaks!

Installing the theme
********************

Inyoka supports multiple themes, all of them are listed (among other
things) on `GitHub <https://github.com/inyokaproject>`_. Please refer to
the spefific theme readme file in order to get installation instructions.
*You will not be able to run Inyoka without installing a theme.*

Creating the documentation
**************************

In order to create or update the documentation (yes, *this*
documentation), run

.. code-block:: console

  (inyoka)$ make html
   
in ``inyoka/inyoka/docs/``.


Working with Inyoka the first time
==================================

Activate Inyoka environment
***************************

For working with Inyoka you need to activate the correct environment. It
will change the PATH and the prompt a little bit:

.. code-block:: console

  $ source ~/.venvs/inyoka/bin/activate

Note: You need to do this everytime you open a new terminal/shell and want
to work with Inyoka! Do not forget!

If the environment is active you'll see the entry *(inyoka)* at the
start of your prompt.

You can check if the environment is active:

.. code-block:: console

  (inyoka)$ echo $PATH

The entry *home/$USER/.venvs/inyoka/bin* should appear at the
beginning.

Using MySQL
***********

Even if you can use other databases than MySQL it's mostly tested with it.
So first install MySQL:

.. code-block:: console

  $ sudo apt-get install mysql-server

You will be asked for a password (maybe several times). You can leave it
empty if you want to.

Then you need to change the developer settings for the database. Edit the
file *development_settings.py*  in the *inyoka* directory. You can leave
the database entries if you haven't set a password during installation of
MySQL above. Otherwise  you need to add your password:

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


.. todo::
  language settings

Creating test database
**********************

For testing you need to add a database in MySQL:

.. code-block:: console

  $ mysql -u root [-p]
  mysql> create database ubuntuusers;
  mysql> quit

You only need to use the ``-p`` if you have set a password in MySQL.

Next you need to add a superuser so that you gain all rights in the
development installation:

.. code-block:: console

  (inyoka)$ python manage.py syncdb
  (inyoka)$  python manage.py migrate
  (inyoka)$  python manage.py create_superuser
  username: admin
  email: admin@localhost
  password: admin
  repeat: admin
  created superuser

Of course you can use another password, but you should keep the  *admin*
as username because it will be used in some test files. It is also
advisable to use that mail adress in order to be able to test
notifications, see :ref:`testing notifications <test-notifies>`.

.. note::

   If you want to change settings in the admin's control panel, you need
   to set the mail adress to ``admin@localhost.local`` to not raise an
   error. The mail adress is then automatically set back to
   ``admin@localhost``.

Now you can create the real test data:

.. code-block:: console

  (inyoka)$ ./make_testdata.py


Starting Inyoka
***************
Finally you can start the server the first time:

.. code-block:: console

  (inyoka)$ python manage.py runserver ubuntuusers.local:8080

In your browser open the url `<http://ubuntuusers.local:8080/>`_. You can
login with the user  *admin* and the given password above.

Before developing you should give your user full rights to everything. So
click on *Portal -> Groups"* and click on the button *"Edit"* at  the
group "Registriert":
`<http://ubuntuusers.local:8080/group/Registriert/edit/>`_

Check all boxes except *Not in use anymore"*.  For accessing the forum
select all random forums via *[Ctrl]* and set all rights to *"Yes"*.
Commit the changes via the button *Send"*

You may should stop the running server via *[Ctrl-C]* and start it
again before the access rights are correct.


Working with Inyoka everytime
=============================

Environment and Server
**********************

First open a terminal, set the environment and start the server:

.. code-block:: console

  $ source ~/.venvs/inyoka/bin/activate
  (inyoka)$ python manage.py runserver ubuntuusers.local:8080

Then open another terminal, set the environment. Here you can work
normally via Git.


And now?
========

Congratulations: You have installed a local instance of Inyoka.  It is
time to start hacking, read :ref:`getting-started` to learn how to submit
your first fix.
