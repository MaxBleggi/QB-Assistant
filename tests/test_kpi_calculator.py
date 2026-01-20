"""
Unit tests for KPICalculator.

Tests current ratio calculation, burn rate computation, and cash runway metrics
with various edge cases and scenarios.
"""
import pandas as pd
import pytest

from src.models.balance_sheet import BalanceSheetModel
from src.models.cash_flow_model import CashFlowModel
from src.metrics import KPICalculator
from src.metrics.exceptions import ZeroDivisionError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_bs_df():
    """Create minimal DataFrame for BalanceSheetModel."""
    return pd.DataFrame([
        {'account_name': 'Assets', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
    ])


@pytest.fixture
def sample_cf_df():
    """Create minimal DataFrame for CashFlowModel."""
    return pd.DataFrame([
        {'account_name': 'OPERATING ACTIVITIES', 'raw_value': '', 'numeric_value': None, 'row_type': 'section'}
    ])


@pytest.fixture
def balance_sheet_normal(sample_bs_df):
    """
    Balance sheet with current assets=50000, current liabilities=25000 for 3 periods.

    Provides normal operating scenario with healthy current ratio (2.0).
    """
    hierarchy = {
        'Assets': {
            'children': [
                {
                    'name': 'Current Assets',
                    'children': [
                        {
                            'name': 'Cash',
                            'values': {
                                '2024-01-31': 20000.0,
                                '2024-02-28': 18000.0,
                                '2024-03-31': 15000.0
                            }
                        },
                        {
                            'name': 'Accounts Receivable',
                            'values': {
                                '2024-01-31': 30000.0,
                                '2024-02-28': 32000.0,
                                '2024-03-31': 35000.0
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
                                '2024-01-31': 25000.0,
                                '2024-02-28': 25000.0,
                                '2024-03-31': 25000.0
                            }
                        }
                    ]
                }
            ]
        }
    }
    return BalanceSheetModel(df=sample_bs_df, hierarchy=hierarchy)


@pytest.fixture
def balance_sheet_zero_liabilities(sample_bs_df):
    """
    Balance sheet with current liabilities=0 for single period.

    Edge case for testing zero denominator handling.
    """
    hierarchy = {
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
                }
            ]
        },
        'Liabilities': {
            'children': [
                {
                    'name': 'Current Liabilities',
                    'children': []  # No current liabilities
                }
            ]
        }
    }
    return BalanceSheetModel(df=sample_bs_df, hierarchy=hierarchy)


@pytest.fixture
def cash_flow_normal(sample_cf_df):
    """
    Cash flow with negative cash changes [-5000, -3000, -4000] over 3 periods.

    Simulates normal burn scenario with varying monthly decreases.
    """
    hierarchy = {
        'OPERATING ACTIVITIES': [
            {
                'name': 'Net Income',
                'values': {
                    '2024-01-31': -5000.0,
                    '2024-02-28': -3000.0,
                    '2024-03-31': -4000.0
                }
            }
        ]
    }
    calculated_rows = [
        {
            'account_name': 'Cash at beginning of period',
            'values': {
                '2024-01-31': 25000.0,
                '2024-02-28': 20000.0,
                '2024-03-31': 17000.0
            }
        },
        {
            'account_name': 'CASH AT END OF PERIOD',
            'values': {
                '2024-01-31': 20000.0,
                '2024-02-28': 17000.0,
                '2024-03-31': 13000.0
            }
        }
    ]
    return CashFlowModel(df=sample_cf_df, hierarchy=hierarchy,
                        calculated_rows=calculated_rows, metadata={})


@pytest.fixture
def cash_flow_positive(sample_cf_df):
    """
    Cash flow with positive cash changes [+2000, +1000] (profitability scenario).

    Tests burn rate when company is growing cash, not burning it.
    """
    hierarchy = {
        'OPERATING ACTIVITIES': [
            {
                'name': 'Net Income',
                'values': {
                    '2024-01-31': 2000.0,
                    '2024-02-28': 1000.0
                }
            }
        ]
    }
    calculated_rows = [
        {
            'account_name': 'Cash at beginning of period',
            'values': {
                '2024-01-31': 10000.0,
                '2024-02-28': 12000.0
            }
        },
        {
            'account_name': 'CASH AT END OF PERIOD',
            'values': {
                '2024-01-31': 12000.0,
                '2024-02-28': 13000.0
            }
        }
    ]
    return CashFlowModel(df=sample_cf_df, hierarchy=hierarchy,
                        calculated_rows=calculated_rows, metadata={})


@pytest.fixture
def cash_flow_single_period(sample_cf_df):
    """
    Cash flow with only 1 period of data.

    Tests edge case where averaging window exceeds available data.
    """
    hierarchy = {
        'OPERATING ACTIVITIES': [
            {
                'name': 'Net Income',
                'values': {'2024-01-31': -5000.0}
            }
        ]
    }
    calculated_rows = [
        {
            'account_name': 'Cash at beginning of period',
            'values': {'2024-01-31': 20000.0}
        },
        {
            'account_name': 'CASH AT END OF PERIOD',
            'values': {'2024-01-31': 15000.0}
        }
    ]
    return CashFlowModel(df=sample_cf_df, hierarchy=hierarchy,
                        calculated_rows=calculated_rows, metadata={})


@pytest.fixture
def cash_flow_mixed_changes(sample_cf_df):
    """
    Cash flow with mixed positive and negative changes [-5000, +2000, -3000].

    Tests that burn rate only includes negative changes.
    """
    hierarchy = {
        'OPERATING ACTIVITIES': [
            {
                'name': 'Net Income',
                'values': {
                    '2024-01-31': -5000.0,
                    '2024-02-28': 2000.0,
                    '2024-03-31': -3000.0
                }
            }
        ]
    }
    calculated_rows = [
        {
            'account_name': 'Cash at beginning of period',
            'values': {
                '2024-01-31': 20000.0,
                '2024-02-28': 15000.0,
                '2024-03-31': 17000.0
            }
        },
        {
            'account_name': 'CASH AT END OF PERIOD',
            'values': {
                '2024-01-31': 15000.0,
                '2024-02-28': 17000.0,
                '2024-03-31': 14000.0
            }
        }
    ]
    return CashFlowModel(df=sample_cf_df, hierarchy=hierarchy,
                        calculated_rows=calculated_rows, metadata={})


# ============================================================================
# TESTS - CURRENT RATIO
# ============================================================================

class TestCurrentRatio:
    """Test suite for current_ratio method."""

    def test_current_ratio_normal_calculation(self, balance_sheet_normal, cash_flow_normal):
        """
        Given: Balance sheet with current assets=50000, current liabilities=25000
        When: current_ratio() is called
        Then: Returns ratio of 2.0 for each period
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_normal)

        result = calculator.current_ratio()

        # Assets: 20000 + 30000 = 50000; Liabilities: 25000; Ratio: 2.0
        assert result['2024-01-31'] == 2.0
        # Assets: 18000 + 32000 = 50000; Liabilities: 25000; Ratio: 2.0
        assert result['2024-02-28'] == 2.0
        # Assets: 15000 + 35000 = 50000; Liabilities: 25000; Ratio: 2.0
        assert result['2024-03-31'] == 2.0

    def test_current_ratio_zero_liabilities(self, balance_sheet_zero_liabilities, cash_flow_normal):
        """
        Given: Balance sheet with current liabilities=0
        When: current_ratio() is called
        Then: Raises ZeroDivisionError with message containing 'current liabilities'
        """
        calculator = KPICalculator(balance_sheet_zero_liabilities, cash_flow_normal)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.current_ratio()

        # Verify exception message contains key information
        assert 'current liabilities' in str(exc_info.value).lower()
        assert '2024-01-31' in str(exc_info.value)

    def test_current_ratio_multiple_periods(self, balance_sheet_normal, cash_flow_normal):
        """
        Given: Balance sheet with 3 periods
        When: current_ratio() is called
        Then: Returns dict with 3 entries, one per period
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_normal)

        result = calculator.current_ratio()

        assert len(result) == 3
        assert '2024-01-31' in result
        assert '2024-02-28' in result
        assert '2024-03-31' in result


# ============================================================================
# TESTS - BURN RATE
# ============================================================================

class TestBurnRate:
    """Test suite for burn_rate method."""

    def test_burn_rate_normal_calculation(self, balance_sheet_normal, cash_flow_normal):
        """
        Given: Cash flow with changes [-5000, -3000, -4000] for 3 months
        When: burn_rate(periods=3) is called
        Then: Returns rolling average burn rate (mean of absolute values)
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_normal)

        result = calculator.burn_rate(periods=3)

        # Period 1: only [-5000] -> average 5000.0
        assert result['2024-01-31'] == 5000.0
        # Period 2: [-5000, -3000] -> average 4000.0
        assert result['2024-02-28'] == 4000.0
        # Period 3: [-5000, -3000, -4000] -> average 4000.0
        assert result['2024-03-31'] == 4000.0

    def test_burn_rate_insufficient_periods(self, balance_sheet_normal, sample_cf_df):
        """
        Given: Cash flow with only 2 periods but burn_rate(periods=3) requested
        When: burn_rate() is called
        Then: Uses 2 available periods without crashing
        """
        hierarchy = {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {
                        '2024-01-31': -5000.0,
                        '2024-02-28': -3000.0
                    }
                }
            ]
        }
        calculated_rows = [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-01-31': 20000.0, '2024-02-28': 15000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01-31': 15000.0, '2024-02-28': 12000.0}
            }
        ]
        cash_flow = CashFlowModel(df=sample_cf_df, hierarchy=hierarchy,
                                  calculated_rows=calculated_rows, metadata={})
        calculator = KPICalculator(balance_sheet_normal, cash_flow)

        # Should not crash even though we request 3-period window with only 2 periods
        result = calculator.burn_rate(periods=3)

        assert '2024-01-31' in result
        assert '2024-02-28' in result
        assert result['2024-01-31'] == 5000.0  # Only 1 period available
        assert result['2024-02-28'] == 4000.0  # 2 periods available

    def test_burn_rate_positive_cash_flow(self, balance_sheet_normal, cash_flow_positive):
        """
        Given: Cash flow with positive changes [+2000, +1000]
        When: burn_rate() is called
        Then: Returns dict with 0.0 values (no burn rate when cash increasing)
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_positive)

        result = calculator.burn_rate()

        # No negative changes, so burn rate should be 0.0
        assert result['2024-01-31'] == 0.0
        assert result['2024-02-28'] == 0.0

    def test_burn_rate_mixed_changes(self, balance_sheet_normal, cash_flow_mixed_changes):
        """
        Given: Cash flow with mixed changes [-5000, +2000, -3000]
        When: burn_rate(periods=2) is called
        Then: Only includes negative changes in average calculation
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_mixed_changes)

        result = calculator.burn_rate(periods=2)

        # Period 1: [-5000] -> 5000.0
        assert result['2024-01-31'] == 5000.0
        # Period 2: [-5000] (ignores +2000) -> 5000.0
        assert result['2024-02-28'] == 5000.0
        # Period 3: [-3000] (2-period window includes only periods 2-3, ignores +2000) -> 3000.0
        assert result['2024-03-31'] == 3000.0

    def test_burn_rate_single_period(self, balance_sheet_normal, cash_flow_single_period):
        """
        Given: Cash flow with only 1 period of data
        When: burn_rate() is called
        Then: Handles single period gracefully
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_single_period)

        result = calculator.burn_rate()

        # Should have exactly 1 entry
        assert len(result) == 1
        assert '2024-01-31' in result
        assert result['2024-01-31'] == 5000.0


# ============================================================================
# TESTS - CASH RUNWAY
# ============================================================================

class TestCashRunway:
    """Test suite for cash_runway method."""

    def test_cash_runway_normal_calculation(self, balance_sheet_normal, cash_flow_normal):
        """
        Given: Current cash and burn rate for each period
        When: cash_runway() is called
        Then: Returns runway in months (cash / burn_rate)
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_normal)

        result = calculator.cash_runway()

        # Period 1: cash=20000, burn=5000 -> runway=4.0
        assert result['2024-01-31'] == 4.0
        # Period 2: cash=17000, burn=4000 -> runway=4.25
        assert result['2024-02-28'] == 4.25
        # Period 3: cash=13000, burn=4000 -> runway=3.25
        assert result['2024-03-31'] == 3.25

    def test_cash_runway_zero_burn(self, balance_sheet_normal, cash_flow_positive):
        """
        Given: Burn rate of 0.0 (profitability or no activity)
        When: cash_runway() is called
        Then: Raises ZeroDivisionError with message containing 'burn rate'
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_positive)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.cash_runway()

        # Verify exception message contains key information
        assert 'burn rate' in str(exc_info.value).lower()

    def test_cash_runway_negative_cash(self, balance_sheet_normal, sample_cf_df):
        """
        Given: Negative cash balance of -5000 and burn rate of 2000
        When: cash_runway() is called
        Then: Returns dict with -2.5 months (already insolvent)
        """
        hierarchy = {
            'OPERATING ACTIVITIES': [
                {
                    'name': 'Net Income',
                    'values': {
                        '2024-01-31': -2000.0,
                        '2024-02-28': -2000.0
                    }
                }
            ]
        }
        calculated_rows = [
            {
                'account_name': 'Cash at beginning of period',
                'values': {'2024-01-31': -3000.0, '2024-02-28': -5000.0}
            },
            {
                'account_name': 'CASH AT END OF PERIOD',
                'values': {'2024-01-31': -5000.0, '2024-02-28': -7000.0}
            }
        ]
        cash_flow = CashFlowModel(df=sample_cf_df, hierarchy=hierarchy,
                                  calculated_rows=calculated_rows, metadata={})
        calculator = KPICalculator(balance_sheet_normal, cash_flow)

        result = calculator.cash_runway()

        # Period 1: cash=-5000, burn=2000 -> runway=-2.5
        assert result['2024-01-31'] == -2.5
        # Period 2: cash=-7000, burn=2000 -> runway=-3.5
        assert result['2024-02-28'] == -3.5

    def test_cash_runway_multiple_periods(self, balance_sheet_normal, cash_flow_normal):
        """
        Given: Multiple periods with varying burn rates
        When: cash_runway() is called
        Then: Returns dict with runway calculated independently for each period
        """
        calculator = KPICalculator(balance_sheet_normal, cash_flow_normal)

        result = calculator.cash_runway()

        # Should have 3 independent runway calculations
        assert len(result) == 3
        assert '2024-01-31' in result
        assert '2024-02-28' in result
        assert '2024-03-31' in result
        # Each period should have different runway based on its cash and burn rate
        assert result['2024-01-31'] != result['2024-02-28']
