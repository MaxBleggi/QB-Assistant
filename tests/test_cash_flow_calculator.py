"""
Unit tests for CashFlowCalculator.

Tests operating cash flow calculation, cash balance change tracking,
free cash flow computation, and trend analysis.
"""
import pandas as pd
import pytest

from src.models.cash_flow_model import CashFlowModel
from src.metrics import CashFlowCalculator


class TestOperatingCashFlow:
    """Test suite for get_operating_cash_flow method."""

    @pytest.fixture
    def sample_df(self):
        """Create minimal DataFrame for CashFlowModel."""
        return pd.DataFrame([
            {'account_name': 'OPERATING ACTIVITIES', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
        ])

    @pytest.fixture
    def single_period_hierarchy(self):
        """Operating activities hierarchy with single period."""
        return {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {'2024-01': 50000.0}
                }
            ]
        }

    @pytest.fixture
    def multiple_periods_hierarchy(self):
        """Operating activities hierarchy with multiple periods."""
        return {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {'2024-01': 50000.0, '2024-02': 55000.0}
                }
            ]
        }

    @pytest.fixture
    def nested_hierarchy(self):
        """Operating activities hierarchy with nested structure."""
        return {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {'2024-01': 30000.0}
                },
                {
                    'name': 'Adjustments',
                    'parent': True,
                    'children': [
                        {
                            'name': 'Depreciation',
                            'values': {'2024-01': 15000.0}
                        },
                        {
                            'name': 'Changes in Working Capital',
                            'parent': True,
                            'children': [
                                {
                                    'name': 'Accounts Receivable',
                                    'values': {'2024-01': 5000.0}
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def test_operating_cash_flow_single_period(self, sample_df, single_period_hierarchy):
        """
        Given: CashFlowModel with operating activities totaling $50,000 for '2024-01'
        When: get_operating_cash_flow() is called
        Then: returns {'2024-01': 50000.0}
        """
        model = CashFlowModel(df=sample_df, hierarchy=single_period_hierarchy,
                             calculated_rows=[], metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_operating_cash_flow()

        assert result['2024-01'] == 50000.0

    def test_operating_cash_flow_nested_hierarchy(self, sample_df, nested_hierarchy):
        """
        Given: CashFlowModel with nested operating activities hierarchy
        When: get_operating_cash_flow() is called
        Then: sums only leaf nodes, skipping parent totals
        """
        model = CashFlowModel(df=sample_df, hierarchy=nested_hierarchy,
                             calculated_rows=[], metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_operating_cash_flow()

        # Should sum: 30000 (Net Income) + 15000 (Depreciation) + 5000 (AR) = 50000
        assert result['2024-01'] == 50000.0

    def test_operating_cash_flow_multiple_periods(self, sample_df, multiple_periods_hierarchy):
        """
        Given: CashFlowModel with multiple periods
        When: get_operating_cash_flow() is called
        Then: returns all periods in Dict[str, float] format
        """
        model = CashFlowModel(df=sample_df, hierarchy=multiple_periods_hierarchy,
                             calculated_rows=[], metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_operating_cash_flow()

        assert '2024-01' in result
        assert '2024-02' in result
        assert result['2024-01'] == 50000.0
        assert result['2024-02'] == 55000.0


class TestCashBalanceChange:
    """Test suite for get_cash_balance_change method."""

    @pytest.fixture
    def sample_df(self):
        """Create minimal DataFrame for CashFlowModel."""
        return pd.DataFrame([
            {'account_name': 'OPERATING ACTIVITIES', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
        ])

    @pytest.fixture
    def complete_cash_position(self):
        """Calculated rows with complete cash position data."""
        return [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-01': 100000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01': 120000.0}
            }
        ]

    @pytest.fixture
    def missing_beginning_cash(self):
        """Calculated rows with missing beginning cash."""
        return [
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01': 120000.0}
            }
        ]

    @pytest.fixture
    def mixed_availability(self):
        """Calculated rows with mixed period availability."""
        return [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-01': 100000.0, '2024-02': 120000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01': 120000.0}  # 2024-02 missing
            }
        ]

    def test_cash_balance_change_complete_data(self, sample_df, complete_cash_position):
        """
        Given: CashFlowModel with beginning_cash=100000, ending_cash=120000 for '2024-01'
        When: get_cash_balance_change() is called
        Then: returns {'2024-01': 20000.0}
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=complete_cash_position, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_change()

        assert result['2024-01'] == 20000.0

    def test_cash_balance_change_missing_beginning(self, sample_df, missing_beginning_cash):
        """
        Given: CashFlowModel with beginning_cash=None for a period
        When: get_cash_balance_change() is called
        Then: skips that period (not in returned dict)
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=missing_beginning_cash, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_change()

        assert '2024-01' not in result

    def test_cash_balance_change_mixed_availability(self, sample_df, mixed_availability):
        """
        Given: CashFlowModel with multiple periods, some complete and some with None values
        When: get_cash_balance_change() is called
        Then: returns only periods with both beginning and ending cash values
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=mixed_availability, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_change()

        assert '2024-01' in result
        assert result['2024-01'] == 20000.0
        assert '2024-02' not in result


class TestFreeCashFlow:
    """Test suite for get_free_cash_flow method."""

    @pytest.fixture
    def sample_df(self):
        """Create minimal DataFrame for CashFlowModel."""
        return pd.DataFrame([
            {'account_name': 'OPERATING ACTIVITIES', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
        ])

    @pytest.fixture
    def hierarchy_with_capex(self):
        """Hierarchy with operating activities and identifiable capex."""
        return {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {'2024-01': 100000.0}
                }
            ],
            'INVESTING ACTIVITIES': [
                {
                    'name': 'Purchase of Equipment',
                    'values': {'2024-01': -30000.0}
                }
            ]
        }

    @pytest.fixture
    def hierarchy_no_capex(self):
        """Hierarchy with operating activities but no identifiable capex."""
        return {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {'2024-01': 100000.0}
                }
            ],
            'INVESTING ACTIVITIES': [
                {
                    'name': 'Sale of Investments',
                    'values': {'2024-01': 50000.0}
                }
            ]
        }

    @pytest.fixture
    def hierarchy_mixed_capex(self):
        """Hierarchy with capex for some periods but not others."""
        return {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {'2024-01': 100000.0, '2024-02': 110000.0}
                }
            ],
            'INVESTING ACTIVITIES': [
                {
                    'name': 'Capital Expenditure',
                    'values': {'2024-01': -30000.0}
                }
            ]
        }

    def test_free_cash_flow_with_capex(self, sample_df, hierarchy_with_capex):
        """
        Given: CashFlowModel with operating cash flow=$100,000 and identifiable capex=$30,000 for '2024-01'
        When: get_free_cash_flow() is called
        Then: returns {'2024-01': 70000.0}
        """
        model = CashFlowModel(df=sample_df, hierarchy=hierarchy_with_capex,
                             calculated_rows=[], metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_free_cash_flow()

        assert result['2024-01'] == 70000.0

    def test_free_cash_flow_no_capex(self, sample_df, hierarchy_no_capex):
        """
        Given: CashFlowModel with operating cash flow but no identifiable capex for a period
        When: get_free_cash_flow() is called
        Then: returns {'period': None} for that period
        """
        model = CashFlowModel(df=sample_df, hierarchy=hierarchy_no_capex,
                             calculated_rows=[], metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_free_cash_flow()

        assert result['2024-01'] is None

    def test_free_cash_flow_mixed_capex_availability(self, sample_df, hierarchy_mixed_capex):
        """
        Given: CashFlowModel with multiple periods, some with capex and some without
        When: get_free_cash_flow() is called
        Then: returns calculated free cash flow where capex exists, None where it doesn't
        """
        model = CashFlowModel(df=sample_df, hierarchy=hierarchy_mixed_capex,
                             calculated_rows=[], metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_free_cash_flow()

        assert result['2024-01'] == 70000.0
        assert result['2024-02'] is None


class TestCashBalanceTrend:
    """Test suite for get_cash_balance_trend method."""

    @pytest.fixture
    def sample_df(self):
        """Create minimal DataFrame for CashFlowModel."""
        return pd.DataFrame([
            {'account_name': 'OPERATING ACTIVITIES', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
        ])

    @pytest.fixture
    def positive_change_rows(self):
        """Calculated rows with positive cash balance change."""
        return [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-01': 100000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01': 120000.0}
            }
        ]

    @pytest.fixture
    def negative_change_rows(self):
        """Calculated rows with negative cash balance change."""
        return [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-02': 120000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-02': 115000.0}
            }
        ]

    @pytest.fixture
    def zero_change_rows(self):
        """Calculated rows with zero cash balance change."""
        return [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-03': 115000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-03': 115000.0}
            }
        ]

    @pytest.fixture
    def missing_periods_rows(self):
        """Calculated rows with some missing cash position data."""
        return [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-01': 100000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01': 120000.0, '2024-02': 125000.0}
            }
        ]

    def test_cash_balance_trend_increase(self, sample_df, positive_change_rows):
        """
        Given: Cash balance change of $20,000 for '2024-01'
        When: get_cash_balance_trend() is called
        Then: returns {'2024-01': {'change': 20000.0, 'direction': 'increase'}}
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=positive_change_rows, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_trend()

        assert '2024-01' in result
        assert result['2024-01']['change'] == 20000.0
        assert result['2024-01']['direction'] == 'increase'

    def test_cash_balance_trend_decrease(self, sample_df, negative_change_rows):
        """
        Given: Cash balance change of -$5,000 for '2024-02'
        When: get_cash_balance_trend() is called
        Then: returns {'2024-02': {'change': -5000.0, 'direction': 'decrease'}}
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=negative_change_rows, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_trend()

        assert '2024-02' in result
        assert result['2024-02']['change'] == -5000.0
        assert result['2024-02']['direction'] == 'decrease'

    def test_cash_balance_trend_stable(self, sample_df, zero_change_rows):
        """
        Given: Cash balance change of $0 for '2024-03'
        When: get_cash_balance_trend() is called
        Then: returns {'2024-03': {'change': 0.0, 'direction': 'stable'}}
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=zero_change_rows, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_trend()

        assert '2024-03' in result
        assert result['2024-03']['change'] == 0.0
        assert result['2024-03']['direction'] == 'stable'

    def test_cash_balance_trend_missing_periods(self, sample_df, missing_periods_rows):
        """
        Given: Multiple periods with some having missing cash position data
        When: get_cash_balance_trend() is called
        Then: returns only periods where cash balance change is calculable
        """
        model = CashFlowModel(df=sample_df, hierarchy={},
                             calculated_rows=missing_periods_rows, metadata={})
        calculator = CashFlowCalculator(model)

        result = calculator.get_cash_balance_trend()

        assert '2024-01' in result
        assert '2024-02' not in result
