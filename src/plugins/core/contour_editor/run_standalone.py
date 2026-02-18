#!/usr/bin/env python3
"""
Standalone runner for Contour Editor Plugin

Run the contour editor plugin in isolation for development and testing.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


class MockControllerService:
    """Mock controller service for standalone testing"""

    class Result:
        """Mock result object"""
        def __init__(self, success=True, data=None, message=""):
            self.success = success
            self.data = data
            self.message = message

    class MockController:
        """Mock controller"""

        def __init__(self):
            self.robot_service = self.MockRobotService()
            self.vision_service = self.MockVisionService()

        def handle(self, endpoint, data=None):
            """
            Mock handle method that mimics the real controller's endpoint handling.

            Args:
                endpoint: The API endpoint being called
                data: Optional data payload

            Returns:
                Appropriate mock response based on endpoint
            """
            import numpy as np

            # Import endpoints to check against
            try:
                from communication_layer.api.v1.endpoints import (
                    camera_endpoints, operations_endpoints, workpiece_endpoints
                )
            except ImportError:
                # If endpoints can't be imported, use string matching
                camera_endpoints = None
                operations_endpoints = None
                workpiece_endpoints = None

            # Convert endpoint to string for comparison
            endpoint_str = str(endpoint)

            # Camera feed update
            if camera_endpoints and endpoint == camera_endpoints.UPDATE_CAMERA_FEED:
                print("[Mock Controller] UPDATE_CAMERA_FEED requested")
                # Return a blank test image
                return np.zeros((720, 1280, 3), dtype=np.uint8)

            # Camera feed (alternative endpoint)
            elif "camera" in endpoint_str.lower() and "feed" in endpoint_str.lower():
                print(f"[Mock Controller] Camera feed requested: {endpoint_str}")
                return np.zeros((720, 1280, 3), dtype=np.uint8)

            # Create workpiece operation
            elif operations_endpoints and endpoint == operations_endpoints.CREATE_WORKPIECE:
                print("[Mock Controller] CREATE_WORKPIECE requested")
                # Return mock workpiece creation response
                mock_contour = np.array([
                    [[100, 100]], [[200, 100]], [[200, 200]], [[100, 200]], [[100, 100]]
                ], dtype=np.int32)

                return (
                    True,  # success
                    "Workpiece created successfully",  # message
                    {
                        'workpiece_contour': mock_contour,
                        'image': np.zeros((480, 640, 3), dtype=np.uint8),
                        'contourArea': 10000,
                        'estimatedHeight': 50,
                        'scaleFactor': 1,
                        'originalContours': [mock_contour]
                    }
                )

            # Workpiece operations
            elif "workpiece" in endpoint_str.lower():
                print(f"[Mock Controller] Workpiece operation: {endpoint_str}")
                return (True, "Operation successful", {})

            # Robot operations
            elif "robot" in endpoint_str.lower():
                print(f"[Mock Controller] Robot operation: {endpoint_str}")
                return {"status": "success", "message": "Robot operation completed"}

            # Settings operations
            elif "settings" in endpoint_str.lower():
                print(f"[Mock Controller] Settings operation: {endpoint_str}")
                return {"status": "success", "data": []}

            # Default response
            else:
                print(f"[Mock Controller] Unknown endpoint: {endpoint_str}")
                return None

        def save_workpiece(self, workpiece_data):
            """
            Mock save_workpiece method that mimics controller's workpiece save.

            Args:
                workpiece_data: Dictionary containing workpiece information

            Returns:
                Tuple of (success: bool, message: str)
            """
            workpiece_name = workpiece_data.get('name', 'Unknown')
            workpiece_id = workpiece_data.get('workpieceId', 'N/A')

            print(f"[Mock Controller] save_workpiece called")
            print(f"   - Name: {workpiece_name}")
            print(f"   - ID: {workpiece_id}")
            print(f"   - Keys: {list(workpiece_data.keys())}")

            # Simulate successful save
            return True, f"Workpiece '{workpiece_name}' saved successfully (mock)"

        def handleExecuteFromGallery(self, workpiece):
            """
            Mock handleExecuteFromGallery method for workpiece execution.

            Args:
                workpiece: Workpiece object to execute

            Returns:
                None (prints execution status)
            """
            print(f"[Mock Controller] handleExecuteFromGallery called")
            print(f"   - Workpiece: {workpiece}")
            print(f"   - Type: {type(workpiece)}")

            # Try to extract workpiece details
            if hasattr(workpiece, 'name'):
                print(f"   - Name: {workpiece.name}")
            if hasattr(workpiece, 'workpieceId'):
                print(f"   - ID: {workpiece.workpieceId}")

            print("   ✅ Mock execution complete (no actual robot movement)")

        class MockRobotService:
            """Mock robot service"""
            def move_to_calibration(self):
                print("[Mock Robot] Moving to calibration position")
                return 0

            def get_position(self):
                print("[Mock Robot] Getting position")
                return [0, 0, 300, 180, 0, 0]

        class MockVisionService:
            """Mock vision service"""
            def capture_image(self):
                print("[Mock Vision] Capturing image")
                import numpy as np
                # Return a blank test image
                return np.zeros((480, 640, 3), dtype=np.uint8)

    class MockSettingsService:
        """Mock settings service"""

        def get_glue_types(self):
            """Return mock glue types"""
            return MockControllerService.Result(
                success=True,
                data=[
                    {"name": "TEST TYPE"},
                    {"name": "TEST TYPE 2"},
                    {"name": "Type A"},
                    {"name": "Type B"}
                ]
            )

        def save_settings(self, settings):
            """Mock save settings"""
            print(f"[Mock Settings] Saving settings: {len(settings)} items")
            return MockControllerService.Result(success=True, message="Settings saved")

    class MockOperationsService:
        """Mock operations service"""

        def capture_workpiece(self):
            """Mock capture workpiece"""
            print("[Mock Operations] Capturing workpiece")
            import numpy as np

            # Return mock capture data
            mock_contour = np.array([
                [[100, 100]], [[200, 100]], [[200, 200]], [[100, 200]], [[100, 100]]
            ], dtype=np.int32)

            return MockControllerService.Result(
                success=True,
                data={
                    'workpiece_contour': mock_contour,
                    'image': np.zeros((480, 640, 3), dtype=np.uint8),
                    'contourArea': 10000,
                    'estimatedHeight': 50
                }
            )

        def save_workpiece(self, workpiece_data):
            """Mock save workpiece"""
            print(f"[Mock Operations] Saving workpiece: {workpiece_data.get('name', 'Unknown')}")
            return MockControllerService.Result(success=True, message="Workpiece saved")

        def execute_workpiece(self, workpiece):
            """Mock execute workpiece"""
            print(f"[Mock Operations] Executing workpiece: {workpiece}")
            return MockControllerService.Result(success=True, message="Execution started")

    def __init__(self):
        self.controller = self.MockController()
        self.settings = self.MockSettingsService()
        self.operations = self.MockOperationsService()


class StandaloneWindow(QMainWindow):
    """Main window for standalone plugin testing"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contour Editor Plugin - Standalone Mode")
        self.resize(1400, 900)

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Import and initialize the plugin
        try:
            from plugins.core.contour_editor.plugin import ContourEditorPlugin

            # Create mock controller service
            controller_service = MockControllerService()

            # Initialize plugin
            self.plugin = ContourEditorPlugin()
            if not self.plugin.initialize(controller_service):
                raise RuntimeError("Plugin initialization failed")

            # Create plugin widget
            self.plugin_widget = self.plugin.create_widget(parent=central_widget)
            layout.addWidget(self.plugin_widget)

            print("✅ Contour Editor Plugin loaded successfully in standalone mode")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Failed to load plugin: {e}")

            from PyQt6.QtWidgets import QLabel
            error_label = QLabel(f"Failed to load plugin:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(error_label)


def main():
    """Main entry point"""
    print("=" * 60)
    print("Contour Editor Plugin - Standalone Runner")
    print("=" * 60)

    app = QApplication(sys.argv)

    window = StandaloneWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

