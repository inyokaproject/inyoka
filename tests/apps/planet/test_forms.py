"""
tests.apps.planet.test_forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test planet forms.

:copyright: (c) 2025-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile

from inyoka.utils.test import TestCase
from tests.utils.test_clamav import EICAR


class TestEditBlogForm(TestCase):
    def setUp(self):
        super().setUp()

        # globally the storage table would not exist
        from inyoka.planet.forms import EditBlogForm

        self.form = EditBlogForm

    @patch('django.forms.fields.ImageField.to_python')
    @patch('django.core.validators.validate_image_file_extension', True)
    @patch('django.core.validators.FileExtensionValidator.__call__', lambda s, x: None)
    def test_icon_contains_eicar(self, mock_method):
        """
        Test that the clamav validator runs on icon field.
        We remove the checks for a valid image file with python mocks.
        """
        mock_method.return_value = EICAR

        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = self.form(
            data={
                'name': 'f',
                'blog_url': 'http://test.example',
                'feed_url': 'http://test.example',
            },
            files={'icon': upload_object},
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'icon': ['File is infected with malware']})
