"""
Unit tests for PLForecastReportWriter.

Tests dynamic column generation based on forecast_horizon, three-row confidence
interval format, bold formatting on Projected row, multi-scenario layout, and
P&L-specific summary metrics with margin percentage formatting.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.exporters.pl_forecast_writer import PLForecastReportWriter
from src.exporters.base_writer import BaseExcelWriter


@pytest.fixture
def mock_pl_forecast_model_6month():
    """Create PLForecastModel fixture with 6-month horizon."""
    model = Mock()
    model.metadata = {'forecast_horizon': 6}
    model.hierarchy = {
        'Income': {
            'name': 'Revenue',
            'projected': {1: 100000, 2: 105000, 3: 110000, 4: 115000, 5: 120000, 6: 125000},
            'lower_bound': {1: 90000, 2: 95000, 3: 100000, 4: 105000, 5: 110000, 6: 115000},
            'upper_bound': {1: 110000, 2: 115000, 3: 120000, 4: 125000, 5: 130000, 6: 135000},
            'children': []
        }
    }
    model.calculated_rows = {
        'gross_profit': {
            'projected': {1: 40000, 2: 42000, 3: 44000, 4: 46000, 5: 48000, 6: 50000},
            'lower_bound': {1: 35000, 2: 37000, 3: 39000, 4: 41000, 5: 43000, 6: 45000},
            'upper_bound': {1: 45000, 2: 47000, 3: 49000, 4: 51000, 5: 53000, 6: 55000}
        },
        'gross_margin_pct': {
            'projected': {1: 0.40, 2: 0.40, 3: 0.40, 4: 0.40, 5: 0.40, 6: 0.40},
            'lower_bound': {1: 0.35, 2: 0.35, 3: 0.35, 4: 0.35, 5: 0.35, 6: 0.35},
            'upper_bound': {1: 0.45, 2: 0.45, 3: 0.45, 4: 0.45, 5: 0.45, 6: 0.45}
        },
        'net_income': {
            'projected': {1: 25000, 2: 26000, 3: 27000, 4: 28000, 5: 29000, 6: 30000},
            'lower_bound': {1: 20000, 2: 21000, 3: 22000, 4: 23000, 5: 24000, 6: 25000},
            'upper_bound': {1: 30000, 2: 31000, 3: 32000, 4: 33000, 5: 34000, 6: 35000}
        }
    }
    return model


@pytest.fixture
def mock_pl_forecast_model_12month():
    """Create PLForecastModel fixture with 12-month horizon."""
    model = Mock()
    model.metadata = {'forecast_horizon': 12}
    model.hierarchy = {
        'Income': {
            'name': 'Revenue',
            'projected': {m: 100000 + m * 5000 for m in range(1, 13)},
            'lower_bound': {m: 90000 + m * 4500 for m in range(1, 13)},
            'upper_bound': {m: 110000 + m * 5500 for m in range(1, 13)},
            'children': []
        }
    }
    model.calculated_rows = {}
    return model


@pytest.fixture
def mock_multi_scenario_2scenarios():
    """Create MultiScenarioForecastResult fixture with 2 scenarios, 12-month horizon."""
    multi_result = Mock()
    multi_result.scenarios = []

    for scenario_name in ['Base', 'Growth']:
        scenario = Mock()
        scenario.metadata = {'forecast_horizon': 12, 'scenario_name': scenario_name}
        scenario.hierarchy = {
            'Income': {
                'name': 'Revenue',
                'projected': {m: 100000 + m * 5000 for m in range(1, 13)},
                'lower_bound': {m: 90000 + m * 4500 for m in range(1, 13)},
                'upper_bound': {m: 110000 + m * 5500 for m in range(1, 13)},
                'children': []
            }
        }
        scenario.calculated_rows = {}
        multi_result.scenarios.append(scenario)

    return multi_result


def test_pl_6month_columns(mock_pl_forecast_model_6month):
    """Test that 6-month horizon generates 7 total columns (Account + 6 months)."""
    # Create writer
    writer = PLForecastReportWriter()
    writer.write(mock_pl_forecast_model_6month)

    # Access the worksheet to check column count
    ws = writer.workbook['P&L Forecast']

    # Check header row has 7 columns (Account + Month 1-6)
    assert ws.cell(row=1, column=1).value == 'Account'
    assert ws.cell(row=1, column=2).value == 'Month 1'
    assert ws.cell(row=1, column=7).value == 'Month 6'
    # Column 8 should be empty (only 7 columns)
    assert ws.cell(row=1, column=8).value is None


def test_pl_12month_columns(mock_pl_forecast_model_12month):
    """Test that 12-month horizon generates 13 total columns (Account + 12 months)."""
    # Create writer
    writer = PLForecastReportWriter()
    writer.write(mock_pl_forecast_model_12month)

    # Access the worksheet to check column count
    ws = writer.workbook['P&L Forecast']

    # Check header row has 13 columns (Account + Month 1-12)
    assert ws.cell(row=1, column=1).value == 'Account'
    assert ws.cell(row=1, column=2).value == 'Month 1'
    assert ws.cell(row=1, column=13).value == 'Month 12'
    # Column 14 should be empty (only 13 columns)
    assert ws.cell(row=1, column=14).value is None


def test_pl_three_row_format(mock_pl_forecast_model_6month):
    """Test that each metric generates three consecutive rows (Lower/Projected/Upper)."""
    # Create writer
    writer = PLForecastReportWriter()
    writer.write(mock_pl_forecast_model_6month)

    # Access the worksheet to check row labels
    ws = writer.workbook['P&L Forecast']

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


def test_pl_projected_bold(mock_pl_forecast_model_6month):
    """Test that Projected row receives bold formatting."""
    # Create writer and patch format_bold method
    writer = PLForecastReportWriter()
    writer.format_bold = Mock()
    writer.write(mock_pl_forecast_model_6month)

    # Check that format_bold was called for Projected rows
    bold_calls = writer.format_bold.call_args_list

    # Should have bold formatting applied (for Projected row labels and values)
    assert len(bold_calls) >= 2, "Projected rows should have bold formatting applied"


def test_pl_multi_scenario_layout(mock_multi_scenario_2scenarios):
    """Test that multi-scenario generates correct column count (Account + 24 month columns)."""
    # Create writer
    writer = PLForecastReportWriter()
    writer.write(mock_multi_scenario_2scenarios)

    # Access the worksheet to check headers
    ws = writer.workbook['P&L Forecast']

    # Check header row: 2 scenarios × 12 months = 24 month columns + 1 Account column = 25 total
    header_values = []
    for col in range(1, 26):
        cell_value = ws.cell(row=1, column=col).value
        if cell_value:
            header_values.append(cell_value)

    assert len(header_values) >= 25, "Should have 25 columns for 2 scenarios with 12-month horizon"

    # Check that scenario names appear in headers
    base_headers = [h for h in header_values if 'Base' in str(h)]
    growth_headers = [h for h in header_values if 'Growth' in str(h)]

    assert len(base_headers) >= 1, "Base scenario should appear in headers"
    assert len(growth_headers) >= 1, "Growth scenario should appear in headers"


def test_pl_summary_rows(mock_pl_forecast_model_6month):
    """Test that Gross Profit and Net Income summary rows appear."""
    # Create writer
    writer = PLForecastReportWriter()
    writer.write(mock_pl_forecast_model_6month)

    # Access the worksheet to check for summary rows
    ws = writer.workbook['P&L Forecast']

    # Collect account names
    gross_profit_rows = []
    net_income_rows = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=1):
        if row[0].value:
            if 'Gross Profit' in str(row[0].value):
                gross_profit_rows.append(row[0].value)
            if 'Net Income' in str(row[0].value):
                net_income_rows.append(row[0].value)

    # Should have 3 rows each (Lower, Projected, Upper)
    assert len(gross_profit_rows) >= 3, "Gross Profit should have three-row format"
    assert len(net_income_rows) >= 3, "Net Income should have three-row format"


@patch.object(BaseExcelWriter, 'format_percentage')
def test_pl_margin_percentage_format(mock_format_pct, mock_pl_forecast_model_6month):
    """Test that margin percentages display as '40.0%' not '0.40'."""
    # Create writer and write model
    writer = PLForecastReportWriter()
    writer.write(mock_pl_forecast_model_6month)

    # Verify format_percentage was called for margin rows
    # Should have percentage formatting for Gross Margin % rows (3 rows: Lower, Projected, Upper)
    percentage_calls = mock_format_pct.call_args_list

    assert len(percentage_calls) >= 3, "Percentage formatting should be applied to margin rows (3 rows: Lower, Projected, Upper)"


def test_pl_currency_formatting(mock_pl_forecast_model_6month):
    """Test that currency formatting is applied to all value columns."""
    # Create writer and patch format_currency method
    writer = PLForecastReportWriter()
    writer.format_currency = Mock()
    writer.write(mock_pl_forecast_model_6month)

    # Check that currency formatting was applied
    currency_calls = writer.format_currency.call_args_list

    assert len(currency_calls) >= 1, "Currency formatting should be applied to value columns"
