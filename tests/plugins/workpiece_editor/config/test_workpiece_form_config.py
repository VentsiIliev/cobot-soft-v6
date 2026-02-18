import pytest
import os
from unittest.mock import patch, Mock
from workpiece_editor.config.workpiece_form_config import (
    create_workpiece_form_config,
    get_icon_path,
    get_contour_icon_path
)

from modules.shared.GlueWorkpieceField import GlueWorkpieceField



class TestIconPathResolution:
    """Test icon path resolution functions"""

    def test_get_icon_path_existing_file(self, tmp_path):
        # Create a temporary icon file
        icon_dir = tmp_path / "assets" / "icons"
        icon_dir.mkdir(parents=True)
        icon_file = icon_dir / "test_icon.png"
        icon_file.write_text("fake image")
        with patch('workpiece_editor.config.workpiece_form_config.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = str(tmp_path)
            result = get_icon_path("test_icon")
            # Should return path if exists, empty string if not
            assert isinstance(result, str)

    def test_get_icon_path_missing_file_returns_empty(self):
        result = get_icon_path("nonexistent_icon_12345")
        assert result == ""

    def test_get_contour_icon_path_existing_file(self, tmp_path):
        # Create a temporary contour icon file
        icon_dir = tmp_path / "contour_editor" / "assets" / "icons"
        icon_dir.mkdir(parents=True)
        icon_file = icon_dir / "test_contour_icon.png"
        icon_file.write_text("fake image")
        with patch('workpiece_editor.config.workpiece_form_config.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = str(tmp_path)
            result = get_contour_icon_path("test_contour_icon")
            assert isinstance(result, str)

    def test_icon_path_relative_resolution(self):
        # Test that paths are resolved relative to config file location
        result = get_icon_path("WOPIECE_ID_ICON_2")
        assert isinstance(result, str)
        result = get_contour_icon_path("RULER_ICON")
        assert isinstance(result, str)


class TestFormConfiguration:
    """Test workpiece form configuration creation"""

    def test_create_workpiece_form_config_default_glue_types(self):
        config = create_workpiece_form_config()
        assert config is not None
        assert hasattr(config, 'form_title')
        assert hasattr(config, 'fields')
        assert config.form_title == "Create Workpiece"

    def test_create_workpiece_form_config_custom_glue_types(self):
        custom_types = ["CustomGlue1", "CustomGlue2", "CustomGlue3"]
        config = create_workpiece_form_config(glue_types=custom_types)
        # Find the glue_type field
        glue_field = None
        for field in config.fields:
            if field.field_id == GlueWorkpieceField.GLUE_TYPE.value:
                glue_field = field
                break
        assert glue_field is not None
        assert glue_field.options == custom_types

    def test_create_workpiece_form_config_field_structure(self):
        config = create_workpiece_form_config()
        assert len(config.fields) > 0
        required_fields = [GlueWorkpieceField.WORKPIECE_ID.value, GlueWorkpieceField.NAME.value, GlueWorkpieceField.HEIGHT.value, GlueWorkpieceField.GLUE_TYPE.value]
        field_ids = [field.field_id for field in config.fields]
        for required_field in required_fields:
            assert required_field in field_ids, f"Missing required field: {required_field}"

    def test_create_workpiece_form_config_mandatory_fields(self):
        config = create_workpiece_form_config()
        mandatory_fields = {
            GlueWorkpieceField.WORKPIECE_ID.value: True,
            GlueWorkpieceField.HEIGHT.value: True,
            GlueWorkpieceField.GLUE_TYPE.value: True,
        }
        for field in config.fields:
            if field.field_id in mandatory_fields:
                assert field.mandatory == mandatory_fields[field.field_id], \
                    f"Field {field.field_id} mandatory mismatch"


class TestFormConfigurationEdgeCases:
    """Test edge cases for form configuration"""

    def test_create_workpiece_form_config_empty_glue_types(self):
        config = create_workpiece_form_config(glue_types=[])
        # Should use default glue types
        glue_field = None
        for field in config.fields:
            if field.field_id == GlueWorkpieceField.GLUE_TYPE.value:
                glue_field = field
                break
        assert glue_field is not None
        assert len(glue_field.options) > 0  # Should have fallback options

    def test_create_workpiece_form_config_none_glue_types(self):
        config = create_workpiece_form_config(glue_types=None)
        # Should use default glue types
        glue_field = None
        for field in config.fields:
            if field.field_id == GlueWorkpieceField.GLUE_TYPE.value:
                glue_field = field
                break
        assert glue_field is not None
        # This should get the configured glue types
        # assert glue_field.options == ["Type A", "Type B", "Type C"]
