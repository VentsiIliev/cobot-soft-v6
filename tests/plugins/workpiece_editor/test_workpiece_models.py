import pytest
from workpiece_editor.models import BaseWorkpiece, GenericWorkpiece, WorkpieceFactory, WorkpieceField
class TestWorkpieceField:
    def test_workpiece_field_enum(self):
        assert WorkpieceField.NAME.value == "name"
        assert WorkpieceField.WORKPIECE_ID.value == "workpieceId"
        assert WorkpieceField.HEIGHT.value == "height"
    def test_workpiece_field_get_as_label(self):
        label = WorkpieceField.CONTOUR_AREA.getAsLabel()
        assert "Contour" in label
class TestBaseWorkpiece:
    def test_base_workpiece_abstract(self):
        with pytest.raises(TypeError):
            BaseWorkpiece("123", "Test")
class TestGenericWorkpiece:
    def test_generic_workpiece_creation(self):
        wp = GenericWorkpiece("123", "Test WP", extra_field="value")
        assert wp.workpieceId == "123"
        assert wp.name == "Test WP"
        assert wp.extra_field == "value"
    def test_generic_workpiece_to_dict(self):
        wp = GenericWorkpiece("123", "Test", height=10)
        result = wp.to_dict()
        assert result["workpieceId"] == "123"
        assert result["name"] == "Test"
        assert result["height"] == 10
    def test_generic_workpiece_from_dict(self):
        data = {
            "workpieceId": "456",
            "name": "Test WP",
            "height": 20,
            "custom": "value"
        }
        wp = GenericWorkpiece.from_dict(data)
        assert wp.workpieceId == "456"
        assert wp.name == "Test WP"
        assert wp.height == 20
        assert wp.custom == "value"
    def test_generic_workpiece_repr(self):
        wp = GenericWorkpiece("123", "Test")
        result = repr(wp)
        assert "123" in result
        assert "Test" in result
class TestWorkpieceFactory:
    def test_create_workpiece_from_dict(self):
        data = {"workpieceId": "123", "name": "Test"}
        wp = WorkpieceFactory.create_workpiece(data)
        assert isinstance(wp, GenericWorkpiece)
        assert wp.workpieceId == "123"
        assert wp.name == "Test"
    def test_set_workpiece_class(self):
        class CustomWorkpiece(BaseWorkpiece):
            def to_dict(self):
                return {}
            @classmethod
            def from_dict(cls, data):
                return cls("1", "Custom")
        WorkpieceFactory.set_workpiece_class(CustomWorkpiece)
        assert WorkpieceFactory.get_workpiece_class() == CustomWorkpiece
        # Reset to default
        WorkpieceFactory.set_workpiece_class(GenericWorkpiece)
    def test_set_invalid_workpiece_class_raises(self):
        class Invalid:
            pass
        with pytest.raises(ValueError):
            WorkpieceFactory.set_workpiece_class(Invalid)
