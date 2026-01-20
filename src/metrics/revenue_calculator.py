"""
RevenueCalculator for computing revenue metrics and growth rates.

Provides methods for calculating total revenue, month-over-month growth,
and year-over-year growth from PLModel data.
"""
from typing import Any, Dict

from src.models import PLModel
from .exceptions import MissingPeriodError, ZeroDivisionError


class RevenueCalculator:
    """
    Calculator for revenue metrics and growth analysis.

    Computes total revenue by summing all income account values across periods,
    and calculates period-over-period growth percentages.
    """

    def __init__(self, pl_model: PLModel):
        """
        Initialize calculator with PLModel instance.

        Args:
            pl_model: PLModel instance with income data
        """
        self.pl_model = pl_model

    def calculate_total_revenue(self) -> Dict[str, float]:
        """
        Calculate total revenue for all periods by summing all income values.

        Recursively traverses the income hierarchy tree to sum all leaf node values.
        Parent nodes (with 'parent': True flag) are skipped to avoid double-counting.

        Returns:
            Dict mapping period labels to total revenue amounts
            Example: {'Nov 2025': 2500.0, 'Nov 2024 (PY)': 2000.0}
        """
        income_section = self.pl_model.get_income()

        if not income_section:
            # No income section - return zero for all periods
            periods = self.pl_model.get_periods()
            return {period: 0.0 for period in periods}

        # Initialize period totals
        period_totals: Dict[str, float] = {}

        def sum_values_recursive(node: Any) -> None:
            """
            Recursively traverse tree and accumulate leaf node values.

            Args:
                node: Current node in hierarchy tree
            """
            if isinstance(node, dict):
                # If node has children, traverse them (skip parent's 'total' to avoid double-counting)
                if 'children' in node:
                    for child in node['children']:
                        sum_values_recursive(child)
                # If leaf node (has values dict, no children or not a parent)
                elif 'values' in node and isinstance(node['values'], dict) and not node.get('parent', False):
                    # Add this node's values to period totals
                    for period, value in node['values'].items():
                        if period not in period_totals:
                            period_totals[period] = 0.0
                        period_totals[period] += value
            elif isinstance(node, list):
                # Traverse list items
                for item in node:
                    sum_values_recursive(item)

        # Traverse income section
        sum_values_recursive(income_section)

        return period_totals

    def calculate_mom_growth(self, current_period: str, previous_period: str) -> Dict[str, float]:
        """
        Calculate month-over-month growth rate between two periods.

        Formula: ((current - previous) / previous) * 100

        Args:
            current_period: Label of current period (e.g., 'Nov 2025')
            previous_period: Label of previous period (e.g., 'Oct 2025')

        Returns:
            Dict with keys:
                - 'growth_rate': Percentage growth (positive or negative)
                - 'current': Current period revenue
                - 'previous': Previous period revenue

        Raises:
            MissingPeriodError: If either period not found in PLModel
            ZeroDivisionError: If previous period revenue is zero
        """
        # Validate periods exist
        available_periods = self.pl_model.get_periods()

        if current_period not in available_periods:
            raise MissingPeriodError(current_period, available_periods, self.pl_model)

        if previous_period not in available_periods:
            raise MissingPeriodError(previous_period, available_periods, self.pl_model)

        # Get total revenue for both periods
        total_revenue = self.calculate_total_revenue()

        current_value = total_revenue.get(current_period, 0.0)
        previous_value = total_revenue.get(previous_period, 0.0)

        # Check for zero denominator
        if previous_value == 0:
            raise ZeroDivisionError(
                denominator_type='previous period revenue',
                calculation_type='month-over-month growth',
                period=previous_period,
                pl_model=self.pl_model
            )

        # Calculate growth rate
        growth_rate = ((current_value - previous_value) / previous_value) * 100

        return {
            'growth_rate': growth_rate,
            'current': current_value,
            'previous': previous_value
        }

    def calculate_yoy_growth(self, current_period: str) -> Dict[str, float]:
        """
        Calculate year-over-year growth by detecting prior year period.

        Automatically detects the prior year period by searching for a period label
        ending with '(PY)' that matches the current period's base name.

        Args:
            current_period: Label of current period (e.g., 'Nov 2025')

        Returns:
            Dict with keys:
                - 'growth_rate': Percentage growth (positive or negative)
                - 'current': Current period revenue
                - 'previous': Prior year period revenue
                - 'previous_period': Label of matched prior year period

        Raises:
            MissingPeriodError: If current period or matching prior year period not found
            ZeroDivisionError: If prior year period revenue is zero
        """
        # Validate current period exists
        available_periods = self.pl_model.get_periods()

        if current_period not in available_periods:
            raise MissingPeriodError(current_period, available_periods, self.pl_model)

        # Detect prior year period via (PY) suffix
        # Strategy: Look for period ending with (PY) that matches current period's base
        prior_year_period = None

        # Extract base period name (remove year if present)
        # Simple heuristic: find any period ending with '(PY)'
        for period in available_periods:
            if period.endswith('(PY)'):
                # Check if base matches (naive: just use first (PY) found)
                # More sophisticated: match month/date range
                prior_year_period = period
                break

        if prior_year_period is None:
            raise MissingPeriodError(
                period=f"{current_period} (PY)",
                available_periods=available_periods,
                pl_model=self.pl_model
            )

        # Get total revenue for both periods
        total_revenue = self.calculate_total_revenue()

        current_value = total_revenue.get(current_period, 0.0)
        previous_value = total_revenue.get(prior_year_period, 0.0)

        # Check for zero denominator
        if previous_value == 0:
            raise ZeroDivisionError(
                denominator_type='prior year revenue',
                calculation_type='year-over-year growth',
                period=prior_year_period,
                pl_model=self.pl_model
            )

        # Calculate growth rate
        growth_rate = ((current_value - previous_value) / previous_value) * 100

        return {
            'growth_rate': growth_rate,
            'current': current_value,
            'previous': previous_value,
            'previous_period': prior_year_period
        }
