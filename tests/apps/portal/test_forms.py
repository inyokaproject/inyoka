"""
    tests.apps.portal.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test portal forms.

    :copyright: (c) 2012-2024 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from functools import partial
from os import path

from django.core.files.uploadedfile import SimpleUploadedFile

from inyoka.portal.forms import EditFileForm, EditStaticPageForm, LoginForm
from inyoka.portal.models import StaticFile, StaticPage
from inyoka.utils.test import TestCase


class TestEditStaticPageForm(TestCase):
    form = EditStaticPageForm

    form_edit = form
    form_create = partial(form, instance=None)

    def test_create_with_already_existing_key(self):
        StaticPage.objects.create(key='foo', title='foo',
                                  content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': title, 'title': title,
                'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Another page with this name already exists. Please '
                      'edit this page.', form.errors['__all__'])

    def test_create_valid_data(self):
        title = 'foo'
        data = {'key': title, 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertTrue(form.is_valid())

    def test_create_without_user_defined_key(self):
        title = 'foo'
        data = {'key': '', 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['key'], title)

    def test_create_key_with_different_case_to_existing_page(self):
        StaticPage.objects.create(key='foo', title='foo',
                                  content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': title, 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Another page with this name already exists. Please '
                      'edit this page.', form.errors['__all__'])

    def test_create_title_with_different_case_to_existing_page(self):
        StaticPage.objects.create(key='foo', title='foo',
                                  content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': '', 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn('Another page with this name already exists. Please '
                      'edit this page.', form.errors['__all__'])

    def test_edit_only_content(self):
        title = 'foo'
        page = StaticPage.objects.create(key=title, title=title,
                                         content='Nobody likes foo?')
        form = self.form_edit({'key': page.title, 'title': page.title, 'content': 'edited'},
                              instance=page)

        self.assertTrue(form.is_valid())

    def test_edit_only_title(self):
        title = 'foo'
        page = StaticPage.objects.create(key=title, title=title,
                                         content='Nobody likes foo?')
        form = self.form_edit({'key': page.title, 'title': 'edited', 'content': page.content},
                              instance=page)

        self.assertTrue(form.is_valid())

    def test_edit_key_changed(self):
        title = 'foo'
        page = StaticPage.objects.create(key=title, title=title,
                                         content='Nobody likes foo?')
        form = self.form_edit({'key': '123', 'title': page.title, 'content': page.content},
                              instance=page)

        self.assertFalse(form.is_valid())
        self.assertIn('It is not allowed to change this key.', form.errors['key'])

    def test_create_empty_title_and_key(self):
        form = self.form_create({'key': '', 'title': '', 'content': 'foo'})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required.', form.errors['title'])

    def test_space_as_title_not_valid(self):
        form = self.form_create({'key': '', 'title': ' ', 'content': 'foo'})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required.', form.errors['title'])


class TestEditFileForm(TestCase):
    path_file1 = path.join(path.dirname(__file__), 'test_attachment.png')
    path_file2 = path.join(path.dirname(__file__), 'test_attachment2.png')

    def test_update(self):
        with open(self.path_file1, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            file = StaticFile.objects.create(identifier='test_attachment.png', file=upload_object)

        with open(self.path_file2, 'rb') as picture_new:
            upload_object = SimpleUploadedFile(picture_new.name, picture_new.read())
            form = EditFileForm(instance=file, files={'file': upload_object})
            self.assertTrue(form.is_valid())

        # identifier is still from the first image
        self.assertEqual(StaticFile.objects.all()[0].identifier, 'test_attachment.png')

    def test_create_file(self):
        with open(self.path_file1, 'rb') as picture_for_upload:
            upload_object = SimpleUploadedFile(picture_for_upload.name, picture_for_upload.read())
            form = EditFileForm(files={'file': upload_object})

            self.assertTrue(form.is_valid())

    def test_create_with_save(self):
        with open(self.path_file1, 'rb') as picture_for_upload:
            upload_object = SimpleUploadedFile(picture_for_upload.name, picture_for_upload.read())
            form = EditFileForm(files={'file': upload_object})
            created_object = form.save()

        self.assertEqual(created_object.identifier, 'test_attachment.png')
        self.assertEqual(StaticFile.objects.count(), 1)

    def test_create_save_commit_false(self):
        with open(self.path_file1, 'rb') as picture_for_upload:
            upload_object = SimpleUploadedFile(picture_for_upload.name, picture_for_upload.read())
            form = EditFileForm(files={'file': upload_object})
            form.save(commit=False)

        self.assertEqual(StaticFile.objects.count(), 0)

    def test_create_with_duplicate(self):
        with open(self.path_file1, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            StaticFile.objects.create(identifier='test_attachment.png', file=upload_object)

            form = EditFileForm(files={'file': upload_object})
            self.assertFalse(form.is_valid())
            self.assertIn('Another file with this name already exists. Please edit this file.', form.errors['file'])

    def test_create_with_duplicate_case_insensitive(self):
        with open(self.path_file1, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            StaticFile.objects.create(identifier='TEST_attachment.png', file=upload_object)

            form = EditFileForm(files={'file': upload_object})
            self.assertFalse(form.is_valid())
            self.assertIn('Another file with this name already exists. Please edit this file.', form.errors['file'])


class TestLoginForm(TestCase):
    form = LoginForm

    def test_no_password(self):
        """Obviously, a login form should miss the password, if no password was submitted."""
        data = {'username': 'user'}
        form = self.form(None, data)

        self.assertFalse(form.is_valid())
        self.assertIn('This field is required.', form.errors['password'])

    def test_password_nul_byte(self):
        data = {'username': 'wUmrLVWz', 'password': '\x00'}
        form = self.form(None, data)

        self.assertFalse(form.is_valid())
        self.assertIn('Null characters are not allowed.', form.errors['password'])

    def test_username_nul_byte(self):
        data = {'username': 'wUmrLVWz\x00', 'password': 'foo'}
        form = self.form(None, data)

        self.assertFalse(form.is_valid())
        self.assertIn('Null characters are not allowed.', form.errors['username'])
