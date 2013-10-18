#-*- coding: utf-8 -*-
import unittest
import magic

from os.path import join, dirname


class TestMagic(unittest.TestCase):

    def setUp(self):
        self.filename = join(dirname(__file__), 'test.pdf')

    def test_from_file(self):
        self.assertEqual(magic.from_file(self.filename), 'PDF document, version 1.4')
        self.assertEqual(magic.from_file(self.filename, mime=True), 'application/pdf')

    def test_from_buffer(self):
        with open(self.filename) as fobj:
            self.assertEqual(magic.from_buffer(fobj.read(1024)), 'PDF document, version 1.4')
