"""
Unit tests for KPIDashboardWriter.

Tests KPI Dashboard sheet generation with metric extraction, formatting
(percentage vs currency), and table structure.
"""
import pytest
import pandas as pd

from src.exporters import KPIDashboardWriter
from src.models import BalanceSheetModel, CashFlowModel


class TestKPIDashboardWriter:
    """Test suite for KPIDashboardWriter class."""

    @pytest.fixture
    def sample_balance_sheet_model(self):
        """Create minimal BalanceSheetModel with 3 periods."""
        hierarchy = {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {
                                    '2024-01-31': 100000.0,
                                    '2024-02-28': 95000.0,
                                    '2024-03-31': 90000.0
                                }
                            },
                            {
                                'name': 'Accounts Receivable',
                                'values': {
                                    '2024-01-31': 50000.0,
                                    '2024-02-28': 55000.0,
                                    '2024-03-31': 60000.0
                                }
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
                                'values': {
                                    '2024-01-31': 30000.0,
                                    '2024-02-28': 35000.0,
                                    '2024-03-31': 40000.0
                                }
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
        """Create minimal CashFlowModel with 3 periods."""
        hierarchy = {
            'Operating Activities': {
                'children': [
                    {
                        'name': 'Net Income',
                        'values': {
                            '2024-01-31': 10000.0,
                            '2024-02-28': 12000.0,
                            '2024-03-31': 11000.0
                        }
                    },
                    {
                        'name': 'Cash from Operations',
                        'values': {
                            '2024-01-31': -50000.0,
                            '2024-02-28': -45000.0,
                            '2024-03-31': -48000.0
                        }
                    }
                ]
            }
        }

        return CashFlowModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy,
            calculated_rows=[],
            metadata={'report_date': '2024-03-31'}
        )

    def test_kpi_dashboard_sheet_creation(self, sample_balance_sheet_model, sample_cash_flow_model):
        """Test KPIDashboardWriter creates 'KPI Dashboard' sheet with metrics."""
        writer = KPIDashboardWriter()
        writer.write(sample_balance_sheet_model, sample_cash_flow_model)

        # Check sheet exists
        assert 'KPI Dashboard' in writer.workbook.sheetnames

        ws = writer.workbook['KPI Dashboard']

        # Check header row
        assert ws['A1'].value == 'Metric'
        assert ws['B1'].value is not None  # Should have period labels

        # Check metric rows exist
        assert ws['A2'].value == 'Current Ratio'
        assert ws['A3'].value == 'Burn Rate'
        assert ws['A4'].value is not None  # Cash Runway

    def test_kpi_percentage_formatting(self, sample_balance_sheet_model, sample_cash_flow_model):
        """Test Current Ratio formatted as percentage."""
        writer = KPIDashboardWriter()
        writer.write(sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['KPI Dashboard']

        # Check that Current Ratio row has percentage format
        # Current Ratio is in row 2, starting from column B
        assert ws['B2'].number_format == '0.00%'
        assert ws['C2'].number_format == '0.00%'
        assert ws['D2'].number_format == '0.00%'

    def test_kpi_currency_formatting(self, sample_balance_sheet_model, sample_cash_flow_model):
        """Test Burn Rate formatted as currency."""
        writer = KPIDashboardWriter()
        writer.write(sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['KPI Dashboard']

        # Check that Burn Rate row has currency format
        # Burn Rate is in row 3, starting from column B
        assert ws['B3'].number_format == '$#,##0.00'
        assert ws['C3'].number_format == '$#,##0.00'
        assert ws['D3'].number_format == '$#,##0.00'

    def test_kpi_table_dimensions(self, sample_balance_sheet_model, sample_cash_flow_model):
        """Test table has correct dimensions (3 metrics × N periods)."""
        writer = KPIDashboardWriter()
        writer.write(sample_balance_sheet_model, sample_cash_flow_model)

        ws = writer.workbook['KPI Dashboard']

        # Should have 4 rows: 1 header + 3 metrics
        assert ws['A1'].value == 'Metric'
        assert ws['A2'].value == 'Current Ratio'
        assert ws['A3'].value == 'Burn Rate'
        assert ws['A4'].value is not None  # Cash Runway

        # Should have 4 columns: 1 metric name + 3 periods
        assert ws['A1'].value is not None
        assert ws['B1'].value is not None
        assert ws['C1'].value is not None
        assert ws['D1'].value is not None

    def test_kpi_missing_data(self):
        """Test KPI Dashboard handles missing period data gracefully."""
        # Create balance sheet with only 2 periods
        hierarchy_bs = {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {
                                    '2024-01-31': 100000.0,
                                    '2024-02-28': 95000.0
                                }
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
                                'values': {
                                    '2024-01-31': 30000.0,
                                    '2024-02-28': 35000.0
                                }
                            }
                        ]
                    }
                ]
            }
        }

        balance_sheet = BalanceSheetModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy_bs
        )

        hierarchy_cf = {
            'Operating Activities': {
                'children': [
                    {
                        'name': 'Cash from Operations',
                        'values': {
                            '2024-01-31': -50000.0,
                            '2024-02-28': -45000.0
                        }
                    }
                ]
            }
        }

        cash_flow = CashFlowModel(
            df=pd.DataFrame(),
            hierarchy=hierarchy_cf,
            calculated_rows=[],
            metadata={'report_date': '2024-02-28'}
        )

        writer = KPIDashboardWriter()

        # Should not raise error
        writer.write(balance_sheet, cash_flow)

        ws = writer.workbook['KPI Dashboard']

        # Should have 2 period columns (plus metric name column)
        assert ws['A1'].value == 'Metric'
        assert ws['B1'].value is not None
        assert ws['C1'].value is not None
