import os, sys
import tempfile, shutil
from os import path

python_version = '2.7.3'
python_main_version = '2.7'


def install_requirements(home_dir, requirements):
    if not requirements:
        return
    home_dir = os.path.abspath(home_dir)
    cmd = [os.path.join(home_dir, 'bin', 'pip')]
    cmd.extend(['install', '--use-mirrors', '-r', os.path.join(home_dir, requirements)])
    call_subprocess(cmd)


def after_install(options, home_dir):
    easy_install('pip', home_dir)
    install_requirements(home_dir, options.requirements)


def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append('-O2')
    cmd.append(package)
    call_subprocess(cmd)


def extend_parser(parser):
    parser.add_option('-r', '--requirements', dest='requirements',
                      default='',
                      help='Path to a requirements file usable with pip')
    parser.add_option('-f', '--force-rebuild', dest='force_rebuild',
                      default=False,
                      help=u'Force rebuilding the python interpreter')


def adjust_options(options, args):
    global FETCH_CMD, logger

    verbosity = options.verbose - options.quiet
    logger = Logger([(Logger.level_for_integer(2-verbosity), sys.stdout)])

    dest_dir = path.abspath(args[0])

    try:
        call_subprocess(['which', 'wget'], show_stdout=False)
        FETCH_CMD = ['wget', '-c']
    except OSError:
        # wget does not exist, try curl instead
        try:
            call_subprocess(['which', 'curl'], show_stdout=False)
            FETCH_CMD = ['curl', '-L', '-O']
        except OSError:
            sys.stderr.write('\\nERROR: need either wget or curl\\n')
            sys.exit(1)

    build_dir = path.join(dest_dir, 'build')
    python_folder = path.join(build_dir, 'Python-%s' % python_version)
    python_was_built = path.join(build_dir,'.python_was_built')
    if not path.exists(build_dir):
        os.makedirs(build_dir)

    if not os.path.exists(python_was_built) or options.force_rebuild:
        # checkout python distribution
        call_subprocess(FETCH_CMD + ['http://python.org/ftp/python/%s/Python-%s.tar.bz2' % (python_version, python_version)],
                        cwd=build_dir)
        call_subprocess(['tar', '-xjf', 'Python-%s.tar.bz2' % python_version],
                        cwd=build_dir)

        # configure python
        call_subprocess(['./configure', '--prefix=%s' % dest_dir,
                         '--enable-unicode=ucs4', '--enable-ipv6',
                         '--with-system-expat', '--with-system-ffi',
                         '--with-fpectl'], cwd=python_folder)
        call_subprocess(['make', 'OPT=-g'], cwd=python_folder)
        call_subprocess(['make', 'install'], cwd=python_folder)

    # touch a special file to indicate we have already build a python interpreter
    with open(python_was_built, 'a'):
        os.utime(python_was_built, None)

    options.python = path.join(python_folder, 'python')
    options.no_site_packages = True
    options.unzip_setuptools = True
    options.use_distribute = True
