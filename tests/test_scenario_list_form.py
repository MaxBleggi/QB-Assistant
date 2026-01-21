"""
GUI tests for ScenarioListForm.

Tests scenario list rendering, CRUD operations, navigation, and error handling
with mocked ConfigManager to avoid file system dependencies.
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock

from src.gui.forms.scenario_list_form import ScenarioListForm
from src.models.forecast_scenario import ForecastScenarioModel, ForecastScenariosCollection


@pytest.fixture
def tk_root():
    """Create Tk root for GUI tests."""
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def mock_parent(tk_root):
    """Create mock parent with get_config_manager and show_form methods."""
    parent = tk_root
    parent.get_config_manager = Mock()
    parent.show_form = Mock()
    return parent


@pytest.fixture
def sample_scenarios():
    """Create sample scenarios for testing."""
    scenario1 = ForecastScenarioModel(
        scenario_id='s1',
        scenario_name='Conservative Forecast',
        description='Conservative scenario'
    )
    scenario2 = ForecastScenarioModel(
        scenario_id='s2',
        scenario_name='Expected Forecast',
        description='Expected scenario'
    )
    scenario3 = ForecastScenarioModel(
        scenario_id='s3',
        scenario_name='Optimistic Forecast',
        description='Optimistic scenario'
    )
    return [scenario1, scenario2, scenario3]


@pytest.fixture
def mock_config_manager(sample_scenarios):
    """Create mock ConfigManager that returns sample scenarios."""
    mock_mgr = Mock()
    collection = ForecastScenariosCollection(scenarios=sample_scenarios)
    mock_mgr.load_config.return_value = collection
    return mock_mgr


class TestScenarioListForm:
    """Test suite for ScenarioListForm class."""

    def test_scenario_list_form_rendering(self, mock_parent, mock_config_manager):
        """
        Given: Mock ConfigManager returns collection with 3 scenarios
        When: ScenarioListForm initialized
        Then: Listbox populated with 3 scenario names
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ScenarioListForm(mock_parent)

        # Verify listbox populated
        listbox_items = form.scenario_listbox.get(0, tk.END)
        assert len(listbox_items) == 3
        assert listbox_items[0] == 'Conservative Forecast'
        assert listbox_items[1] == 'Expected Forecast'
        assert listbox_items[2] == 'Optimistic Forecast'

    def test_scenario_list_form_handles_empty_file(self, mock_parent):
        """
        Given: Config file does not exist (FileNotFoundError)
        When: Form loads scenarios
        Then: Creates empty ForecastScenariosCollection, no error displayed
        """
        mock_mgr = Mock()
        mock_mgr.load_config.side_effect = FileNotFoundError("File not found")
        mock_parent.get_config_manager.return_value = mock_mgr

        form = ScenarioListForm(mock_parent)

        # Verify empty listbox
        listbox_items = form.scenario_listbox.get(0, tk.END)
        assert len(listbox_items) == 0

        # Verify collection created
        assert form.scenarios_collection is not None
        assert len(form.scenarios_collection.list_scenarios()) == 0

    @patch('src.gui.forms.scenario_list_form.ForecastTemplateService')
    @patch('src.gui.forms.scenario_list_form.ScenarioCreateDialog')
    def test_scenario_list_form_create(
        self,
        mock_dialog_class,
        mock_template_service,
        mock_parent,
        mock_config_manager
    ):
        """
        Given: User simulates Create button click with name='New' and template='Expected'
        When: Create operation executes
        Then: Mock ConfigManager.save_config called, parent.show_form called with
              ForecastParamsForm and scenario_id
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        # Mock template service
        mock_template_service.get_template.return_value = {
            'revenue_growth_rates': {'monthly_rate': 0.05},
            'expense_trend_adjustments': {},
            'cash_flow_timing_params': {},
            'major_cash_events': {}
        }

        # Mock dialog to return scenario name and template
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.result = ('New Scenario', 'Expected')
        mock_dialog_class.return_value = mock_dialog_instance

        form = ScenarioListForm(mock_parent)

        # Simulate create button click
        form.on_create_clicked()

        # Verify save_config was called
        mock_config_manager.save_config.assert_called_once()

        # Verify show_form was called with ForecastParamsForm and scenario_id
        mock_parent.show_form.assert_called_once()
        call_args = mock_parent.show_form.call_args

        # First argument should be ForecastParamsForm class
        from src.gui.forms.forecast_params_form import ForecastParamsForm
        assert call_args[0][0] == ForecastParamsForm

        # Should have scenario_id kwarg
        assert 'scenario_id' in call_args[1]

    def test_scenario_list_form_edit_navigation(self, mock_parent, mock_config_manager):
        """
        Given: Scenario selected in Listbox
        When: Edit button clicked
        Then: parent.show_form called with ForecastParamsForm and scenario_id
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ScenarioListForm(mock_parent)

        # Select first scenario in listbox
        form.scenario_listbox.selection_clear(0, tk.END)
        form.scenario_listbox.selection_set(0)

        # Click edit button
        form.on_edit_clicked()

        # Verify show_form called with ForecastParamsForm and scenario_id
        mock_parent.show_form.assert_called_once()
        call_args = mock_parent.show_form.call_args

        from src.gui.forms.forecast_params_form import ForecastParamsForm
        assert call_args[0][0] == ForecastParamsForm
        assert 'scenario_id' in call_args[1]
        assert call_args[1]['scenario_id'] == 's1'  # First scenario

    @patch('src.gui.forms.scenario_list_form.messagebox')
    def test_scenario_list_form_delete(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: Scenario selected in Listbox, user confirms delete
        When: Delete button clicked
        Then: Mock ConfigManager.save_config called, Listbox item count reduced by 1
        """
        mock_parent.get_config_manager.return_value = mock_config_manager
        mock_messagebox.askyesno.return_value = True  # Confirm deletion

        form = ScenarioListForm(mock_parent)

        # Verify initial state
        assert form.scenario_listbox.size() == 3

        # Select second scenario
        form.scenario_listbox.selection_clear(0, tk.END)
        form.scenario_listbox.selection_set(1)

        # Click delete button
        form.on_delete_clicked()

        # Verify save_config was called
        mock_config_manager.save_config.assert_called_once()

        # Verify listbox refreshed (should have 2 items now)
        assert form.scenario_listbox.size() == 2

        # Verify correct scenario was removed (s2)
        listbox_items = form.scenario_listbox.get(0, tk.END)
        assert 'Conservative Forecast' in listbox_items
        assert 'Optimistic Forecast' in listbox_items
        assert 'Expected Forecast' not in listbox_items

    @patch('src.gui.forms.scenario_list_form.messagebox')
    def test_delete_button_shows_confirmation_dialog(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: Scenario selected
        When: Delete button clicked
        Then: Confirmation dialog shown (messagebox.askyesno called)
        """
        mock_parent.get_config_manager.return_value = mock_config_manager
        mock_messagebox.askyesno.return_value = False  # Cancel deletion

        form = ScenarioListForm(mock_parent)

        # Select scenario
        form.scenario_listbox.selection_set(0)

        # Click delete button
        form.on_delete_clicked()

        # Verify confirmation dialog was shown
        mock_messagebox.askyesno.assert_called_once()
        assert 'Conservative Forecast' in str(mock_messagebox.askyesno.call_args)

    @patch('src.gui.forms.scenario_list_form.messagebox')
    def test_edit_button_without_selection_shows_warning(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: No scenario selected
        When: Edit button clicked
        Then: Warning message shown (messagebox.showwarning called)
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ScenarioListForm(mock_parent)

        # Ensure no selection
        form.scenario_listbox.selection_clear(0, tk.END)

        # Click edit button
        form.on_edit_clicked()

        # Verify warning shown
        mock_messagebox.showwarning.assert_called_once()

    @patch('src.gui.forms.scenario_list_form.messagebox')
    def test_delete_button_without_selection_shows_warning(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: No scenario selected
        When: Delete button clicked
        Then: Warning message shown (messagebox.showwarning called)
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ScenarioListForm(mock_parent)

        # Ensure no selection
        form.scenario_listbox.selection_clear(0, tk.END)

        # Click delete button
        form.on_delete_clicked()

        # Verify warning shown
        mock_messagebox.showwarning.assert_called_once()

    @patch('src.gui.forms.scenario_list_form.messagebox')
    def test_load_error_handling(self, mock_messagebox, mock_parent):
        """
        Given: ConfigManager raises unexpected exception
        When: Form loads scenarios
        Then: Error message displayed via messagebox.showerror
        """
        mock_mgr = Mock()
        mock_mgr.load_config.side_effect = Exception("Unexpected error")
        mock_parent.get_config_manager.return_value = mock_mgr

        form = ScenarioListForm(mock_parent)

        # Verify error message shown
        mock_messagebox.showerror.assert_called_once()
        assert 'Failed to load scenarios' in str(mock_messagebox.showerror.call_args)
