import pytest
from PyQt6.QtWidgets import QApplication
import sys
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
@pytest.fixture(scope="module", autouse=True)
def register_segment_manager():
    """Register default segment manager for workpiece_editor tests"""
    from contour_editor.persistence.data.segment_provider import SegmentManagerProvider
    from contour_editor.models.bezier_segment_manager import BezierSegmentManager
    SegmentManagerProvider.get_instance().set_manager_class(BezierSegmentManager)
    yield
    SegmentManagerProvider._instance = None
