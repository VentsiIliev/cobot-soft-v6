import pytest
from unittest.mock import Mock, patch
from workpiece_editor.config.segment_settings_provider import SegmentSettingsProvider
from contour_editor import ISettingsProvider

from applications.glue_dispensing_application.settings.enums import GlueSettingKey


class TestSegmentSettingsProviderInterface:
    """Test ISettingsProvider interface implementation"""

    def test_implements_isettings_provider_interface(self):
        provider = SegmentSettingsProvider()
        assert isinstance(provider, ISettingsProvider)

    def test_get_default_values_returns_dict(self):
        provider = SegmentSettingsProvider()
        result = provider.get_default_values()
        assert isinstance(result, dict)

    def test_get_all_setting_keys_returns_list(self):
        provider = SegmentSettingsProvider()
        result = provider.get_all_setting_keys()
        assert isinstance(result, list)


class TestSegmentSettingsProviderSettingsRetrieval:
    """Test settings retrieval functionality"""

    def test_get_default_values_contains_required_keys(self):

        required_keys = [
            key.value
            for key in GlueSettingKey
            if key != GlueSettingKey.SPRAY_ON
        ]

        provider = SegmentSettingsProvider()
        defaults = provider.get_default_values()

        for key in required_keys:
            assert key in defaults, f"Missing required key: {key}"

    def test_get_default_values_correct_types(self):
        provider = SegmentSettingsProvider()
        defaults = provider.get_default_values()
        for key, value in defaults.items():
            assert isinstance(value, str), f"Value for {key} should be string, got {type(value)}"

    def test_get_all_setting_keys_matches_defaults(self):
        provider = SegmentSettingsProvider()
        defaults = provider.get_default_values()
        keys = provider.get_all_setting_keys()
        assert set(keys) == set(defaults.keys())

    def test_get_available_material_types_returns_list(self):
        provider = SegmentSettingsProvider()
        material_types = provider.get_available_material_types()
        assert isinstance(material_types, list)

    def test_get_available_material_types_default_values(self):
        provider = SegmentSettingsProvider()
        material_types = provider.get_available_material_types()
        assert len(material_types) > 0, "Should have at least one material type"
        for material_type in material_types:
            assert isinstance(material_type, str)

    def test_custom_material_types_configuration(self):
        custom_types = ["CustomType1", "CustomType2", "CustomType3"]
        provider = SegmentSettingsProvider(material_types=custom_types)
        result = provider.get_available_material_types()
        assert result == custom_types


class TestSegmentSettingsProviderValidation:
    """Test settings validation"""

    def test_validate_setting_value_valid_cases(self):
        provider = SegmentSettingsProvider()
        assert provider.validate_setting( GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, "1") == True
        assert provider.validate_setting(GlueSettingKey.MOTOR_SPEED.value , "500") == True
        assert provider.validate_setting( GlueSettingKey.TIME_BEFORE_MOTION.value, "0.1",) == True

    def test_validate_setting_value_invalid_cases(self):
        provider = SegmentSettingsProvider()
        assert provider.validate_setting("speed", "") == False
        assert provider.validate_setting("invalid_key", "value") == False

    def test_setting_constraints_enforcement(self):
        provider = SegmentSettingsProvider()
        # Numeric settings should validate numeric strings
        assert provider.validate_setting(GlueSettingKey.GENERATOR_TIMEOUT, "abc") == False
        assert provider.validate_setting(GlueSettingKey.GENERATOR_TIMEOUT, "-5") == False


class TestSegmentSettingsProviderEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_material_types_fallback(self):
        provider = SegmentSettingsProvider(material_types=[])
        material_types = provider.get_available_material_types()
        assert len(material_types) > 0, "Should fallback to default material types"

    def test_none_handling(self):
        provider = SegmentSettingsProvider(material_types=None)
        material_types = provider.get_available_material_types()
        assert isinstance(material_types, list)
        assert len(material_types) > 0

    def test_get_setting_value(self):
        provider = SegmentSettingsProvider()
        # Should return the default value for a known setting
        value = provider.get_setting_value(GlueSettingKey.GENERATOR_TIMEOUT.value)
        assert value is not None
        assert isinstance(value, str)
