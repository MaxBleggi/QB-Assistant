"""
Unit tests for ForecastParamsForm external_events section.

Tests field validation, list operations (add/delete), parameter collection,
and initialization from templates and saved configurations.
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch

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
    """Create mock parent with required methods."""
    parent = tk_root
    parent.get_config_manager = Mock()
    parent.show_form = Mock()
    return parent


@pytest.fixture
def mock_scenario():
    """Create mock ForecastScenario with external_events parameter."""
    scenario = Mock(spec=ForecastScenarioModel)
    scenario.scenario_id = 'test-scenario-1'
    scenario.scenario_name = 'Test Scenario'
    scenario.parameters = {
        'revenue_growth_rates': {'monthly_rate': 0.05, 'use_averaged': True},
        'expense_trend_adjustments': {'cogs_trend': 0.03, 'opex_trend': 0.02},
        'cash_flow_timing_params': {'collection_period_days': 45, 'payment_terms_days': 30},
        'major_cash_events': {'planned_capex': [], 'debt_payments': []},
        'external_events': {'events': []}
    }
    scenario.get_parameter = lambda key, default=None: scenario.parameters.get(key, default)
    scenario.set_parameter = Mock()
    return scenario


@pytest.fixture
def mock_collection(mock_scenario):
    """Create mock ForecastScenariosCollection."""
    collection = Mock(spec=ForecastScenariosCollection)
    collection.get_scenario = Mock(return_value=mock_scenario)
    return collection


@pytest.fixture
def forecast_form(mock_parent, mock_collection):
    """Create ForecastParamsForm instance with mocked dependencies."""
    mock_config_mgr = Mock()
    mock_config_mgr.load_config = Mock(return_value=mock_collection)
    mock_parent.get_config_manager.return_value = mock_config_mgr

    form = ForecastParamsForm(mock_parent, 'test-scenario-1')
    return form


class TestExternalEventsValidation:
    """Test suite for external events field validation."""

    def test_month_validation_accepts_valid_range(self, forecast_form):
        """
        Given: Valid month values 1-12
        When: Add event button clicked
        Then: Event added successfully without error
        """
        # Test boundary values and middle value
        for month in [1, 6, 12]:
            forecast_form.external_event_month_field.set_value(str(month))
            forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
            forecast_form.external_event_magnitude_field.set_value('10.5')
            forecast_form.external_event_description_field.set_value('Test event')

            initial_count = len(forecast_form.external_events_list)
            forecast_form._on_add_external_event_clicked()

            # Event should be added
            assert len(forecast_form.external_events_list) == initial_count + 1

    def test_month_validation_rejects_zero(self, forecast_form):
        """
        Given: Month value 0
        When: Add event button clicked
        Then: Validation error shown, event not added
        """
        forecast_form.external_event_month_field.set_value('0')
        forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
        forecast_form.external_event_magnitude_field.set_value('10.5')
        forecast_form.external_event_description_field.set_value('Test event')

        initial_count = len(forecast_form.external_events_list)

        with patch('tkinter.messagebox.showerror') as mock_error:
            forecast_form._on_add_external_event_clicked()
            mock_error.assert_called_once()

        # Event should not be added
        assert len(forecast_form.external_events_list) == initial_count

    def test_month_validation_rejects_thirteen(self, forecast_form):
        """
        Given: Month value 13
        When: Add event button clicked
        Then: Validation error shown, event not added
        """
        forecast_form.external_event_month_field.set_value('13')
        forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
        forecast_form.external_event_magnitude_field.set_value('10.5')
        forecast_form.external_event_description_field.set_value('Test event')

        initial_count = len(forecast_form.external_events_list)

        with patch('tkinter.messagebox.showerror') as mock_error:
            forecast_form._on_add_external_event_clicked()
            mock_error.assert_called_once()

        # Event should not be added
        assert len(forecast_form.external_events_list) == initial_count

    def test_month_validation_rejects_negative(self, forecast_form):
        """
        Given: Negative month value
        When: Add event button clicked
        Then: Validation error shown, event not added
        """
        forecast_form.external_event_month_field.set_value('-5')
        forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
        forecast_form.external_event_magnitude_field.set_value('10.5')
        forecast_form.external_event_description_field.set_value('Test event')

        initial_count = len(forecast_form.external_events_list)

        with patch('tkinter.messagebox.showerror') as mock_error:
            forecast_form._on_add_external_event_clicked()
            mock_error.assert_called_once()

        # Event should not be added
        assert len(forecast_form.external_events_list) == initial_count

    def test_description_validation_rejects_empty(self, forecast_form):
        """
        Given: Empty description field
        When: Add event button clicked
        Then: Validation error shown, event not added
        """
        forecast_form.external_event_month_field.set_value('5')
        forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
        forecast_form.external_event_magnitude_field.set_value('10.5')
        forecast_form.external_event_description_field.set_value('')

        initial_count = len(forecast_form.external_events_list)

        with patch('tkinter.messagebox.showerror') as mock_error:
            forecast_form._on_add_external_event_clicked()
            mock_error.assert_called_once()

        # Event should not be added
        assert len(forecast_form.external_events_list) == initial_count


class TestExternalEventsOperations:
    """Test suite for external events add/delete operations."""

    def test_add_event_appears_in_listbox(self, forecast_form):
        """
        Given: Valid event data entered
        When: Add button clicked
        Then: Event appears in listbox with correct formatting
        """
        forecast_form.external_event_month_field.set_value('5')
        forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
        forecast_form.external_event_magnitude_field.set_value('10.5')
        forecast_form.external_event_description_field.set_value('New tariff')

        forecast_form._on_add_external_event_clicked()

        # Check listbox contents
        listbox_items = forecast_form.external_events_listbox.get(0, tk.END)
        assert len(listbox_items) == 1
        assert 'Month 5' in listbox_items[0]
        assert 'Revenue Reduction' in listbox_items[0]
        assert '10.5%' in listbox_items[0]
        assert 'New tariff' in listbox_items[0]

    def test_add_event_clears_form_fields(self, forecast_form):
        """
        Given: Valid event data entered and added
        When: Add operation completes
        Then: Form fields are cleared for next entry
        """
        forecast_form.external_event_month_field.set_value('5')
        forecast_form.external_event_impact_type_field.set_value('Revenue Reduction')
        forecast_form.external_event_magnitude_field.set_value('10.5')
        forecast_form.external_event_description_field.set_value('New tariff')

        forecast_form._on_add_external_event_clicked()

        # Check fields are cleared (empty or default)
        assert forecast_form.external_event_month_field.get_value() == '' or \
               forecast_form.external_event_month_field.entry.get() == ''
        assert forecast_form.external_event_magnitude_field.entry.get() == ''
        assert forecast_form.external_event_description_field.get_value() == ''

    def test_delete_event_removes_from_listbox(self, forecast_form):
        """
        Given: Two events in listbox
        When: User selects second event and clicks Delete (confirms)
        Then: Event removed from list
        """
        # Add two events
        forecast_form.external_events_list = [
            {'month': 3, 'impact_type': 'Cost Increase', 'magnitude': 15.0, 'description': 'Wage law'},
            {'month': 7, 'impact_type': 'Revenue Reduction', 'magnitude': 5.0, 'description': 'Market shift'}
        ]
        forecast_form._refresh_external_events_listbox()

        # Select second event
        forecast_form.external_events_listbox.selection_set(1)

        # Mock confirmation dialog to return True
        with patch('tkinter.messagebox.askyesno', return_value=True):
            forecast_form._on_delete_external_event_clicked()

        # Check event was removed
        assert len(forecast_form.external_events_list) == 1
        assert forecast_form.external_events_list[0]['month'] == 3

        # Check listbox updated
        listbox_items = forecast_form.external_events_listbox.get(0, tk.END)
        assert len(listbox_items) == 1
        assert 'Month 3' in listbox_items[0]

    def test_delete_event_cancelled_no_change(self, forecast_form):
        """
        Given: Event selected in listbox
        When: User clicks Delete but cancels confirmation
        Then: Event remains in list
        """
        # Add event
        forecast_form.external_events_list = [
            {'month': 3, 'impact_type': 'Cost Increase', 'magnitude': 15.0, 'description': 'Wage law'}
        ]
        forecast_form._refresh_external_events_listbox()

        # Select event
        forecast_form.external_events_listbox.selection_set(0)

        # Mock confirmation dialog to return False
        with patch('tkinter.messagebox.askyesno', return_value=False):
            forecast_form._on_delete_external_event_clicked()

        # Check event still exists
        assert len(forecast_form.external_events_list) == 1

    def test_delete_with_no_selection_shows_warning(self, forecast_form):
        """
        Given: No event selected in listbox
        When: Delete button clicked
        Then: Warning message shown, no changes made
        """
        forecast_form.external_events_list = [
            {'month': 3, 'impact_type': 'Cost Increase', 'magnitude': 15.0, 'description': 'Wage law'}
        ]
        forecast_form._refresh_external_events_listbox()

        # Don't select anything
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            forecast_form._on_delete_external_event_clicked()
            mock_warning.assert_called_once()

        # Check list unchanged
        assert len(forecast_form.external_events_list) == 1


class TestExternalEventsInitialization:
    """Test suite for external events initialization from params."""

    def test_empty_events_list_on_new_scenario(self, mock_parent, mock_collection, mock_scenario):
        """
        Given: Scenario with empty external_events
        When: Form loads
        Then: Listbox is empty, no errors
        """
        mock_scenario.parameters['external_events'] = {'events': []}

        mock_config_mgr = Mock()
        mock_config_mgr.load_config = Mock(return_value=mock_collection)
        mock_parent.get_config_manager.return_value = mock_config_mgr

        form = ForecastParamsForm(mock_parent, 'test-scenario-1')

        # Check listbox is empty
        assert len(form.external_events_list) == 0
        listbox_items = form.external_events_listbox.get(0, tk.END)
        assert len(listbox_items) == 0

    def test_existing_events_loaded_from_params(self, mock_parent, mock_collection, mock_scenario):
        """
        Given: Scenario with saved external_events
        When: Form loads
        Then: Events displayed in listbox with correct formatting
        """
        mock_scenario.parameters['external_events'] = {
            'events': [
                {'month': 3, 'impact_type': 'Cost Increase', 'magnitude': 15.0, 'description': 'Wage law'},
                {'month': 7, 'impact_type': 'Revenue Reduction', 'magnitude': 5.0, 'description': 'Market shift'}
            ]
        }

        mock_config_mgr = Mock()
        mock_config_mgr.load_config = Mock(return_value=mock_collection)
        mock_parent.get_config_manager.return_value = mock_config_mgr

        form = ForecastParamsForm(mock_parent, 'test-scenario-1')

        # Check events loaded
        assert len(form.external_events_list) == 2

        # Check listbox contents
        listbox_items = form.external_events_listbox.get(0, tk.END)
        assert len(listbox_items) == 2
        assert 'Month 3' in listbox_items[0]
        assert 'Cost Increase' in listbox_items[0]
        assert '15.0%' in listbox_items[0]
        assert 'Wage law' in listbox_items[0]
        assert 'Month 7' in listbox_items[1]


class TestExternalEventsParameterCollection:
    """Test suite for external events parameter collection on save."""

    def test_save_collects_events_list(self, forecast_form, mock_scenario, mock_collection):
        """
        Given: Two external events added to form
        When: Save button clicked
        Then: scenario.set_parameter called with correct events structure
        """
        # Add events
        forecast_form.external_events_list = [
            {'month': 3, 'impact_type': 'Cost Increase', 'magnitude': 15.0, 'description': 'Wage law'},
            {'month': 7, 'impact_type': 'Revenue Reduction', 'magnitude': 5.0, 'description': 'Market shift'}
        ]

        # Mock config manager to return collection on reload
        mock_config_mgr = Mock()
        mock_config_mgr.load_config = Mock(return_value=mock_collection)
        forecast_form.parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to avoid popup
        with patch('tkinter.messagebox.showinfo'):
            forecast_form.on_save_clicked()

        # Verify set_parameter was called for external_events
        set_parameter_calls = mock_scenario.set_parameter.call_args_list
        external_events_call = None
        for call in set_parameter_calls:
            if call[0][0] == 'external_events':
                external_events_call = call
                break

        assert external_events_call is not None
        external_events_params = external_events_call[0][1]
        assert 'events' in external_events_params
        assert len(external_events_params['events']) == 2
        assert external_events_params['events'][0]['month'] == 3
        assert external_events_params['events'][1]['month'] == 7

    def test_save_empty_events_list(self, forecast_form, mock_scenario, mock_collection):
        """
        Given: No external events added
        When: Save button clicked
        Then: scenario.set_parameter called with empty events list
        """
        forecast_form.external_events_list = []

        # Mock config manager to return collection on reload
        mock_config_mgr = Mock()
        mock_config_mgr.load_config = Mock(return_value=mock_collection)
        forecast_form.parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to avoid popup
        with patch('tkinter.messagebox.showinfo'):
            forecast_form.on_save_clicked()

        # Verify set_parameter was called for external_events with empty list
        set_parameter_calls = mock_scenario.set_parameter.call_args_list
        external_events_call = None
        for call in set_parameter_calls:
            if call[0][0] == 'external_events':
                external_events_call = call
                break

        assert external_events_call is not None
        external_events_params = external_events_call[0][1]
        assert external_events_params == {'events': []}

    def test_save_reloads_collection_before_collecting(self, forecast_form, mock_collection):
        """
        Given: Scenario may have been modified by another form
        When: Save button clicked
        Then: Collection reloaded before collecting parameters
        """
        # Mock config manager
        mock_config_mgr = Mock()
        mock_config_mgr.load_config = Mock(return_value=mock_collection)
        forecast_form.parent.get_config_manager.return_value = mock_config_mgr

        # Mock messagebox to avoid popup
        with patch('tkinter.messagebox.showinfo'):
            forecast_form.on_save_clicked()

        # Verify reload happened (load_config called)
        mock_config_mgr.load_config.assert_called()


class TestExternalEventsTemplateInitialization:
    """Test suite for template initialization with external_events."""

    def test_templates_have_external_events_initialized(self):
        """
        Given: Forecast templates (Conservative, Expected, Optimistic)
        When: Template accessed
        Then: external_events key exists with empty events list
        """
        from src.services.forecast_templates import ForecastTemplateService

        for template_name in ['Conservative', 'Expected', 'Optimistic']:
            template = ForecastTemplateService.get_template(template_name)

            assert 'external_events' in template
            assert 'events' in template['external_events']
            assert template['external_events']['events'] == []
