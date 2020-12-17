# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.generate_requirements
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to create
    requirement-files with the help of pip-tools.

    :copyright: (c) 2011-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from typing import List

import argparse
import os
import subprocess
import sys
import platform

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update requirement files. The packages can be installed with pip-sync"
    stage_dev = 'development'
    stage_prod = 'production'
    stages = (stage_prod, stage_dev)
    requirements_path = 'extra/requirements'

    def add_arguments(self, parser):
        parser.add_argument('--upgrade', action='extend', nargs='*', type=str, default=argparse.SUPPRESS,
                            dest='upgrade_packages', help='Define one or more packages that should be upgraded. '
                                                          'If only the option is given, all packages are upgraded.')

    def generate_requirements_file(self, stage: str, upgrade_all: bool = False, upgrade_packages: List = []) -> None:
        py_major, py_minor, _ = platform.python_version_tuple()
        file = '{}-py{}.{}-{}.txt'.format(sys.platform, py_major, py_minor, stage)
        full_path = os.path.join(self.requirements_path, file)

        program_name = 'pip-compile'
        arguments = ['--allow-unsafe', '--generate-hashes', '--output-file', full_path]

        if upgrade_all and upgrade_packages:
            raise ValueError("Both upgrade_all and upgrade_packages are given. That's invalid")
        if upgrade_all:
            arguments.append('--upgrade')
        for p in upgrade_packages:
            arguments += ['--upgrade-package', p]

        if stage == self.stage_dev:
            arguments += [os.path.join(self.requirements_path, 'development.in')]

        custom_env = os.environ
        custom_env["CUSTOM_COMPILE_COMMAND"] = "python manage.py generate_requirements"

        print('Generating', file)
        try:
            subprocess.run([program_name] + arguments, capture_output=True, check=True, env=custom_env)
        except subprocess.CalledProcessError as e:
            print('stdout')
            print(e.stdout.decode())

            print('stderr')
            print(e.stderr.decode())

    def handle(self, *args, **options):
        upgrade_all = False
        upgrade_packages = []
        if hasattr(options, 'upgrade_packages'):
            if len(options.upgrade_packages) == 0:
                upgrade_all = True
            else:
                upgrade_packages = options.upgrade_packages

        for s in self.stages:
            self.generate_requirements_file(s, upgrade_all, upgrade_packages)
