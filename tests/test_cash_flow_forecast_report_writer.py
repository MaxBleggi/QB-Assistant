"""
Unit tests for CashFlowForecastReportWriter.

Tests dynamic column generation based on forecast_horizon, three-row confidence
interval format, bold formatting on Projected row, and multi-scenario layout.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.exporters.cash_flow_forecast_writer import CashFlowForecastReportWriter


@pytest.fixture
def mock_cf_forecast_model_6month():
    """Create CashFlowForecastModel fixture with 6-month horizon."""
    model = Mock()
    model.metadata = {'forecast_horizon': 6}
    model.hierarchy = {
        'Operating Activities': {
            'name': 'Operating Cash Flow',
            'projected': {1: 10000, 2: 12000, 3: 11000, 4: 13000, 5: 14000, 6: 15000},
            'lower_bound': {1: 8000, 2: 9000, 3: 8500, 4: 10000, 5: 11000, 6: 12000},
            'upper_bound': {1: 12000, 2: 15000, 3: 14000, 4: 16000, 5: 17000, 6: 18000},
            'children': []
        }
    }
    model.calculated_rows = {
        'ending_cash': {
            'projected': {1: 50000, 2: 52000, 3: 53000, 4: 56000, 5: 60000, 6: 65000},
            'lower_bound': {1: 45000, 2: 46000, 3: 47000, 4: 49000, 5: 52000, 6: 55000},
            'upper_bound': {1: 55000, 2: 58000, 3: 60000, 4: 63000, 5: 68000, 6: 75000}
        }
    }
    return model


@pytest.fixture
def mock_cf_forecast_model_12month():
    """Create CashFlowForecastModel fixture with 12-month horizon."""
    model = Mock()
    model.metadata = {'forecast_horizon': 12}
    model.hierarchy = {
        'Operating Activities': {
            'name': 'Operating Cash Flow',
            'projected': {m: 10000 + m * 1000 for m in range(1, 13)},
            'lower_bound': {m: 8000 + m * 800 for m in range(1, 13)},
            'upper_bound': {m: 12000 + m * 1200 for m in range(1, 13)},
            'children': []
        }
    }
    model.calculated_rows = {}
    return model


@pytest.fixture
def mock_multi_scenario_3scenarios():
    """Create MultiScenarioForecastResult fixture with 3 scenarios, 6-month horizon."""
    multi_result = Mock()
    multi_result.scenarios = []

    for scenario_name in ['Base', 'Optimistic', 'Pessimistic']:
        scenario = Mock()
        scenario.metadata = {'forecast_horizon': 6, 'scenario_name': scenario_name}
        scenario.hierarchy = {
            'Operating Activities': {
                'name': 'Operating Cash Flow',
                'projected': {m: 10000 + m * 1000 for m in range(1, 7)},
                'lower_bound': {m: 8000 + m * 800 for m in range(1, 7)},
                'upper_bound': {m: 12000 + m * 1200 for m in range(1, 7)},
                'children': []
            }
        }
        scenario.calculated_rows = {}
        multi_result.scenarios.append(scenario)

    return multi_result


def test_cash_flow_6month_columns(mock_cf_forecast_model_6month):
    """Test that 6-month horizon generates 7 total columns (Account + 6 months)."""
    # Create writer
    writer = CashFlowForecastReportWriter()
    writer.write(mock_cf_forecast_model_6month)

    # Access the worksheet to check column count
    ws = writer.workbook['Cash Flow Forecast']

    # Check header row has 7 columns (Account + Month 1-6)
    assert ws.cell(row=1, column=1).value == 'Account'
    assert ws.cell(row=1, column=2).value == 'Month 1'
    assert ws.cell(row=1, column=7).value == 'Month 6'
    # Column 8 should be empty (only 7 columns)
    assert ws.cell(row=1, column=8).value is None


def test_cash_flow_12month_columns(mock_cf_forecast_model_12month):
    """Test that 12-month horizon generates 13 total columns (Account + 12 months)."""
    # Create writer
    writer = CashFlowForecastReportWriter()
    writer.write(mock_cf_forecast_model_12month)

    # Access the worksheet to check column count
    ws = writer.workbook['Cash Flow Forecast']

    # Check header row has 13 columns (Account + Month 1-12)
    assert ws.cell(row=1, column=1).value == 'Account'
    assert ws.cell(row=1, column=2).value == 'Month 1'
    assert ws.cell(row=1, column=13).value == 'Month 12'
    # Column 14 should be empty (only 13 columns)
    assert ws.cell(row=1, column=14).value is None


def test_cash_flow_three_row_format(mock_cf_forecast_model_6month):
    """Test that each metric generates three consecutive rows (Lower/Projected/Upper)."""
    # Create writer
    writer = CashFlowForecastReportWriter()
    writer.write(mock_cf_forecast_model_6month)

    # Access the worksheet to check row labels
    ws = writer.workbook['Cash Flow Forecast']

    # Collect account names from column A (starting from row 2)
    account_names = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1):
        if row[0].value:
            account_names.append(row[0].value)

    # Should have three rows per metric (Lower, Projected, Upper)
    lower_rows = [name for name in account_names if '(Lower)' in str(name)]
    projected_rows = [name for name in account_names if '(Projected)' in str(name)]
    upper_rows = [name for name in account_names if '(Upper)' in str(name)]

    assert len(lower_rows) >= 1, "Should have Lower Bound rows"
    assert len(projected_rows) >= 1, "Should have Projected rows"
    assert len(upper_rows) >= 1, "Should have Upper Bound rows"


def test_cash_flow_projected_bold(mock_cf_forecast_model_6month):
    """Test that Projected row receives bold formatting."""
    # Create writer and patch format_bold method
    writer = CashFlowForecastReportWriter()
    writer.format_bold = Mock()
    writer.write(mock_cf_forecast_model_6month)

    # Check that format_bold was called for Projected rows
    bold_calls = writer.format_bold.call_args_list

    # Should have bold formatting applied (for Projected row labels and values)
    assert len(bold_calls) >= 2, "Projected rows should have bold formatting applied"


def test_cash_flow_multi_scenario_layout(mock_multi_scenario_3scenarios):
    """Test that multi-scenario generates correct column count (Account + 18 month columns)."""
    # Create writer
    writer = CashFlowForecastReportWriter()
    writer.write(mock_multi_scenario_3scenarios)

    # Access the worksheet to check headers
    ws = writer.workbook['Cash Flow Forecast']

    # Check header row: 3 scenarios × 6 months = 18 month columns + 1 Account column = 19 total
    header_values = []
    for col in range(1, 20):
        cell_value = ws.cell(row=1, column=col).value
        if cell_value:
            header_values.append(cell_value)

    assert len(header_values) >= 19, "Should have 19 columns for 3 scenarios with 6-month horizon"

    # Check that scenario names appear in headers
    base_headers = [h for h in header_values if 'Base' in str(h)]
    optimistic_headers = [h for h in header_values if 'Optimistic' in str(h)]
    pessimistic_headers = [h for h in header_values if 'Pessimistic' in str(h)]

    assert len(base_headers) >= 1, "Base scenario should appear in headers"
    assert len(optimistic_headers) >= 1, "Optimistic scenario should appear in headers"
    assert len(pessimistic_headers) >= 1, "Pessimistic scenario should appear in headers"


def test_cash_flow_summary_rows(mock_cf_forecast_model_6month):
    """Test that Ending Cash summary row appears with three-row format."""
    # Create writer
    writer = CashFlowForecastReportWriter()
    writer.write(mock_cf_forecast_model_6month)

    # Access the worksheet to check for Ending Cash rows
    ws = writer.workbook['Cash Flow Forecast']

    # Collect account names that contain 'Ending Cash'
    ending_cash_rows = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1):
        if row[0].value and 'Ending Cash' in str(row[0].value):
            ending_cash_rows.append(row[0].value)

    # Should have 3 rows (Lower, Projected, Upper)
    assert len(ending_cash_rows) >= 3, "Ending Cash should have three-row format"


def test_cash_flow_currency_formatting(mock_cf_forecast_model_6month):
    """Test that currency formatting is applied to all value columns."""
    # Create writer and patch format_currency method
    writer = CashFlowForecastReportWriter()
    writer.format_currency = Mock()
    writer.write(mock_cf_forecast_model_6month)

    # Check that currency formatting was applied
    currency_calls = writer.format_currency.call_args_list

    assert len(currency_calls) >= 1, "Currency formatting should be applied to value columns"
