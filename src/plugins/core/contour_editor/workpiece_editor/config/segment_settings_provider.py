from contour_editor import ISettingsProvider

from applications.glue_dispensing_application.settings.enums import GlueSettingKey
from core.model.settings.RobotConfigKey import RobotSettingKey


def _get_default_glue_type() -> str:
    try:
        from modules.shared.tools.glue_monitor_system.core.cell_manager import GlueCellsManagerSingleton
        cells_manager = GlueCellsManagerSingleton.get_instance()
        if cells_manager.cells and len(cells_manager.cells) > 0:
            first_cell = cells_manager.cells[0]
            default_type = first_cell.glueType
            print(f"Using default glue type: '{default_type}'")
            return default_type
        else:
            print("WARNING: No cells found in configuration")
            return ""
    except Exception as e:
        print(f"WARNING: Could not get default glue type: {e}")
        return ""


class SegmentSettingsProvider(ISettingsProvider):
    """Settings provider for workpiece editing"""

    def __init__(self, material_types=None):
        self._default_settings = {
            GlueSettingKey.SPRAY_WIDTH.value: "10",
            GlueSettingKey.SPRAYING_HEIGHT.value: "0",
            GlueSettingKey.FAN_SPEED.value: "100",
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: "1",
            GlueSettingKey.MOTOR_SPEED.value: "500",
            GlueSettingKey.REVERSE_DURATION.value: "0.5",
            GlueSettingKey.SPEED_REVERSE.value: "3000",
            GlueSettingKey.RZ_ANGLE.value: "0",
            GlueSettingKey.GLUE_TYPE.value: _get_default_glue_type(),
            GlueSettingKey.GENERATOR_TIMEOUT.value: "5",
            GlueSettingKey.TIME_BEFORE_MOTION.value: "0.1",
            GlueSettingKey.TIME_BEFORE_STOP.value: "1.0",
            GlueSettingKey.REACH_START_THRESHOLD.value: "1.0",
            GlueSettingKey.REACH_END_THRESHOLD.value: "30.0",
            GlueSettingKey.GLUE_SPEED_COEFFICIENT.value: "5",
            GlueSettingKey.GLUE_ACCELERATION_COEFFICIENT.value: "0",
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: "1.0",
            GlueSettingKey.INITIAL_RAMP_SPEED.value: "5000",
            GlueSettingKey.REVERSE_RAMP_STEPS.value: "1",
            GlueSettingKey.FORWARD_RAMP_STEPS.value: "3",
            GlueSettingKey.ADAPTIVE_SPACING_MM.value: "10",
            GlueSettingKey.SPLINE_DENSITY_MULTIPLIER.value: "2.0",
            GlueSettingKey.SMOOTHING_LAMBDA.value: "0.0",
            RobotSettingKey.VELOCITY.value: "60",
            RobotSettingKey.ACCELERATION.value: "30",
        }
        self._material_types = material_types if material_types else ["Type A", "Type B", "Type C"]

    def get_all_setting_keys(self):
        return list(self._default_settings.keys())

    def get_default_values(self):
        return self._default_settings.copy()

    def get_material_type_key(self):
        return GlueSettingKey.GLUE_TYPE.value

    def get_available_material_types(self):
        return self._material_types

    def get_default_material_type(self):
        return self._material_types[0] if self._material_types else "Type A"

    def get_setting_label(self, key: str):
        return key.replace('_', ' ').title()

    def get_setting_value(self, key: str):
        """Get default value for a setting"""
        return self._default_settings.get(key)

    def validate_setting(self, key: str, value: str) -> bool:
        """Validate a setting value"""
        if key not in self._default_settings:
            return False
        if not value or value.strip() == "":
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return key == GlueSettingKey.GLUE_TYPE.value

    def validate_setting_value(self, key: str, value: str) -> bool:
        """Alias for validate_setting for backward compatibility"""
        return self.validate_setting(key, value)

    def get_settings_tabs_config(self):
        return [("Settings", list(self._default_settings.keys()))]
