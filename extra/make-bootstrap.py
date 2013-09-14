#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Inyoka Bootstrap Creation Script
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a bootstrap script for inyoka.

    :copyright: (c) 2009-2013 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import with_statement

from os.path import join, dirname, realpath

# virtualenv is stored wrong in debian squeeze
try:
    from virtualenv import create_bootstrap_script
except ImportError:
    from virtualenv.virtualenv import create_bootstrap_script


base_dir = realpath(join(dirname(__file__)))
with open(join(base_dir, 'bootstrap-extra.py'), 'r') as fobj:
    EXTRA_TEXT = fobj.read()

if __name__ == '__main__':
    print(create_bootstrap_script(EXTRA_TEXT))
