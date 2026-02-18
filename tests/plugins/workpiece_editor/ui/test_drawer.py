import pytest
from unittest.mock import Mock, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QPoint
from workpiece_editor.ui.Drawer import Drawer
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
@pytest.fixture
def parent_widget(qapp):
    """Create parent widget for drawer"""
    widget = QWidget()
    widget.setGeometry(0, 0, 800, 600)
    return widget
class TestDrawerInitialization:
    """Test Drawer initialization"""
    def test_drawer_initialization(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        assert drawer is not None
        assert drawer.parent() == parent_widget
    def test_drawer_default_values(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        assert drawer.animation_duration == 300
        assert drawer.side == "right"
        assert drawer.is_open == False
        assert drawer.heightOffset == 0
    def test_drawer_custom_duration(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget, animation_duration=500)
        assert drawer.animation_duration == 500
        assert drawer.animation.duration() == 500
    def test_drawer_left_side(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget, side="left")
        assert drawer.side == "left"
class TestDrawerAnimation:
    """Test Drawer animation functionality"""
    def test_drawer_has_animation(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        assert drawer.animation is not None
        assert drawer.animation.duration() == drawer.animation_duration
    def test_toggle_changes_state(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        drawer.setFixedWidth(200)
        initial_state = drawer.is_open
        drawer.toggle()
        assert drawer.is_open != initial_state
    def test_toggle_twice_returns_to_original(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        drawer.setFixedWidth(200)
        initial_state = drawer.is_open
        drawer.toggle()
        drawer.toggle()
        assert drawer.is_open == initial_state
class TestDrawerPositioning:
    """Test Drawer positioning"""
    def test_resize_to_parent_height(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        drawer.setFixedWidth(200)
        drawer.resize_to_parent_height()
        expected_height = parent_widget.height() - drawer.heightOffset
        assert drawer.height() == expected_height
    def test_position_right_side(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget, side="right")
        drawer.setFixedWidth(200)
        drawer.resize_to_parent_height()
        # When closed, drawer should be off-screen to the right
        assert drawer.x() == parent_widget.width()
    def test_position_left_side(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget, side="left")
        drawer.setFixedWidth(200)
        drawer.resize_to_parent_height()
        # When closed, drawer should be off-screen to the left
        assert drawer.x() == -drawer.width()
class TestDrawerHeightOffset:
    """Test Drawer height offset functionality"""
    def test_height_offset_default(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        assert drawer.heightOffset == 0
    def test_height_offset_affects_height(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        drawer.heightOffset = 50
        drawer.setFixedWidth(200)
        drawer.resize_to_parent_height()
        expected_height = parent_widget.height() - 50
        assert drawer.height() == expected_height
    def test_height_offset_affects_y_position(self, qapp, parent_widget):
        drawer = Drawer(parent=parent_widget)
        drawer.heightOffset = 50
        drawer.setFixedWidth(200)
        drawer.resize_to_parent_height()
        assert drawer.y() == 50
