# -*- coding: utf-8 -*-
"""
    tests.utils.test_files
    ~~~~~~~~~~~~~~~~~~~~~~

    Test the uniqueness of file names, as well as the file name length.

    :copyright: (c) 2012-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from django.core.files.base import ContentFile

from inyoka.utils.files import InyokaFSStorage


class TestFileStorage(unittest.TestCase):
    def setUp(self):
        self.s = InyokaFSStorage()

    def test_dangerous_name(self):
        self.assertRaises(ValueError, self.s.get_available_name, u'A/../B')
        self.assertRaises(ValueError, self.s.get_available_name, u'../B')
        self.assertRaises(ValueError, self.s.get_available_name, u'B/..')
        self.assertRaises(ValueError, self.s.get_available_name, u'B/../')

    def test_long_name_no_path(self):
        self.s.max_length = 20
        self.s.min_file_root_length = 5

        name = '12345.jpg'
        self.assertEqual(self.s.get_available_name(name), '12345.jpg')

        name = '123456789012345.jpg'
        self.assertEqual(self.s.get_available_name(name), '123456789012345.jpg')

        name = '1234567890123456.jpg'
        self.assertEqual(self.s.get_available_name(name), '1234567890123456.jpg')

        name = '12345678901234567.jpg'
        self.assertEqual(self.s.get_available_name(name), '1234567890123456.jpg')

    def test_long_name_short_file_root(self):
        self.s.max_length = 20
        self.s.min_file_root_length = 5

        path = '1234/'
        name = path + '12345.jpg'
        self.assertEqual(self.s.get_available_name(name), path + '12345.jpg')

        path = '123456789/'
        name = path + '12345.jpg'
        self.assertEqual(self.s.get_available_name(name), path + '12345.jpg')

        path = '1234567890/'
        name = path + '12345.jpg'
        self.assertEqual(self.s.get_available_name(name), path + '12345.jpg')

        path = '12345678901/'
        name = path + '12345.jpg'
        self.assertRaises(AssertionError, self.s.get_available_name, name)

    def test_long_name_overlength_file_root(self):
        self.s.max_length = 20
        self.s.min_file_root_length = 5

        path = '1234567890/'
        name = path + '123456.jpg'
        self.assertEqual(self.s.get_available_name(name), path + '12345.jpg')

        path = '1234567890/'
        name = path + '1234567890.jpg'
        self.assertEqual(self.s.get_available_name(name), path + '12345.jpg')

        path = '123456789/'
        name = path + '1234567890.jpg'
        self.assertEqual(self.s.get_available_name(name), path + '123456.jpg')

    def test_add_underscore_exact_length(self):
        self.s.max_length = 20
        self.s.min_file_root_length = 5

        path = '123456789/'
        name = path + '123456.jpg'
        created_files = []
        # The length of the original file path is equal to max_length
        try:
            new_name = self.s.save(name, ContentFile('data'))
            created_files.append(new_name)
            self.assertEqual(new_name, path + '123456.jpg')
            for i in xrange(1, 10):
                new_name = self.s.save(name, ContentFile('data'))
                created_files.append(new_name)
                self.assertEqual(new_name, path + '1234_%d.jpg' % i)
            for i in xrange(10, 15):
                new_name = self.s.save(name, ContentFile('data'))
                created_files.append(new_name)
                self.assertEqual(new_name, path + '123_%d.jpg' % i)
            self.assertEqual(len(created_files), 15)
        finally:
            for f in created_files:
                self.s.delete(f)

    def test_add_underscore_overlength(self):
        self.s.max_length = 20
        self.s.min_file_root_length = 5

        path = '1234567/'
        name = path + '123456.jpg'
        created_files = []
        try:
            new_name = self.s.save(name, ContentFile('data'))
            created_files.append(new_name)
            # This complete path is shorter than max_length
            self.assertEqual(new_name, path + '123456.jpg')
            for i in xrange(1, 10):
                new_name = self.s.save(name, ContentFile('data'))
                created_files.append(new_name)
                # This complete path length is equal to max_length
                self.assertEqual(new_name, path + '123456_%d.jpg' % i)
            for i in xrange(10, 15):
                new_name = self.s.save(name, ContentFile('data'))
                created_files.append(new_name)
                # This complete path length would be greater than max_length,
                # hence the file_root is truncated at the end
                self.assertEqual(new_name, path + '12345_%d.jpg' % i)
            self.assertEqual(len(created_files), 15)
        finally:
            for f in created_files:
                self.s.delete(f)

    def test_add_underscore_underlength(self):
        self.s.max_length = 20
        self.s.min_file_root_length = 5

        path = '1234/'
        name = path + '123456.jpg'
        created_files = []
        # All complete paths are shorter than max_length
        try:
            new_name = self.s.save(name, ContentFile('data'))
            created_files.append(new_name)
            self.assertEqual(new_name, path + '123456.jpg')
            for i in xrange(1, 10):
                new_name = self.s.save(name, ContentFile('data'))
                created_files.append(new_name)
                self.assertEqual(new_name, path + '123456_%d.jpg' % i)
            for i in xrange(10, 15):
                new_name = self.s.save(name, ContentFile('data'))
                created_files.append(new_name)
                self.assertEqual(new_name, path + '123456_%d.jpg' % i)
            self.assertEqual(len(created_files), 15)
        finally:
            for f in created_files:
                self.s.delete(f)
