import os
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def mkdummy(name):
    def dummy(*args, **kwargs):
        return name
    return dummy


def mkenv(root):
    env = Environment(
        loader=FileSystemLoader(root),
        extensions=['jinja2.ext.i18n', 'jinja2.ext.do']
    )

    env.globals.update(
        INYOKA_VERSION=None,
        WIKI_MAIN_PAGE='Welcome',
        href=mkdummy('href-link'),
        csrf_token=lambda: 'csrf_token-content'
    )

    for n in ('date', 'datetime', 'hnumber', 'ischeckbox', 'jsonencode',
              'naturalday', 'time', 'timetz', 'timedeltaformat', 'url', 'urlencode'):
        env.filters[n] = mkdummy(n)

    return env


class TestTemplateSyntax(unittest.TestCase):

    def setUp(self):
        self.env = mkenv(inyoka_root)


def main(root):

    def gen_test_func(template_name):
        def test_func(self):
            self.env.get_template(template_name)
        return test_func

    for file in root.glob('./**/jinja2/**/*.html'):
        name = os.path.relpath(os.path.join(file), root)
        func_name = 'test_%s' % name.replace('/', '__').replace('.', '_')
        setattr(TestTemplateSyntax, func_name, gen_test_func(name))


inyoka_root = Path(__file__).resolve().parent.parent.parent.parent
main(inyoka_root)
