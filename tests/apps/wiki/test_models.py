from os import path
from unittest.mock import patch

from django.core.cache import cache
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from inyoka.utils.test import TestCase
from inyoka.wiki.exceptions import CaseSensitiveException
from inyoka.wiki.models import Attachment, Page, Revision

BASE_PATH = path.dirname(__file__)


class TestPageManager(TestCase):
    def test_get_by_name_case_sensitive(self):
        """
        Tests that get_by_name does not ignore case.
        """
        Page.objects.create('test', 'test content')

        with self.assertRaises(CaseSensitiveException):
            Page.objects.get_by_name('Test', cached=False)

    def test_get_by_name_cache_case_sensitive_set(self):
        """
        Tests that get_by_name creates the correct cache.
        """
        Page.objects.create('Test', 'test content')

        Page.objects.get_by_name('Test')

        self.assertIsNone(cache.get('wiki/page/Test'))
        self.assertIsNotNone(cache.get('wiki/page/test'))

    @patch('inyoka.wiki.models.is_privileged_wiki_page')
    def test_get_by_name__privileged_page(self, mock):
        """
        Test that get_by_name returns Page.DoesNotExist, if querying for privileged page,
        but it should be excluded via parameter.
        """
        Page.objects.create('Test', 'test content')

        mock.return_value = True
        with self.assertRaises(Page.DoesNotExist):
            Page.objects.get_by_name('Test', exclude_privileged=True)

    def test_get_by_name__deleted_page(self):
        """
        Test that get_by_name raises Page.DoesNotExist, if querying for a deleted page.
        """
        page = Page.objects.create('Test', 'test content')
        page.edit(deleted=True)

        with self.assertRaises(Page.DoesNotExist):
            Page.objects.get_by_name('Test', raise_on_deleted=True)

    def test_get_by_name__accent_page(self):
        page = Page.objects.create('Downloads', 'test content')

        try:
            Page.objects.get_by_name('Döwnloads')
        except CaseSensitiveException as e:
            self.assertEqual(page.pk, e.page.pk)

    def test_get_by_name__not_existing(self):
        with self.assertRaises(Page.DoesNotExist):
            Page.objects.get_by_name('Döwnloads')

    def test_get_by_name__queries_used(self):
        Page.objects.create('Test', 'test content')

        with self.assertNumQueries(2):
            Page.objects.get_by_name('Test')

    def test_get_by_name__case_queries_used(self):
        Page.objects.create('Test', 'test content')

        with self.assertNumQueries(2):
            with self.assertRaises(CaseSensitiveException):
                Page.objects.get_by_name('test')

    def test_get_by_name__accent_queries_used(self):
        Page.objects.create('Downloads', 'test content')

        with self.assertNumQueries(4):
            with self.assertRaises(CaseSensitiveException):
                Page.objects.get_by_name('Döwnloads')

    def test_get_missing(self):
        """
        Tests, that get_missing returns a dict with the correct content.
        """
        Page.objects.create('test1', 'test content')
        Page.objects.create('test2', '[:test1:] content')
        test3 = Page.objects.create('test3', '[:missing:] content')

        missing_pages = Page.objects.get_missing()

        self.assertEqual(dict(missing_pages), {'missing': [test3]})

    def test_render_all_pages(self):
        """
        Test, that a rendered page will be put into the cache.
        """
        page = Page.objects.create('test1', '[:test1:] content')

        self.assertFalse(page.rev.text.is_value_in_cache()[0])

        Page.objects.render_all_pages()

        self.assertTrue(page.rev.text.is_value_in_cache()[0])

    def test_render_all_pages__two_pages(self):
        """
        Test, that two rendered pages will be put into the cache.
        """
        page = Page.objects.create('test1', '[:test1:] content')
        page2 = Page.objects.create('test2', 'test content')

        self.assertFalse(page.rev.text.is_value_in_cache()[0])
        self.assertFalse(page2.rev.text.is_value_in_cache()[0])

        Page.objects.render_all_pages()

        self.assertTrue(page.rev.text.is_value_in_cache()[0])
        self.assertTrue(page2.rev.text.is_value_in_cache()[0])


class TestAttachment(TestCase):

    FILE_ANGEL = 'angel.png'
    FILE_EVIL = 'evil.png'
    FILE_HAPPY = 'happy.png'

    def test_attachment_mimetype(self):
        path_file = path.join(BASE_PATH, self.FILE_EVIL)

        with open(path_file, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            attachment = Attachment.objects.create(file=upload_object)

        self.assertEqual(attachment.mimetype, 'image/png')

    def test_attachment_for_page(self):
        path_file = path.join(BASE_PATH, self.FILE_EVIL)

        with open(path_file, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            page = Page.objects.create('test/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                       text='foo', note='create')

        attachment = Page.objects.attachment_for_page(page.name)
        self.assertTrue(attachment.startswith('wiki/attachments/'))

    def test_attachment_for_page__latest(self):
        with open(path.join(BASE_PATH, self.FILE_EVIL), 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            page = Page.objects.create('test/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                       text='foo', note='create')

        attachment1 = Page.objects.attachment_for_page(page.name)
        self.assertTrue(attachment1.startswith('wiki/attachments/'))
        self.assertIn('evil', attachment1)

        with open(path.join(BASE_PATH, self.FILE_ANGEL), 'rb') as angel:
            page.edit(text='', attachment=File(angel), attachment_filename=self.FILE_ANGEL)

        attachment2 = Page.objects.attachment_for_page(page.name)
        self.assertTrue(attachment2.startswith('wiki/attachments/'))
        self.assertIn('angel', attachment2)

        self.assertNotEqual(attachment1, attachment2)

    def test_attachment_for_page__page_does_not_exist(self):
        attachment = Page.objects.attachment_for_page('foobarbar23456678')
        self.assertIsNone(attachment)

    def test_attachment_for_page__page_has_no_attachment(self):
        page = Page.objects.create('test', '[:test1:] content')
        attachment = Page.objects.attachment_for_page(page.name)
        self.assertIsNone(attachment)

    def test_attachment_for_page__deleted_ignored(self):
        with open(path.join(BASE_PATH, self.FILE_EVIL), 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            page = Page.objects.create('test/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                       text='foo', note='create')

        page.edit(deleted=True)
        attachment = Page.objects.attachment_for_page(page.name)
        self.assertIsNotNone(attachment)  # TODO should it be None?

    def test_attachment_for_page__different_case(self):
        with open(path.join(BASE_PATH, self.FILE_EVIL), 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            page = Page.objects.create('test/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                       text='foo', note='create')

        attachment = Page.objects.attachment_for_page(page.name.upper())
        self.assertIsNotNone(attachment)

    def test_attachment_for_page__accent(self):
        """Page name has no ö, but we query its attachment with ö"""
        with open(path.join(BASE_PATH, self.FILE_EVIL), 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            Page.objects.create('Downloads/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                text='foo', note='create')

        attachment = Page.objects.attachment_for_page('Döwnloads/evil.png')
        self.assertIsNone(attachment)

    def test_attachment_for_page__different_case__queries(self):
        with open(path.join(BASE_PATH, self.FILE_EVIL), 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            page = Page.objects.create('test/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                       text='foo', note='create')

        with self.assertNumQueries(2):
            Page.objects.attachment_for_page(page.name.upper())

    def test_attachment_for_page__accent__queries(self):
        with open(path.join(BASE_PATH, self.FILE_EVIL), 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            Page.objects.create('Downloads/evil.png', attachment_filename='evil.png', attachment=upload_object,
                                text='foo', note='create')

        with self.assertNumQueries(2):
            Page.objects.attachment_for_page('Döwnloads/evil.png')
