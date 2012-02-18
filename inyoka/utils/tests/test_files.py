#-*- coding: utf-8 -*-
from django.core.files.base import ContentFile
from django.utils.unittest import TestCase
from inyoka.utils.files import InyokaFSStorage


class TestFileStorage(TestCase):
    def setUp(self):
        self.storage = InyokaFSStorage()

    def testDangerousName(self):
        self.assertRaises(ValueError, self.storage.get_available_name, u'A/../B')

    def testLongName(self):
        path = '1234567890' * 9
        name = path + '/1234567890.jpg'
        self.assertEqual(self.storage.get_available_name(name), path + '/12345.jpg')

    def testAddUnderscore(self):
        path = '1234567890' * 9
        name = path + '/1234567890.jpg'
        created_files = []
        try:
            new_name = self.storage.save(name, ContentFile('data'))
            created_files.append(new_name)
            self.assertEqual(new_name, path + '/12345.jpg')
            new_name = self.storage.save(name, ContentFile('data'))
            created_files.append(new_name)
            self.assertEqual(new_name, path + '/123_1.jpg')
        finally:
            for f in created_files:
                self.storage.delete(f)

