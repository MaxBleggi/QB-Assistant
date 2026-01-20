"""
Unit tests for BudgetParamsForm integration.

Tests form creation, save/load integration with ConfigManager (mocked),
hierarchical field collection, defaults service integration, and error handling.
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, patch

from src.gui.forms.budget_params_form import BudgetParamsForm
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
def budget_form(mock_parent):
    """Create BudgetParamsForm instance with mocked parent and defaults service."""
    # Patch BudgetDefaultsService to avoid dependency on historical data
    with patch('src.gui.forms.budget_params_form.BudgetDefaultsService') as mock_service:
        mock_service.calculate_defaults.return_value = {
            'revenue_growth_rate': 0.05,
            'expense_adjustment': 1.0,
            'budget_methodology': 'Growth from Prior Year',
            'category_growth_rates': {}
        }
        form = BudgetParamsForm(mock_parent)
    return form


class TestBudgetParamsForm:
    """Test suite for BudgetParamsForm class."""

    def test_form_creates_with_fields(self, budget_form):
        """
        Given: Mock parent
        When: BudgetParamsForm instantiated
        Then: Form contains revenue, expense, and methodology fields
        """
        assert budget_form.revenue_growth_field is not None
        assert budget_form.expense_adjustment_field is not None
        assert budget_form.methodology_field is not None

    def test_form_has_save_and_load_buttons(self, budget_form):
        """
        Given: BudgetParamsForm instance
        When: Form initialized
        Then: Save and Load button methods exist
        """
        assert hasattr(budget_form, 'on_save_clicked')
        assert hasattr(budget_form, 'on_load_clicked')

    def test_save_creates_config_file(self, budget_form, mock_parent):
        """
        Given: BudgetParamsForm with valid field values
        When: on_save_clicked called
        Then: ConfigManager.save_config called with ParameterModel containing all field values
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set field values
        budget_form.revenue_growth_field.set_value("0.08")
        budget_form.methodology_field.set_value("Historical Average")
        budget_form.expense_adjustment_field.set_value("1.1")

        # Mock messagebox to avoid GUI popup
        with patch('src.gui.forms.budget_params_form.messagebox'):
            budget_form.on_save_clicked()

        # Verify save_config was called
        mock_config_mgr.save_config.assert_called_once()

        # Verify model passed to save_config has correct parameters
        call_args = mock_config_mgr.save_config.call_args
        saved_model = call_args[0][0]
        assert isinstance(saved_model, ParameterModel)
        assert saved_model.get_parameter('revenue_growth_rate') == 0.08
        assert saved_model.get_parameter('budget_methodology') == 'Historical Average'
        assert saved_model.get_parameter('expense_adjustment_factor') == 1.1

    def test_load_populates_fields(self, budget_form, mock_parent):
        """
        Given: config/budget_parameters.json exists with saved values
        When: Load button clicked
        Then: All fields populated with saved values via set_value()
        """
        # Setup mock config manager with test data
        mock_config_mgr = Mock()
        test_model = ParameterModel(parameters={
            'revenue_growth_rate': 0.12,
            'budget_methodology': 'Zero-Based',
            'category_growth_rates': {},
            'expense_adjustment_factor': 0.95
        })
        mock_config_mgr.load_config.return_value = test_model
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to avoid GUI popup
        with patch('src.gui.forms.budget_params_form.messagebox'):
            budget_form.on_load_clicked()

        # Verify load_config was called
        mock_config_mgr.load_config.assert_called_once()

        # Verify fields populated with loaded values
        assert budget_form.revenue_growth_field.get_value() == 0.12
        assert budget_form.methodology_field.get_value() == 'Zero-Based'
        assert budget_form.expense_adjustment_field.get_value() == 0.95

    def test_save_error_shows_message(self, budget_form, mock_parent):
        """
        Given: ConfigManager.save_config raises exception
        When: on_save_clicked called
        Then: messagebox.showerror called with error message
        """
        # Setup mock config manager that raises exception
        mock_config_mgr = Mock()
        mock_config_mgr.save_config.side_effect = IOError("Disk full")
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set valid values
        budget_form.revenue_growth_field.set_value("0.05")
        budget_form.expense_adjustment_field.set_value("1.0")

        # Mock messagebox to capture error call
        with patch('src.gui.forms.budget_params_form.messagebox') as mock_msgbox:
            budget_form.on_save_clicked()

            # Verify error displayed
            mock_msgbox.showerror.assert_called_once()
            error_call = mock_msgbox.showerror.call_args[0]
            assert 'Error' in str(error_call) or 'error' in str(error_call).lower()

    def test_defaults_service_integration(self, mock_parent):
        """
        Given: BudgetDefaultsService.calculate_defaults mocked to return specific defaults
        When: BudgetParamsForm.__init__ executes
        Then: Revenue growth rate field initialized with default_value from service
        """
        # Patch BudgetDefaultsService to return specific defaults
        with patch('src.gui.forms.budget_params_form.BudgetDefaultsService') as mock_service:
            mock_service.calculate_defaults.return_value = {
                'revenue_growth_rate': 0.08,
                'expense_adjustment': 1.2,
                'budget_methodology': 'Historical Average',
                'category_growth_rates': {}
            }

            form = BudgetParamsForm(mock_parent)

            # Verify fields initialized with defaults from service
            assert form.revenue_growth_field.get_value() == 0.08
            assert form.expense_adjustment_field.get_value() == 1.2
            assert form.methodology_field.get_value() == 'Historical Average'

    def test_hierarchical_field_collection(self, budget_form, mock_parent):
        """
        Given: BudgetParamsForm with values in all three sections
        When: on_save_clicked called
        Then: ConfigManager.save_config called with parameters from all sections (revenue, expense, overrides)
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set values in different sections
        budget_form.revenue_growth_field.set_value("0.06")  # Revenue section
        budget_form.methodology_field.set_value("Growth from Prior Year")  # Revenue section
        budget_form.expense_adjustment_field.set_value("1.05")  # Expense section

        # Mock messagebox
        with patch('src.gui.forms.budget_params_form.messagebox'):
            budget_form.on_save_clicked()

        # Verify all section values collected
        call_args = mock_config_mgr.save_config.call_args
        saved_model = call_args[0][0]

        # Revenue section parameters
        assert saved_model.get_parameter('revenue_growth_rate') == 0.06
        assert saved_model.get_parameter('budget_methodology') == 'Growth from Prior Year'

        # Expense section parameters
        assert saved_model.get_parameter('expense_adjustment_factor') == 1.05

        # Category rates (even if empty, should be present)
        assert 'category_growth_rates' in saved_model.parameters

    def test_form_graceful_degradation(self, mock_parent):
        """
        Given: BudgetDefaultsService raises exception during __init__
        When: BudgetParamsForm created
        Then: Form still renders with fallback defaults, no crash
        """
        # Patch BudgetDefaultsService to raise exception
        with patch('src.gui.forms.budget_params_form.BudgetDefaultsService') as mock_service:
            mock_service.calculate_defaults.side_effect = Exception("Service error")

            # Should not raise exception
            form = BudgetParamsForm(mock_parent)

            # Form should still have fields (with fallback defaults)
            assert form.revenue_growth_field is not None
            assert form.expense_adjustment_field is not None

    def test_save_handles_validation_error(self, budget_form, mock_parent):
        """
        Given: BudgetParamsForm with invalid field value
        When: on_save_clicked called
        Then: Error message displayed, save not attempted
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set invalid value in field
        budget_form.revenue_growth_field.set_value("invalid_number")

        # Mock messagebox to capture error call
        with patch('src.gui.forms.budget_params_form.messagebox') as mock_msgbox:
            budget_form.on_save_clicked()

            # Verify error displayed
            mock_msgbox.showerror.assert_called_once()

        # Verify save_config was NOT called (error caught before save)
        mock_config_mgr.save_config.assert_not_called()

    def test_load_handles_file_error(self, budget_form, mock_parent):
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
        with patch('src.gui.forms.budget_params_form.messagebox') as mock_msgbox:
            budget_form.on_load_clicked()

            # Verify error displayed
            mock_msgbox.showerror.assert_called_once()

    def test_save_displays_success_message(self, budget_form, mock_parent):
        """
        Given: BudgetParamsForm with valid values
        When: on_save_clicked succeeds
        Then: Success message displayed to user
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set valid values
        budget_form.revenue_growth_field.set_value("0.05")
        budget_form.expense_adjustment_field.set_value("1.0")

        # Mock messagebox to capture success call
        with patch('src.gui.forms.budget_params_form.messagebox') as mock_msgbox:
            budget_form.on_save_clicked()

            # Verify success message displayed
            mock_msgbox.showinfo.assert_called_once()
            success_call = mock_msgbox.showinfo.call_args[0]
            assert 'Success' in str(success_call) or 'success' in str(success_call).lower()

    def test_load_displays_success_message(self, budget_form, mock_parent):
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
        with patch('src.gui.forms.budget_params_form.messagebox') as mock_msgbox:
            budget_form.on_load_clicked()

            # Verify success message displayed
            mock_msgbox.showinfo.assert_called_once()

    def test_form_uses_correct_config_filepath(self, budget_form, mock_parent):
        """
        Given: BudgetParamsForm instance
        When: Save called
        Then: Uses 'config/budget_parameters.json' filepath
        """
        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set valid values and save
        budget_form.revenue_growth_field.set_value("0.05")
        budget_form.expense_adjustment_field.set_value("1.0")

        with patch('src.gui.forms.budget_params_form.messagebox'):
            budget_form.on_save_clicked()

        # Verify filepath argument
        call_args = mock_config_mgr.save_config.call_args
        filepath = call_args[0][1]
        assert 'budget_parameters.json' in filepath
        assert 'config' in filepath

    def test_load_populates_only_existing_parameters(self, budget_form, mock_parent):
        """
        Given: Loaded model has only some parameters
        When: on_load_clicked called
        Then: Only available parameter fields are updated
        """
        # Setup mock config manager with partial data
        mock_config_mgr = Mock()
        test_model = ParameterModel(parameters={
            'revenue_growth_rate': 0.12
            # Missing other parameters
        })
        mock_config_mgr.load_config.return_value = test_model
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Set initial values
        budget_form.revenue_growth_field.set_value("0.05")
        budget_form.expense_adjustment_field.set_value("1.0")

        # Mock messagebox
        with patch('src.gui.forms.budget_params_form.messagebox'):
            budget_form.on_load_clicked()

        # Verify revenue field updated, expense field unchanged
        assert budget_form.revenue_growth_field.get_value() == 0.12
        assert budget_form.expense_adjustment_field.get_value() == 1.0

    def test_form_creates_dynamic_category_fields(self, mock_parent):
        """
        Given: BudgetDefaultsService returns category_growth_rates with 2 categories
        When: BudgetParamsForm created
        Then: Dynamic category fields created for each category
        """
        # Patch BudgetDefaultsService to return category rates
        with patch('src.gui.forms.budget_params_form.BudgetDefaultsService') as mock_service:
            mock_service.calculate_defaults.return_value = {
                'revenue_growth_rate': 0.05,
                'expense_adjustment': 1.0,
                'budget_methodology': 'Growth from Prior Year',
                'category_growth_rates': {
                    'Product Sales': 0.08,
                    'Service Revenue': 0.06
                }
            }

            form = BudgetParamsForm(mock_parent)

            # Verify category fields created
            assert 'Product Sales' in form.category_fields
            assert 'Service Revenue' in form.category_fields
            assert form.category_fields['Product Sales'].get_value() == 0.08
            assert form.category_fields['Service Revenue'].get_value() == 0.06

    def test_save_includes_category_rates(self, mock_parent):
        """
        Given: BudgetParamsForm with dynamic category fields
        When: on_save_clicked called
        Then: category_growth_rates saved with all category values
        """
        # Create form with category fields
        with patch('src.gui.forms.budget_params_form.BudgetDefaultsService') as mock_service:
            mock_service.calculate_defaults.return_value = {
                'revenue_growth_rate': 0.05,
                'expense_adjustment': 1.0,
                'budget_methodology': 'Growth from Prior Year',
                'category_growth_rates': {
                    'Product Sales': 0.08
                }
            }

            form = BudgetParamsForm(mock_parent)

        # Setup mock config manager
        mock_config_mgr = Mock()
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Modify category field value
        form.category_fields['Product Sales'].set_value("0.12")

        # Mock messagebox and save
        with patch('src.gui.forms.budget_params_form.messagebox'):
            form.on_save_clicked()

        # Verify category rates saved
        call_args = mock_config_mgr.save_config.call_args
        saved_model = call_args[0][0]
        category_rates = saved_model.get_parameter('category_growth_rates')
        assert category_rates['Product Sales'] == 0.12

    def test_load_populates_category_rates(self, mock_parent):
        """
        Given: Saved config has category_growth_rates
        When: on_load_clicked called
        Then: Dynamic category fields populated with saved values
        """
        # Create form with category fields
        with patch('src.gui.forms.budget_params_form.BudgetDefaultsService') as mock_service:
            mock_service.calculate_defaults.return_value = {
                'revenue_growth_rate': 0.05,
                'expense_adjustment': 1.0,
                'budget_methodology': 'Growth from Prior Year',
                'category_growth_rates': {
                    'Product Sales': 0.08,
                    'Service Revenue': 0.06
                }
            }

            form = BudgetParamsForm(mock_parent)

        # Setup mock config manager with saved category rates
        mock_config_mgr = Mock()
        test_model = ParameterModel(parameters={
            'revenue_growth_rate': 0.10,
            'category_growth_rates': {
                'Product Sales': 0.15,
                'Service Revenue': 0.12
            }
        })
        mock_config_mgr.load_config.return_value = test_model
        mock_parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox and load
        with patch('src.gui.forms.budget_params_form.messagebox'):
            form.on_load_clicked()

        # Verify category fields populated
        assert form.category_fields['Product Sales'].get_value() == 0.15
        assert form.category_fields['Service Revenue'].get_value() == 0.12
