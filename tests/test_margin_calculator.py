"""
Unit tests for MarginCalculator.

Tests gross margin, EBITDA margin, net margin calculations, and edge case handling.
"""
import pandas as pd
import pytest

from src.models import PLModel
from src.metrics import MarginCalculator, InvalidDataError, ZeroDivisionError


class TestGrossMargin:
    """Test suite for calculate_gross_margin method."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    @pytest.fixture
    def with_cogs_hierarchy(self):
        """Hierarchy with Income and COGS sections."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 10000.0, 'Nov 2024 (PY)': 8000.0}
                    }
                ]
            },
            'Cost of Goods Sold': {
                'children': [
                    {
                        'name': 'COGS',
                        'values': {'Nov 2025': 6000.0, 'Nov 2024 (PY)': 5000.0}
                    }
                ]
            }
        }

    @pytest.fixture
    def without_cogs_hierarchy(self):
        """Hierarchy without COGS section (service business)."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 10000.0}
                    }
                ]
            },
            'Expenses': {
                'children': []
            }
        }

    @pytest.fixture
    def zero_revenue_hierarchy(self):
        """Hierarchy with zero revenue."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 0.0}
                    }
                ]
            },
            'Cost of Goods Sold': {
                'children': [
                    {
                        'name': 'COGS',
                        'values': {'Nov 2025': 1000.0}
                    }
                ]
            }
        }

    def test_calculate_gross_margin_valid_cogs(self, sample_dataframe, with_cogs_hierarchy):
        """
        Given: Revenue=10000, COGS=6000 for Nov 2025
        When: calculate_gross_margin() called
        Then: returns 40.0% gross margin
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=with_cogs_hierarchy, calculated_rows=[])
        calculator = MarginCalculator(pl_model)

        result = calculator.calculate_gross_margin()

        # (10000 - 6000) / 10000 * 100 = 40%
        assert round(result['Nov 2025'], 2) == 40.0
        # (8000 - 5000) / 8000 * 100 = 37.5%
        assert round(result['Nov 2024 (PY)'], 2) == 37.5

    def test_calculate_gross_margin_missing_cogs(self, sample_dataframe, without_cogs_hierarchy):
        """
        Given: PLModel without COGS section
        When: calculate_gross_margin() called
        Then: raises InvalidDataError with actionable message
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=without_cogs_hierarchy, calculated_rows=[])
        calculator = MarginCalculator(pl_model)

        with pytest.raises(InvalidDataError) as exc_info:
            calculator.calculate_gross_margin()

        assert 'COGS' in str(exc_info.value)
        assert 'required' in str(exc_info.value)
        assert 'gross margin' in str(exc_info.value)

    def test_calculate_gross_margin_zero_revenue(self, sample_dataframe, zero_revenue_hierarchy):
        """
        Given: Revenue is zero for Nov 2025
        When: calculate_gross_margin() called
        Then: raises ZeroDivisionError
        """
        pl_model = PLModel(df=sample_dataframe, hierarchy=zero_revenue_hierarchy, calculated_rows=[])
        calculator = MarginCalculator(pl_model)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.calculate_gross_margin()

        assert 'revenue' in str(exc_info.value)
        assert 'zero' in str(exc_info.value)
        assert 'Nov 2025' in str(exc_info.value)

    def test_calculate_gross_margin_nested_cogs(self, sample_dataframe):
        """
        Given: Nested COGS hierarchy with multiple accounts
        When: calculate_gross_margin() called
        Then: sums all COGS values correctly
        """
        nested_hierarchy = {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 10000.0}
                    }
                ]
            },
            'Cost of Goods Sold': {
                'children': [
                    {
                        'name': 'Materials',
                        'values': {'Nov 2025': 3000.0}
                    },
                    {
                        'name': 'Labor',
                        'values': {'Nov 2025': 2000.0}
                    }
                ]
            }
        }

        pl_model = PLModel(df=sample_dataframe, hierarchy=nested_hierarchy, calculated_rows=[])
        calculator = MarginCalculator(pl_model)

        result = calculator.calculate_gross_margin()

        # (10000 - 5000) / 10000 * 100 = 50%
        assert round(result['Nov 2025'], 2) == 50.0


class TestNetMargin:
    """Test suite for calculate_net_margin method."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    @pytest.fixture
    def positive_income_hierarchy(self):
        """Hierarchy with positive net income."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 10000.0}
                    }
                ]
            }
        }

    @pytest.fixture
    def positive_calculated_rows(self):
        """Calculated rows with positive net income."""
        return [
            {
                'account_name': 'Net Income',
                'values': {'Nov 2025': 1000.0}
            }
        ]

    @pytest.fixture
    def negative_calculated_rows(self):
        """Calculated rows with negative net income (loss)."""
        return [
            {
                'account_name': 'Net Income',
                'values': {'Nov 2025': -500.0}
            }
        ]

    @pytest.fixture
    def zero_revenue_hierarchy(self):
        """Hierarchy with zero revenue."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 0.0}
                    }
                ]
            }
        }

    def test_calculate_net_margin_positive(self, sample_dataframe, positive_income_hierarchy, positive_calculated_rows):
        """
        Given: Net Income=1000, Revenue=10000 for Nov 2025
        When: calculate_net_margin() called
        Then: returns 10.0% net margin
        """
        pl_model = PLModel(
            df=sample_dataframe,
            hierarchy=positive_income_hierarchy,
            calculated_rows=positive_calculated_rows
        )
        calculator = MarginCalculator(pl_model)

        result = calculator.calculate_net_margin()

        # 1000 / 10000 * 100 = 10%
        assert round(result['Nov 2025'], 2) == 10.0

    def test_calculate_net_margin_negative(self, sample_dataframe, positive_income_hierarchy, negative_calculated_rows):
        """
        Given: Net Income=-500 (loss), Revenue=10000 for Nov 2025
        When: calculate_net_margin() called
        Then: returns -5.0% net margin (negative margin is valid)
        """
        pl_model = PLModel(
            df=sample_dataframe,
            hierarchy=positive_income_hierarchy,
            calculated_rows=negative_calculated_rows
        )
        calculator = MarginCalculator(pl_model)

        result = calculator.calculate_net_margin()

        # -500 / 10000 * 100 = -5%
        assert round(result['Nov 2025'], 2) == -5.0

    def test_calculate_net_margin_zero_revenue(self, sample_dataframe, zero_revenue_hierarchy, positive_calculated_rows):
        """
        Given: Revenue is zero for Nov 2025
        When: calculate_net_margin() called
        Then: raises ZeroDivisionError
        """
        pl_model = PLModel(
            df=sample_dataframe,
            hierarchy=zero_revenue_hierarchy,
            calculated_rows=positive_calculated_rows
        )
        calculator = MarginCalculator(pl_model)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.calculate_net_margin()

        assert 'revenue' in str(exc_info.value)
        assert 'zero' in str(exc_info.value)
        assert 'net margin' in str(exc_info.value)


class TestEBITDAMargin:
    """Test suite for calculate_ebitda_margin method."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    @pytest.fixture
    def income_hierarchy(self):
        """Hierarchy with income data."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 10000.0}
                    }
                ]
            }
        }

    @pytest.fixture
    def net_income_calculated_rows(self):
        """Calculated rows with Net Income (EBITDA proxy)."""
        return [
            {
                'account_name': 'Net Income',
                'values': {'Nov 2025': 1500.0}
            }
        ]

    def test_calculate_ebitda_margin_net_income_proxy(self, sample_dataframe, income_hierarchy, net_income_calculated_rows):
        """
        Given: Net Income=1500 (EBITDA proxy), Revenue=10000 for Nov 2025
        When: calculate_ebitda_margin() called
        Then: returns 15.0% EBITDA margin using Net Income as proxy
        """
        pl_model = PLModel(
            df=sample_dataframe,
            hierarchy=income_hierarchy,
            calculated_rows=net_income_calculated_rows
        )
        calculator = MarginCalculator(pl_model)

        result = calculator.calculate_ebitda_margin()

        # 1500 / 10000 * 100 = 15%
        assert round(result['Nov 2025'], 2) == 15.0

    def test_calculate_ebitda_margin_zero_revenue(self, sample_dataframe, net_income_calculated_rows):
        """
        Given: Revenue is zero
        When: calculate_ebitda_margin() called
        Then: raises ZeroDivisionError
        """
        zero_revenue = {
            'Income': {
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {'Nov 2025': 0.0}
                    }
                ]
            }
        }

        pl_model = PLModel(
            df=sample_dataframe,
            hierarchy=zero_revenue,
            calculated_rows=net_income_calculated_rows
        )
        calculator = MarginCalculator(pl_model)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.calculate_ebitda_margin()

        assert 'revenue' in str(exc_info.value)
        assert 'EBITDA margin' in str(exc_info.value)


class TestExceptionMessages:
    """Test suite for exception message quality."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create minimal DataFrame for PLModel."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'}
        ])

    def test_invalid_data_error_message_actionable(self, sample_dataframe):
        """
        Given: PLModel without COGS
        When: InvalidDataError raised
        Then: message explains problem and solution
        """
        hierarchy = {
            'Income': {
                'children': [
                    {'name': 'Revenue', 'values': {'Nov 2025': 1000.0}}
                ]
            }
        }

        pl_model = PLModel(df=sample_dataframe, hierarchy=hierarchy, calculated_rows=[])
        calculator = MarginCalculator(pl_model)

        with pytest.raises(InvalidDataError) as exc_info:
            calculator.calculate_gross_margin()

        error_msg = str(exc_info.value)
        # Check message is actionable
        assert 'required' in error_msg
        assert 'COGS' in error_msg
        assert 'gross margin' in error_msg
        assert 'ensure' in error_msg.lower()

    def test_zero_division_error_message_actionable(self, sample_dataframe):
        """
        Given: Zero revenue scenario
        When: ZeroDivisionError raised
        Then: message explains denominator is zero and suggests data review
        """
        hierarchy = {
            'Income': {
                'children': [
                    {'name': 'Revenue', 'values': {'Nov 2025': 0.0}}
                ]
            },
            'Cost of Goods Sold': {
                'children': [
                    {'name': 'COGS', 'values': {'Nov 2025': 100.0}}
                ]
            }
        }

        pl_model = PLModel(df=sample_dataframe, hierarchy=hierarchy, calculated_rows=[])
        calculator = MarginCalculator(pl_model)

        with pytest.raises(ZeroDivisionError) as exc_info:
            calculator.calculate_gross_margin()

        error_msg = str(exc_info.value)
        # Check message is actionable
        assert 'revenue' in error_msg
        assert 'zero' in error_msg
        assert 'Nov 2025' in error_msg
        assert 'review' in error_msg.lower()
