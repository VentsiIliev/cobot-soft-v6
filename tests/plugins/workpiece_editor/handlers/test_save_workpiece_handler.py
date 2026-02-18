import pytest
from unittest.mock import Mock, patch
from workpiece_editor.handlers.SaveWorkpieceHandler import SaveWorkpieceHandler


class TestSaveWorkpieceHandlerDataExport:
    """Test data export functionality"""

    def test_export_data_basic(self):
        """Test basic export_data without Field dependency"""
        mock_workpiece_manager = Mock()
        mock_editor_data = Mock()
        mock_workpiece_manager.export_editor_data.return_value = mock_editor_data
        with patch.object(SaveWorkpieceHandler, '_merge_data') as mock_merge:
            with patch('workpiece_editor.handlers.SaveWorkpieceHandler.WorkpieceAdapter') as mock_adapter:
                mock_adapter.to_workpiece_data.return_value = {
                    "main_contour": Mock(),
                    "spray_pattern": {}
                }
                mock_merge.return_value = {"workpieceId": "WP123"}
                form_data = {"workpieceId": "WP123", "name": "Test"}
                result = SaveWorkpieceHandler.export_data(mock_workpiece_manager, form_data)
                assert result is not None
                mock_adapter.to_workpiece_data.assert_called_once()
                mock_merge.assert_called_once()

    def test_export_data_calls_adapter(self):
        """Test that export_data calls WorkpieceAdapter"""
        mock_workpiece_manager = Mock()
        mock_editor_data = Mock()
        mock_workpiece_manager.export_editor_data.return_value = mock_editor_data
        with patch.object(SaveWorkpieceHandler, '_merge_data') as mock_merge:
            with patch('workpiece_editor.handlers.SaveWorkpieceHandler.WorkpieceAdapter') as mock_adapter:
                mock_adapter.to_workpiece_data.return_value = {
                    "main_contour": Mock(),
                    "spray_pattern": {}
                }
                mock_merge.return_value = {}
                SaveWorkpieceHandler.export_data(mock_workpiece_manager, {})
                mock_adapter.to_workpiece_data.assert_called_once_with(mock_editor_data)


class TestSaveWorkpieceHandlerValidation:
    """Test validation functionality with WorkpieceFieldProvider"""

    def test_validate_form_data_valid_data(self):
        """Test validation with valid form data"""
        form_data = {
            "workpieceId": "WP123",
            "height": "50",
            "glueType": "Type A"
        }
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert is_valid == True
        assert len(errors) == 0

    def test_validate_form_data_missing_required_fields(self):
        """Test validation with missing required fields"""
        form_data = {
            "name": "Test"  # Missing workpieceId, height, glueType
        }
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert is_valid == False
        assert len(errors) > 0
        # Should have errors for missing required fields
        assert any("workpiece" in err.lower() for err in errors)

    def test_validate_form_data_invalid_height(self):
        """Test validation with invalid height value"""
        form_data = {
            "workpieceId": "WP123",
            "height": "invalid",  # Invalid numeric value
            "glueType": "Type A"
        }
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert is_valid == False
        assert any("height" in err.lower() for err in errors)

    def test_validate_form_data_negative_height(self):
        """Test validation with negative height"""
        form_data = {
            "workpieceId": "WP123",
            "height": "-10",
            "glueType": "Type A"
        }
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert is_valid == False
        assert any("height" in err.lower() and "positive" in err.lower() for err in errors)

    def test_validate_form_data_returns_error_list(self):
        """Test that validation returns list of errors"""
        form_data = {}  # Missing all required fields
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert isinstance(errors, list)
        assert len(errors) >= 3  # At least 3 required fields


class TestSaveWorkpieceHandlerSaveWorkflow:
    """Test complete save workflow"""

    @patch('workpiece_editor.handlers.SaveWorkpieceHandler.DialogProvider')
    @patch('workpiece_editor.handlers.SaveWorkpieceHandler.WorkpieceAdapter')
    def test_save_workpiece_success(self, mock_adapter, mock_dialog):
        """Test successful save workflow"""
        mock_workpiece_manager = Mock()
        mock_editor_data = Mock()
        mock_editor_data = Mock()

        # Mock get_statistics() to return proper structure
        mock_editor_data.get_statistics.return_value = {
            'total_layers': 3,
            'total_segments': 5,
            'total_points': 100,
            'layers': {
                'Workpiece': {'segments': 1, 'points': 20},
                'Contour': {'segments': 2, 'points': 40},
                'Fill': {'segments': 2, 'points': 40}
            }
        }

        mock_workpiece_manager.export_editor_data.return_value = mock_editor_data
        mock_adapter.to_workpiece_data.return_value = {
            "main_contour": Mock(),
            "spray_pattern": {}
        }
        mock_controller = Mock()
        mock_controller.save_workpiece.return_value = (True, "Success")
        form_data = {
            "workpieceId": "WP123",
            "height": "50",
            "glueType": "Type A"
        }
        success, message = SaveWorkpieceHandler.save_workpiece(
            mock_workpiece_manager,
            form_data,
            mock_editor_data,
            mock_controller
        )
        assert success == True
        assert "Success" in message
        mock_controller.save_workpiece.assert_called_once()

    @patch('workpiece_editor.handlers.SaveWorkpieceHandler.DialogProvider')
    def test_save_workpiece_validation_failure(self, mock_dialog):
        """Test save workflow with validation failure"""
        mock_workpiece_manager = Mock()
        mock_controller = Mock()
        form_data = {}  # Missing required fields
        mock_editor_data = Mock()
        success, message = SaveWorkpieceHandler.save_workpiece(
            mock_workpiece_manager,
            form_data,
            mock_editor_data,
            mock_controller
        )
        assert success == False
        assert "Validation" in message
        # Controller should not be called if validation fails
        mock_controller.save_workpiece.assert_not_called()

    @patch('workpiece_editor.handlers.SaveWorkpieceHandler.DialogProvider')
    @patch('workpiece_editor.handlers.SaveWorkpieceHandler.WorkpieceAdapter')
    def test_save_workpiece_controller_failure(self, mock_adapter, mock_dialog):
        """Test save workflow when controller fails"""
        mock_workpiece_manager = Mock()
        mock_editor_data = Mock()
        mock_workpiece_manager.export_editor_data.return_value = mock_editor_data
        mock_adapter.to_workpiece_data.return_value = {
            "main_contour": Mock(),
            "spray_pattern": {}
        }
        mock_controller = Mock()
        mock_controller.save_workpiece.return_value = (False, "Database error")

        form_data = {
            "workpieceId": "WP123",
            "height": "50",
            "glueType": "Type A"
        }

        success, message = SaveWorkpieceHandler.save_workpiece(
            mock_workpiece_manager,
            form_data,
            mock_editor_data,
            mock_controller
        )

        assert success == False
        assert "error" in message.lower()


class TestSaveWorkpieceHandlerEdgeCases:
    """Test edge cases in save handler"""

    def test_validate_form_data_empty_strings(self):
        """Test validation with empty string values"""
        form_data = {
            "workpieceId": "",
            "height": "",
            "glueType": ""
        }
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert is_valid == False
        assert len(errors) >= 3

    def test_validate_form_data_whitespace_only(self):
        """Test validation with whitespace-only values"""
        form_data = {
            "workpieceId": "   ",
            "height": "50",
            "glueType": "Type A"
        }
        is_valid, errors = SaveWorkpieceHandler.validate_form_data(form_data)
        assert is_valid == False
        assert any("workpiece" in err.lower() for err in errors)

    @patch('workpiece_editor.handlers.SaveWorkpieceHandler.WorkpieceAdapter')
    def test_export_data_with_empty_spray_pattern(self, mock_adapter):
        """Test export with empty spray pattern"""
        mock_workpiece_manager = Mock()
        mock_editor_data = Mock()
        mock_workpiece_manager.export_editor_data.return_value = mock_editor_data
        mock_adapter.to_workpiece_data.return_value = {
            "main_contour": None,
            "spray_pattern": {"Contour": [], "Fill": []}
        }
        form_data = {"workpieceId": "WP123"}
        result = SaveWorkpieceHandler.export_data(mock_workpiece_manager, form_data)
        assert result is not None
        assert "workpieceId" in result
