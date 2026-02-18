import pytest
from workpiece_editor.adapters import WorkpieceAdapter
class TestWorkpieceEditorIntegration:
    """Integration tests for workpiece_editor package"""
    def test_layer_name_compatibility(self):
        """Test that workpiece_editor uses correct layer names"""
        # Workpiece still uses "Workpiece" internally for backward compatibility
        assert WorkpieceAdapter.LAYER_WORKPIECE == "Workpiece"
        assert WorkpieceAdapter.LAYER_CONTOUR == "Contour"
        assert WorkpieceAdapter.LAYER_FILL == "Fill"
