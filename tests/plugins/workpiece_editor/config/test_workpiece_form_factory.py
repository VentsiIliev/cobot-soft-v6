import pytest
from unittest.mock import Mock, patch
from workpiece_editor.config.workpiece_form_factory import WorkpieceFormFactory
class TestWorkpieceFormFactoryInitialization:
    """Test factory initialization"""
    def test_factory_initialization_default_glue_types(self):
        factory = WorkpieceFormFactory()
        assert factory.glue_types == ["Type A", "Type B", "Type C"]
    def test_factory_initialization_custom_glue_types(self):
        custom_types = ["CustomGlue1", "CustomGlue2"]
        factory = WorkpieceFormFactory(glue_types=custom_types)
        assert factory.glue_types == custom_types
class TestWorkpieceFormFactoryFormCreation:
    """Test form creation"""
    @patch('workpiece_editor.config.workpiece_form_factory.CreateWorkpieceForm')
    @patch('workpiece_editor.config.workpiece_form_factory.create_workpiece_form_config')
    def test_create_form_returns_createworkpieceform(self, mock_config, mock_form):
        factory = WorkpieceFormFactory()
        mock_config.return_value = Mock()
        mock_form.return_value = Mock()
        result = factory.create_form()
        assert mock_config.called
        assert mock_form.called
    @patch('workpiece_editor.config.workpiece_form_factory.CreateWorkpieceForm')
    @patch('workpiece_editor.config.workpiece_form_factory.create_workpiece_form_config')
    def test_create_form_uses_configured_glue_types(self, mock_config, mock_form):
        custom_types = ["GlueA", "GlueB", "GlueC"]
        factory = WorkpieceFormFactory(glue_types=custom_types)
        mock_config.return_value = Mock()
        mock_form.return_value = Mock()
        factory.create_form()
        mock_config.assert_called_once_with(custom_types)
class TestWorkpieceFormFactoryEdgeCases:
    """Test edge cases"""
    @patch('workpiece_editor.config.workpiece_form_factory.CreateWorkpieceForm')
    @patch('workpiece_editor.config.workpiece_form_factory.create_workpiece_form_config')
    def test_create_form_with_parent_widget(self, mock_config, mock_form):
        factory = WorkpieceFormFactory()
        parent_widget = Mock()
        mock_config.return_value = Mock()
        mock_form.return_value = Mock()
        factory.create_form(parent=parent_widget)
        # Verify parent was passed to CreateWorkpieceForm
        call_kwargs = mock_form.call_args[1]
        assert call_kwargs['parent'] == parent_widget
