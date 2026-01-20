"""
Unit tests for LiquidityCalculator.

Tests working capital calculation with various Balance Sheet hierarchy structures.
"""
import pandas as pd
import pytest

from src.models.balance_sheet import BalanceSheetModel
from src.metrics import LiquidityCalculator


class TestWorkingCapital:
    """Test suite for get_working_capital method."""

    @pytest.fixture
    def sample_df(self):
        """Create minimal DataFrame for BalanceSheetModel."""
        return pd.DataFrame([
            {'account_name': 'Assets', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
        ])

    @pytest.fixture
    def single_period_hierarchy(self):
        """Balance sheet hierarchy with current assets and liabilities for single period."""
        return {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {'2024-01-31': 50000.0}
                            },
                            {
                                'name': 'Accounts Receivable',
                                'values': {'2024-01-31': 100000.0}
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
                                'values': {'2024-01-31': 50000.0}
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def nested_current_hierarchy(self):
        """Balance sheet hierarchy with nested current asset accounts."""
        return {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {'2024-01-31': 50000.0}
                            },
                            {
                                'name': 'Receivables',
                                'parent': True,
                                'children': [
                                    {
                                        'name': 'Accounts Receivable',
                                        'values': {'2024-01-31': 75000.0}
                                    },
                                    {
                                        'name': 'Notes Receivable',
                                        'values': {'2024-01-31': 25000.0}
                                    }
                                ]
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
                                'values': {'2024-01-31': 50000.0}
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def multiple_periods_hierarchy(self):
        """Balance sheet hierarchy with multiple periods."""
        return {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {'2024-01-31': 50000.0, '2024-02-28': 55000.0}
                            },
                            {
                                'name': 'Accounts Receivable',
                                'values': {'2024-01-31': 100000.0, '2024-02-28': 105000.0}
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
                                'values': {'2024-01-31': 50000.0, '2024-02-28': 55000.0}
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def with_noncurrent_hierarchy(self):
        """Balance sheet hierarchy with both current and non-current assets/liabilities."""
        return {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {'2024-01-31': 50000.0}
                            }
                        ]
                    },
                    {
                        'name': 'Fixed Assets',
                        'children': [
                            {
                                'name': 'Property',
                                'values': {'2024-01-31': 200000.0}
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
                                'values': {'2024-01-31': 30000.0}
                            }
                        ]
                    },
                    {
                        'name': 'Long-term Liabilities',
                        'children': [
                            {
                                'name': 'Mortgage Payable',
                                'values': {'2024-01-31': 150000.0}
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def negative_working_capital_hierarchy(self):
        """Balance sheet hierarchy where current liabilities exceed current assets."""
        return {
            'Assets': {
                'children': [
                    {
                        'name': 'Current Assets',
                        'children': [
                            {
                                'name': 'Cash',
                                'values': {'2024-01-31': 30000.0}
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
                                'values': {'2024-01-31': 50000.0}
                            }
                        ]
                    }
                ]
            }
        }

    def test_working_capital_single_period(self, sample_df, single_period_hierarchy):
        """
        Given: BalanceSheetModel with Current Assets=$150,000 and Current Liabilities=$50,000 for '2024-01-31'
        When: get_working_capital() is called
        Then: returns {'2024-01-31': 100000.0}
        """
        model = BalanceSheetModel(df=sample_df, hierarchy=single_period_hierarchy)
        calculator = LiquidityCalculator(model)

        result = calculator.get_working_capital()

        assert result['2024-01-31'] == 100000.0

    def test_working_capital_nested_hierarchy(self, sample_df, nested_current_hierarchy):
        """
        Given: BalanceSheetModel with nested accounts under Current Assets and Current Liabilities
        When: get_working_capital() is called
        Then: sums only leaf nodes under these parent sections, skipping intermediate parents
        """
        model = BalanceSheetModel(df=sample_df, hierarchy=nested_current_hierarchy)
        calculator = LiquidityCalculator(model)

        result = calculator.get_working_capital()

        # Current Assets: 50000 (Cash) + 75000 (AR) + 25000 (Notes) = 150000
        # Current Liabilities: 50000 (AP)
        # Working Capital: 150000 - 50000 = 100000
        assert result['2024-01-31'] == 100000.0

    def test_working_capital_multiple_periods(self, sample_df, multiple_periods_hierarchy):
        """
        Given: BalanceSheetModel with multiple periods
        When: get_working_capital() is called
        Then: returns working capital for all periods in Dict[str, float] format
        """
        model = BalanceSheetModel(df=sample_df, hierarchy=multiple_periods_hierarchy)
        calculator = LiquidityCalculator(model)

        result = calculator.get_working_capital()

        assert '2024-01-31' in result
        assert '2024-02-28' in result
        assert result['2024-01-31'] == 100000.0  # (50000 + 100000) - 50000
        assert result['2024-02-28'] == 105000.0  # (55000 + 105000) - 55000

    def test_working_capital_excludes_noncurrent(self, sample_df, with_noncurrent_hierarchy):
        """
        Given: BalanceSheetModel with non-current assets and liabilities present
        When: get_working_capital() is called
        Then: validates that non-current assets are excluded from calculation
        """
        model = BalanceSheetModel(df=sample_df, hierarchy=with_noncurrent_hierarchy)
        calculator = LiquidityCalculator(model)

        result = calculator.get_working_capital()

        # Should only use Current Assets (50000) and Current Liabilities (30000)
        # Should NOT include Fixed Assets (200000) or Long-term Liabilities (150000)
        assert result['2024-01-31'] == 20000.0  # 50000 - 30000

    def test_working_capital_negative(self, sample_df, negative_working_capital_hierarchy):
        """
        Given: BalanceSheetModel where current liabilities exceed current assets
        When: get_working_capital() is called
        Then: validates correct negative result when current liabilities exceed current assets
        """
        model = BalanceSheetModel(df=sample_df, hierarchy=negative_working_capital_hierarchy)
        calculator = LiquidityCalculator(model)

        result = calculator.get_working_capital()

        assert result['2024-01-31'] == -20000.0  # 30000 - 50000
