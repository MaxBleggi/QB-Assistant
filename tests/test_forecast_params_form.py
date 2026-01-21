"""
GUI tests for ForecastParamsForm.

Tests form initialization, field population, save operations, back navigation,
and error handling with mocked ConfigManager.
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, patch

from src.gui.forms.forecast_params_form import ForecastParamsForm
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
def sample_scenario():
    """Create sample scenario with parameters for testing."""
    params = {
        'revenue_growth_rates': {
            'monthly_rate': 0.07,
            'use_averaged': True
        },
        'expense_trend_adjustments': {
            'cogs_trend': 0.04,
            'opex_trend': 0.03
        },
        'cash_flow_timing_params': {
            'collection_period_days': 50,
            'payment_terms_days': 35
        },
        'major_cash_events': {
            'planned_capex': ['100000', '50000'],
            'debt_payments': ['25000']
        }
    }

    return ForecastScenarioModel(
        parameters=params,
        scenario_id='test-scenario-id',
        scenario_name='Q2 Forecast',
        description='Test scenario'
    )


@pytest.fixture
def mock_config_manager(sample_scenario):
    """Create mock ConfigManager that returns sample scenario collection."""
    mock_mgr = Mock()
    collection = ForecastScenariosCollection(scenarios=[sample_scenario])
    mock_mgr.load_config.return_value = collection
    return mock_mgr


class TestForecastParamsForm:
    """Test suite for ForecastParamsForm class."""

    def test_forecast_params_form_load(self, mock_parent, mock_config_manager):
        """
        Given: Scenario with monthly_rate=0.07
        When: ForecastParamsForm initialized with that scenario_id
        Then: monthly_rate field displays 0.07
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Verify monthly_rate field populated correctly
        monthly_rate_value = form.fields['monthly_rate'].get_value()
        assert monthly_rate_value == 0.07

    def test_forecast_params_form_title(self, mock_parent, mock_config_manager):
        """
        Given: Form initialized with scenario name 'Q2 Forecast'
        When: Form rendered
        Then: Title label text contains 'Q2 Forecast'
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Find title label (first child in grid)
        title_label = None
        for child in form.winfo_children():
            if isinstance(child, tk.Label):
                title_label = child
                break

        assert title_label is not None
        assert 'Q2 Forecast' in title_label.cget('text')

    def test_forecast_params_form_sections(self, mock_parent, mock_config_manager):
        """
        Given: ForecastParamsForm initialized
        When: Form rendered
        Then: Four parameter category sections created
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Verify all required fields exist
        assert 'monthly_rate' in form.fields
        assert 'use_averaged' in form.fields
        assert 'cogs_trend' in form.fields
        assert 'opex_trend' in form.fields
        assert 'collection_period_days' in form.fields
        assert 'payment_terms_days' in form.fields
        assert 'planned_capex' in form.fields
        assert 'debt_payments' in form.fields

    def test_forecast_params_form_field_population(self, mock_parent, mock_config_manager):
        """
        Given: Scenario with various parameter values
        When: Form initialized
        Then: All fields populated with scenario's parameter values
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Verify revenue section fields
        assert form.fields['monthly_rate'].get_value() == 0.07
        assert form.fields['use_averaged'].get() == 1  # Checkbutton returns 1 for True

        # Verify expense section fields
        assert form.fields['cogs_trend'].get_value() == 0.04
        assert form.fields['opex_trend'].get_value() == 0.03

        # Verify cash flow section fields
        assert form.fields['collection_period_days'].get_value() == 50
        assert form.fields['payment_terms_days'].get_value() == 35

        # Verify major events section fields
        capex_value = form.fields['planned_capex'].get_value()
        assert '100000' in capex_value
        assert '50000' in capex_value

    @patch('src.gui.forms.forecast_params_form.messagebox')
    def test_forecast_params_form_save(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: User modifies cogs_trend field to 0.05, clicks Save
        When: Save operation executes
        Then: Scenario in mock collection updated with cogs_trend=0.05, save_config called
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Modify cogs_trend field
        form.fields['cogs_trend'].set_value("0.05")

        # Click save button
        form.on_save_clicked()

        # Verify save_config was called
        mock_config_manager.save_config.assert_called()

        # Verify scenario was updated
        call_args = mock_config_manager.save_config.call_args
        saved_collection = call_args[0][0]
        saved_scenario = saved_collection.get_scenario('test-scenario-id')
        assert saved_scenario.get_parameter('expense_trend_adjustments')['cogs_trend'] == 0.05

        # Verify success message shown
        mock_messagebox.showinfo.assert_called_once()

    def test_forecast_params_form_back_navigation(self, mock_parent, mock_config_manager):
        """
        Given: User clicks Back button
        When: Button clicked
        Then: parent.show_form called with ScenarioListForm class, no kwargs
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Click back button
        form.on_back_clicked()

        # Verify show_form called with ScenarioListForm
        mock_parent.show_form.assert_called_once()
        call_args = mock_parent.show_form.call_args

        from src.gui.forms.scenario_list_form import ScenarioListForm
        assert call_args[0][0] == ScenarioListForm

        # Verify no kwargs passed (back to list with no context)
        assert len(call_args[1]) == 0

    @patch('src.gui.forms.forecast_params_form.messagebox')
    def test_save_operation_updates_all_parameter_categories(
        self,
        mock_messagebox,
        mock_parent,
        mock_config_manager
    ):
        """
        Given: User modifies fields in all four sections
        When: Save clicked
        Then: All parameter categories updated in scenario
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Modify fields in all sections
        form.fields['monthly_rate'].set_value("0.08")
        form.fields['cogs_trend'].set_value("0.06")
        form.fields['collection_period_days'].set_value("60")
        form.fields['planned_capex'].set_value("200000, 100000")

        # Save
        form.on_save_clicked()

        # Verify all categories updated
        call_args = mock_config_manager.save_config.call_args
        saved_collection = call_args[0][0]
        saved_scenario = saved_collection.get_scenario('test-scenario-id')

        assert saved_scenario.get_parameter('revenue_growth_rates')['monthly_rate'] == 0.08
        assert saved_scenario.get_parameter('expense_trend_adjustments')['cogs_trend'] == 0.06
        assert saved_scenario.get_parameter('cash_flow_timing_params')['collection_period_days'] == 60
        assert '200000' in saved_scenario.get_parameter('major_cash_events')['planned_capex']

    @patch('src.gui.forms.forecast_params_form.messagebox')
    def test_load_error_handling(self, mock_messagebox, mock_parent):
        """
        Given: ConfigManager raises exception during load
        When: Form initialized
        Then: Error message displayed via messagebox.showerror
        """
        mock_mgr = Mock()
        mock_mgr.load_config.side_effect = Exception("Load failed")
        mock_parent.get_config_manager.return_value = mock_mgr

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Verify error message shown
        mock_messagebox.showerror.assert_called_once()
        assert 'Failed to load scenario' in str(mock_messagebox.showerror.call_args)

        # Verify current_scenario is None
        assert form.current_scenario is None

    @patch('src.gui.forms.forecast_params_form.messagebox')
    def test_save_error_handling(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: ConfigManager raises exception during save
        When: Save button clicked
        Then: Error message displayed via messagebox.showerror
        """
        mock_parent.get_config_manager.return_value = mock_config_manager
        mock_config_manager.save_config.side_effect = Exception("Save failed")

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Click save button
        form.on_save_clicked()

        # Verify error message shown
        assert mock_messagebox.showerror.call_count >= 1
        error_calls = [str(call) for call in mock_messagebox.showerror.call_args_list]
        assert any('Failed to save' in call or 'Save failed' in call for call in error_calls)

    def test_use_averaged_checkbox_state(self, mock_parent, mock_config_manager):
        """
        Given: Scenario with use_averaged=True
        When: Form initialized
        Then: use_averaged checkbox is checked
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Verify checkbox state
        checkbox_value = form.fields['use_averaged'].get()
        assert checkbox_value == 1  # 1 = checked

    @patch('src.gui.forms.forecast_params_form.messagebox')
    def test_save_preserves_checkbox_state(self, mock_messagebox, mock_parent, mock_config_manager):
        """
        Given: User unchecks use_averaged checkbox
        When: Save clicked
        Then: Scenario updated with use_averaged=False
        """
        mock_parent.get_config_manager.return_value = mock_config_manager

        form = ForecastParamsForm(mock_parent, scenario_id='test-scenario-id')

        # Uncheck checkbox
        form.fields['use_averaged'].set(0)

        # Save
        form.on_save_clicked()

        # Verify checkbox state saved
        call_args = mock_config_manager.save_config.call_args
        saved_collection = call_args[0][0]
        saved_scenario = saved_collection.get_scenario('test-scenario-id')

        assert saved_scenario.get_parameter('revenue_growth_rates')['use_averaged'] is False
