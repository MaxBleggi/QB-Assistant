"""
Unit tests for PLForecastWriter.

Tests P&L Forecast sheet generation with hierarchy, confidence intervals,
indentation, and margin rows.
"""
import pytest
import pandas as pd

from src.exporters import PLForecastWriter
from src.models import PLForecastModel


class TestPLForecastWriter:
    """Test suite for PLForecastWriter class."""

    @pytest.fixture
    def sample_pl_forecast_model(self):
        """Create PLForecastModel with nested hierarchy and margins."""
        # Create hierarchy with Income and Expenses sections
        hierarchy = {
            'Income': [
                {
                    'name': 'Income',
                    'projected': {'Jan 2025': 50000.0, 'Feb 2025': 55000.0},
                    'lower_bound': {'Jan 2025': 45000.0, 'Feb 2025': 50000.0},
                    'upper_bound': {'Jan 2025': 55000.0, 'Feb 2025': 60000.0},
                    'children': [
                        {
                            'name': 'Product Sales',
                            'projected': {'Jan 2025': 30000.0, 'Feb 2025': 33000.0},
                            'lower_bound': {'Jan 2025': 27000.0, 'Feb 2025': 30000.0},
                            'upper_bound': {'Jan 2025': 33000.0, 'Feb 2025': 36000.0}
                        },
                        {
                            'name': 'Service Revenue',
                            'projected': {'Jan 2025': 20000.0, 'Feb 2025': 22000.0},
                            'lower_bound': {'Jan 2025': 18000.0, 'Feb 2025': 20000.0},
                            'upper_bound': {'Jan 2025': 22000.0, 'Feb 2025': 24000.0}
                        }
                    ]
                }
            ],
            'Expenses': [
                {
                    'name': 'Expenses',
                    'projected': {'Jan 2025': 30000.0, 'Feb 2025': 32000.0},
                    'lower_bound': {'Jan 2025': 28000.0, 'Feb 2025': 30000.0},
                    'upper_bound': {'Jan 2025': 32000.0, 'Feb 2025': 34000.0},
                    'children': [
                        {
                            'name': 'Operating Expenses',
                            'projected': {'Jan 2025': 30000.0, 'Feb 2025': 32000.0},
                            'lower_bound': {'Jan 2025': 28000.0, 'Feb 2025': 30000.0},
                            'upper_bound': {'Jan 2025': 32000.0, 'Feb 2025': 34000.0}
                        }
                    ]
                }
            ]
        }

        # Create calculated margin rows
        calculated_rows = {
            'gross_profit': {
                'projected': {'Jan 2025': 20000.0, 'Feb 2025': 23000.0},
                'lower_bound': {'Jan 2025': 17000.0, 'Feb 2025': 20000.0},
                'upper_bound': {'Jan 2025': 23000.0, 'Feb 2025': 26000.0}
            },
            'operating_income': {
                'projected': {'Jan 2025': 15000.0, 'Feb 2025': 17000.0},
                'lower_bound': {'Jan 2025': 13000.0, 'Feb 2025': 15000.0},
                'upper_bound': {'Jan 2025': 17000.0, 'Feb 2025': 19000.0}
            },
            'net_income': {
                'projected': {'Jan 2025': 12000.0, 'Feb 2025': 14000.0},
                'lower_bound': {'Jan 2025': 10000.0, 'Feb 2025': 12000.0},
                'upper_bound': {'Jan 2025': 14000.0, 'Feb 2025': 16000.0}
            }
        }

        metadata = {
            'confidence_level': 0.95,
            'forecast_horizon': 2,
            'excluded_periods': [],
            'warnings': []
        }

        return PLForecastModel(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

    def test_pl_forecast_sheet_creation(self, sample_pl_forecast_model):
        """Test PLForecastWriter creates sheet with correct sections."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        # Check sheet exists
        assert 'P&L Forecast' in writer.workbook.sheetnames

        ws = writer.workbook['P&L Forecast']

        # Check header row exists
        assert ws['A1'].value == 'Account'

        # Check Income section exists (row 2 should be "Income" header)
        assert 'Income' in str(ws['A2'].value)

        # Check that there are data rows (Income parent + 2 children)
        assert ws['A3'].value is not None  # Income parent
        assert ws['A4'].value is not None  # Product Sales
        assert ws['A5'].value is not None  # Service Revenue

    def test_pl_forecast_header_columns(self, sample_pl_forecast_model):
        """Test header has Account + 3 columns per period (Projected, Lower, Upper)."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        ws = writer.workbook['P&L Forecast']

        # Should have 7 columns: Account + (Jan: Proj/Lower/Upper) + (Feb: Proj/Lower/Upper)
        assert ws['A1'].value == 'Account'
        assert 'Jan 2025' in str(ws['B1'].value)  # Jan Projected
        assert 'Jan 2025' in str(ws['C1'].value)  # Jan Lower
        assert 'Jan 2025' in str(ws['D1'].value)  # Jan Upper
        assert 'Feb 2025' in str(ws['E1'].value)  # Feb Projected
        assert 'Feb 2025' in str(ws['F1'].value)  # Feb Lower
        assert 'Feb 2025' in str(ws['G1'].value)  # Feb Upper

    def test_pl_forecast_confidence_intervals(self, sample_pl_forecast_model):
        """Test three value columns per period with currency format."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        ws = writer.workbook['P&L Forecast']

        # Find Income parent row (should be row 3)
        income_row = 3

        # Check that three consecutive cells have values and currency format
        # Jan: Projected, Lower, Upper
        assert ws.cell(row=income_row, column=2).value == 50000.0  # Projected
        assert ws.cell(row=income_row, column=3).value == 45000.0  # Lower
        assert ws.cell(row=income_row, column=4).value == 55000.0  # Upper

        # Check currency formatting
        assert ws.cell(row=income_row, column=2).number_format == '$#,##0.00'
        assert ws.cell(row=income_row, column=3).number_format == '$#,##0.00'
        assert ws.cell(row=income_row, column=4).number_format == '$#,##0.00'

    def test_pl_forecast_margins(self, sample_pl_forecast_model):
        """Test margin rows (gross_profit, operating_income, net_income) present."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        ws = writer.workbook['P&L Forecast']

        # Find margin rows (should be near end of sheet)
        # Scan for margin labels
        found_margins = []
        for row in range(1, ws.max_row + 1):
            cell_value = ws.cell(row=row, column=1).value
            if cell_value in ['Gross Profit', 'Operating Income', 'Net Income']:
                found_margins.append(cell_value)

        # All three margins should be present
        assert 'Gross Profit' in found_margins
        assert 'Operating Income' in found_margins
        assert 'Net Income' in found_margins

    def test_pl_forecast_indentation(self, sample_pl_forecast_model):
        """Test child accounts indented relative to parents."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        ws = writer.workbook['P&L Forecast']

        # Income parent (row 3) should have indent level 1
        income_cell = ws.cell(row=3, column=1)
        income_indent = income_cell.alignment.indent if income_cell.alignment else 0

        # Product Sales child (row 4) should have indent level 2
        product_sales_cell = ws.cell(row=4, column=1)
        product_indent = product_sales_cell.alignment.indent if product_sales_cell.alignment else 0

        # Child should be indented more than parent
        assert product_indent > income_indent

    def test_pl_forecast_borders(self, sample_pl_forecast_model):
        """Test table has borders applied."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        ws = writer.workbook['P&L Forecast']

        # Check that header row has borders
        assert ws['A1'].border.top.style == 'thin'
        assert ws['A1'].border.left.style == 'thin'

        # Check that data rows have borders
        assert ws['A2'].border.top.style == 'thin'
        assert ws['B3'].border.top.style == 'thin'

    def test_pl_forecast_all_sections(self, sample_pl_forecast_model):
        """Test Income, Expenses, and Margins all written correctly."""
        writer = PLForecastWriter()
        writer.write(sample_pl_forecast_model)

        ws = writer.workbook['P&L Forecast']

        # Collect all account names
        account_names = []
        for row in range(1, ws.max_row + 1):
            value = ws.cell(row=row, column=1).value
            if value and value != 'Account':
                account_names.append(str(value))

        # Check Income section
        assert 'Income' in account_names
        assert 'Product Sales' in account_names
        assert 'Service Revenue' in account_names

        # Check Expenses section
        assert 'Expenses' in account_names
        assert 'Operating Expenses' in account_names

        # Check Margins
        assert 'Gross Profit' in account_names
        assert 'Operating Income' in account_names
        assert 'Net Income' in account_names
