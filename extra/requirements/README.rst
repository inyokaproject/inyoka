.. _packagemanagement:

Packagemanagement
=================

To ease pinning of requirements, Inyoka uses
`pip-tools <https://github.com/jazzband/pip-tools>`_.

An requirements file has to be generated for each environment. According
to the pip-tools documentation an environment is “the combination of
Operating System, Python version (2.7, 3.6, etc.), and Python
implementation (CPython, PyPy, etc.)”

Generate requirement files
--------------------------

To generate requirement files for your used python version run

::

   python manage.py generate_requirements

The production dependencies are defined in ``pyproject.toml``.
It also contains the development dependencies via a ``dev`` extra.

To update all packages run

::

   python manage.py generate_requirements --upgrade

To update a specific package (in this example ``django``) run

::

   python manage.py generate_requirements --upgrade django


Generate for multiple python versions
-------------------------------------

A docker compose file exists to generate the requirements for all python versions
Inyoka supports.

If needed adjust the variables ``INYOKA_GID`` and ``INYOKA_UID`` in ``build-requirements.yml``.
These variables define the user and group id of the generated requirement files.
Adjust to your needs, if your user uses different IDs.

To start the build procedure, run the following command:

::

   docker compose --file build-requirements.yml up

After the command terminated, you can review and commit all the generated requirement files.


Installation of packages
------------------------

See :ref:`installation`.
