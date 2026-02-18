from typing import List, Dict, Any
from contour_editor import ISettingsProvider
class GlueSettingsProvider(ISettingsProvider):
    def get_all_setting_keys(self) -> List[str]:
        return [
            "Spray Width", "Spraying Height", "Fan Speed", "Generator-Glue Delay",
            "Pump Speed", "Pump Reverse Time", "Pump Speed Reverse", "RZ Angle",
            "Generator Timeout", "Time Before Motion", "Time Before Stop",
            "Reach Start Threshold", "Reach End Threshold", "Glue Speed Coefficient",
            "Glue Acceleration Coefficient", "Initial Ramp Speed Duration",
            "Initial Ramp Speed", "Reverse Ramp Steps", "Forward Ramp Steps",
            "Adaptive Spacing MM", "Spline Density Multiplier", "Smoothing Lambda",
            "Velocity", "Acceleration",
        ]
    def get_default_values(self) -> Dict[str, Any]:
        return {
            "Spray Width": "10.0", "Spraying Height": "15.0", "Fan Speed": "100.0",
            "Generator-Glue Delay": "1.0", "Pump Speed": "0.0", "Pump Reverse Time": "0.5",
            "Pump Speed Reverse": "3000.0", "RZ Angle": "0.0", "Generator Timeout": "5.0",
            "Time Before Motion": "0.1", "Time Before Stop": "1.0",
            "Reach Start Threshold": "100.0", "Reach End Threshold": "70.0",
            "Glue Speed Coefficient": "5.0", "Glue Acceleration Coefficient": "50.0",
            "Initial Ramp Speed Duration": "1.0", "Initial Ramp Speed": "5000.0",
            "Reverse Ramp Steps": "1.0", "Forward Ramp Steps": "3.0",
            "Adaptive Spacing MM": "10.0", "Spline Density Multiplier": "2.0",
            "Smoothing Lambda": "0.0", "Velocity": "60.0", "Acceleration": "30.0",
            "Glue Type": self.get_default_material_type(),
        }
    def get_material_type_key(self) -> str:
        return "Glue Type"
    def get_available_material_types(self) -> List[str]:
        try:
            from modules.shared.tools.glue_monitor_system.core.cell_manager import GlueCellsManagerSingleton
            manager = GlueCellsManagerSingleton.get_instance()
            glue_types = manager.get_all_glue_type_names()
            return glue_types if glue_types else ["TEST TYPE"]
        except:
            return ["TEST TYPE"]
    def get_default_material_type(self) -> str:
        types = self.get_available_material_types()
        return types[0] if types else "TEST TYPE"
    def get_setting_label(self, key: str) -> str:
        return f"{key}:"
    def get_settings_tabs_config(self) -> List[tuple[str, List[str]]]:
        return [
            ("General", ["Spray Width", "Spraying Height", "Glue Type"]),
            ("Pump", ["Pump Speed", "Forward Ramp Steps", "Initial Ramp Speed",
                     "Initial Ramp Speed Duration", "Pump Reverse Time", "Pump Speed Reverse",
                     "Reverse Ramp Steps", "Glue Speed Coefficient", "Glue Acceleration Coefficient"]),
            ("Robot", ["Velocity", "Acceleration", "RZ Angle", "Adaptive Spacing MM",
                      "Spline Density Multiplier", "Smoothing Lambda"]),
            ("Advanced", ["Generator-Glue Delay", "Generator Timeout", "Reach Start Threshold",
                         "Reach End Threshold", "Time Before Motion", "Time Before Stop"]),
        ]
