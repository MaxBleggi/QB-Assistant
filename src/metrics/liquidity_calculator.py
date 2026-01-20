"""
LiquidityCalculator for computing working capital and liquidity metrics.

Provides methods for calculating working capital from Balance Sheet data.
"""
from typing import Any, Dict

from src.models.balance_sheet import BalanceSheetModel


class LiquidityCalculator:
    """
    Calculator for liquidity metrics and working capital analysis.

    Computes working capital (current assets - current liabilities) from
    Balance Sheet data using hierarchical account traversal.
    """

    def __init__(self, balance_sheet_model: BalanceSheetModel):
        """
        Initialize calculator with BalanceSheetModel instance.

        Args:
            balance_sheet_model: BalanceSheetModel instance with balance sheet data
        """
        self.balance_sheet_model = balance_sheet_model

    def get_working_capital(self) -> Dict[str, float]:
        """
        Calculate working capital for all periods.

        Formula: current_assets - current_liabilities

        Locates 'Current Assets' and 'Current Liabilities' parent nodes in the
        Balance Sheet hierarchy and sums their children. Non-current assets and
        liabilities are excluded.

        Returns:
            Dict mapping period labels to working capital values
            Example: {'2024-01-31': 100000.0, '2024-02-28': 95000.0}
        """
        # Get assets and liabilities sections
        assets_section = self.balance_sheet_model.get_assets()
        liabilities_section = self.balance_sheet_model.get_liabilities()

        # Initialize period totals
        current_assets_totals: Dict[str, float] = {}
        current_liabilities_totals: Dict[str, float] = {}

        def sum_section_recursive(node: Any, target_section: str, totals: Dict[str, float]) -> None:
            """
            Recursively find and sum a specific section (e.g., 'Current Assets').

            Args:
                node: Current node in hierarchy tree
                target_section: Section name to find and sum
                totals: Dict to accumulate period totals
            """
            if isinstance(node, dict):
                # Check if this node is the target section
                name = node.get('name', '')

                if name == target_section:
                    # Found target section - sum all children
                    sum_children_recursive(node, totals)
                    return

                # Not the target, but might contain it - check children
                if 'children' in node:
                    for child in node['children']:
                        sum_section_recursive(child, target_section, totals)

            elif isinstance(node, list):
                for item in node:
                    sum_section_recursive(item, target_section, totals)

        def sum_children_recursive(node: Any, totals: Dict[str, float]) -> None:
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

        # Find and sum Current Assets
        sum_section_recursive(assets_section, 'Current Assets', current_assets_totals)

        # Find and sum Current Liabilities
        sum_section_recursive(liabilities_section, 'Current Liabilities', current_liabilities_totals)

        # Calculate working capital for each period
        working_capital: Dict[str, float] = {}

        # Get all periods from both current assets and current liabilities
        all_periods = set(current_assets_totals.keys()) | set(current_liabilities_totals.keys())

        for period in all_periods:
            current_assets = current_assets_totals.get(period, 0.0)
            current_liabilities = current_liabilities_totals.get(period, 0.0)
            working_capital[period] = current_assets - current_liabilities

        return working_capital
