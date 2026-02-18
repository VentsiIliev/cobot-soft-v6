import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from workpiece_editor.ui.CreateWorkpieceForm import (
    CreateWorkpieceForm,
    FormFieldConfig,
    GenericFormConfig,
    FormConfigManager
)
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
@pytest.fixture
def sample_fields():
    """Create sample field configurations"""
    return [
        FormFieldConfig(
            field_id="name",
            field_type="text",
            label="Name",
            icon_path="",
            mandatory=True,
            placeholder="Enter name"
        ),
        FormFieldConfig(
            field_id="description",
            field_type="text",
            label="Description",
            icon_path="",
            mandatory=False
        ),
        FormFieldConfig(
            field_id="type",
            field_type="dropdown",
            label="Type",
            icon_path="",
            options=["Type A", "Type B", "Type C"],
            mandatory=True
        )
    ]
@pytest.fixture
def form_config(sample_fields):
    """Create form configuration"""
    return GenericFormConfig(
        form_title="Test Form",
        fields=sample_fields,
        accept_button_icon="",
        cancel_button_icon=""
    )
class TestFormFieldConfig:
    """Test FormFieldConfig data class"""
    def test_field_config_creation(self):
        field = FormFieldConfig(
            field_id="test_field",
            field_type="text",
            label="Test Field",
            icon_path="/path/icon.png"
        )
        assert field.field_id == "test_field"
        assert field.field_type == "text"
        assert field.label == "Test Field"
        assert field.visible == True
        assert field.mandatory == False
    def test_field_config_to_dict(self):
        field = FormFieldConfig(
            field_id="test",
            field_type="text",
            label="Test",
            icon_path=""
        )
        result = field.to_dict()
        assert isinstance(result, dict)
        assert result["field_id"] == "test"
        assert result["field_type"] == "text"
    def test_field_config_from_dict(self):
        data = {
            "field_id": "test",
            "field_type": "dropdown",
            "label": "Test Label",
            "icon_path": "/path",
            "visible": False,
            "mandatory": True,
            "placeholder": "Enter...",
            "options": ["A", "B"],
            "default_value": "A"
        }
        field = FormFieldConfig.from_dict(data)
        assert field.field_id == "test"
        assert field.visible == False
        assert field.mandatory == True
        assert field.options == ["A", "B"]
class TestGenericFormConfig:
    """Test GenericFormConfig functionality"""
    def test_form_config_creation(self, sample_fields):
        config = GenericFormConfig(
            form_title="My Form",
            fields=sample_fields
        )
        assert config.form_title == "My Form"
        assert len(config.fields) == 3
    def test_get_field(self, form_config):
        field = form_config.get_field("name")
        assert field is not None
        assert field.field_id == "name"
    def test_get_field_not_found(self, form_config):
        field = form_config.get_field("nonexistent")
        assert field is None
    def test_get_visible_fields(self, sample_fields):
        sample_fields[1].visible = False
        config = GenericFormConfig(
            form_title="Test",
            fields=sample_fields
        )
        visible = config.get_visible_fields()
        assert len(visible) == 2
        assert all(f.visible for f in visible)
class TestFormConfigManager:
    """Test FormConfigManager functionality"""
    def test_config_manager_initialization(self, form_config):
        manager = FormConfigManager(form_config)
        assert manager.form_config == form_config
        assert manager.runtime_config is not None
    def test_load_config_creates_default(self, form_config):
        manager = FormConfigManager(form_config)
        config = manager.get_config()
        assert "name" in config
        assert "description" in config
        assert config["name"]["visible"] == True
    def test_is_field_visible(self, form_config):
        manager = FormConfigManager(form_config)
        assert manager.is_field_visible("name") == True
    def test_is_field_mandatory(self, form_config):
        manager = FormConfigManager(form_config)
        assert manager.is_field_mandatory("name") == True
        assert manager.is_field_mandatory("description") == False
class TestCreateWorkpieceForm:
    """Test CreateWorkpieceForm widget"""
    def test_form_widget_creation(self, qapp, form_config):
        form = CreateWorkpieceForm(
            parent=None,
            form_config=form_config,
            showButtons=False
        )
        assert form is not None
        assert form.form_config == form_config
    def test_form_has_interface_methods(self, qapp, form_config):
        form = CreateWorkpieceForm(
            parent=None,
            form_config=form_config,
            showButtons=False
        )
        assert hasattr(form, 'get_data')
        assert hasattr(form, 'clear')

    def test_get_data(self, qapp, form_config):
        form = CreateWorkpieceForm(
            parent=None,
            form_config=form_config,
            showButtons=False
        )
        data = form.get_data()
        assert isinstance(data, dict)

    def test_clear_form(self, qapp, form_config):
        form = CreateWorkpieceForm(
            parent=None,
            form_config=form_config,
            showButtons=False
        )
        # Should not raise exception
        form.clear()
        form.clear_form()
        data = form.get_data()
        assert isinstance(data, dict)
