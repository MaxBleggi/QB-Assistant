"""
Unit tests for SampleParamsForm integration.

Tests form creation, save/load integration with ConfigManager (mocked),
and error handling.
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch

from src.gui.forms.sample_params_form import SampleParamsForm
from src.models.parameters import ParameterModel


@pytest.fixture
def tk_root():
    """Create Tk root for GUI tests."""
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def mock_parent(tk_root):
    """Create mock parent with get_config_manager method."""
    parent = tk_root
    parent.get_config_manager = Mock()
    return parent


@pytest.fixture
def sample_form(mock_parent):
    """Create SampleParamsForm instance with mocked parent."""
    return SampleParamsForm(mock_parent)


class TestSampleParamsForm:
    """Test suite for SampleParamsForm class."""

    def test_form_creates_with_fields(self, sample_form):
        """
        Given: Mock parent
        When: SampleParamsForm instantiated
        Then: Form contains revenue growth and expense adjustment fields
        """
        assert sample_form.revenue_growth_field is not None
        assert sample_form.expense_adjustment_field is not None

    def test_form_has_save_and_load_buttons(self, sample_form):
        """
        Given: SampleParamsForm instance
        When: form initialized
        Then: Save and Load buttons exist (verified by method existence)
        """
        # Verify methods exist (buttons call these methods)
        assert hasattr(sample_form, 'on_save_clicked')
        assert hasattr(sample_form, 'on_load_clicked')

    def test_save_button_calls_config_manager(self, sample_form, mock_parent):
        """
        Given: SampleParamsForm with valid field values
        When: on_save_clicked called
        Then: ConfigManager.save_config called with correct parameters
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set field values
        sample_form.revenue_growth_field.set_value("0.05")
        sample_form.expense_adjustment_field.set_value("1.1")

        # Mock messagebox to avoid GUI popup
        with patch('src.gui.forms.sample_params_form.messagebox'):
            sample_form.on_save_clicked()

        # Verify save_config was called
        mock_config_mgr.save_config.assert_called_once()

        # Verify model passed to save_config has correct parameters
        call_args = mock_config_mgr.save_config.call_args
        saved_model = call_args[0][0]
        assert isinstance(saved_model, ParameterModel)
        assert saved_model.get_parameter('revenue_growth_rate') == 0.05
        assert saved_model.get_parameter('expense_adjustment_factor') == 1.1

    def test_load_button_calls_config_manager(self, sample_form, mock_parent):
        """
        Given: SampleParamsForm instance
        When: on_load_clicked called
        Then: ConfigManager.load_config called and fields populated
        """
        # Setup mock config manager with test data
        mock_config_mgr = Mock()
        test_model = ParameterModel(parameters={
            'revenue_growth_rate': 0.08,
            'expense_adjustment_factor': 1.2
        })
        mock_config_mgr.load_config.return_value = test_model
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to avoid GUI popup
        with patch('src.gui.forms.sample_params_form.messagebox'):
            sample_form.on_load_clicked()

        # Verify load_config was called
        mock_config_mgr.load_config.assert_called_once()

        # Verify fields populated with loaded values
        assert sample_form.revenue_growth_field.get_value() == 0.08
        assert sample_form.expense_adjustment_field.get_value() == 1.2

    def test_save_handles_validation_error(self, sample_form, mock_parent):
        """
        Given: SampleParamsForm with invalid field value
        When: on_save_clicked called
        Then: Error message displayed, save not attempted
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set invalid value in field
        sample_form.revenue_growth_field.set_value("invalid_number")

        # Mock messagebox to capture error call
        with patch('src.gui.forms.sample_params_form.messagebox') as mock_msgbox:
            sample_form.on_save_clicked()

            # Verify error displayed
            mock_msgbox.showerror.assert_called_once()

        # Verify save_config was NOT called (error caught before save)
        mock_config_mgr.save_config.assert_not_called()

    def test_save_handles_file_io_error(self, sample_form, mock_parent):
        """
        Given: SampleParamsForm with valid values but ConfigManager raises error
        When: on_save_clicked called
        Then: Error message displayed to user
        """
        # Setup mock config manager that raises exception
        mock_config_mgr = Mock()
        mock_config_mgr.save_config.side_effect = IOError("Disk full")
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set valid values
        sample_form.revenue_growth_field.set_value("0.05")
        sample_form.expense_adjustment_field.set_value("1.0")

        # Mock messagebox to capture error call
        with patch('src.gui.forms.sample_params_form.messagebox') as mock_msgbox:
            sample_form.on_save_clicked()

            # Verify error displayed
            mock_msgbox.showerror.assert_called_once()
            error_call = mock_msgbox.showerror.call_args[0]
            assert 'Error' in error_call or 'error' in str(error_call).lower()

    def test_load_handles_file_error(self, sample_form, mock_parent):
        """
        Given: ConfigManager.load_config raises exception
        When: on_load_clicked called
        Then: Error message displayed to user
        """
        # Setup mock config manager that raises exception
        mock_config_mgr = Mock()
        mock_config_mgr.load_config.side_effect = Exception("File not found")
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to capture error call
        with patch('src.gui.forms.sample_params_form.messagebox') as mock_msgbox:
            sample_form.on_load_clicked()

            # Verify error displayed
            mock_msgbox.showerror.assert_called_once()

    def test_save_displays_success_message(self, sample_form, mock_parent):
        """
        Given: SampleParamsForm with valid values
        When: on_save_clicked succeeds
        Then: Success message displayed to user
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set valid values
        sample_form.revenue_growth_field.set_value("0.05")
        sample_form.expense_adjustment_field.set_value("1.0")

        # Mock messagebox to capture success call
        with patch('src.gui.forms.sample_params_form.messagebox') as mock_msgbox:
            sample_form.on_save_clicked()

            # Verify success message displayed
            mock_msgbox.showinfo.assert_called_once()
            success_call = mock_msgbox.showinfo.call_args[0]
            assert 'Success' in str(success_call) or 'success' in str(success_call).lower()

    def test_load_displays_success_message(self, sample_form, mock_parent):
        """
        Given: ConfigManager.load_config succeeds
        When: on_load_clicked called
        Then: Success message displayed to user
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        test_model = ParameterModel(parameters={
            'revenue_growth_rate': 0.05,
            'expense_adjustment_factor': 1.0
        })
        mock_config_mgr.load_config.return_value = test_model
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to capture success call
        with patch('src.gui.forms.sample_params_form.messagebox') as mock_msgbox:
            sample_form.on_load_clicked()

            # Verify success message displayed
            mock_msgbox.showinfo.assert_called_once()

    def test_load_populates_only_existing_parameters(self, sample_form, mock_parent):
        """
        Given: Loaded model has only one of two parameters
        When: on_load_clicked called
        Then: Only available parameter field is updated
        """
        # Setup mock config manager with partial data
        mock_config_mgr = Mock()
        test_model = ParameterModel(parameters={
            'revenue_growth_rate': 0.12
            # Missing 'expense_adjustment_factor'
        })
        mock_config_mgr.load_config.return_value = test_model
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set initial values
        sample_form.revenue_growth_field.set_value("0.05")
        sample_form.expense_adjustment_field.set_value("1.0")

        # Mock messagebox
        with patch('src.gui.forms.sample_params_form.messagebox'):
            sample_form.on_load_clicked()

        # Verify revenue field updated, expense field unchanged
        assert sample_form.revenue_growth_field.get_value() == 0.12
        assert sample_form.expense_adjustment_field.get_value() == 1.0

    def test_form_uses_correct_config_filepath(self, sample_form, mock_parent):
        """
        Given: SampleParamsForm instance
        When: save or load called
        Then: Uses 'config/default_parameters.json' filepath
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set valid values and save
        sample_form.revenue_growth_field.set_value("0.05")
        sample_form.expense_adjustment_field.set_value("1.0")

        with patch('src.gui.forms.sample_params_form.messagebox'):
            sample_form.on_save_clicked()

        # Verify filepath argument
        call_args = mock_config_mgr.save_config.call_args
        filepath = call_args[0][1]
        assert 'default_parameters.json' in filepath
        assert 'config' in filepath
