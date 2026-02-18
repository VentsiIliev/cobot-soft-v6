import pytest
from unittest.mock import Mock, patch
from workpiece_editor.handlers.CaptureHandler import CaptureHandler


@pytest.fixture
def mock_editor_frame():
    """Mock MainApplicationFrame with required structure"""
    frame = Mock()
    frame.contourEditor = Mock()
    frame.contourEditor.workpiece_manager = Mock()
    return frame


@pytest.fixture
def capture_handler(mock_editor_frame):
    """Create CaptureHandler instance"""
    return CaptureHandler(mock_editor_frame)


class TestCaptureHandlerInitialization:
    """Test CaptureHandler initialization"""

    def test_capture_handler_initialization(self, mock_editor_frame):
        handler = CaptureHandler(mock_editor_frame)
        assert handler.editor_frame == mock_editor_frame


class TestCaptureHandlerProcessing:
    """Test capture data processing"""

    @patch('workpiece_editor.handlers.CaptureHandler.CaptureDataHandler')
    def test_handle_capture_data_basic(self, mock_handler, capture_handler, mock_editor_frame):
        capture_data = {"workpiece_contour": [[10, 20], [30, 40]]}
        mock_editor_data = Mock()
        mock_handler.handle_capture_data.return_value = mock_editor_data
        result = capture_handler.handle_capture_data(capture_data, close_contour=True)
        mock_handler.handle_capture_data.assert_called_once_with(
            workpiece_manager=mock_editor_frame.contourEditor.workpiece_manager,
            capture_data=capture_data,
            close_contour=True
        )
        assert result == mock_editor_data

    @patch('workpiece_editor.handlers.CaptureHandler.CaptureDataHandler')
    def test_handle_capture_data_with_close_contour_true(self, mock_handler, capture_handler, mock_editor_frame):
        capture_data = Mock()
        capture_handler.handle_capture_data(capture_data, close_contour=True)
        call_kwargs = mock_handler.handle_capture_data.call_args[1]
        assert call_kwargs['close_contour'] == True

    @patch('workpiece_editor.handlers.CaptureHandler.CaptureDataHandler')
    def test_handle_capture_data_with_close_contour_false(self, mock_handler, capture_handler, mock_editor_frame):
        capture_data = Mock()
        capture_handler.handle_capture_data(capture_data, close_contour=False)
        call_kwargs = mock_handler.handle_capture_data.call_args[1]
        assert call_kwargs['close_contour'] == False

    @patch('workpiece_editor.handlers.CaptureHandler.CaptureDataHandler')
    def test_handle_capture_data_calls_capture_data_handler(self, mock_handler, capture_handler, mock_editor_frame):
        capture_data = Mock()
        capture_handler.handle_capture_data(capture_data)
        mock_handler.handle_capture_data.assert_called_once()


class TestCaptureHandlerErrorHandling:
    """Test error handling"""

    def test_handle_capture_data_missing_workpiece_manager(self, capture_handler):
        # Remove workpiece_manager attribute
        delattr(capture_handler.editor_frame.contourEditor, 'workpiece_manager')
        result = capture_handler.handle_capture_data({})
        assert result is None

    @patch('workpiece_editor.handlers.CaptureHandler.CaptureDataHandler')
    def test_handle_capture_data_exception_handling(self, mock_handler, capture_handler, mock_editor_frame):
        mock_handler.handle_capture_data.side_effect = Exception("Test error")
        result = capture_handler.handle_capture_data({})
        assert result is None
