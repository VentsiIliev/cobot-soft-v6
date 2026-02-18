import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QPointF
from workpiece_editor.handlers.StartHandler import StartHandler


@pytest.fixture
def mock_editor_frame():
    """Mock MainApplicationFrame with required structure"""
    frame = Mock()
    frame.contourEditor = Mock()
    frame.contourEditor.manager = Mock()
    frame.contourEditor.manager.get_segments = Mock(return_value=[])
    frame.contourEditor.workpiece_manager = Mock()
    frame.contourEditor.pickup_point = None
    frame.contourEditor.editor_with_rulers = Mock()
    frame.contourEditor.editor_with_rulers.editor = Mock()
    frame.contourEditor.editor_with_rulers.editor.fetch_glue_types_requested = Mock()
    frame.contourEditor.editor_with_rulers.editor.fetch_glue_types_requested.emit = Mock()
    frame.contourEditor.editor_with_rulers.editor.glue_type_names = []
    frame.execute_requested = Mock()
    frame.execute_requested.emit = Mock()
    return frame


@pytest.fixture
def start_handler(mock_editor_frame):
    """Create StartHandler instance"""
    return StartHandler(mock_editor_frame)


class TestStartHandlerInitialization:
    """Test StartHandler initialization"""

    def test_start_handler_initialization(self, mock_editor_frame):
        handler = StartHandler(mock_editor_frame)
        assert handler.editor_frame == mock_editor_frame


class TestStartHandlerGlueTypeValidation:
    """Test glue type validation logic"""

    @patch('workpiece_editor.handlers.StartHandler.QMessageBox')
    def test_handle_start_no_glue_types_shows_error(self, mock_msgbox, start_handler, mock_editor_frame):
        mock_editor_frame.contourEditor.editor_with_rulers.editor.glue_type_names = []
        start_handler.handle_start()
        mock_msgbox.critical.assert_called_once()
        args = mock_msgbox.critical.call_args[0]
        assert "No Glue Types Configured" in args[1]

    @patch('workpiece_editor.handlers.StartHandler.QMessageBox')
    @patch('workpiece_editor.models.WorkpieceFactory')
    def test_handle_start_valid_glue_types_proceeds(self, mock_factory, mock_msgbox, start_handler, mock_editor_frame):
        # Setup valid glue types
        mock_editor_frame.contourEditor.editor_with_rulers.editor.glue_type_names = ["Type A", "Type B"]
        # Mock workpiece manager export
        mock_editor_data = Mock()
        mock_editor_frame.contourEditor.workpiece_manager.export_editor_data.return_value = mock_editor_data
        # Mock adapter
        with patch('workpiece_editor.adapters.workpiece_adapter.WorkpieceAdapter') as mock_adapter:
            mock_adapter.to_workpiece_data.return_value = {
                "main_contour": Mock(size=10),
                "spray_pattern": {
                    "Contour": [{"contour": Mock(size=10, __len__=lambda s: 10)}],
                    "Fill": []
                }
            }
            # Mock workpiece creation
            mock_workpiece = Mock()
            mock_factory.create_workpiece.return_value = mock_workpiece
            start_handler.handle_start()
            # Should create workpiece and emit execute signal
            mock_factory.create_workpiece.assert_called_once()
            mock_editor_frame.execute_requested.emit.assert_called_once_with(mock_workpiece)

    def test_fetch_glue_types_empty_list(self, start_handler, mock_editor_frame):
        mock_editor_frame.contourEditor.editor_with_rulers.editor.glue_type_names = []
        result = start_handler._fetch_glue_types()
        assert result == []

    def test_fetch_glue_types_populated_list(self, start_handler, mock_editor_frame):
        mock_editor_frame.contourEditor.editor_with_rulers.editor.glue_type_names = ["GlueA", "GlueB", "GlueC"]
        result = start_handler._fetch_glue_types()
        assert result == ["GlueA", "GlueB", "GlueC"]


class TestStartHandlerSegmentValidation:
    """Test segment validation logic"""

    def test_validate_segment_glue_types_all_valid(self, start_handler, mock_editor_frame):
        # Create mock segments with valid settings
        segment1 = Mock()
        segment1.settings = {"Glue Type": "Type A"}
        segment2 = Mock()
        segment2.settings = {"Glue Type": "Type B"}
        mock_editor_frame.contourEditor.manager.get_segments.return_value = [segment1, segment2]
        registered_types = ["Type A", "Type B", "Type C"]
        result = start_handler._validate_segment_glue_types(registered_types)
        assert result == []

    def test_validate_segment_glue_types_invalid_segments(self, start_handler, mock_editor_frame):
        # Create segments with invalid glue types
        segment1 = Mock()
        segment1.settings = {"Glue Type": "InvalidType"}
        segment2 = Mock()
        segment2.settings = {}
        mock_editor_frame.contourEditor.manager.get_segments.return_value = [segment1, segment2]
        registered_types = ["Type A", "Type B"]
        result = start_handler._validate_segment_glue_types(registered_types)
        assert len(result) == 2
        assert "Invalid glue type 'InvalidType'" in result[0]
        assert "No glue type set" in result[1]

    def test_validate_segment_glue_types_empty_segments(self, start_handler, mock_editor_frame):
        mock_editor_frame.contourEditor.manager.get_segments.return_value = []
        result = start_handler._validate_segment_glue_types(["Type A"])
        assert result == []

    def test_validate_segment_glue_types_missing_settings(self, start_handler, mock_editor_frame):
        # Segment without settings attribute
        segment = Mock(spec=[])
        mock_editor_frame.contourEditor.manager.get_segments.return_value = [segment]
        result = start_handler._validate_segment_glue_types(["Type A"])
        assert len(result) == 1
        assert "No glue type set" in result[0]


class TestStartHandlerExecutionFlow:
    """Test complete execution flow"""

    @patch('workpiece_editor.handlers.StartHandler.QMessageBox')
    @patch('workpiece_editor.models.WorkpieceFactory')
    @patch('workpiece_editor.adapters.workpiece_adapter.WorkpieceAdapter')
    def test_handle_start_success_emits_execute(self, mock_adapter, mock_factory, mock_msgbox,
                                                start_handler, mock_editor_frame):
        # Setup complete success scenario
        mock_editor_frame.contourEditor.editor_with_rulers.editor.glue_type_names = ["Type A"]
        mock_editor_frame.contourEditor.workpiece_manager.export_editor_data.return_value = Mock()
        mock_adapter.to_workpiece_data.return_value = {
            "main_contour": Mock(size=10),
            "spray_pattern": {
                "Contour": [{"contour": Mock(size=5, __len__=lambda s: 5)}],
                "Fill": []
            }
        }
        mock_workpiece = Mock()
        mock_factory.create_workpiece.return_value = mock_workpiece
        start_handler.handle_start()
        mock_editor_frame.execute_requested.emit.assert_called_once_with(mock_workpiece)

    @patch('workpiece_editor.handlers.StartHandler.QMessageBox')
    def test_handle_start_validation_failure_aborts(self, mock_msgbox, start_handler, mock_editor_frame):
        # Setup validation failure
        segment = Mock()
        segment.settings = {"Glue Type": "InvalidType"}
        mock_editor_frame.contourEditor.manager.get_segments.return_value = [segment]
        mock_editor_frame.contourEditor.editor_with_rulers.editor.glue_type_names = ["Type A"]
        start_handler.handle_start()
        # Should show error and not emit execute signal
        mock_msgbox.critical.assert_called_once()
        mock_editor_frame.execute_requested.emit.assert_not_called()
