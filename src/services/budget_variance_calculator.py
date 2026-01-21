"""
BudgetVarianceCalculator service for calculating budget vs actual variances.

Compares budget projections to actual P&L results, calculating:
- Dollar variance (actual - budget)
- Percentage variance ((actual - budget) / budget * 100)
- Favorable vs unfavorable determination (section-aware)
- Significant variance flagging based on configurable thresholds
"""
from typing import Any, Dict, List
import copy

import pandas as pd

from src.models import BudgetModel, PLModel, VarianceModel
from .line_item_matcher import LineItemMatcher


class BudgetVarianceCalculator:
    """
    Calculator for budget vs actual variance analysis.

    Accepts BudgetModel and PLModel as inputs, matches accounts using LineItemMatcher,
    calculates variances with proper favorable/unfavorable logic, flags significant
    deviations based on thresholds, returns VarianceModel.
    """

    def __init__(self, budget_model: BudgetModel, pl_model: PLModel):
        """
        Initialize calculator with budget and actual data.

        Args:
            budget_model: BudgetModel instance with budget projections
            pl_model: PLModel instance with actual P&L data
        """
        self._budget_model = budget_model
        self._pl_model = pl_model

    def calculate(self, threshold_pct: float, threshold_abs: float) -> VarianceModel:
        """
        Calculate budget vs actual variances with threshold-based flagging.

        Process:
        1. Match budget accounts to actual accounts using LineItemMatcher
        2. Calculate dollar variance (actual - budget)
        3. Calculate percentage variance ((actual - budget) / budget * 100)
        4. Determine favorable vs unfavorable (section-aware)
        5. Flag significant variances exceeding thresholds
        6. Build variance hierarchy with all attributes
        7. Calculate section-level summaries
        8. Return VarianceModel with variance data and unmatched lists

        Args:
            threshold_pct: Percentage threshold for flagging (e.g., 10 for 10%)
            threshold_abs: Absolute dollar threshold for flagging (e.g., 10000 for $10k)

        Returns:
            VarianceModel instance with variance hierarchy, calculated_rows, and unmatched accounts
        """
        # Get hierarchies from models
        budget_hierarchy = self._budget_model.hierarchy
        actual_hierarchy = self._pl_model.hierarchy

        # Match accounts using LineItemMatcher
        section_mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy,
            actual_hierarchy
        )

        # Build variance hierarchy
        variance_hierarchy = {}

        # Process each section (Income, Expenses)
        for section_name in ['Income', 'Expenses']:
            budget_section = budget_hierarchy.get(section_name, {})
            actual_section = actual_hierarchy.get(section_name, {})
            mapping = section_mappings.get(section_name, {})

            if budget_section or actual_section:
                variance_section = self._process_section(
                    section_name,
                    budget_section,
                    actual_section,
                    mapping,
                    threshold_pct,
                    threshold_abs
                )
                variance_hierarchy[section_name] = variance_section

        # Get periods from budget model
        periods = self._budget_model.get_periods() if hasattr(self._budget_model, 'get_periods') else []
        if not periods:
            # Fallback: extract from first account in hierarchy
            periods = self._extract_periods_from_hierarchy(variance_hierarchy)

        # Create DataFrame for VarianceModel
        df = self._create_variance_dataframe(variance_hierarchy, periods)

        # Calculate section-level summaries
        calculated_rows = self._calculate_totals(variance_hierarchy, periods)

        return VarianceModel(
            df=df,
            hierarchy=variance_hierarchy,
            calculated_rows=calculated_rows,
            unmatched_budget_accounts=unmatched_budget,
            unmatched_actual_accounts=unmatched_actual
        )

    def _process_section(
        self,
        section_name: str,
        budget_section: Dict[str, Any],
        actual_section: Dict[str, Any],
        mapping: Dict[str, str],
        threshold_pct: float,
        threshold_abs: float
    ) -> Dict[str, Any]:
        """
        Process a single section (Income or Expenses) to calculate variances.

        Args:
            section_name: Section name ('Income' or 'Expenses')
            budget_section: Budget section from hierarchy
            actual_section: Actual section from hierarchy
            mapping: Dict mapping budget account names to actual account names
            threshold_pct: Percentage threshold
            threshold_abs: Absolute threshold

        Returns:
            Variance section dict with children containing variance attributes
        """
        # Create section container
        variance_section = {
            'name': section_name,
            'children': []
        }

        # Process matched accounts
        for budget_name, actual_name in mapping.items():
            # Find account nodes in hierarchies
            budget_node = self._find_account_by_name(budget_section, budget_name)
            actual_node = self._find_account_by_name(actual_section, actual_name)

            if budget_node and actual_node:
                # Calculate variances for this account
                variance_account = self._calculate_account_variance(
                    budget_name,
                    budget_node,
                    actual_node,
                    section_name,
                    threshold_pct,
                    threshold_abs
                )
                variance_section['children'].append(variance_account)

        return variance_section

    def _calculate_account_variance(
        self,
        account_name: str,
        budget_node: Dict[str, Any],
        actual_node: Dict[str, Any],
        section_name: str,
        threshold_pct: float,
        threshold_abs: float
    ) -> Dict[str, Any]:
        """
        Calculate variance for a single matched account across all periods.

        Args:
            account_name: Account name
            budget_node: Budget account node with values dict
            actual_node: Actual account node with values dict
            section_name: Section name for favorable/unfavorable logic
            threshold_pct: Percentage threshold
            threshold_abs: Absolute threshold

        Returns:
            Variance account dict with budget_value, actual_value, dollar_variance,
            pct_variance, is_favorable, is_flagged per period
        """
        budget_values = budget_node.get('values', {})
        actual_values = actual_node.get('values', {})

        # Get all periods (union of budget and actual periods)
        all_periods = set(list(budget_values.keys()) + list(actual_values.keys()))

        variance_data = {}

        for period in all_periods:
            budget_value = budget_values.get(period, 0.0)
            actual_value = actual_values.get(period, 0.0)

            # Calculate dollar variance
            dollar_variance = actual_value - budget_value

            # Calculate percentage variance (handle zero budget)
            if budget_value != 0:
                pct_variance = (dollar_variance / budget_value) * 100
            else:
                pct_variance = None  # Cannot calculate percentage with zero budget

            # Determine if favorable
            is_favorable = self._is_favorable(section_name, dollar_variance)

            # Flag if exceeds thresholds
            is_flagged = False
            if pct_variance is not None:
                if abs(pct_variance) > threshold_pct or abs(dollar_variance) > threshold_abs:
                    is_flagged = True
            else:
                # If pct_variance is None (zero budget), flag based on absolute only
                if abs(dollar_variance) > threshold_abs:
                    is_flagged = True

            variance_data[period] = {
                'budget_value': budget_value,
                'actual_value': actual_value,
                'dollar_variance': dollar_variance,
                'pct_variance': pct_variance,
                'is_favorable': is_favorable,
                'is_flagged': is_flagged
            }

        return {
            'name': account_name,
            'values': variance_data
        }

    def _is_favorable(self, section_name: str, dollar_variance: float) -> bool:
        """
        Determine if variance is favorable based on section type.

        For Income: actual > budget (positive variance) is favorable
        For Expenses: actual < budget (negative variance) is favorable

        Args:
            section_name: Section name ('Income' or 'Expenses')
            dollar_variance: Dollar variance (actual - budget)

        Returns:
            True if variance is favorable, False otherwise
        """
        if section_name == 'Income':
            return dollar_variance > 0  # More revenue is good
        else:  # Expenses
            return dollar_variance < 0  # Less expenses is good

    def _find_account_by_name(self, section: Dict[str, Any], account_name: str) -> Dict[str, Any]:
        """
        Search section hierarchy for account by name.

        Args:
            section: Section dict from hierarchy
            account_name: Account name to find

        Returns:
            Account node dict if found, None otherwise
        """
        def search_node(node: Any) -> Dict[str, Any]:
            """Recursively search for account."""
            if isinstance(node, dict):
                # Check if this node matches
                if node.get('name') == account_name and not node.get('parent', False):
                    return node

                # Search children
                if 'children' in node:
                    for child in node['children']:
                        result = search_node(child)
                        if result:
                            return result

            elif isinstance(node, list):
                for item in node:
                    result = search_node(item)
                    if result:
                        return result

            return None

        return search_node(section)

    def _extract_periods_from_hierarchy(self, hierarchy: Dict[str, Any]) -> List[str]:
        """
        Extract period labels from variance hierarchy.

        Args:
            hierarchy: Variance hierarchy tree

        Returns:
            List of period labels
        """
        def find_first_values(node: Any) -> Dict[str, Any]:
            """Recursively search for first values dict."""
            if isinstance(node, dict):
                if 'values' in node and isinstance(node['values'], dict):
                    return node['values']

                if 'children' in node:
                    for child in node['children']:
                        result = find_first_values(child)
                        if result:
                            return result

                for key, value in node.items():
                    if key != 'values':
                        result = find_first_values(value)
                        if result:
                            return result

            elif isinstance(node, list):
                for item in node:
                    result = find_first_values(item)
                    if result:
                        return result

            return None

        first_values = find_first_values(hierarchy)
        if first_values:
            # Get first period's data (the keys in the values dict are periods)
            first_period_data = list(first_values.values())[0]
            if isinstance(first_period_data, dict):
                # This shouldn't happen in variance hierarchy, but handle gracefully
                return list(first_values.keys())
            else:
                return list(first_values.keys())
        return []

    def _create_variance_dataframe(self, hierarchy: Dict[str, Any], periods: List[str]) -> pd.DataFrame:
        """
        Create DataFrame with variance account metadata.

        Args:
            hierarchy: Variance hierarchy tree
            periods: List of period labels

        Returns:
            DataFrame with account names and metadata
        """
        rows = []

        def extract_accounts(node: Any, section: str = None) -> None:
            """Recursively extract account information."""
            if isinstance(node, dict):
                if 'name' in node:
                    rows.append({
                        'account_name': node['name'],
                        'section': section,
                        'is_parent': node.get('parent', False)
                    })

                if 'children' in node:
                    for child in node['children']:
                        extract_accounts(child, section)

            elif isinstance(node, list):
                for item in node:
                    extract_accounts(item, section)

        # Extract accounts from each section
        for section_name, section_data in hierarchy.items():
            extract_accounts(section_data, section_name)

        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def _calculate_totals(self, hierarchy: Dict[str, Any], periods: List[str]) -> List[Dict[str, Any]]:
        """
        Calculate section-level variance summaries for calculated_rows.

        Args:
            hierarchy: Variance hierarchy tree
            periods: List of period labels

        Returns:
            List of calculated row dicts with variance summaries
        """
        calculated_rows = []

        # Calculate Income variance total
        income_total = self._sum_section_variances(hierarchy.get('Income', {}), periods)
        if income_total:
            calculated_rows.append({
                'account_name': 'Total Income Variance',
                'values': income_total
            })

        # Calculate Expenses variance total
        expenses_total = self._sum_section_variances(hierarchy.get('Expenses', {}), periods)
        if expenses_total:
            calculated_rows.append({
                'account_name': 'Total Expenses Variance',
                'values': expenses_total
            })

        return calculated_rows

    def _sum_section_variances(self, section: Dict[str, Any], periods: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Sum all variance values in a section.

        Args:
            section: Section dict from variance hierarchy
            periods: List of period labels

        Returns:
            Dict mapping periods to aggregated variance data
        """
        # Initialize period totals
        period_totals = {}
        for period in periods:
            period_totals[period] = {
                'budget_value': 0.0,
                'actual_value': 0.0,
                'dollar_variance': 0.0,
                'pct_variance': None,  # Will calculate after summing
                'is_favorable': None,  # Will determine after summing
                'is_flagged': False
            }

        def sum_node(node: Any) -> None:
            """Recursively sum variance values."""
            if isinstance(node, dict):
                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            sum_node(child)
                    return

                # Sum leaf node values
                if 'values' in node and isinstance(node['values'], dict):
                    for period, variance_data in node['values'].items():
                        if period in period_totals and isinstance(variance_data, dict):
                            period_totals[period]['budget_value'] += variance_data.get('budget_value', 0.0)
                            period_totals[period]['actual_value'] += variance_data.get('actual_value', 0.0)
                            period_totals[period]['dollar_variance'] += variance_data.get('dollar_variance', 0.0)

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        sum_node(child)

            elif isinstance(node, list):
                for item in node:
                    sum_node(item)

        sum_node(section)

        # Calculate percentage variance for totals
        for period in period_totals:
            budget_total = period_totals[period]['budget_value']
            if budget_total != 0:
                period_totals[period]['pct_variance'] = (
                    period_totals[period]['dollar_variance'] / budget_total
                ) * 100

        return period_totals if any(period_totals.values()) else {}
