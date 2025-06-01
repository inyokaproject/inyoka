.. _packagemanagement:

Packagemanagement
=================

To ease pinning of requirements, Inyoka uses
`uv <https://docs.astral.sh/uv/>`_ with a little wrapper.

Generate requirement files
--------------------------

To generate requirement files for Inyoka run

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


Installation of packages
------------------------

See :ref:`installation`.
