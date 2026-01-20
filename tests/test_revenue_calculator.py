"""
Unit tests for RevenueCalculator.

Tests total revenue calculation, month-over-month growth, year-over-year growth,
and edge case handling.
"""
import pandas as pd
import pytest

from src.models import PLModel
from src.metrics import RevenueCalculator, MissingPeriodError, ZeroDivisionError


class TestTotalRevenue:
    """Test suite for calculate_total_revenue method."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    @pytest.fixture
    def single_account_hierarchy(self):
        """Income hierarchy with single account."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Design income',
                        'values': {'Nov 2025': 1000.0, 'Nov 2024 (PY)': 800.0}
                    }
                ]
            }
        }

    @pytest.fixture
    def multiple_accounts_hierarchy(self):
        """Income hierarchy with multiple accounts."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Design income',
                        'values': {'Nov 2025': 1000.0, 'Nov 2024 (PY)': 800.0}
                    },
                    {
                        'name': 'Consulting',
                        'values': {'Nov 2025': 500.0, 'Nov 2024 (PY)': 600.0}
                    }
                ]
            }
        }

    @pytest.fixture
    def nested_hierarchy(self):
        """Income hierarchy with nested structure."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Design income',
                        'values': {'Nov 2025': 637.50, 'Nov 2024 (PY)': 500.00}
                    },
                    {
                        'name': 'Landscaping Services',
                        'parent': True,
                        'children': [
                            {
                                'name': 'Job Materials',
                                'parent': True,
                                'children': [
                                    {
                                        'name': 'Plants and Soil',
                                        'values': {'Nov 2025': 1766.98, 'Nov 2024 (PY)': 1500.00}
                                    }
                                ],
                                'total': {'Nov 2025': 1766.98, 'Nov 2024 (PY)': 1500.00}
                            }
                        ],
                        'total': {'Nov 2025': 1766.98, 'Nov 2024 (PY)': 1500.00}
                    }
                ]
            }
        }

    def test_calculate_total_revenue_single_account(self, sample_dataframe, single_account_hierarchy):
        """
        Given: PLModel with single income account (1000 for Nov 2025, 800 for Nov 2024)
        When: calculate_total_revenue() called
        Then: returns correct totals for each period
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=single_account_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_total_revenue()

        assert result['Nov 2025'] == 1000.0
        assert result['Nov 2024 (PY)'] == 800.0

    def test_calculate_total_revenue_multiple_accounts(self, sample_dataframe, multiple_accounts_hierarchy):
        """
        Given: PLModel with two income accounts (1000+500 for Nov 2025, 800+600 for Nov 2024)
        When: calculate_total_revenue() called
        Then: returns sum of all accounts for each period
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=multiple_accounts_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_total_revenue()

        assert result['Nov 2025'] == 1500.0
        assert result['Nov 2024 (PY)'] == 1400.0

    def test_calculate_total_revenue_nested_hierarchy(self, sample_dataframe, nested_hierarchy):
        """
        Given: PLModel with nested income hierarchy (parent and child accounts)
        When: calculate_total_revenue() called
        Then: sums only leaf node values, avoiding double-counting parent totals
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=nested_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_total_revenue()

        # Should sum: 637.50 (Design income) + 1766.98 (Plants and Soil) = 2404.48
        assert round(result['Nov 2025'], 2) == 2404.48
        assert round(result['Nov 2024 (PY)'], 2) == 2000.00

    def test_calculate_total_revenue_empty_income(self, sample_dataframe):
        """
        Given: PLModel with no income section
        When: calculate_total_revenue() called
        Then: returns zero for all periods
        """
        hierarchy = {'Expenses': {'children': []}}
        pl_model = PLModel(df=sample_dataframe, hierarchy=hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_total_revenue()

        # Should return empty dict or zeros
        assert isinstance(result, dict)


class TestMoMGrowth:
    """Test suite for calculate_mom_growth method."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    @pytest.fixture
    def growth_hierarchy(self):
        """Income hierarchy with data for growth calculations."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            'Oct 2025': 2000.0,
                            'Nov 2025': 2500.0,
                            'Dec 2025': 1800.0
                        }
                    }
                ]
            }
        }

    @pytest.fixture
    def zero_revenue_hierarchy(self):
        """Income hierarchy with zero revenue in previous period."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            'Oct 2025': 0.0,
                            'Nov 2025': 2500.0
                        }
                    }
                ]
            }
        }

    def test_calculate_mom_growth_positive(self, sample_dataframe, growth_hierarchy):
        """
        Given: Revenue increases from 2000 (Oct) to 2500 (Nov)
        When: calculate_mom_growth('Nov 2025', 'Oct 2025') called
        Then: returns 25% growth rate
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=growth_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_mom_growth('Nov 2025', 'Oct 2025')

        assert result['growth_rate'] == pytest.approx(25.0)
        assert result['current'] == pytest.approx(2500.0)
        assert result['previous'] == pytest.approx(2000.0)

    def test_calculate_mom_growth_negative(self, sample_dataframe, growth_hierarchy):
        """
        Given: Revenue decreases from 2500 (Nov) to 1800 (Dec)
        When: calculate_mom_growth('Dec 2025', 'Nov 2025') called
        Then: returns negative growth rate (-28%)
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=growth_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_mom_growth('Dec 2025', 'Nov 2025')

        assert result['growth_rate'] == pytest.approx(-28.0)
        assert result['current'] == pytest.approx(1800.0)
        assert result['previous'] == pytest.approx(2500.0)

    def test_calculate_mom_growth_zero_previous_revenue(self, sample_dataframe, zero_revenue_hierarchy):
        """
        Given: Previous period revenue is zero
        When: calculate_mom_growth('Nov 2025', 'Oct 2025') called
        Then: raises ZeroDivisionError with actionable message
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=zero_revenue_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.calculate_mom_growth('Nov 2025', 'Oct 2025')

        assert 'previous period revenue is zero' in str(exc_info.value)
        assert 'Oct 2025' in str(exc_info.value)

    def test_calculate_mom_growth_missing_current_period(self, sample_dataframe, growth_hierarchy):
        """
        Given: Current period 'Jan 2026' not in PLModel
        When: calculate_mom_growth('Jan 2026', 'Nov 2025') called
        Then: raises MissingPeriodError listing available periods
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=growth_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        with pytest.raises(MissingPeriodError) as exc_info:
            calculator.calculate_mom_growth('Jan 2026', 'Nov 2025')

        assert 'Jan 2026' in str(exc_info.value)
        assert 'not found' in str(exc_info.value)

    def test_calculate_mom_growth_missing_previous_period(self, sample_dataframe, growth_hierarchy):
        """
        Given: Previous period 'Sep 2025' not in PLModel
        When: calculate_mom_growth('Nov 2025', 'Sep 2025') called
        Then: raises MissingPeriodError listing available periods
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=growth_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        with pytest.raises(MissingPeriodError) as exc_info:
            calculator.calculate_mom_growth('Nov 2025', 'Sep 2025')

        assert 'Sep 2025' in str(exc_info.value)
        assert 'not found' in str(exc_info.value)


class TestYoYGrowth:
    """Test suite for calculate_yoy_growth method."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    @pytest.fixture
    def yoy_hierarchy(self):
        """Income hierarchy with current and prior year data."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            'Nov 2025': 2500.0,
                            'Nov 2024 (PY)': 2000.0
                        }
                    }
                ]
            }
        }

    @pytest.fixture
    def no_prior_year_hierarchy(self):
        """Income hierarchy without prior year period."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            'Nov 2025': 2500.0
                        }
                    }
                ]
            }
        }

    @pytest.fixture
    def zero_prior_year_hierarchy(self):
        """Income hierarchy with zero prior year revenue."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            'Nov 2025': 2500.0,
                            'Nov 2024 (PY)': 0.0
                        }
                    }
                ]
            }
        }

    def test_calculate_yoy_growth_detection(self, sample_dataframe, yoy_hierarchy):
        """
        Given: PLModel with 'Nov 2025' and 'Nov 2024 (PY)' periods
        When: calculate_yoy_growth('Nov 2025') called
        Then: automatically matches prior year period and calculates 25% growth
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=yoy_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        result = calculator.calculate_yoy_growth('Nov 2025')

        assert result['growth_rate'] == 25.0
        assert result['current'] == 2500.0
        assert result['previous'] == 2000.0
        assert result['previous_period'] == 'Nov 2024 (PY)'

    def test_calculate_yoy_missing_prior_year(self, sample_dataframe, no_prior_year_hierarchy):
        """
        Given: PLModel without prior year period (no (PY) suffix)
        When: calculate_yoy_growth('Nov 2025') called
        Then: raises MissingPeriodError
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=no_prior_year_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        with pytest.raises(MissingPeriodError) as exc_info:
            calculator.calculate_yoy_growth('Nov 2025')

        assert '(PY)' in str(exc_info.value)
        assert 'not found' in str(exc_info.value)

    def test_calculate_yoy_zero_prior_year_revenue(self, sample_dataframe, zero_prior_year_hierarchy):
        """
        Given: Prior year revenue is zero
        When: calculate_yoy_growth('Nov 2025') called
        Then: raises ZeroDivisionError
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=zero_prior_year_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.calculate_yoy_growth('Nov 2025')

        assert 'prior year revenue' in str(exc_info.value)
        assert 'Nov 2024 (PY)' in str(exc_info.value)

    def test_calculate_yoy_missing_current_period(self, sample_dataframe, yoy_hierarchy):
        """
        Given: Current period 'Dec 2025' not in PLModel
        When: calculate_yoy_growth('Dec 2025') called
        Then: raises MissingPeriodError
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=yoy_hierarchy, calculated_rows=[])
        calculator = RevenueCalculator(pl_model)

        with pytest.raises(MissingPeriodError) as exc_info:
            calculator.calculate_yoy_growth('Dec 2025')

        assert 'Dec 2025' in str(exc_info.value)
        assert 'not found' in str(exc_info.value)
