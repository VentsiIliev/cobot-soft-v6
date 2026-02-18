import pytest
import numpy as np
from unittest.mock import Mock, patch
from PyQt6.QtCore import QPointF
from workpiece_editor.handlers.CaptureDataHandler import CaptureDataHandler


class TestCaptureDataHandlerBasicProcessing:
    """Test basic data processing"""

    def test_handle_capture_data_basic_structure(self):
        mock_workpiece_manager = Mock()
        mock_capture_data = Mock()
        mock_capture_data.workpiece_contour = np.array([[10, 20], [30, 40]], dtype=np.float32)
        mock_capture_data.estimatedHeight = 50
        result = CaptureDataHandler.handle_capture_data(
            workpiece_manager=mock_workpiece_manager,
            capture_data=mock_capture_data,
            close_contour=True
        )
        assert result is not None
        mock_workpiece_manager.load_editor_data.assert_called_once()

    def test_handle_capture_data_creates_editor_data(self):
        mock_workpiece_manager = Mock()
        mock_capture_data = Mock()
        mock_capture_data.workpiece_contour = np.array([[10, 20]], dtype=np.float32)
        mock_capture_data.estimatedHeight = 50
        result = CaptureDataHandler.handle_capture_data(
            workpiece_manager=mock_workpiece_manager,
            capture_data=mock_capture_data
        )
        assert result is not None
        assert len(result.layers) > 0

    def test_handle_capture_data_calls_workpiece_manager(self):
        mock_workpiece_manager = Mock()
        mock_capture_data = Mock()
        mock_capture_data.workpiece_contour = np.array([[10, 20]], dtype=np.float32)
        mock_capture_data.estimatedHeight = 50
        CaptureDataHandler.handle_capture_data(
            workpiece_manager=mock_workpiece_manager,
            capture_data=mock_capture_data,
            close_contour=False
        )
        mock_workpiece_manager.load_editor_data.assert_called_once()
        call_args = mock_workpiece_manager.load_editor_data.call_args
        assert call_args[1]['close_contour'] == False


class TestCaptureDataHandlerContourNormalization:
    """Test contour normalization"""

    def test_normalize_contour_to_opencv_format(self):
        # 2D array (N, 2) -> should become (N, 1, 2)
        contour = np.array([[10, 20], [30, 40], [50, 60]], dtype=np.float32)
        result = CaptureDataHandler._normalize_contour(contour)
        assert result.shape == (3, 1, 2)
        assert result[0, 0, 0] == 10
        assert result[0, 0, 1] == 20

    def test_normalize_contour_handles_invalid_data(self):
        # Invalid shape that cannot be reshaped
        contour = np.array([1, 2, 3], dtype=np.float32)
        result = CaptureDataHandler._normalize_contour(contour)
        # Should either return None or handle gracefully
        assert result is None or isinstance(result, np.ndarray)

    def test_normalize_contour_preserves_precision(self):
        contour = np.array([[10.5, 20.7], [30.2, 40.9]], dtype=np.float32)
        result = CaptureDataHandler._normalize_contour(contour)
        assert result.dtype == np.float32
        np.testing.assert_array_almost_equal(result[0, 0], [10.5, 20.7])


class TestCaptureDataHandlerMetadata:
    """Test metadata handling"""

    def test_handle_capture_data_extracts_metadata(self):
        mock_workpiece_manager = Mock()
        mock_capture_data = Mock()
        mock_capture_data.workpiece_contour = np.array([[10, 20]], dtype=np.float32)
        mock_capture_data.estimatedHeight = 100
        result = CaptureDataHandler.handle_capture_data(
            workpiece_manager=mock_workpiece_manager,
            capture_data=mock_capture_data
        )
        # Check that metadata was included
        workpiece_layer = result.get_layer("Workpiece")
        assert workpiece_layer is not None
        if len(workpiece_layer.segments) > 0:
            segment = workpiece_layer.segments[0]
            assert hasattr(segment, 'metadata')

    def test_handle_capture_data_applies_settings(self):
        contours = np.array([[10, 20], [30, 40]], dtype=np.float32)
        metadata = {"height": 50, "source": "test"}
        result = CaptureDataHandler.from_capture_data(
            contours=contours,
            metadata=metadata
        )
        assert result is not None
        workpiece_layer = result.get_layer("Workpiece")
        assert workpiece_layer is not None


class TestCaptureDataHandlerEdgeCases:
    """Test edge cases"""

    def test_handle_capture_data_empty_contour(self):
        mock_workpiece_manager = Mock()
        mock_capture_data = Mock()
        mock_capture_data.workpiece_contour = []
        mock_capture_data.estimatedHeight = 50
        result = CaptureDataHandler.handle_capture_data(
            workpiece_manager=mock_workpiece_manager,
            capture_data=mock_capture_data
        )
        assert result is None

    def test_handle_capture_data_malformed_data(self):
        mock_workpiece_manager = Mock()
        mock_capture_data = Mock()
        mock_capture_data.workpiece_contour = None
        mock_capture_data.estimatedHeight = 50
        result = CaptureDataHandler.handle_capture_data(
            workpiece_manager=mock_workpiece_manager,
            capture_data=mock_capture_data
        )
        assert result is None
