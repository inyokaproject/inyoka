========
Releases
========

Like described in :doc:`/security`, only the latest release is supported.


Version schema
==============

A version follows the schema ``{major}.{django}.{patch}``.

* Major is increased by one, if a new feature is introduced.
  What a feature is can be subjective and does not follow a strict schema.

* The used django version is in the middle (where the minor version uses to be).
  An example: if inyoka uses django 4.2, the version has the scheme ``x.42.y``.
  Even if the major part is increased, the django-part is stable.

* Patch is increased by one, if bugs were fixed or code refactored.


Changelog
=========

.. toctree::
    :maxdepth: 1

    0.x
    0.0.x
