"""
A special settings file which sets the database name to the postgres default
'postgres'. Latter exists always. This is useful for CI runs, where no
interaction with the DB is made, but a valid django configuration has to be
provided.
"""

from .postgresql import *  # noqa

DATABASES['default']['NAME'] = 'postgres'
