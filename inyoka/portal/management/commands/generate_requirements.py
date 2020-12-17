# -*- coding: utf-8 -*-
"""
    inyoka.portal.management.commands.generate_requirements
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to create
    requirement-files with the help of pip-tools.

    :copyright: (c) 2011-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
import subprocess
import sys
import platform

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create all requirement files"
    stage_dev = 'development'
    stage_prod = 'production'
    stages = (stage_prod, stage_dev)
    requirements_path = 'extra/requirements'

    def add_arguments(self, parser):
        parser.add_argument('--update', action='store', default=None, dest='packages')

    def generate_requirements_file(self, stage: str) -> None:
        py_major, py_minor, _ = platform.python_version_tuple()
        file = '{}-py{}.{}-{}.txt'.format(sys.platform, py_major, py_minor, stage)
        full_path = os.path.join(self.requirements_path, file)

        print('Generating', file)

        program_name = 'pip-compile'
        arguments = ['--allow-unsafe', '--generate-hashes', '--output-file', full_path]

        if stage == self.stage_prod:
            arguments += [os.path.join(self.requirements_path, 'development.in')]

        try:
            subprocess.run([program_name] + arguments, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print('stdout')
            print(e.stdout.decode())

            print('stderr')
            print(e.stderr.decode())

    def handle(self, *args, **options):
        for s in self.stages:
            self.generate_requirements_file(s)
