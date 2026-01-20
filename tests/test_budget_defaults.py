"""
Unit tests for BudgetDefaultsService.

Tests defaults calculation from PLModel data, fallback behavior when historical
data unavailable, and edge cases (zero values, single period, negative growth).
"""
import pytest
from unittest.mock import Mock

from src.services.budget_defaults import BudgetDefaultsService


class TestBudgetDefaultsService:
    """Test suite for BudgetDefaultsService class."""

    def test_calculate_defaults_with_none_model(self):
        """
        Given: pl_model is None
        When: calculate_defaults() called
        Then: Returns fallback defaults (revenue_growth_rate=0.05, expense_adjustment=1.0, etc.)
        """
        defaults = BudgetDefaultsService.calculate_defaults(pl_model=None)

        assert defaults['revenue_growth_rate'] == 0.05
        assert defaults['expense_adjustment'] == 1.0
        assert defaults['budget_methodology'] == 'Growth from Prior Year'
        assert defaults['category_growth_rates'] == {}

    def test_calculate_defaults_with_valid_pl_model(self):
        """
        Given: PLModel with 3+ periods of Income data
        When: calculate_defaults(pl_model) called
        Then: revenue_growth_rate calculated from period-to-period change
        """
        # Create mock PLModel with 3 periods: 100, 110, 121 (10% growth per period)
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 100,
                '2024-02': 110,
                '2024-03': 121
            },
            'children': []
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Expected: (121 - 100) / 100 / 2 = 0.21 / 2 = 0.105
        assert abs(defaults['revenue_growth_rate'] - 0.105) < 0.001
        assert defaults['expense_adjustment'] == 1.0
        assert defaults['budget_methodology'] == 'Growth from Prior Year'

    def test_calculate_defaults_extracts_category_rates(self):
        """
        Given: PLModel with 2 revenue categories (Product Sales, Service Revenue)
        When: calculate_defaults(pl_model) called
        Then: category_growth_rates dict contains rates for both categories
        """
        # Create mock PLModel with 2 revenue categories
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 150,
                '2024-02': 165,
                '2024-03': 180
            },
            'children': [
                {
                    'name': 'Product Sales',
                    'values': {
                        '2024-01': 100,
                        '2024-02': 110,
                        '2024-03': 120
                    }
                },
                {
                    'name': 'Service Revenue',
                    'values': {
                        '2024-01': 50,
                        '2024-02': 55,
                        '2024-03': 60
                    }
                }
            ]
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        category_rates = defaults['category_growth_rates']
        assert 'Product Sales' in category_rates
        assert 'Service Revenue' in category_rates

        # Product Sales: (120 - 100) / 100 / 2 = 0.10
        assert abs(category_rates['Product Sales'] - 0.10) < 0.001

        # Service Revenue: (60 - 50) / 50 / 2 = 0.10
        assert abs(category_rates['Service Revenue'] - 0.10) < 0.001

    def test_calculate_defaults_handles_single_period(self):
        """
        Given: PLModel with only 1 period
        When: calculate_defaults(pl_model) called
        Then: Returns fallback defaults without crashing (insufficient data)
        """
        # Create mock PLModel with only 1 period
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 100
            },
            'children': []
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Should return fallback defaults due to insufficient data
        assert defaults['revenue_growth_rate'] == 0.05
        assert defaults['category_growth_rates'] == {}

    def test_calculate_defaults_handles_zero_values(self):
        """
        Given: PLModel with get_income() returning period with value 0
        When: calculate_defaults(pl_model) called
        Then: No ZeroDivisionError raised, fallback defaults returned
        """
        # Create mock PLModel with zero value in period
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 0,
                '2024-02': 100,
                '2024-03': 110
            },
            'children': []
        }

        # Should not raise ZeroDivisionError
        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Should return fallback due to zero value
        assert defaults['revenue_growth_rate'] == 0.05

    def test_calculate_defaults_handles_negative_growth(self):
        """
        Given: PLModel with declining revenue (negative growth)
        When: calculate_defaults(pl_model) called
        Then: Negative growth rate returned (allowed for revenue decline scenarios)
        """
        # Create mock PLModel with declining revenue: 120, 110, 100
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 120,
                '2024-02': 110,
                '2024-03': 100
            },
            'children': []
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Expected: (100 - 120) / 120 / 2 = -0.20 / 120 / 2 ≈ -0.0833
        # Calculation: -20 / 120 / 2 = -0.0833
        assert defaults['revenue_growth_rate'] < 0
        assert abs(defaults['revenue_growth_rate'] - (-0.0833)) < 0.001

    def test_calculate_defaults_handles_missing_values_key(self):
        """
        Given: PLModel.get_income() returns dict without 'values' key
        When: calculate_defaults(pl_model) called
        Then: Returns fallback defaults without crashing
        """
        # Create mock PLModel with missing 'values' key
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'children': []
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        assert defaults['revenue_growth_rate'] == 0.05
        assert defaults['category_growth_rates'] == {}

    def test_calculate_defaults_handles_empty_values(self):
        """
        Given: PLModel.get_income() returns dict with empty 'values'
        When: calculate_defaults(pl_model) called
        Then: Returns fallback defaults without crashing
        """
        # Create mock PLModel with empty values
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {},
            'children': []
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        assert defaults['revenue_growth_rate'] == 0.05
        assert defaults['category_growth_rates'] == {}

    def test_calculate_defaults_handles_get_income_exception(self):
        """
        Given: PLModel.get_income() raises exception
        When: calculate_defaults(pl_model) called
        Then: Returns fallback defaults without propagating exception
        """
        # Create mock PLModel that raises exception
        mock_pl_model = Mock()
        mock_pl_model.get_income.side_effect = Exception("Data error")

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Should gracefully handle exception and return fallback
        assert defaults['revenue_growth_rate'] == 0.05
        assert defaults['expense_adjustment'] == 1.0

    def test_calculate_defaults_handles_two_periods(self):
        """
        Given: PLModel with exactly 2 periods
        When: calculate_defaults(pl_model) called
        Then: Returns fallback defaults (need at least 3 periods)
        """
        # Create mock PLModel with 2 periods
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 100,
                '2024-02': 110
            },
            'children': []
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Should return fallback due to insufficient periods
        assert defaults['revenue_growth_rate'] == 0.05

    def test_calculate_defaults_category_with_insufficient_periods(self):
        """
        Given: PLModel with categories that have < 3 periods
        When: calculate_defaults(pl_model) called
        Then: Category gets fallback default rate
        """
        # Create mock PLModel with category having only 2 periods
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 100,
                '2024-02': 110,
                '2024-03': 120
            },
            'children': [
                {
                    'name': 'Product Sales',
                    'values': {
                        '2024-02': 50,
                        '2024-03': 55
                    }
                }
            ]
        }

        defaults = BudgetDefaultsService.calculate_defaults(pl_model=mock_pl_model)

        # Category should get fallback rate due to insufficient periods
        assert defaults['category_growth_rates']['Product Sales'] == 0.05

    def test_calculate_defaults_ignores_bs_model(self):
        """
        Given: bs_model parameter provided (reserved for future)
        When: calculate_defaults(pl_model, bs_model) called
        Then: bs_model is accepted but not used in calculations
        """
        mock_pl_model = Mock()
        mock_pl_model.get_income.return_value = {
            'values': {
                '2024-01': 100,
                '2024-02': 110,
                '2024-03': 121
            },
            'children': []
        }

        mock_bs_model = Mock()

        # Should not raise error even though bs_model provided
        defaults = BudgetDefaultsService.calculate_defaults(
            pl_model=mock_pl_model,
            bs_model=mock_bs_model
        )

        assert defaults['revenue_growth_rate'] > 0
        # bs_model not used, so no calls expected
        assert not mock_bs_model.called
