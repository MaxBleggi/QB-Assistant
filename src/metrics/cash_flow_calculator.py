"""
CashFlowCalculator for computing cash flow and liquidity metrics.

Provides methods for calculating operating cash flow, cash balance changes,
free cash flow, and trend analysis from CashFlowModel data.
"""
from typing import Any, Dict, Optional

from src.models.cash_flow_model import CashFlowModel


class CashFlowCalculator:
    """
    Calculator for cash flow metrics and trend analysis.

    Computes operating cash flow, cash balance changes, free cash flow,
    and provides trend indicators for cash position over time.
    """

    def __init__(self, cash_flow_model: CashFlowModel):
        """
        Initialize calculator with CashFlowModel instance.

        Args:
            cash_flow_model: CashFlowModel instance with cash flow data
        """
        self.cash_flow_model = cash_flow_model

    def get_operating_cash_flow(self) -> Dict[str, float]:
        """
        Calculate operating cash flow for all periods.

        Sums all operating activities from the Cash Flow statement using
        recursive hierarchy traversal. Parent nodes are skipped to avoid
        double-counting.

        Returns:
            Dict mapping period labels to operating cash flow totals
            Example: {'2024-01': 50000.0, '2024-02': 55000.0}
        """
        operating_section = self.cash_flow_model.get_operating()

        if not operating_section:
            # No operating section - return empty dict
            return {}

        # Initialize period totals
        period_totals: Dict[str, float] = {}

        def sum_operating_recursive(node: Any) -> None:
            """
            Recursively traverse operating activities tree and accumulate leaf node values.

            Args:
                node: Current node in hierarchy tree
            """
            if isinstance(node, dict):
                # If node has children, traverse them
                if 'children' in node:
                    for child in node['children']:
                        sum_operating_recursive(child)
                # If leaf node (has values dict, no children, not a parent)
                elif 'values' in node and isinstance(node['values'], dict) and not node.get('parent', False):
                    # Add this node's values to period totals
                    for period, value in node['values'].items():
                        if period not in period_totals:
                            period_totals[period] = 0.0
                        period_totals[period] += value
            elif isinstance(node, list):
                # Traverse list items
                for item in node:
                    sum_operating_recursive(item)

        # Traverse operating section
        sum_operating_recursive(operating_section)

        return period_totals

    def get_cash_balance_change(self) -> Dict[str, float]:
        """
        Calculate cash balance change for all periods.

        Computes ending_cash - beginning_cash for each period. Periods with
        missing cash position data (None values) are skipped.

        Returns:
            Dict mapping period labels to cash balance changes
            Example: {'2024-01': 20000.0, '2024-02': -5000.0}
        """
        # Get all periods from the model
        periods = self.cash_flow_model.get_periods()

        changes: Dict[str, float] = {}

        for period in periods:
            # Get beginning and ending cash for this period
            # Note: CashFlowModel properties return single values (first period)
            # We need to extract from calculated_rows for each period
            beginning_cash = None
            ending_cash = None

            for row in self.cash_flow_model.calculated_rows:
                if row.get('account_name') == 'Cash at beginning of period':
                    values = row.get('values', {})
                    if isinstance(values, dict):
                        beginning_cash = values.get(period)
                    elif period in self.cash_flow_model.get_periods() and len(self.cash_flow_model.get_periods()) == 1:
                        # Single period case - use the value directly
                        beginning_cash = row.get('value')

                if row.get('account_name') == 'CASH AT END OF PERIOD':
                    values = row.get('values', {})
                    if isinstance(values, dict):
                        ending_cash = values.get(period)
                    elif period in self.cash_flow_model.get_periods() and len(self.cash_flow_model.get_periods()) == 1:
                        # Single period case - use the value directly
                        ending_cash = row.get('value')

            # Only calculate change if both values are available
            if beginning_cash is not None and ending_cash is not None:
                changes[period] = ending_cash - beginning_cash

        return changes

    def get_free_cash_flow(self) -> Dict[str, Optional[float]]:
        """
        Calculate free cash flow for all periods.

        Formula: operating_cash_flow - capital_expenditures

        Returns None for periods where capital expenditures cannot be identified
        from investing activities.

        Returns:
            Dict mapping period labels to free cash flow (or None if capex unavailable)
            Example: {'2024-01': 70000.0, '2024-02': None}
        """
        # Get operating cash flow
        operating_cf = self.get_operating_cash_flow()

        # Get investing activities to find capex
        investing_section = self.cash_flow_model.get_investing()

        # Extract capex values for all periods
        capex_totals: Dict[str, float] = {}

        def find_capex_recursive(node: Any) -> None:
            """
            Recursively search for capital expenditure items in investing activities.

            Args:
                node: Current node in hierarchy tree
            """
            if isinstance(node, dict):
                # Check if this node represents capex
                name = node.get('name', '').lower()
                capex_keywords = ['capital expenditure', 'purchase of equipment',
                                 'purchase of property', 'fixed asset', 'capex',
                                 'property and equipment', 'pp&e']

                is_capex = any(keyword in name for keyword in capex_keywords)

                if is_capex and 'values' in node and isinstance(node['values'], dict):
                    # Found capex - add to totals
                    for period, value in node['values'].items():
                        if period not in capex_totals:
                            capex_totals[period] = 0.0
                        # Capex is typically negative in investing activities, so we use absolute value
                        capex_totals[period] += abs(value)

                # Traverse children if present
                if 'children' in node:
                    for child in node['children']:
                        find_capex_recursive(child)

            elif isinstance(node, list):
                for item in node:
                    find_capex_recursive(item)

        # Search for capex in investing activities
        find_capex_recursive(investing_section)

        # Calculate free cash flow for each period
        free_cf: Dict[str, Optional[float]] = {}

        for period in operating_cf.keys():
            operating_value = operating_cf[period]

            if period in capex_totals:
                # Capex found - calculate free cash flow
                free_cf[period] = operating_value - capex_totals[period]
            else:
                # No capex found - return None
                free_cf[period] = None

        return free_cf

    def get_cash_balance_trend(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze cash balance trends over time.

        Returns directional indicators (increase/decrease/stable) based on
        cash balance changes. Periods with missing cash position data are skipped.

        Returns:
            Dict mapping period labels to trend data
            Example: {'2024-01': {'change': 20000.0, 'direction': 'increase'}}
        """
        # Get cash balance changes
        changes = self.get_cash_balance_change()

        # Build trend data for each period
        trends: Dict[str, Dict[str, Any]] = {}

        for period, change in changes.items():
            # Determine direction based on change value
            if change > 0:
                direction = 'increase'
            elif change < 0:
                direction = 'decrease'
            else:
                direction = 'stable'

            trends[period] = {
                'change': change,
                'direction': direction
            }

        return trends
