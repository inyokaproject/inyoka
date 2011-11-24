# -*- coding: utf-8 -*-
"""
    Fabfile for Inyoka
    ~~~~~~~~~~~~~~~~~~

    This script is used by fabric for easy deployment.

    :copyright: Copyright 2008-2011 by Florian Apolloner.
    :license: GNU GPL.
"""
import os
from fabric.api import env, run, local, put, require, prompt, open_shell, \
    roles, settings
from fabric.contrib.project import rsync_project
from fabric.context_managers import cd


env.roledefs.update({
    'web': ['ubuntu_de@dongo.ubuntu-eu.org',
            'ubuntu_de@unkul.ubuntu-eu.org',
            'ubuntu_de@oya.ubuntu-eu.org'],
    'static': ['apollo13@lisa.ubuntu-eu.org']
})

env.repository = 'git@github.com:inyokaproject/inyoka'
env.target_dir = '~/virtualenv/inyoka'

STATIC_DIRECTORY = '/home/ubuntu_de_static'


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
    compile_static()
    with settings(target_dir=STATIC_DIRECTORY):
        rsync_project(env.target_dir, 'inyoka/static')


def pip():
    """Run pip on the server"""
    if not getattr(env, 'parameters', None):
        prompt('pip parameters', key='parameters')
    run('unlet PYTHONPATH;'
        'source {target_dir}/../bin/activate;'
        'pip {parameters}'.format(**{
            'target_dir': env.target_dir,
            'parameters': env.parameters}))


def check_js():
    rhino = 'java -jar extra/js.jar'
    local("%s extra/jslint-check.js" % rhino, capture=False)


def compile_js(file=None):
    """Minimize js files"""
    rhino = 'java -jar extra/js.jar'
    minjar = 'java -jar extra/google-compiler.jar'
    #TODO: find some way to preserve comments on top
    if file is None:
        files = os.listdir('inyoka/static/js')
        files = [fn for fn in files if not '.min.' in fn and not fn.startswith('.')]
    else:
        files = [file]
    for file in files:
        local("%s --js inyoka/static/js/%s --warning_level QUIET > inyoka/static/js/%s" %
            (minjar, file, file.split('.js')[0] + '.min.js'), capture=False)


def compile_css(file=None):
    """Create sprited css files for deployment"""
    files = u' inyoka/static/style/'.join(('', 'main.less', 'forum.less', 'editor.less'))
    local("java -classpath extra/smartsprites -Djava.ext.dirs=extra/smartsprites "
          "org.carrot2.labs.smartsprites.SmartSprites"
          " %s" % files, capture=False)

    less = './extra/less.js/bin/lessc -x -O2'
    if file is None:
        files = [fn for fn in os.listdir('inyoka/static/style') if fn.endswith('.less')]
    else:
        files = [file]
    for file in files:
        local("%s inyoka/static/style/%s > inyoka/static/style/%s" %
            (less, file, file.split('.less')[0] + '.css'), capture=False)


def compile_static():
    compile_js()
    compile_css()

def compile_translations():
    """Build mo files from po"""
    local('python manage.py compilemessages', capture=False)
