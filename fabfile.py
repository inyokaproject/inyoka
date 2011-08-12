# -*- coding: utf-8 -*-
"""
    Fabfile for Inyoka
    ~~~~~~~~~~~~~~~~~~

    This script is used by fabric for easy deployment.

    :copyright: Copyright 2008-2011 by Florian Apolloner.
    :license: GNU GPL.
"""
import os
from fabric.api import env, run, local, put, require, prompt, open_shell
from fabric.contrib.project import rsync_project
from fabric.context_managers import cd
from tempfile import mktemp as _mktemp

env.user = 'ubuntu_de'
INYOKA_REPO = 'https://inyoka:Faraex3d@hg.apolloner.eu/inyoka-prod/'


def test():
    """
    Fabric target for localhost
    """
    env.hosts = ['127.0.0.1']
    env.user = 'ubuntu_de'

def static():
    """
    Fabric target for static files
    """
    env.hosts = ['lisa.ubuntu-eu.org']
    env.repository = INYOKA_REPO
    env.target_dir = '/home/ubuntu_de_static'
    env.user = 'apollo13'

def production():
    """
    Fabric target for ubuntu-eu.org production servers
    """
    env.hosts = ['dongo.ubuntu-eu.org', 'unkul.ubuntu-eu.org', 'oya.ubuntu-eu.org']
    env.repository = INYOKA_REPO
    env.target_dir = '~/virtualenv/inyoka'
    env.user = 'ubuntu_de'

def bootstrap():
    """Create a virtual environment.  Call this once on every new server."""
    env.hosts = [x.strip() for x in raw_input('Servers: ').split(',')],
    env.interpreter = raw_input('Python-executable (default: python2.5): ').strip() or 'python2.5'
    env.target_dir = raw_input('Location (default: ~/virtualenv): ').strip().rstrip('/') or '~/virtualenv'
    run('mkdir {target_dir}'.format(target_dir=env.target_dir))
    run('hg clone {repository} {target_dir}/inyoka'.format(target_dir=env.target_dir))
    run('{interpreter} {target_dir}/inyoka/make-bootstrap.py > {target_dir}/bootstrap.py'.format(**{
        'interpreter': env.interpreter,
        'target_dir': env.target_dir}))
    run('unset PYTHONPATH; {interpreter} {target_dir}/bootstrap.py --no-site-packages {target_dir}'.format(**{
        'interpreter': env.interpreter,
        'target_dir': env.target_dir}))
    run("ln -s {target_dir}/inyoka/inyoka {target_dir}/lib/python`{interpreter} -V 2>&1|grep -o '[0-9].[0-9]'`/site-packages".format(**{
        'target_dir': env.target_dir,
        'interpreter': env.interpreter}))

def deploy():
    """Update Inyoka and touch the wsgi file"""
    require('hosts', provided_by=[test, production])
    run('unset PYTHONPATH;'
        'source {target_dir}/../bin/activate;'
        'hg pull -R {target_dir} -u {repository}'.format(**{
            'target_dir': env.target_dir,
            'repository': env.repository}))

def deploy_static():
    """Deploy static files"""
    require('hosts', provided_by=[static])
    local('fab compile_static', capture=False)
    rsync_project(env.target_dir, 'inyoka/static')

def pip():
    """Run pip on the server"""
    require('hosts', provided_by=[test, production])
    if not getattr(env, 'parameters', None):
        prompt('pip parameters', key='parameters')
    run('unlet PYTHONPATH;'
        'source {target_dir}/../bin/activate;'
        'pip {parameters}'.format(**{
            'target_dir': env.target_dir,
            'parameters': env.parameters}))


def run_tests(module=''):
    """Run tests"""
    local('python manage.py test --failfast {module}'.format(**{
        'module': module
    }), capture=False)


def reindent():
    """Reindent all python sources"""
    local("extra/reindent.py -r -B .", capture=False)


def syncdb():
    """Sync database models"""
    local("python manage.py syncdb", capture=False)


def migrate():
    """Migrate database"""
    local("python manage.py migrate", capture=False)


def create_test_data():
    """Creates some data, usefull for testing inyoka without production db dump"""
    local("python make_testdata.py", capture=False)


def server():
    """Start development server"""
    local("python manage.py runserver", capture=False)


def shell():
    """Start development shell"""
    local("python manage.py shell", capture=False)


def bash():
    """start a shell within the current context"""
    open_shell()


def dbshell():
    """
    Start a Database Shell for the configured database
    """
    local("python manage.py dbshell", capture=False)


def celeryd():
    """
    Start a celery worker, using our config.
    """
    # we start celery with -B option to make periodic tasks possible
    cmd = ('python manage.py celeryd --loglevel=DEBUG -B')
    local(cmd, capture=False)


def clean_files():
    """Clean most temporary files"""
    for f in '*.py[co]', '*~', '*.orig', '*.rej':
        local("rm -rf `find -name '%s'|grep -v .hg`" % f)

    for f in '*.css', '*.min.js':
        local("rm -rf `find inyoka/static -name '%s'|grep -v .hg|grep -v mobile.css`" % f)


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
