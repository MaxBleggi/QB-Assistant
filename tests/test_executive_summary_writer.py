"""
Unit tests for ExecutiveSummaryWriter.

Tests Executive Summary sheet generation with revenue metrics, trends,
profitability metrics, and formatting (trend indicators, bold headers, currency/percentage).
"""
import pytest
import pandas as pd

from src.exporters import ExecutiveSummaryWriter
from src.models import PLModel, BalanceSheetModel, CashFlowModel


class TestExecutiveSummaryWriter:
    """Test suite for ExecutiveSummaryWriter class."""

    @pytest.fixture
    def sample_pl_model(self):
        """Create minimal PLModel with 12 periods of revenue/expense data."""
        # Create 12 periods with monthly progression
        periods = [
            '2024-01-31', '2024-02-28', '2024-03-31', '2024-04-30',
            '2024-05-31', '2024-06-30', '2024-07-31', '2024-08-31',
            '2024-09-30', '2024-10-31', '2024-11-30', '2024-12-31'
        ]

        # Revenue progressing from $90k to $110k with 5% MoM growth trend
        revenue_values = {}
        base_revenue = 90000.0
        for i, period in enumerate(periods):
            revenue_values[period] = base_revenue * (1.05 ** i)

        # Add prior year period for YoY comparison
        revenue_values['2024-11-30 (PY)'] = 95000.0  # Previous year same month

        hierarchy = {
            'Income': {
                'children': [
                    {
                        'name': 'Sales Revenue',
                        'values': revenue_values
                    }
                ]
            },
            'Cost of Goods Sold': {
                'children': [
                    {
                        'name': 'COGS',
                        'values': {period: revenue_values[period] * 0.6 for period in periods}
                    }
                ]
            },
            'Expenses': {
                'children': [
                    {
                        'name': 'Operating Expenses',
                        'values': {period: 10000.0 for period in periods}
                    }
                ]
            }
        }

        # Calculate Net Income
        net_income_values = {}
        for period in periods:
            revenue = revenue_values[period]
            cogs = revenue * 0.6
            expenses = 10000.0
            net_income_values[period] = revenue - cogs - expenses

        calculated_rows = [
            {
                'account_name': 'Gross Profit',
                'values': {period: revenue_values[period] * 0.4 for period in periods}
            },
            {
                'account_name': 'Net Income',
                'values': net_income_values
            }
        ]

        return PLModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy,
            calculated_rows=calculated_rows
        )

    @pytest.fixture
    def sample_balance_sheet_model(self):
        """Create minimal BalanceSheetModel with asset/liability data."""
        hierarchy = {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {'2024-12-31': 100000.0}
                            }
                        ]
                    }
                ]
            },
            'Liabilities': {
                'children': [
                    {
                        'name': 'Current Liabilities',
                        'children': [
                            {
                                'name': 'Accounts Payable',
                                'values': {'2024-12-31': 50000.0}
                            }
                        ]
                    }
                ]
            }
        }

        return BalanceSheetModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy
        )

    @pytest.fixture
    def sample_cash_flow_model(self):
        """Create minimal CashFlowModel with cash flow data."""
        hierarchy = {
            'Operating Activities': {
                'children': [
                    {
                        'name': 'Net Income',
                        'values': {'2024-12-31': 25000.0}
                    },
                    {
                        'name': 'Cash from Operations',
                        'values': {'2024-12-31': 30000.0}
                    }
                ]
            }
        }

        return CashFlowModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy,
            calculated_rows=[],
            metadata={'report_date': '2024-12-31'}
        )

    @pytest.fixture
    def single_period_pl_model(self):
        """Create PLModel with only 1 period (no MoM comparison)."""
        hierarchy = {
            'Income': {
                'children': [
                    {
                        'name': 'Sales Revenue',
                        'values': {'2024-01-31': 100000.0}
                    }
                ]
            }
        }

        calculated_rows = [
            {
                'account_name': 'Net Income',
                'values': {'2024-01-31': 20000.0}
            }
        ]

        return PLModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy,
            calculated_rows=calculated_rows
        )

    def test_sheet_creation(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test ExecutiveSummaryWriter creates 'Executive Summary' sheet."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        # Check sheet exists
        assert 'Executive Summary' in writer.workbook.sheetnames

    def test_revenue_with_mom_growth(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test current revenue displayed with MoM growth calculation."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Find Revenue section
        # Expected: Row 1 = "Revenue" (bold header)
        assert ws['A1'].value == 'Revenue'
        assert ws['A1'].font.bold is True

        # Row 2 = Current Period Revenue with currency formatting
        assert 'Revenue' in ws['A2'].value
        assert ws['B2'].value > 0  # Should have revenue value
        assert ws['B2'].number_format == '$#,##0.00'

        # Row 3 = MoM Growth with percentage formatting
        assert 'MoM Growth' in ws['A3'].value
        # MoM growth should be positive (5% trend in fixture)
        assert ws['B3'].value > 0
        assert ws['B3'].number_format == '0.00%'

    def test_gross_margin_display(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test gross margin percentage formatted correctly."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Find Profitability section
        # Should contain "Gross Margin" row
        found_gross_margin = False
        for row in range(1, 20):  # Search first 20 rows
            cell_value = ws[f'A{row}'].value
            if cell_value and 'Gross Margin' in str(cell_value):
                found_gross_margin = True
                # Check percentage formatting
                assert ws[f'B{row}'].number_format == '0.00%'
                break

        assert found_gross_margin, "Gross Margin row not found"

    def test_operating_cash_flow_display(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test operating cash flow with currency formatting."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Find Cash Flow section
        found_cash_flow = False
        for row in range(1, 20):
            cell_value = ws[f'A{row}'].value
            if cell_value and 'Operating Cash Flow' in str(cell_value):
                found_cash_flow = True
                # Check currency formatting
                assert ws[f'B{row}'].number_format == '$#,##0.00'
                break

        assert found_cash_flow, "Operating Cash Flow row not found"

    def test_net_income_with_margin(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test net income displays with margin percentage."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Find Net Income row
        found_net_income = False
        for row in range(1, 20):
            cell_value = ws[f'A{row}'].value
            if cell_value and 'Net Income' in str(cell_value):
                found_net_income = True
                # Check currency formatting
                assert ws[f'B{row}'].number_format == '$#,##0.00'
                # Check margin is in adjacent cell
                margin_text = ws[f'C{row}'].value
                assert margin_text is not None
                assert 'margin' in str(margin_text).lower()
                break

        assert found_net_income, "Net Income row not found"

    def test_section_headers_bold(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test section headers are bold formatted."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Check that section headers (Revenue, Profitability, Cash Flow) are bold
        section_headers = ['Revenue', 'Profitability', 'Cash Flow']
        for header in section_headers:
            found = False
            for row in range(1, 20):
                if ws[f'A{row}'].value == header:
                    assert ws[f'A{row}'].font.bold is True
                    found = True
                    break
            assert found, f"Section header '{header}' not found"

    def test_trend_indicator_positive(self, sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test green upward arrow displayed for positive growth."""
        writer = ExecutiveSummaryWriter()
        writer.write(sample_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Find MoM Growth row (should have positive trend)
        for row in range(1, 20):
            if ws[f'A{row}'].value and 'MoM Growth' in str(ws[f'A{row}'].value):
                # Trend indicator should be in column C
                assert ws[f'C{row}'].value == '▲'
                # Font color should be green (00B050)
                assert ws[f'C{row}'].font.color.rgb == '00B050'
                break

    def test_trend_indicator_negative(self):
        """Test red downward arrow displayed for negative growth."""
        # Create fixture with negative growth
        hierarchy = {
            'Income': {
                'children': [
                    {
                        'name': 'Sales Revenue',
                        'values': {
                            '2024-01-31': 100000.0,
                            '2024-02-28': 95000.0  # 5% decline
                        }
                    }
                ]
            }
        }

        calculated_rows = [
            {
                'account_name': 'Net Income',
                'values': {
                    '2024-01-31': 20000.0,
                    '2024-02-28': 18000.0
                }
            }
        ]

        pl_model = PLModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy,
            calculated_rows=calculated_rows
        )

        # Minimal other models
        balance_sheet = BalanceSheetModel(
            df=pd.DataFrame(),
            hierarchy={'Assets': {'children': []}, 'Liabilities': {'children': []}}
        )
        cash_flow = CashFlowModel(
            df=pd.DataFrame(),
            hierarchy={'Operating Activities': {'children': []}},
            calculated_rows=[],
            metadata={}
        )

        writer = ExecutiveSummaryWriter()
        writer.write(pl_model, balance_sheet, cash_flow)

        ws = writer.workbook['Executive Summary']

        # Find MoM Growth row (should have negative trend)
        for row in range(1, 20):
            if ws[f'A{row}'].value and 'MoM Growth' in str(ws[f'A{row}'].value):
                # Trend indicator should be in column C
                assert ws[f'C{row}'].value == '▼'
                # Font color should be red (C00000) - openpyxl returns ARGB format
                assert ws[f'C{row}'].font.color.rgb == '00C00000'
                break

    def test_trend_indicator_zero(self):
        """Test gray dash displayed for zero/missing growth."""
        # Create fixture with zero growth
        hierarchy = {
            'Income': {
                'children': [
                    {
                        'name': 'Sales Revenue',
                        'values': {
                            '2024-01-31': 100000.0,
                            '2024-02-28': 100000.0  # 0% growth
                        }
                    }
                ]
            }
        }

        calculated_rows = [
            {
                'account_name': 'Net Income',
                'values': {
                    '2024-01-31': 20000.0,
                    '2024-02-28': 20000.0
                }
            }
        ]

        pl_model = PLModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy,
            calculated_rows=calculated_rows
        )

        # Minimal other models
        balance_sheet = BalanceSheetModel(
            df=pd.DataFrame(),
            hierarchy={'Assets': {'children': []}, 'Liabilities': {'children': []}}
        )
        cash_flow = CashFlowModel(
            df=pd.DataFrame(),
            hierarchy={'Operating Activities': {'children': []}},
            calculated_rows=[],
            metadata={}
        )

        writer = ExecutiveSummaryWriter()
        writer.write(pl_model, balance_sheet, cash_flow)

        ws = writer.workbook['Executive Summary']

        # Find MoM Growth row (should have neutral trend)
        for row in range(1, 20):
            if ws[f'A{row}'].value and 'MoM Growth' in str(ws[f'A{row}'].value):
                # Trend indicator should be in column C
                assert ws[f'C{row}'].value == '—'
                # Font color should be gray (808080) - openpyxl returns ARGB format
                assert ws[f'C{row}'].font.color.rgb == '00808080'
                break

    def test_single_period_edge_case(self, single_period_pl_model, sample_balance_sheet_model, sample_cash_flow_model):
        """Test single period with no MoM comparison available."""
        writer = ExecutiveSummaryWriter()
        writer.write(single_period_pl_model, sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['Executive Summary']

        # Should have Revenue section
        assert ws['A1'].value == 'Revenue'

        # Should NOT have MoM Growth row (only 1 period)
        mom_found = False
        for row in range(1, 20):
            if ws[f'A{row}'].value and 'MoM Growth' in str(ws[f'A{row}'].value):
                mom_found = True
                break

        assert not mom_found, "MoM Growth should not be present with single period"
