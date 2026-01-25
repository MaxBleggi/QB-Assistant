"""
Unit tests for BudgetVarianceReportWriter.

Tests variance highlighting logic, four-column layout, subtotal inclusion,
and edge cases for variance threshold boundaries.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.exporters.budget_variance_writer import BudgetVarianceReportWriter
from src.exporters.base_writer import BaseExcelWriter


@pytest.fixture
def mock_variance_model_unfavorable_high():
    """Create VarianceModel fixture with 15% unfavorable variance (should be red)."""
    model = Mock()
    model.hierarchy = {
        'Income': {
            'name': 'Revenue',
            'values': {
                'Jan 2024': {
                    'budget_value': 100000,
                    'actual_value': 85000,
                    'dollar_variance': -15000,
                    'pct_variance': -0.15,  # -15%
                    'is_favorable': False,
                    'is_flagged': True
                }
            },
            'children': []
        }
    }
    model.calculated_rows = []
    return model


@pytest.fixture
def mock_variance_model_unfavorable_moderate():
    """Create VarianceModel fixture with 7% unfavorable variance (should be yellow)."""
    model = Mock()
    model.hierarchy = {
        'Expenses': {
            'name': 'Operating Expenses',
            'values': {
                'Jan 2024': {
                    'budget_value': 50000,
                    'actual_value': 53500,
                    'dollar_variance': 3500,
                    'pct_variance': 0.07,  # 7%
                    'is_favorable': False,
                    'is_flagged': True
                }
            },
            'children': []
        }
    }
    model.calculated_rows = []
    return model


@pytest.fixture
def mock_variance_model_favorable():
    """Create VarianceModel fixture with 12% favorable variance (no highlighting)."""
    model = Mock()
    model.hierarchy = {
        'Income': {
            'name': 'Revenue',
            'values': {
                'Jan 2024': {
                    'budget_value': 100000,
                    'actual_value': 112000,
                    'dollar_variance': 12000,
                    'pct_variance': 0.12,  # 12%
                    'is_favorable': True,
                    'is_flagged': True
                }
            },
            'children': []
        }
    }
    model.calculated_rows = []
    return model


@pytest.fixture
def mock_variance_model_edge_10pct():
    """Create VarianceModel fixture with exactly 10.0% unfavorable variance."""
    model = Mock()
    model.hierarchy = {
        'Expenses': {
            'name': 'Cost of Goods Sold',
            'values': {
                'Jan 2024': {
                    'budget_value': 60000,
                    'actual_value': 66000,
                    'dollar_variance': 6000,
                    'pct_variance': 0.10,  # Exactly 10%
                    'is_favorable': False,
                    'is_flagged': True
                }
            },
            'children': []
        }
    }
    model.calculated_rows = []
    return model


@pytest.fixture
def mock_variance_model_with_subtotals():
    """Create VarianceModel fixture with calculated_rows subtotals."""
    model = Mock()
    model.hierarchy = {
        'Income': {
            'name': 'Revenue',
            'values': {
                'Jan 2024': {
                    'budget_value': 100000,
                    'actual_value': 95000,
                    'dollar_variance': -5000,
                    'pct_variance': -0.05,
                    'is_favorable': False,
                    'is_flagged': True
                }
            },
            'children': []
        }
    }
    model.calculated_rows = [
        {
            'account_name': 'Total Revenue',
            'values': {
                'Jan 2024': {
                    'budget_value': 100000,
                    'actual_value': 95000,
                    'dollar_variance': -5000,
                    'pct_variance': -0.05,
                    'is_favorable': False,
                    'is_flagged': True
                }
            }
        },
        {
            'account_name': 'Total Expenses',
            'values': {
                'Jan 2024': {
                    'budget_value': 60000,
                    'actual_value': 58000,
                    'dollar_variance': -2000,
                    'pct_variance': -0.033,
                    'is_favorable': True,
                    'is_flagged': False
                }
            }
        },
        {
            'account_name': 'Net Income',
            'values': {
                'Jan 2024': {
                    'budget_value': 40000,
                    'actual_value': 37000,
                    'dollar_variance': -3000,
                    'pct_variance': -0.075,
                    'is_favorable': False,
                    'is_flagged': True
                }
            }
        }
    ]
    return model


@patch.object(BaseExcelWriter, 'apply_conditional_highlight')
def test_budget_variance_red_highlighting(mock_highlight, mock_variance_model_unfavorable_high):
    """Test that unfavorable variance >10% receives red highlighting."""
    # Create writer and write variance model
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_unfavorable_high)

    # Verify mock_highlight was called with red color (FFC7CE)
    # Should be called twice: once for D column (dollar variance) and once for E column (pct variance)
    assert len(mock_highlight.call_args_list) >= 1, "Red highlighting should be applied for >10% unfavorable variance"

    # Check that red color code appears in the calls
    calls = [c for c in mock_highlight.call_args_list
             if 'FFC7CE' in str(c)]
    assert len(calls) >= 1, "Red highlighting (FFC7CE) should be applied"


@patch.object(BaseExcelWriter, 'apply_conditional_highlight')
def test_budget_variance_yellow_highlighting(mock_highlight, mock_variance_model_unfavorable_moderate):
    """Test that unfavorable variance 5-10% receives yellow highlighting."""
    # Create writer and write variance model
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_unfavorable_moderate)

    # Verify mock_highlight was called with yellow color (FFE699)
    assert len(mock_highlight.call_args_list) >= 1, "Yellow highlighting should be applied for 5-10% unfavorable variance"

    # Check that yellow color code appears in the calls
    calls = [c for c in mock_highlight.call_args_list
             if 'FFE699' in str(c)]
    assert len(calls) >= 1, "Yellow highlighting (FFE699) should be applied"


@patch.object(BaseExcelWriter, 'apply_conditional_highlight')
def test_budget_variance_favorable_no_highlight(mock_highlight, mock_variance_model_favorable):
    """Test that favorable variances are not highlighted."""
    # Create writer and write variance model
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_favorable)

    # No highlighting should be applied for favorable variance
    assert mock_highlight.call_count == 0, \
        "No highlighting should be applied for favorable variance"


@patch.object(BaseExcelWriter, 'apply_conditional_highlight')
def test_budget_variance_edge_10pct(mock_highlight, mock_variance_model_edge_10pct):
    """Test edge case: exactly 10.0% unfavorable variance (should not be red)."""
    # Create writer and write variance model
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_edge_10pct)

    # Verify mock_highlight was called
    assert len(mock_highlight.call_args_list) >= 1, "Highlighting should be applied at 10%"

    # 10% exactly should NOT trigger red (>10% is exclusive)
    # Should trigger yellow (>=5%)
    red_calls = [c for c in mock_highlight.call_args_list
                 if 'FFC7CE' in str(c)]
    yellow_calls = [c for c in mock_highlight.call_args_list
                    if 'FFE699' in str(c)]

    assert len(red_calls) == 0, "Red highlighting should not apply at exactly 10%"
    assert len(yellow_calls) >= 1, "Yellow highlighting should apply at 10%"


def test_budget_variance_subtotals(mock_variance_model_with_subtotals):
    """Test that subtotal rows appear for Revenue, Expenses, Net Income sections."""
    # Create writer
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_with_subtotals)

    # Check that cells were written for subtotals
    # Access the worksheet to verify subtotal rows were written
    ws = writer.workbook['Budget vs Actual']

    # Verify that calculated_rows is not empty
    assert len(mock_variance_model_with_subtotals.calculated_rows) == 3, "Fixture should have 3 calculated rows"

    # Count all data rows (header is row 1, data starts row 2)
    # Expected: 1 header + 1 hierarchy row + 3 calculated rows = 5 total rows
    # So ws.max_row should be 5, meaning 4 data rows
    data_row_count = ws.max_row - 1

    # Should have 1 hierarchy row + 3 calculated rows = 4 data rows minimum
    assert data_row_count >= 4, f"Expected 4+ data rows (1 hierarchy + 3 calculated), got {data_row_count}"


def test_budget_variance_four_column_layout(mock_variance_model_unfavorable_high):
    """Test that four-column layout (Budget, Actual, Variance $, Variance %) is created."""
    # Create writer
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_unfavorable_high)

    # Access the worksheet to check headers
    ws = writer.workbook['Budget vs Actual']

    # Check that header row has 5 columns (Account, Budget, Actual, Variance $, Variance %)
    assert ws.cell(row=1, column=1).value == 'Account'
    assert ws.cell(row=1, column=2).value == 'Budget'
    assert ws.cell(row=1, column=3).value == 'Actual'
    assert ws.cell(row=1, column=4).value == 'Variance ($)'
    assert ws.cell(row=1, column=5).value == 'Variance (%)'


@patch.object(BaseExcelWriter, 'format_percentage')
def test_budget_variance_percentage_format(mock_format_pct, mock_variance_model_unfavorable_high):
    """Test that variance percentages are formatted with % symbol and 1 decimal place."""
    # Create writer and write variance model
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_unfavorable_high)

    # Verify format_percentage was called for percentage column
    assert len(mock_format_pct.call_args_list) >= 1, "Percentage formatting should be applied to Variance % column"

    # Check that percentage formatting was applied to column E
    percentage_calls = [c for c in mock_format_pct.call_args_list
                        if 'E' in str(c)]

    assert len(percentage_calls) >= 1, "Percentage formatting should be applied to column E (Variance %)"


@patch.object(BaseExcelWriter, 'format_currency')
def test_budget_variance_dollar_format(mock_format_currency, mock_variance_model_unfavorable_high):
    """Test that dollar amounts are formatted with $ symbol and thousand separators."""
    # Create writer and write variance model
    writer = BudgetVarianceReportWriter()
    writer.write(mock_variance_model_unfavorable_high)

    # Verify format_currency was called
    # Should have 3 calls: one for column B (Budget), one for C (Actual), one for D (Variance $)
    currency_calls = mock_format_currency.call_args_list

    # Should have formatting for Budget (B), Actual (C), and Variance $ (D) columns
    assert len(currency_calls) >= 3, "Currency formatting should be applied to Budget, Actual, and Variance $ columns"
