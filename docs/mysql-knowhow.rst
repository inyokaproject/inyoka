
===============
MySQL Settings
===============

The following two settings have to be set in the ``my.cnf``, e.g.
``/etc/mysql/my.cnf``.

.. code-block:: none

  max_allowed_packet = 64M
  innodb_log_buffer_size = 256M

===============
Importing Dumps
===============

When importing Dumps it is advisable to disable binary logs to avoid filling up
the disc. This can be done by importing the dump as follows:

.. code-block:: console

  mysql -u root -p -f ubuntuusers
  SET sql_log_bin = 0;
  source /absolute/path/to/dump.sql;
