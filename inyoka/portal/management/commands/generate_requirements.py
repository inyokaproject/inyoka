"""
    inyoka.portal.management.commands.generate_requirements
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides a command to the Django ``manage.py`` file to create
    requirement-files.

    :copyright: (c) 2011-2025 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
import re
import subprocess
from importlib.metadata import metadata

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update requirement files. The packages can be installed with pip, pip-sync or uv pip"
    stage_dev = 'development'
    stage_prod = 'production'
    stages = (stage_prod, stage_dev)
    requirements_path = 'extra/requirements'

    def add_arguments(self, parser):
        parser.add_argument('--upgrade', action='extend', nargs='*', type=str,
                            dest='upgrade_packages', help='Define one or more packages that should be upgraded. '
                                                          'By default, all packages are upgraded.')

    def _get_requirements_path(self, stage: str) -> str:
        file = f'{stage}.txt'
        full_path = os.path.join(self.requirements_path, file)
        return full_path


    def generate_requirements_file(self, stage: str, upgrade_all: bool = False, upgrade_packages: list = []) -> None:
        full_path = self._get_requirements_path(stage)

        program_name = 'uv'
        arguments = ['pip', 'compile', '--python-version', self._minimum_python(), '--universal', '--generate-hashes', '--output-file', full_path, "pyproject.toml"]

        if upgrade_all and upgrade_packages:
            raise ValueError("Both upgrade_all and upgrade_packages are given. That's invalid")
        if upgrade_all:
            arguments.append('--upgrade')
        for p in upgrade_packages:
            arguments += ['--upgrade-package', p]

        if stage == self.stage_dev:
            arguments += ['--extra', 'dev']

        print('Generating', full_path)
        try:
            subprocess.run([program_name] + arguments, check=True,
                           capture_output=True)
        except subprocess.CalledProcessError as e:
            print('stdout')
            print(e.stdout.decode())

            print('stderr')
            print(e.stderr.decode())

    def _minimum_python(self) -> str:
        minimum =  metadata('inyoka')['Requires-Python']
        minimum = re.search(">=(?P<version>[^,]*).*", minimum)['version']

        if not minimum:
            raise ValueError("Could not parse minimum python version for inyoka")
        return minimum

    def handle(self, *args, **options):
        upgrade_all = True
        upgrade_packages = []
        if hasattr(options, 'upgrade_packages') and len(options.upgrade_packages) > 0:
            upgrade_packages = options.upgrade_packages
            upgrade_all = False

        for s in self.stages:
            self.generate_requirements_file(s, upgrade_all, upgrade_packages)
