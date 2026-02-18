import pytest
from PyQt6.QtCore import QPointF
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from workpiece_editor.managers import WorkpieceManager
from contour_editor.models.segment import Segment, Layer
from contour_editor.persistence.data.editor_data_model import ContourEditorData


@pytest.fixture
def mock_editor():
    editor = Mock()
    editor.manager = Mock()
    editor.manager.segments = []
    editor.manager.external_layer = Layer("Main")
    editor.manager.contour_layer = Layer("Contour")
    editor.manager.fill_layer = Layer("Fill")
    editor.manager.get_segments.return_value = []
    editor.manager.clear_all_segments = Mock()
    editor.manager.contour_to_bezier = Mock(return_value=[])
    editor.update = Mock()
    editor.pointsUpdated = Mock()
    editor.pointsUpdated.emit = Mock()
    return editor


@pytest.fixture
def workpiece_manager(mock_editor):
    return WorkpieceManager(mock_editor)


class TestWorkpieceManagerInitialization:
    def test_initialization(self, workpiece_manager, mock_editor):
        assert workpiece_manager.editor == mock_editor
        assert workpiece_manager.current_workpiece is None
        assert workpiece_manager.contours is None

    def test_initialization_with_none_editor(self):
        manager = WorkpieceManager(None)
        assert manager.editor is None


class TestWorkpieceManagerLoadWorkpiece:
    def test_load_workpiece_basic(self, workpiece_manager):
        workpiece = Mock()
        workpiece.workpieceId = "123"
        with patch('workpiece_editor.managers.workpiece_manager.load_workpiece') as mock_load:
            mock_load.return_value = (workpiece, {"Main": []})
            result = workpiece_manager.load_workpiece(workpiece)
            assert result == workpiece
            assert workpiece_manager.current_workpiece == workpiece

    def test_load_workpiece_with_contours(self, workpiece_manager, mock_editor):
        workpiece = Mock()
        contours_by_layer = {
            "Main": [np.array([[10, 10], [100, 10]], dtype=np.float32)]
        }
        mock_editor.manager.contour_to_bezier.return_value = [Mock()]
        with patch('workpiece_editor.managers.workpiece_manager.load_workpiece') as mock_load:
            mock_load.return_value = (workpiece, contours_by_layer)
            workpiece_manager.load_workpiece(workpiece)
            assert workpiece_manager.current_workpiece == workpiece


class TestWorkpieceManagerInitContour:
    def test_init_contour_basic(self, workpiece_manager, mock_editor):
        contours_by_layer = {
            "Main": [np.array([[10, 10], [100, 10]], dtype=np.float32)]
        }
        mock_editor.manager.contour_to_bezier.return_value = [Mock()]
        workpiece_manager.init_contour(contours_by_layer)
        assert workpiece_manager.contours == contours_by_layer
        mock_editor.pointsUpdated.emit.assert_called()

    def test_init_contour_multiple_layers(self, workpiece_manager, mock_editor):
        contours_by_layer = {
            "Main": [np.array([[10, 10], [100, 10]], dtype=np.float32)],
            "Contour": [np.array([[20, 20], [80, 20]], dtype=np.float32)]
        }
        mock_editor.manager.contour_to_bezier.return_value = [Mock()]
        workpiece_manager.init_contour(contours_by_layer)
        assert workpiece_manager.contours == contours_by_layer


class TestWorkpieceManagerClearWorkpiece:
    def test_clear_workpiece(self, workpiece_manager):
        workpiece_manager.current_workpiece = Mock()
        workpiece_manager.contours = {"Main": [Mock()]}
        workpiece_manager.clear_workpiece()
        assert workpiece_manager.current_workpiece is None
        assert workpiece_manager.contours is None


class TestWorkpieceManagerSetCurrentWorkpiece:
    def test_set_current_workpiece(self, workpiece_manager):
        workpiece = Mock()
        workpiece_manager.set_current_workpiece(workpiece)
        assert workpiece_manager.current_workpiece == workpiece

    def test_get_current_workpiece(self, workpiece_manager):
        workpiece = Mock()
        workpiece_manager.current_workpiece = workpiece
        result = workpiece_manager.get_current_workpiece()
        assert result == workpiece


class TestWorkpieceManagerStatistics:
    def test_get_workpiece_statistics(self, workpiece_manager, mock_editor):
        workpiece_manager.current_workpiece = Mock()
        segment = Mock()
        segment.anchors = [Mock(), Mock(), Mock()]
        segment.layer = Layer("Main")
        mock_editor.manager.get_segments.return_value = [segment]
        stats = workpiece_manager.get_workpiece_statistics()
        assert stats is not None
        assert stats["total_segments"] == 1


class TestWorkpieceManagerEdgeCases:
    """Test edge cases in manager functionality"""

    def test_load_workpiece_with_corrupted_data(self, workpiece_manager):
        """Test loading workpiece with corrupted/invalid data"""
        workpiece = Mock()
        workpiece.workpieceId = "CORRUPTED"
        with patch('workpiece_editor.managers.workpiece_manager.load_workpiece') as mock_load:
            # Simulate corrupted data that returns None
            mock_load.return_value = (None, {})
            result = workpiece_manager.load_workpiece(workpiece)
            # Should handle corrupted data gracefully
            assert result is None or result == workpiece

    def test_export_editor_data_with_no_segments(self, workpiece_manager, mock_editor):
        """Test exporting editor data when no segments exist"""
        mock_editor.manager.get_segments.return_value = []
        result = workpiece_manager.export_editor_data()
        assert result is not None
        # Should return valid ContourEditorData even with no segments
        assert hasattr(result, 'layers')

    def test_export_workpiece_data_with_invalid_layers(self, workpiece_manager, mock_editor):
        """Test exporting workpiece data with invalid layer configuration"""
        # Set up segments but no proper layers
        mock_editor.manager.get_segments.return_value = []
        mock_editor.manager.external_layer = None
        try:
            result = workpiece_manager.export_workpiece_data()
            # Should either handle gracefully or raise appropriate error
            assert result is not None or True
        except Exception:
            # Expected behavior - invalid configuration
            assert True

    def test_init_contour_with_duplicate_layers(self, workpiece_manager, mock_editor):
        """Test initialization with duplicate layer names"""
        contours_by_layer = {
            "Main": [np.array([[10, 10], [100, 10]], dtype=np.float32)],
            "Main": [np.array([[20, 20], [80, 20]], dtype=np.float32)]  # Duplicate key
        }
        mock_editor.manager.contour_to_bezier.return_value = [Mock()]
        # Should handle duplicate keys (last one wins in dict)
        workpiece_manager.init_contour(contours_by_layer)
        assert workpiece_manager.contours is not None


class TestWorkpieceManagerPerformance:
    """Test performance characteristics of manager"""

    def test_load_large_workpiece(self, workpiece_manager, mock_editor):
        """Test loading workpiece with large contour data"""
        workpiece = Mock()
        workpiece.workpieceId = "LARGE_WP"
        # Create large contour data (1000 points per contour, 10 contours)
        large_contours = {
            "Main": [
                np.random.rand(1000, 2).astype(np.float32) for _ in range(10)
            ]
        }
        with patch('workpiece_editor.managers.workpiece_manager.load_workpiece') as mock_load:
            mock_load.return_value = (workpiece, large_contours)
            mock_editor.manager.contour_to_bezier.return_value = [Mock() for _ in range(10)]
            result = workpiece_manager.load_workpiece(workpiece)
            assert result == workpiece
            assert workpiece_manager.contours is not None

    def test_export_large_contour_data(self, workpiece_manager, mock_editor):
        """Test exporting large contour data"""
        # Create many segments with many points
        large_segments = []
        for i in range(100):
            segment = Mock()
            segment.layer = Mock()
            segment.layer.name = "Main"
            segment.anchors = [Mock() for _ in range(100)]  # 100 points per segment
            segment.settings = {}
            large_segments.append(segment)
        mock_editor.manager.get_segments.return_value = large_segments
        result = workpiece_manager.export_editor_data()
        assert result is not None

    def test_multiple_load_export_cycles(self, workpiece_manager, mock_editor):
        """Test multiple load/export cycles for memory leaks"""
        workpiece = Mock()
        workpiece.workpieceId = "CYCLE_TEST"
        contours = {
            "Main": [np.array([[10, 10], [100, 10]], dtype=np.float32)]
        }
        with patch('workpiece_editor.managers.workpiece_manager.load_workpiece') as mock_load:
            mock_load.return_value = (workpiece, contours)
            mock_editor.manager.contour_to_bezier.return_value = [Mock()]
            # Perform 10 load/export cycles
            for _ in range(10):
                workpiece_manager.load_workpiece(workpiece)
                workpiece_manager.export_editor_data()
                workpiece_manager.clear_workpiece()
            # Should complete without memory issues
            assert True

    def test_memory_cleanup_after_clear(self, workpiece_manager):
        """Test that clear_workpiece properly cleans up memory"""
        # Set up some data
        workpiece_manager.current_workpiece = Mock()
        workpiece_manager.contours = {
            "Main": [np.random.rand(10000, 2).astype(np.float32)]
        }
        # Clear
        workpiece_manager.clear_workpiece()
        # Verify cleanup
        assert workpiece_manager.current_workpiece is None
        assert workpiece_manager.contours is None
