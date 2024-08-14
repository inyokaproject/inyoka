.. _packagemanagement:

Packagemanagement
=================

To make the handling with requirements easier, Inyoka uses
`pip-tools <https://github.com/jazzband/pip-tools>`_.

An requirements file has to be generated for each environment. According
to the pip-tools documentation an environment is “the combination of
Operating System, Python version (2.7, 3.6, etc.), and Python
implementation (CPython, PyPy, etc.)”

Generate requirement files
--------------------------

To generate the requirement files run

::

   python manage.py generate_requirements

The production and development dependencies are defined in ``pyproject.toml``,
the latter via a ``dev`` extra.

To update all packages run

::

   python manage.py generate_requirements --upgrade

To update a specific package (in this example ``django``) run

::

   python manage.py generate_requirements --upgrade django

If you want to generate the requirements for a python version you have
not installed, there are tools like
`pyenv <https://github.com/pyenv/pyenv>`__. They allow to have multiple
versions of python installed in parallel.

Installation of packages
------------------------

See :ref:`installation`.
