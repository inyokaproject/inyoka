"""
tests.apps.portal.test_forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test portal forms.

:copyright: (c) 2012-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from functools import partial
from os import path
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from guardian.shortcuts import assign_perm

from inyoka.forum.models import Forum, Topic
from inyoka.ikhaya.models import Category
from inyoka.portal.forms import (
    EditFileForm,
    EditStaticPageForm,
    ForumFeedSelectorForm,
    IkhayaFeedSelectorForm,
    LoginForm,
    PlanetFeedSelectorForm,
    WikiFeedSelectorForm,
)
from inyoka.portal.models import StaticFile, StaticPage
from inyoka.portal.user import User
from inyoka.utils.test import TestCase
from tests.utils.test_clamav import EICAR


class TestEditStaticPageForm(TestCase):
    form = EditStaticPageForm

    form_edit = form
    form_create = staticmethod(partial(form, instance=None))

    def test_create_with_already_existing_key(self):
        StaticPage.objects.create(key='foo', title='foo', content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': title, 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Another page with this name already exists. Please edit this page.',
            form.errors['__all__'],
        )

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
        StaticPage.objects.create(key='foo', title='foo', content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': title, 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Another page with this name already exists. Please edit this page.',
            form.errors['__all__'],
        )

    def test_create_title_with_different_case_to_existing_page(self):
        StaticPage.objects.create(key='foo', title='foo', content='Nobody likes foo?')

        title = 'FOO'
        data = {'key': '', 'title': title, 'content': 'Nobody likes foo?'}
        form = self.form_create(data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Another page with this name already exists. Please edit this page.',
            form.errors['__all__'],
        )

    def test_edit_only_content(self):
        title = 'foo'
        page = StaticPage.objects.create(
            key=title, title=title, content='Nobody likes foo?'
        )
        form = self.form_edit(
            {'key': page.title, 'title': page.title, 'content': 'edited'}, instance=page
        )

        self.assertTrue(form.is_valid())

    def test_edit_only_title(self):
        title = 'foo'
        page = StaticPage.objects.create(
            key=title, title=title, content='Nobody likes foo?'
        )
        form = self.form_edit(
            {'key': page.title, 'title': 'edited', 'content': page.content},
            instance=page,
        )

        self.assertTrue(form.is_valid())

    def test_edit_key_changed(self):
        title = 'foo'
        page = StaticPage.objects.create(
            key=title, title=title, content='Nobody likes foo?'
        )
        form = self.form_edit(
            {'key': '123', 'title': page.title, 'content': page.content}, instance=page
        )

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
            file = StaticFile.objects.create(
                identifier='test_attachment.png', file=upload_object
            )

        with open(self.path_file2, 'rb') as picture_new:
            upload_object = SimpleUploadedFile(picture_new.name, picture_new.read())
            form = EditFileForm(instance=file, files={'file': upload_object})
            self.assertTrue(form.is_valid())

        # identifier is still from the first image
        self.assertEqual(StaticFile.objects.all()[0].identifier, 'test_attachment.png')

    def test_create_file(self):
        with open(self.path_file1, 'rb') as picture_for_upload:
            upload_object = SimpleUploadedFile(
                picture_for_upload.name, picture_for_upload.read()
            )
            form = EditFileForm(files={'file': upload_object})

            self.assertTrue(form.is_valid())

    def test_create_with_save(self):
        with open(self.path_file1, 'rb') as picture_for_upload:
            upload_object = SimpleUploadedFile(
                picture_for_upload.name, picture_for_upload.read()
            )
            form = EditFileForm(files={'file': upload_object})
            created_object = form.save()

        self.assertEqual(created_object.identifier, 'test_attachment.png')
        self.assertEqual(StaticFile.objects.count(), 1)

    def test_create_save_commit_false(self):
        with open(self.path_file1, 'rb') as picture_for_upload:
            upload_object = SimpleUploadedFile(
                picture_for_upload.name, picture_for_upload.read()
            )
            form = EditFileForm(files={'file': upload_object})
            form.save(commit=False)

        self.assertEqual(StaticFile.objects.count(), 0)

    def test_create_with_duplicate(self):
        with open(self.path_file1, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            StaticFile.objects.create(
                identifier='test_attachment.png', file=upload_object
            )

            form = EditFileForm(files={'file': upload_object})
            self.assertFalse(form.is_valid())
            self.assertIn(
                'Another file with this name already exists. Please edit this file.',
                form.errors['file'],
            )

    def test_create_with_duplicate_case_insensitive(self):
        with open(self.path_file1, 'rb') as f:
            upload_object = SimpleUploadedFile(f.name, f.read())
            StaticFile.objects.create(
                identifier='TEST_attachment.png', file=upload_object
            )

            form = EditFileForm(files={'file': upload_object})
            self.assertFalse(form.is_valid())
            self.assertIn(
                'Another file with this name already exists. Please edit this file.',
                form.errors['file'],
            )

    def test_attachment_contains_eicar(self):
        """
        Test that the clamav validator runs on the file field with the eicar test file.
        """
        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = EditFileForm(files={'file': upload_object})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'file': ['File is infected with malware']})


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

    def test_longer_email_as_username(self):
        """
        Form should be valid with an email that is longer than the maximum allowed length
        of a username.
        """
        data = {'username': 'xxxx-xxxxxxx.xxxxxxx@inyoka-test.test', 'password': 'foo'}

        User.objects.register_user(
            'user', email=data['username'], password=data['password'], send_mail=False
        )

        form = self.form(None, data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_too_long_email_as_username(self):
        data = {'username': f'{256 * "x"}@inyoka.test', 'password': 'foo'}

        form = self.form(None, data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                'username': [
                    'Ensure this value has at most 254 characters (it has 268).'
                ]
            },
        )


class TestConfigurationForm(TestCase):
    def setUp(self):
        super().setUp()

        # globally the storage table would not exist
        from inyoka.portal.forms import ConfigurationForm

        self.form = ConfigurationForm

    @patch('django.forms.fields.ImageField.to_python')
    @patch('django.core.validators.validate_image_file_extension', True)
    @patch('django.core.validators.FileExtensionValidator.__call__', lambda s, x: None)
    def test_team_icon_contains_eicar(self, mock_method):
        """
        Test that the clamav validator runs on the team icon field.
        We remove the checks for a valid image file with python mocks.
        """
        mock_method.return_value = EICAR

        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = self.form(files={'team_icon': upload_object})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'team_icon': ['File is infected with malware']})


class TestLinkMapFormset(TestCase):
    def setUp(self):
        super().setUp()

        # globally the storage table would not exist
        from inyoka.portal.forms import LinkMapFormset

        self.form = LinkMapFormset

    @patch('django.forms.fields.ImageField.to_python')
    @patch('django.core.validators.validate_image_file_extension', True)
    @patch('django.core.validators.FileExtensionValidator.__call__', lambda s, x: None)
    def test_icon_contains_eicar(self, mock_method):
        """
        Test that the clamav validator runs on the icon field.
        We remove the checks for a valid image file with python mocks.
        """
        mock_method.return_value = EICAR

        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = self.form(
            data={
                'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-0-url': 'https://test.example',
                'form-0-token': 'eicartest',
            },
            files={'form-0-icon': upload_object},
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, [{'icon': ['File is infected with malware']}])


class TestForumFeedSelectorForm(TestCase):
    def setUp(self):
        super().setUp()

        self.user = User.objects.register_user(
            'user', email='foo@test.example', password='foo', send_mail=False
        )

        anonymous_user = User.objects.get_anonymous_user()

        self.category = Forum(name='category')
        self.category.save()
        self.forum1 = Forum(name='forum1', parent=self.category)
        self.forum1.save()

        assign_perm('forum.view_forum', anonymous_user, self.category)
        assign_perm('forum.view_forum', anonymous_user, self.forum1)

        self.topic = Topic.objects.create(title='A test Topic', author=self.user,
                                     forum=self.forum1)
        # self.post = Post.objects.create(text='Post 1', author=self.user, topic=self.topic, position=0)

        self.form = ForumFeedSelectorForm

    def test_form_valid(self):
        form = self.form({'count': 10, 'mode': 'short'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://forum.{settings.BASE_DOMAIN_NAME}/feeds/short/10/')

    def test_both_forum_and_topic__form_invalid(self):
        form = self.form({'count': 10, 'mode': 'short', 'topic': self.topic.get_absolute_url(), 'forum': self.forum1.id})
        self.assertFalse(form.is_valid())
        self.assertFormError(form, None, errors=['Only forum or topic can be provided.'])

    def test_with_forum(self):
        form = self.form({'count': 10, 'mode': 'short', 'forum': self.forum1.id})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://forum.{settings.BASE_DOMAIN_NAME}/feeds/forum/forum1/short/10/')

    def test_with_topic(self):
        form = self.form({'count': 10, 'mode': 'short', 'topic': self.topic.get_absolute_url()})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://forum.{settings.BASE_DOMAIN_NAME}/feeds/topic/A%20test%20Topic/short/10/')

    def test_invalid_count(self):
        form = self.form({'count': '8', 'mode': 'short'})
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'count',
                             errors=['Select a valid choice. 8 is not one of the available choices.'])

    def test_topic_without_permission(self):
        forum2 = Forum(name='forum2', parent=self.category)
        forum2.save()

        topic = Topic.objects.create(title='Another test Topic', author=self.user,
                                          forum=forum2)
        form = self.form({'count': 10, 'mode': 'short', 'topic': topic.get_absolute_url()})
        self.assertFormError(form, 'topic', errors=['This topic does not exist.'])

    def test_topic_not_existing(self):
        form = self.form({'count': 10, 'mode': 'short', 'topic': 'barbaz'})
        self.assertFormError(form, 'topic', errors=['This topic does not exist.'])

    def test_forum_without_permission(self):
        forum2 = Forum(name='forum2', parent=self.category)
        forum2.save()

        form = self.form({'count': 10, 'mode': 'short', 'forum': forum2.id})
        self.assertFalse(form.is_valid())
        self.assertFormError(
            form,
            'forum',
            errors=[f'Select a valid choice. {forum2.id} is not one of the available choices.']
        )

    def test_forum_not_existing(self):
        form = self.form({'count': 10, 'mode': 'short', 'forum': -5})
        self.assertFalse(form.is_valid())
        self.assertFormError(
            form,
            'forum',
            errors=[
                'Select a valid choice. -5 is not one of the available choices.']
        )

class TestIkhayaFeedSelectorForm(TestCase):
    def setUp(self):
        super().setUp()

        self.category1 = Category.objects.create(name='Test Category')

        self.form = IkhayaFeedSelectorForm

    def test_form_valid__all_categories(self):
        form = self.form({'category': '*', 'mode': 'short', 'count': 20})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/feeds/short/20/')

    def test_form_valid__one_category(self):
        form = self.form({'category': self.category1.slug, 'mode': 'short', 'count': 20})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://ikhaya.{settings.BASE_DOMAIN_NAME}/feeds/test-category/short/20/')

    def test_form_invalid(self):
        form = self.form({'mode': 'short', 'count': 20})
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'category', errors=['This field is required.'])


class TestPlanetFeedSelectorForm(TestCase):
    def setUp(self):
        super().setUp()

        self.form = PlanetFeedSelectorForm

    def test_form_valid(self):
        form = self.form({'mode': 'short', 'count': 20})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://planet.{settings.BASE_DOMAIN_NAME}/feeds/short/20/')

    def test_form_invalid(self):
        form = self.form({'count': 20})
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'mode', errors=['This field is required.'])

class TestWikiFeedSelectorForm(TestCase):
    def setUp(self):
        super().setUp()

        self.form = WikiFeedSelectorForm

    def test_form_valid__with_page(self):
        form = self.form({'mode': 'title', 'count': 20, 'page': 'baz'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://wiki.{settings.BASE_DOMAIN_NAME}/baz/a/feed/20/')

    def test_form_valid__no_page(self):
        form = self.form({'mode': 'title', 'count': 20})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_url(), f'http://wiki.{settings.BASE_DOMAIN_NAME}/_feed/20/')

    def test_form_invalid(self):
        form = self.form({})
        self.assertFalse(form.is_valid())
        self.assertFormError(form, 'count', errors=['This field is required.'])


class TestUserCPProfileForm(TestCase):
    def setUp(self):
        super().setUp()

        self.user = User.objects.register_user(
            'user', email='foo@test.example', password='foo', send_mail=False
        )

        # globally the storage table would not exist
        from inyoka.portal.forms import UserCPProfileForm

        self.form = UserCPProfileForm

    @patch('django.forms.fields.ImageField.to_python')
    @patch('django.core.validators.validate_image_file_extension', True)
    @patch('django.core.validators.FileExtensionValidator.__call__', lambda s, x: None)
    @patch(
        'inyoka.portal.forms.UserCPProfileForm.clean_avatar',
        lambda s: s.cleaned_data['avatar'],
    )
    def test_avatar_contains_eicar(self, mock_method):
        """
        Test that the clamav validator runs on the avatar field.
        We remove the checks for a valid image file with python mocks.
        """
        mock_method.return_value = EICAR

        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = self.form(
            data={'email': self.user.email},
            files={'avatar': upload_object},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'avatar': ['File is infected with malware']})

    def test_avatar_no_image(self):
        EICAR.seek(0)
        upload_object = SimpleUploadedFile('eicar', EICAR.read())
        form = self.form(
            data={'email': self.user.email},
            files={'avatar': upload_object},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                'avatar': [
                    'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
                ]
            },
        )
