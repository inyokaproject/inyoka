"""
tests.wiki.test_forms
~~~~~~~~~~~~~~~~~~~~~

Test wiki forms.

:copyright: (c) 2011-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from functools import partial
from os import path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile

from inyoka.portal.user import User
from inyoka.utils.storage import storage
from inyoka.utils.test import TestCase
from inyoka.wiki.models import Page
from tests.utils.test_clamav import EICAR


# disable surge protection for this test case
@patch('inyoka.wiki.forms.NewArticleForm.surge_protection_timeout', None)
class TestNewArticleForm(TestCase):
    def setUp(self):
        super().setUp()

        self.user = User.objects.register_user(
            'user', 'user@example.test', 'user', False
        )

        from inyoka.wiki.forms import (
            NewArticleForm,  # globally the storage table would not exist
        )

        self.form = partial(NewArticleForm, user=self.user)
        self.data = {'name': 'new', 'template': ''}

        storage['wiki_newpage_root'] = 'prefix'

        self._create_page(
            'ACL',
            '#X-Behave: Access-Control-List\n'
            '{{{\n'
            '[*]\n'
            'user=none\n'
            '[prefix/*]\n'
            'user=all\n'
            '}}}',
        )

    def _create_page(self, name, text, **kwargs):
        return Page.objects.create(name, text, user=self.user, note='comment', **kwargs)

    def _post_form(self):
        form = self.form(data=self.data)
        form.full_clean()

        self.assertEqual(
            form.cleaned_data['name'],
            storage['wiki_newpage_root'] + '/' + self.data['name'],
        )

    def test_unprivileged_creates_article(self):
        self._post_form()

    def test_unprivileged_creates_subarticle(self):
        self.data['name'] = 'Howto/new'
        self._post_form()


class TestManageDiscussionForm(TestCase):
    def setUp(self):
        super().setUp()

        # globally the storage table would not exist
        from inyoka.wiki.forms import ManageDiscussionForm

        self.form = ManageDiscussionForm

    def test_no_topic(self):
        form = self.form(data={'topic': ''})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['topic'], None)

    def test_not_existing_topic(self):
        form = self.form(data={'topic': 'not_existing'})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'topic': ['This topic does not exist.']})


class TestAddAttachmentForm(TestCase):
    def setUp(self):
        super().setUp()

        # globally the storage table would not exist
        from inyoka.wiki.forms import AddAttachmentForm

        self.form = AddAttachmentForm

    def test_attachment_contains_eicar(self):
        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar.txt', EICAR.read())
        form = self.form(files={'attachment': upload_object})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'attachment': ['File is infected with malware']})

    def test_mime_not_an_image(self):
        upload_object = SimpleUploadedFile('eicar.png', b'foobar', content_type='image/png')
        form = self.form(files={'attachment': upload_object})

        self.assertEqual(form.errors, {'attachment': ['Invalid image.']})

    def test_wrong_file_extension(self):
        path_file = path.join(path.dirname(__file__), 'happy.png')

        with open(path_file, 'rb') as f:
            upload_object = SimpleUploadedFile('eicar.pdf', f.read(), content_type='image/png')
        form = self.form(files={'attachment': upload_object})

        self.assertEqual(form.errors, {'attachment': ['File extension does not fit to the files mime type.']})

    def test_valid_images(self):
        to_test = (
            {'filename': 'happy.png', 'mime': 'image/png'},
            {'filename': 'test_attachment.avif', 'mime': 'image/avif'},
            {'filename': 'test_attachment.gif', 'mime': 'image/gif'},
            {'filename': 'test_attachment.jpg', 'mime': 'image/jpeg'},
            {'filename': 'test_attachment.webp', 'mime': 'image/webp'},
        )

        for t in to_test:
            with self.subTest(t['filename']):
                path_file = path.join(path.dirname(__file__), t['filename'])

                with open(path_file, 'rb') as f:
                    upload_object = SimpleUploadedFile(t['filename'], f.read(), content_type=t['mime'])
                form = self.form(files={'attachment': upload_object})

                self.assertTrue(form.is_valid())

    def test_pdf(self):
        path_file = path.join(path.dirname(__file__), '../../utils/test.pdf')

        with open(path_file, 'rb') as f:
            upload_object = SimpleUploadedFile('test.pdf', f.read(), content_type='application/pdf')
        form = self.form(files={'attachment': upload_object})

        self.assertTrue(form.is_valid())

    def test_missmatch_content_typ_and_mimetype(self):
        path_file = path.join(path.dirname(__file__), 'happy.png')

        with open(path_file, 'rb') as f:
            upload_object = SimpleUploadedFile('eicar.png', f.read(), content_type='image/jpeg')
        form = self.form(files={'attachment': upload_object})

        self.assertEqual(form.errors, {'attachment': ['Transmitted mimetype does not fit the files mimetype.']})

    def test_no_file_extension(self):
        upload_object = SimpleUploadedFile('eicar', b'foobar', content_type='image/png')
        form = self.form(files={'attachment': upload_object})

        self.assertEqual(form.errors, {'attachment': ['File has no file extension.']})

    def test_partial_png(self):
        path_file = path.join(path.dirname(__file__), 'test_partial.png')

        with open(path_file, 'rb') as f:
            upload_object = SimpleUploadedFile('partial.png', f.read(), content_type='image/png')
        form = self.form(files={'attachment': upload_object})
        self.assertEqual(form.errors, {'attachment': ['Corrupted image.']})

    def test_bat(self):
        upload_object = SimpleUploadedFile('eicar.gz', b'foobar', content_type='application/gzip')
        form = self.form(files={'attachment': upload_object})

        self.assertTrue(form.is_valid())


class TestEditAttachmentForm(TestCase):
    def setUp(self):
        super().setUp()

        # globally the storage table would not exist
        from inyoka.wiki.forms import EditAttachmentForm

        self.form = EditAttachmentForm

    def test_attachment_contains_eicar(self):
        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = self.form(files={'attachment': upload_object})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'attachment': ['File is infected with malware']})
