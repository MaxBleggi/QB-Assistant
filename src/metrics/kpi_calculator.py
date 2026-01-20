"""
KPICalculator for computing financial health Key Performance Indicators.

Provides methods for calculating current ratio, burn rate, and cash runway
using composition of LiquidityCalculator and CashFlowCalculator.
"""
from typing import Dict

from src.models.balance_sheet import BalanceSheetModel
from src.models.cash_flow_model import CashFlowModel
from src.metrics.liquidity_calculator import LiquidityCalculator
from src.metrics.cash_flow_calculator import CashFlowCalculator
from src.metrics.exceptions import ZeroDivisionError


class KPICalculator:
    """
    Calculator for Key Performance Indicators (KPIs) related to financial health.

    Composes LiquidityCalculator and CashFlowCalculator to provide:
    - Current Ratio (current assets / current liabilities)
    - Burn Rate (average monthly cash decrease)
    - Cash Runway (months until cash depleted)
    """

    def __init__(self, balance_sheet: BalanceSheetModel, cash_flow: CashFlowModel):
        """
        Initialize calculator with BalanceSheetModel and CashFlowModel instances.

        Args:
            balance_sheet: BalanceSheetModel instance with balance sheet data
            cash_flow: CashFlowModel instance with cash flow data
        """
        self._balance_sheet = balance_sheet
        self._cash_flow = cash_flow
        self._liquidity_calc = LiquidityCalculator(balance_sheet)
        self._cash_flow_calc = CashFlowCalculator(cash_flow)

    def current_ratio(self) -> Dict[str, float]:
        """
        Calculate current ratio for all periods.

        Formula: current_assets / current_liabilities

        The current ratio measures liquidity by comparing current assets to
        current liabilities. A ratio above 1.0 indicates more current assets
        than current liabilities.

        Returns:
            Dict mapping period labels to current ratio values
            Example: {'2024-01-31': 2.0, '2024-02-28': 1.8}

        Raises:
            ZeroDivisionError: If current liabilities are zero for any period
        """
        # Extract current assets and liabilities using existing logic
        assets_section = self._balance_sheet.get_assets()
        liabilities_section = self._balance_sheet.get_liabilities()

        # Initialize period totals
        current_assets_totals: Dict[str, float] = {}
        current_liabilities_totals: Dict[str, float] = {}

        # Reuse the recursive extraction pattern from LiquidityCalculator
        def sum_section_recursive(node, target_section: str, totals: Dict[str, float]) -> None:
            """
            Recursively find and sum a specific section.

            Args:
                node: Current node in hierarchy tree
                target_section: Section name to find and sum
                totals: Dict to accumulate period totals
            """
            if isinstance(node, dict):
                name = node.get('name', '')

                if name == target_section:
                    # Found target section - sum all children
                    sum_children_recursive(node, totals)
                    return

                # Check children
                if 'children' in node:
                    for child in node['children']:
                        sum_section_recursive(child, target_section, totals)

            elif isinstance(node, list):
                for item in node:
                    sum_section_recursive(item, target_section, totals)

        def sum_children_recursive(node, totals: Dict[str, float]) -> None:
            """
            Recursively sum all leaf nodes under a parent node.

            Args:
                node: Current node in hierarchy tree
                totals: Dict to accumulate period totals
            """
            if isinstance(node, dict):
                # If node has children, traverse them
                if 'children' in node:
                    for child in node['children']:
                        sum_children_recursive(child, totals)
                # If leaf node (has values dict, no children, not a parent)
                elif 'values' in node and isinstance(node['values'], dict) and not node.get('parent', False):
                    # Add this node's values to period totals
                    for period, value in node['values'].items():
                        if period not in totals:
                            totals[period] = 0.0
                        totals[period] += value
            elif isinstance(node, list):
                for item in node:
                    sum_children_recursive(item, totals)

        # Extract current assets and current liabilities
        sum_section_recursive(assets_section, 'Current Assets', current_assets_totals)
        sum_section_recursive(liabilities_section, 'Current Liabilities', current_liabilities_totals)

        # Calculate current ratio for each period
        current_ratios: Dict[str, float] = {}

        # Get all periods from both current assets and current liabilities
        all_periods = set(current_assets_totals.keys()) | set(current_liabilities_totals.keys())

        for period in all_periods:
            current_assets = current_assets_totals.get(period, 0.0)
            current_liabilities = current_liabilities_totals.get(period, 0.0)

            # Check for zero denominator
            if current_liabilities == 0.0:
                raise ZeroDivisionError(
                    denominator_type='current liabilities',
                    calculation_type='current ratio',
                    period=period
                )

            # Calculate ratio
            current_ratios[period] = current_assets / current_liabilities

        return current_ratios

    def burn_rate(self, periods: int = 3) -> Dict[str, float]:
        """
        Calculate rolling average burn rate for all periods.

        Burn rate is the average monthly cash decrease, calculated as a rolling
        average of negative cash changes. Positive cash changes (increases) are
        excluded from the calculation.

        Args:
            periods: Number of periods to use for rolling average (default 3)

        Returns:
            Dict mapping period labels to burn rate values (absolute values)
            Example: {'2024-03-31': 4000.0} for average $4000/month burn
            Returns 0.0 for periods with no negative cash changes

        Note:
            If fewer periods exist than requested window, uses all available periods.
        """
        # Get cash balance changes
        cash_changes = self._cash_flow_calc.get_cash_balance_change()

        # Extract all periods in order (assuming they're in chronological order)
        all_periods = list(cash_changes.keys())

        # Filter to only negative changes (cash decreases)
        negative_changes = {period: change for period, change in cash_changes.items() if change < 0}

        # Calculate rolling average burn rate for each period
        burn_rates: Dict[str, float] = {}

        for i, period in enumerate(all_periods):
            # Determine the window of periods to include in rolling average
            start_idx = max(0, i - periods + 1)
            window_periods = all_periods[start_idx:i + 1]

            # Get negative changes within this window
            window_negative_changes = [
                abs(cash_changes[p]) for p in window_periods
                if p in negative_changes
            ]

            # Calculate average burn rate
            if window_negative_changes:
                burn_rates[period] = sum(window_negative_changes) / len(window_negative_changes)
            else:
                # No burn if cash is increasing or stable
                burn_rates[period] = 0.0

        return burn_rates

    def cash_runway(self, periods: int = 3) -> Dict[str, float]:
        """
        Calculate cash runway in months for all periods.

        Cash runway is the number of months until cash is depleted at the
        current burn rate. Calculated as: current_cash / burn_rate

        Args:
            periods: Number of periods to use for burn rate calculation (default 3)

        Returns:
            Dict mapping period labels to runway in months
            Example: {'2024-03-31': 6.0} for 6 months of runway
            Negative values indicate already insolvent (negative cash balance)

        Raises:
            ZeroDivisionError: If burn rate is zero (indicating profitability)
        """
        # Get burn rates for all periods
        burn_rates = self.burn_rate(periods)

        # Extract ending cash for each period from cash flow model
        ending_cash_by_period: Dict[str, float] = {}

        for row in self._cash_flow.calculated_rows:
            if row.get('account_name') == 'CASH AT END OF PERIOD':
                values = row.get('values', {})
                if isinstance(values, dict):
                    # Multi-period case
                    ending_cash_by_period.update(values)
                else:
                    # Single period case - get the scalar value and map to first period
                    value = row.get('value')
                    if value is not None and self._cash_flow.get_periods():
                        first_period = self._cash_flow.get_periods()[0]
                        ending_cash_by_period[first_period] = value

        # Calculate runway for each period
        runways: Dict[str, float] = {}

        for period in burn_rates.keys():
            burn_rate_value = burn_rates[period]
            current_cash = ending_cash_by_period.get(period, 0.0)

            # Check for zero burn rate
            if burn_rate_value == 0.0:
                raise ZeroDivisionError(
                    denominator_type='burn rate',
                    calculation_type='cash runway',
                    period=period
                )

            # Calculate runway (can be negative if cash is negative)
            runways[period] = current_cash / burn_rate_value

        return runways
