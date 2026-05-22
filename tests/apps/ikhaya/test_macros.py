"""
inyoka.ikhaya.test_macros
~~~~~~~~~~~~~~~~~~~~~~~~~

Tests for inyoka.ikhaya.macros.

:copyright: (c) 2025-2026 by the Inyoka Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import os
import tempfile
from unittest.mock import Mock, patch

from inyoka.ikhaya.macros import build_ikhaya_picture_node
from inyoka.markup import nodes
from inyoka.portal.models import StaticFile
from inyoka.utils.test import TestCase


class TestBuildIkhayaPictureNode(TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

  def tearDown(self):
    import shutil
    if os.path.exists(self.temp_dir):
      shutil.rmtree(self.temp_dir)

  def test_returns_none_when_context_application_not_ikhaya(self):
    """Test that function returns None when context.application is not 'ikhaya'."""
    sender = Mock()

    context = Mock()
    context.application = 'wiki' # not 'ikhaya'

    result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsNone(result)

  def test_returns_image_node_without_dimensions(self):
    """Test returns Image node when no width/height specified."""
    # Create temporary file
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    # Create StaticFile
    static_file = StaticFile(
      identifier='test.png',
      file=test_file_path
    )
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = None
    sender.height = None
    sender.alt = 'Test Alt'
    sender.align = 'left'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
        mock_url_for.return_value = '/media/portal/files/test.png'

        result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Image)
    self.assertEqual(result.alt, 'Test Alt')
    self.assertEqual(result.class_, 'image-left')
    self.assertEqual(result.title, 'Test Title')

  def test_returns_image_node_with_default_align(self):
    """Test Image node has 'image-default' class when align is None."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = StaticFile(
      identifier='test.png',
      file=test_file_path
    )
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = None
    sender.height = None
    sender.alt = 'Test Alt'
    sender.align = None
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
        mock_url_for.return_value = '/media/portal/files/test.png'

        result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Image)
    self.assertEqual(result.class_, 'image-default')

  def test_generates_thumbnail_with_width_and_height(self):
    """Test thumbnail generation when both width and height are provided."""
    # Create temporary file
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = 100
    sender.height = 50
    sender.alt = 'Test Alt'
    sender.align = 'center'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          mock_thumbnail.return_value = 'portal/thumbnails/test100x50.png'
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/test.png'

            result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Link)
    self.assertEqual(mock_thumbnail.call_count, 1)

    # Verify the call arguments
    call_args = mock_thumbnail.call_args
    self.assertIn('100x50', str(call_args))

  def test_fallback_to_original_when_thumbnail_generation_fails(self):
    """Test fallback to original file when thumbnail generation returns None."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = 100
    sender.height = 50
    sender.alt = 'Test Alt'
    sender.align = 'right'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          mock_thumbnail.return_value = None
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/test.png'

            result = build_ikhaya_picture_node(sender, context, 'html')

    # Should still return a Link wrapping the Image
    self.assertIsInstance(result, nodes.Link)
    mock_url_for.assert_called()

  def test_no_thumbnail_when_file_does_not_exist(self):
    """Test that thumbnail is not generated if file doesn't exist on disk."""
    static_file = Mock(spec=StaticFile)
    static_file.file.path = '/nonexistent/path/test.png'
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = 100
    sender.height = 50
    sender.alt = 'Test Alt'
    sender.align = 'left'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = False
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/test.png'

            result = build_ikhaya_picture_node(sender, context, 'html')

    # Should return Image without Link (no dimensions)
    self.assertIsInstance(result, nodes.Image)
    mock_thumbnail.assert_not_called()

  def test_handles_static_file_does_not_exist_exception(self):
    """Test that function returns None when StaticFile does not exist."""
    sender = Mock()
    sender.target = 'nonexistent.png'
    sender.width = 100
    sender.height = 50
    sender.alt = 'Test Alt'
    sender.align = 'left'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.side_effect = StaticFile.DoesNotExist()

      result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsNone(result)

  def test_link_wraps_image_when_dimensions_provided(self):
    """Test that Image is wrapped in Link when dimensions are provided."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = 200
    sender.height = 100
    sender.alt = 'Test Alt'
    sender.align = 'right'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          mock_thumbnail.return_value = 'portal/thumbnails/test200x100.png'
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/test.png'

            result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Link)
    self.assertIsInstance(result.children[0], nodes.Image)

  def test_image_not_linked_when_no_dimensions(self):
    """Test that Image is not wrapped in Link when no dimensions provided."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = None
    sender.height = None
    sender.alt = 'Test Alt'
    sender.align = 'left'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
        mock_url_for.return_value = '/media/portal/files/test.png'

        result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Image)
    self.assertNotIsInstance(result, nodes.Link)

  def test_thumbnail_path_construction(self):
    """Test that thumbnail path is correctly constructed with dimensions."""
    test_file_path = os.path.join(self.temp_dir, 'image.jpg')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/image.jpg'

    sender = Mock()
    sender.target = 'image.jpg'
    sender.width = 150
    sender.height = 75
    sender.alt = 'Test Alt'
    sender.align = 'center'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          mock_thumbnail.return_value = 'portal/thumbnails/image150x75.jpg'
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/image.jpg'

            build_ikhaya_picture_node(sender, context, 'html')

    # Verify get_thumbnail was called with correct destination path
    call_args = mock_thumbnail.call_args
    self.assertIsNotNone(call_args)
    # The destination should contain the dimension string
    self.assertIn('150x75', str(call_args))

  def test_width_only_dimension(self):
    """Test thumbnail generation with only width specified."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = 200
    sender.height = None
    sender.align = 'left'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          mock_thumbnail.return_value = 'portal/thumbnails/test200x.png'
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/test.png'

            result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Link)
    mock_thumbnail.assert_called_once()

  def test_height_only_dimension(self):
    """Test thumbnail generation with only height specified."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = None
    sender.height = 100
    sender.alt = 'Test Alt'
    sender.align = 'right'
    sender.title = 'Test Title'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('inyoka.ikhaya.macros.get_thumbnail') as mock_thumbnail:
          mock_thumbnail.return_value = 'portal/thumbnails/testx100.png'
          with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
            mock_url_for.return_value = '/media/portal/files/test.png'

            result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertIsInstance(result, nodes.Link)
    mock_thumbnail.assert_called_once()

  def test_image_attributes_preserved(self):
    """Test that all image attributes are properly set."""
    test_file_path = os.path.join(self.temp_dir, 'test.png')
    with open(test_file_path, 'wb') as f:
      f.write(b'fake image data')

    static_file = Mock(spec=StaticFile)
    static_file.file.path = test_file_path
    static_file.file.name = 'portal/files/test.png'

    sender = Mock()
    sender.target = 'test.png'
    sender.width = None
    sender.height = None
    sender.alt = 'Custom Alt Text'
    sender.align = 'center'
    sender.title = 'Custom Title Text'

    context = Mock()
    context.application = 'ikhaya'

    with patch('inyoka.ikhaya.macros.StaticFile.objects.get') as mock_get:
      mock_get.return_value = static_file
      with patch('inyoka.ikhaya.macros.url_for') as mock_url_for:
        mock_url_for.return_value = '/media/portal/files/test.png'

        result = build_ikhaya_picture_node(sender, context, 'html')

    self.assertEqual(result.alt, 'Custom Alt Text')
    self.assertEqual(result.title, 'Custom Title Text')
    self.assertEqual(result.class_, 'image-center')
