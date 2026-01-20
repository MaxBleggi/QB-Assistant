"""
Budget defaults calculation service.

Calculates intelligent defaults for budget parameters based on historical data
from PLModel. Provides graceful fallback when historical data is unavailable
(Sprint 1.5 historical parser not yet implemented).
"""
from typing import Any, Dict, Optional


class BudgetDefaultsService:
    """
    Service for calculating budget parameter defaults from historical data.

    Analyzes PLModel income/expense data to calculate reasonable defaults
    for revenue growth rates, expense adjustments, and category-specific rates.
    Handles missing data gracefully with sensible fallback values.
    """

    # Fallback defaults when historical data unavailable
    DEFAULT_REVENUE_GROWTH = 0.05  # 5% growth
    DEFAULT_EXPENSE_ADJUSTMENT = 1.0  # No adjustment
    DEFAULT_METHODOLOGY = 'Growth from Prior Year'

    @staticmethod
    def calculate_defaults(pl_model=None, bs_model=None) -> Dict[str, Any]:
        """
        Calculate budget parameter defaults from historical data.

        Args:
            pl_model: Optional PLModel with historical P&L data
            bs_model: Optional BalanceSheetModel (reserved for future, currently unused)

        Returns:
            Dictionary with keys:
            - revenue_growth_rate: Overall revenue growth rate (float)
            - expense_adjustment: Expense adjustment factor (float)
            - budget_methodology: Default methodology string
            - category_growth_rates: Dict of category_name -> growth_rate
        """
        # If no PLModel provided, return fallback defaults
        if pl_model is None:
            return {
                'revenue_growth_rate': BudgetDefaultsService.DEFAULT_REVENUE_GROWTH,
                'expense_adjustment': BudgetDefaultsService.DEFAULT_EXPENSE_ADJUSTMENT,
                'budget_methodology': BudgetDefaultsService.DEFAULT_METHODOLOGY,
                'category_growth_rates': {}
            }

        # Extract income data from PLModel
        try:
            income_data = pl_model.get_income()

            # Calculate overall revenue growth rate
            revenue_growth = BudgetDefaultsService._calculate_growth_rate(income_data)

            # Extract category-specific growth rates
            category_rates = BudgetDefaultsService._extract_category_rates(income_data)

            return {
                'revenue_growth_rate': revenue_growth,
                'expense_adjustment': BudgetDefaultsService.DEFAULT_EXPENSE_ADJUSTMENT,
                'budget_methodology': BudgetDefaultsService.DEFAULT_METHODOLOGY,
                'category_growth_rates': category_rates
            }

        except Exception:
            # Any error in processing -> fallback to defaults
            return {
                'revenue_growth_rate': BudgetDefaultsService.DEFAULT_REVENUE_GROWTH,
                'expense_adjustment': BudgetDefaultsService.DEFAULT_EXPENSE_ADJUSTMENT,
                'budget_methodology': BudgetDefaultsService.DEFAULT_METHODOLOGY,
                'category_growth_rates': {}
            }

    @staticmethod
    def _calculate_growth_rate(income_data: Dict[str, Any]) -> float:
        """
        Calculate growth rate from income data with period values.

        Uses last 3 periods to calculate average monthly growth rate.
        Formula: ((latest - 3_periods_ago) / 3_periods_ago) / 3

        Args:
            income_data: Income section dict from PLModel.get_income()

        Returns:
            Growth rate as float, or DEFAULT_REVENUE_GROWTH if insufficient data
        """
        # Income data structure: {'values': {'2024-01': 100, '2024-02': 110, ...}, 'children': [...]}
        if 'values' not in income_data or not income_data['values']:
            return BudgetDefaultsService.DEFAULT_REVENUE_GROWTH

        values = income_data['values']

        # Sort periods to get chronological order
        periods = sorted(values.keys())

        # Need at least 3 periods for growth calculation
        if len(periods) < 3:
            return BudgetDefaultsService.DEFAULT_REVENUE_GROWTH

        # Get values from 3 periods ago and latest period
        try:
            oldest_value = values[periods[-3]]  # 3 periods ago
            latest_value = values[periods[-1]]  # Latest period

            # Handle zero or negative values
            if oldest_value <= 0 or latest_value <= 0:
                return BudgetDefaultsService.DEFAULT_REVENUE_GROWTH

            # Calculate average monthly growth rate
            # (latest - oldest) / oldest gives total growth over 2 periods
            # Divide by 2 to get average per-period growth rate
            total_growth = (latest_value - oldest_value) / oldest_value
            avg_growth_rate = total_growth / 2

            return avg_growth_rate

        except (KeyError, ZeroDivisionError, TypeError):
            return BudgetDefaultsService.DEFAULT_REVENUE_GROWTH

    @staticmethod
    def _extract_category_rates(income_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract growth rates for each revenue category from income hierarchy.

        Args:
            income_data: Income section dict from PLModel.get_income()

        Returns:
            Dict mapping category name to growth rate
        """
        category_rates = {}

        # Income hierarchy has 'children' list with revenue categories
        if 'children' not in income_data or not income_data['children']:
            return category_rates

        for category in income_data['children']:
            if 'name' not in category or 'values' not in category:
                continue

            category_name = category['name']

            # Calculate growth rate for this category
            category_growth = BudgetDefaultsService._calculate_growth_rate(category)
            category_rates[category_name] = category_growth

        return category_rates
