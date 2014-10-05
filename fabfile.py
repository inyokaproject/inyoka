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

from fabric.api import env, put, run, roles, local, prompt, require, settings, open_shell
from fabric.contrib.project import rsync_project
from fabric.context_managers import cd
from fabric.operations import sudo

env.roledefs.update({
    'web': ['ubuntu_de@dongo.ubuntu-eu.org',
            'ubuntu_de@unkul.ubuntu-eu.org',
            'ubuntu_de@oya.ubuntu-eu.org'],
    'static': ['encbladexp@ellegua.ubuntu-eu.org']
})

env.repository = 'git@github.com:inyokaproject/inyoka'
env.target_dir = '~/virtualenv/inyoka'

STATIC_TMP = '/tmp/ubuntuusers/static/'  # mind the trailing /
STATIC_DIRECTORY = '/srv/www/ubuntuusers/static'  # mind missing /


def bootstrap():
    """Create a virtual environment.  Call this once on every new server."""
    env.hosts = [x.strip() for x in raw_input('Servers: ').split(',')]
    env.interpreter = raw_input('Python-executable (default: python2.5): ').strip() or 'python2.5'
    env.target_dir = raw_input('Location (default: %s): ' % TARGET_DIR).strip().rstrip('/') or TARGET_DIR
    run('mkdir {target_dir}'.format(target_dir=env.target_dir))
    run('git clone {repository} {target_dir}/inyoka'.format(target_dir=env.target_dir))
    run('{interpreter} {target_dir}/inyoka/make-bootstrap.py > {target_dir}/bootstrap.py'.format(**{
        'interpreter': env.interpreter,
        'target_dir': env.target_dir}))
    run('unset PYTHONPATH; {interpreter} {target_dir}/bootstrap.py --no-site-packages {target_dir}'.format(**{
        'interpreter': env.interpreter,
        'target_dir': env.target_dir}))
    run("ln -s {target_dir}/inyoka/inyoka {target_dir}/lib/python`{interpreter} -V 2>&1|grep -o '[0-9].[0-9]'`/site-packages".format(**{
        'target_dir': env.target_dir,
        'interpreter': env.interpreter}))


@roles('web')
def deploy(tag):
    """Update Inyoka to a specific tag"""
    with cd(env.target_dir):
        run('git fetch origin master --tags;'
            'git checkout {tag}'.format(tag=tag))


@roles('web')
def rollback(tag):
    """Rollback to a specific tag."""
    with cd(env.target_dir):
        run('git checkout {tag}'.format(tag=tag))


@roles('static')
def deploy_static():
    """Deploy static files"""
    #compile_static()
    local('python manage.py collectstatic')
    run('mkdir -p ' + STATIC_TMP)
    rsync_project(STATIC_TMP, os.path.join('inyoka', 'static-collected/'))
    with settings(shell='/bin/bash -c', sudo_user='ubuntuusers'): 
        sudo('mkdir -p ' + STATIC_DIRECTORY)
        sudo('rsync -rt --delete ' + STATIC_TMP + ' ' + STATIC_DIRECTORY)


@roles('web')
def pip():
    """Run pip on the server"""
    if not getattr(env, 'parameters', None):
        prompt('pip parameters', key='parameters')
    run('source {target_dir}/../bin/activate;'
        'pip {parameters}'.format(**{
            'target_dir': env.target_dir,
            'parameters': env.parameters}))


def check_js():
    rhino = 'java -jar extra/js.jar'
    local("%s extra/jslint-check.js" % rhino, capture=False)


def compile_js(file=None):
    """Minimize js files"""
    minjar = 'java -jar extra/google-compiler.jar'
    #TODO: find some way to preserve comments on top
    if file is None:
        dirs = ['inyoka/static/js/']
        for app in ['forum']:
            dirs += ['inyoka/%s/static/%s/js/' % (app, app)]
        files = []
        for dir in dirs:
            files += [dir + fn for fn in os.listdir(dir) if not '.min.' in fn and not fn.startswith('.')]
    else:
        files = [file]
    for file in files:
        local("%s --js %s > %s" % (minjar, file, file.split('.js')[0] + '.min.js'), capture=False)


def compile_css(file=None):
    """Create sprited css files for deployment"""
    files = u' inyoka/static/style/'.join(('', 'main.less', 'forum.less', 'editor.less'))
    local("java -classpath extra/smartsprites -Djava.ext.dirs=extra/smartsprites "
          "org.carrot2.labs.smartsprites.SmartSprites"
          " %s" % files, capture=False)

    less = './extra/less.js/bin/lessc -x -O2'
    if file is None:
        dirs = ['inyoka/static/style/']
        files = []
        for dir in dirs:
            files += [dir + fn for fn in os.listdir(dir) if fn.endswith('.less')]
        for app in ['forum', 'ikhaya', 'planet', 'portal', 'wiki']:
            files.append('inyoka/%s/static/%s/style/overall.m.less' % (app, app))
    else:
        files = [file]
    for file in files:
        # we need to '_/_/' to successfully compile the less files within app directories
        local("%s --verbose --include-path=inyoka/static/_/_/ %s > %s" % (less, file, file.split('.less')[0] + '.css'), capture=False)


def compile_static():
    compile_js()
    compile_css()


def compile_translations():
    """Build mo files from po"""
    local('python manage.py compilemessages', capture=False)
