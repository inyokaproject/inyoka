# -*- coding: utf-8 -*-
import unittest
from os.path import dirname, join

import magic


class TestMagic(unittest.TestCase):

    def setUp(self):
        self.filename = join(dirname(__file__), 'test.pdf')

    def test_from_file(self):
        self.assertTrue(magic.from_file(self.filename).startswith('PDF document, version 1.4'))
        self.assertEqual(magic.from_file(self.filename, mime=True), 'application/pdf')

    def test_from_buffer(self):
        with open(self.filename, 'rb') as fobj:
            self.assertTrue(magic.from_buffer(fobj.read(1024)).startswith('PDF document, version 1.4'))
