# -*- coding: utf-8 -*-
import sys
import datetime
import django
from os import environ
from os.path import join, dirname
from subprocess import PIPE, Popen

sys.path.insert(0, join(dirname(__file__), '..'))

environ['DJANGO_SETTINGS_MODULE'] = 'development_settings'

django.setup()

#########################################
# Overrides to fix doc build exceptions #
#########################################

# Fix FileField
from django.db.models.fields.files import FileDescriptor
FileDescriptor.__get__ = lambda self, *args, **kwargs: self

#Fix JSONField
from inyoka.utils.database import SimpleDescriptor
SimpleDescriptor.__get__ = lambda self, *args, **kwargs: self

# Remove Redis dependency
from inyoka.utils.storage import CachedStorage
CachedStorage.get = lambda self, key, *args, **kwargs: key

extensions = ['sphinx.ext.doctest', 'sphinx.ext.intersphinx', 'sphinx.ext.todo',
    'sphinx.ext.coverage', 'sphinx.ext.extlinks', 'sphinx.ext.autodoc']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Inyoka'
copyright = '2007 - %d by the Inyoka Team, see AUTHORS for more details' % datetime.date.today().year

# Show todo notes
todo_include_todos = True

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = Popen(['git', 'describe', '--abbrev=0'],
        stdout=PIPE).communicate()[0]
version = version.decode('utf-8').strip()
# The full version, including alpha/beta/rc tags.
release = Popen(['git', 'describe'], stdout=PIPE).communicate()[0]
release = release.decode('utf-8').strip()

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'django': ('https://docs.djangoproject.com/en/1.8',
               'http://docs.djangoproject.com/en/1.8/_objects'),
    'python': ('http://docs.python.org/2.7', None),
    'sphinx': ('http://sphinx.pocoo.org/', None),
}

extlinks = {
    'ticket': ('http://trac.inyokaproject.org/ticket/%s', 'Ticket #'),
    'pr': ('https://github.com/inyokaproject/inyoka/pull/%s', 'PR #'),
}

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Output file base name for HTML help builder.
htmlhelp_basename = 'Inyokadoc'
