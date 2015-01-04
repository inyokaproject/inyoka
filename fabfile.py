# -*- coding: utf-8 -*-
"""
    Fabfile for Inyoka
    ~~~~~~~~~~~~~~~~~~

    This script is used by fabric for easy deployment.

    :copyright: Copyright 2008-2011 by Florian Apolloner.
    :copyright: (c) 2011-2014 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os

from fabric.api import env, run, roles, local, prompt
from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project

env.roledefs.update({
    'web': ['ubuntuusers@ruwa.ubuntu-eu.org',
            'ubuntuusers@tali.ubuntu-eu.org'],
    'static': ['ubuntuusers@ellegua.ubuntu-eu.org']
})

env.repository = 'git@github.com:inyokaproject/inyoka'
env.target_dir = '/srv/local/ubuntuusers/inyoka'

env.theme_repository = 'git@github.com:inyokaproject/theme-ubuntuusers'
env.theme_target_dir = '/srv/local/ubuntuusers/theme-ubuntuusers'

STATIC_TMP = '/tmp/ubuntuusers/static/'  # mind the trailing /
STATIC_DIRECTORY = '/srv/www/ubuntuusers/static'  # mind missing /


@roles('web')
def bootstrap(tag):
    """Bootstrap repository clones"""
    if not exists(env.target_dir):
        run(
            'git clone {repo} {dir}'.format(
                repo=env.repository,
                dir=env.target_dir
            )
        )
    if not exists(env.theme_target_dir):
        run(
            'git clone {repo} {dir}'.format(
                repo=env.theme_repository,
                dir=env.theme_target_dir
            )
        )


@roles('web')
def deploy(tag):
    """Update Inyoka to a specific tag"""
    with cd(env.target_dir):
        run(
            'git fetch origin master --tags;'
            'git checkout {tag}'.format(tag=tag)
        )


@roles('web')
def rollback(tag):
    """Rollback to a specific tag."""
    with cd(env.target_dir):
        run('git checkout {tag}'.format(tag=tag))


@roles('web')
def deploy_theme(tag):
    """Update Inyoka to a specific tag"""
    with cd(env.theme_target_dir):
        run(
            'git fetch origin master --tags;'
            'git checkout {tag}'.format(tag=tag)
        )


@roles('web')
def rollback_theme(tag):
    """Rollback to a specific tag."""
    with cd(env.theme_target_dir):
        run('git checkout {tag}'.format(tag=tag))


@roles('static')
def deploy_static():
    """Deploy static files"""
    local('python manage.py collectstatic')
    run('mkdir -p ' + STATIC_TMP)
    rsync_project(STATIC_TMP, os.path.join('inyoka', 'static-collected/'))
    run('mkdir -p ' + STATIC_DIRECTORY)
    run('rsync -rt --delete ' + STATIC_TMP + ' ' + STATIC_DIRECTORY)


@roles('web')
def pip():
    """Run pip on the server"""
    if not getattr(env, 'parameters', None):
        prompt('pip parameters', key='parameters')
    run(
        'source {target_dir}/../bin/activate;'
        'pip {parameters}'.format(
            **{
                'target_dir': env.target_dir,
                'parameters': env.parameters
            }
        )
    )
