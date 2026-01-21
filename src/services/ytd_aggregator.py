"""
YTDAggregator service for calculating year-to-date aggregations.

Accumulates monthly budget and actual values from fiscal year start, computes:
- Cumulative budget and actual values
- Cumulative dollar variance (cumulative_actual - cumulative_budget)
- Cumulative percentage variance
- YTD percentage of budget
- Favorable vs unfavorable determination (section-aware)
- Section-level summaries
"""
from typing import Any, Dict, List, Tuple
from datetime import datetime

import pandas as pd

from src.models import BudgetModel, PLModel, YTDModel


class YTDAggregator:
    """
    Aggregator for year-to-date cumulative budget and actual analysis.

    Accepts BudgetModel and PLModel as inputs, orders periods by fiscal year,
    accumulates values cumulatively, calculates YTD variances, computes section
    summaries, returns YTDModel.
    """

    def __init__(self, budget_model: BudgetModel, pl_model: PLModel):
        """
        Initialize aggregator with budget and actual data.

        Args:
            budget_model: BudgetModel instance with budget projections
            pl_model: PLModel instance with actual P&L data
        """
        self._budget_model = budget_model
        self._pl_model = pl_model

    def calculate(self, fiscal_year_start_month: int = 1) -> YTDModel:
        """
        Calculate year-to-date aggregations with fiscal year ordering.

        Process:
        1. Extract periods from PLModel
        2. Order periods by fiscal year (reorder if fiscal_year_start_month != 1)
        3. Detect aggregation start period (earliest available)
        4. Iterate periods in fiscal order, accumulate budget and actual values
        5. For each period, compute cumulative variances
        6. Build YTD hierarchy with cumulative data per account per period
        7. Calculate section-level summaries
        8. Create DataFrame and return YTDModel instance

        Args:
            fiscal_year_start_month: Fiscal year start month (1=Jan, 7=Jul, etc.)

        Returns:
            YTDModel instance with cumulative YTD hierarchy, calculated_rows, and metadata
        """
        # Extract periods from PLModel
        periods = self._pl_model.get_periods()

        # Order periods by fiscal year
        ordered_periods = self._order_periods_by_fiscal_year(periods, fiscal_year_start_month)

        # Detect aggregation start period (earliest available)
        aggregation_start_period = ordered_periods[0] if ordered_periods else None

        # Get hierarchies from models
        budget_hierarchy = self._budget_model.hierarchy
        pl_hierarchy = self._pl_model.hierarchy

        # Build YTD hierarchy
        ytd_hierarchy = {}

        # Process each section (Income, Expenses)
        for section_name in ['Income', 'Expenses']:
            budget_section = budget_hierarchy.get(section_name, {})
            pl_section = pl_hierarchy.get(section_name, {})

            if budget_section or pl_section:
                ytd_section = self._process_section(
                    section_name,
                    budget_section,
                    pl_section,
                    ordered_periods
                )
                ytd_hierarchy[section_name] = ytd_section

        # Create DataFrame for YTDModel
        df = self._create_ytd_dataframe(ytd_hierarchy)

        # Calculate section-level summaries
        calculated_rows = self._calculate_section_summaries(ytd_hierarchy, ordered_periods)

        return YTDModel(
            df=df,
            hierarchy=ytd_hierarchy,
            calculated_rows=calculated_rows,
            fiscal_year_start_month=fiscal_year_start_month,
            aggregation_start_period=aggregation_start_period
        )

    def _order_periods_by_fiscal_year(
        self,
        periods: List[str],
        fiscal_year_start_month: int
    ) -> List[str]:
        """
        Order periods by fiscal year (calendar or non-calendar).

        Args:
            periods: List of period labels in 'YYYY-MM' format
            fiscal_year_start_month: Fiscal year start month (1-12)

        Returns:
            List of period labels ordered by fiscal year
        """
        if not periods:
            return []

        # Parse periods to datetime objects for sorting
        parsed_periods = []
        for period in periods:
            try:
                # Parse 'YYYY-MM' format
                dt = datetime.strptime(period, '%Y-%m')
                parsed_periods.append((period, dt))
            except ValueError:
                # If parsing fails, skip this period
                continue

        # Sort by datetime (chronological order)
        parsed_periods.sort(key=lambda x: x[1])

        # If fiscal year starts in January (calendar year), return chronological order
        if fiscal_year_start_month == 1:
            return [p[0] for p in parsed_periods]

        # For non-calendar fiscal years, reorder periods
        # Split periods into fiscal year groups and reorder
        fiscal_ordered = []
        current_fiscal_year = []

        for period, dt in parsed_periods:
            # Check if this period starts a new fiscal year
            if dt.month >= fiscal_year_start_month and current_fiscal_year:
                # Check if we've crossed into a new fiscal year
                if current_fiscal_year and current_fiscal_year[-1][1].month < fiscal_year_start_month:
                    # New fiscal year starts
                    fiscal_ordered.extend([p[0] for p in current_fiscal_year])
                    current_fiscal_year = [(period, dt)]
                else:
                    current_fiscal_year.append((period, dt))
            else:
                current_fiscal_year.append((period, dt))

        # Add remaining periods
        if current_fiscal_year:
            fiscal_ordered.extend([p[0] for p in current_fiscal_year])

        return fiscal_ordered if fiscal_ordered else [p[0] for p in parsed_periods]

    def _process_section(
        self,
        section_name: str,
        budget_section: Dict[str, Any],
        pl_section: Dict[str, Any],
        ordered_periods: List[str]
    ) -> Dict[str, Any]:
        """
        Process a single section (Income or Expenses) to calculate YTD aggregations.

        Args:
            section_name: Section name ('Income' or 'Expenses')
            budget_section: Budget section from hierarchy
            pl_section: Actual section from hierarchy
            ordered_periods: List of period labels in fiscal year order

        Returns:
            YTD section dict with children containing cumulative variance attributes
        """
        # Create section container
        ytd_section = {
            'name': section_name,
            'children': []
        }

        # Get all account names from both budget and actual
        budget_accounts = self._extract_account_names(budget_section)
        pl_accounts = self._extract_account_names(pl_section)
        all_accounts = list(set(budget_accounts + pl_accounts))

        # Process each account
        for account_name in all_accounts:
            # Find account nodes in hierarchies
            budget_node = self._find_account_by_name(budget_section, account_name)
            pl_node = self._find_account_by_name(pl_section, account_name)

            # Calculate YTD for this account
            ytd_account = self._calculate_account_ytd(
                account_name,
                budget_node,
                pl_node,
                section_name,
                ordered_periods
            )
            ytd_section['children'].append(ytd_account)

        return ytd_section

    def _calculate_account_ytd(
        self,
        account_name: str,
        budget_node: Dict[str, Any],
        pl_node: Dict[str, Any],
        section_name: str,
        ordered_periods: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate YTD aggregation for a single account across all periods.

        Args:
            account_name: Account name
            budget_node: Budget account node with values dict (or None)
            pl_node: Actual account node with values dict (or None)
            section_name: Section name for favorable/unfavorable logic
            ordered_periods: List of period labels in fiscal year order

        Returns:
            YTD account dict with cumulative_budget, cumulative_actual,
            cumulative_dollar_variance, cumulative_pct_variance, ytd_pct_of_budget,
            is_favorable, is_flagged per period
        """
        budget_values = budget_node.get('values', {}) if budget_node else {}
        pl_values = pl_node.get('values', {}) if pl_node else {}

        ytd_data = {}
        cumulative_budget = 0.0
        cumulative_actual = 0.0

        for period in ordered_periods:
            # Get period values
            period_budget = budget_values.get(period, 0.0)
            period_actual = pl_values.get(period, 0.0)

            # Accumulate
            cumulative_budget += period_budget
            cumulative_actual += period_actual

            # Calculate cumulative dollar variance
            cumulative_dollar_variance = cumulative_actual - cumulative_budget

            # Calculate cumulative percentage variance (handle zero budget)
            if cumulative_budget != 0:
                cumulative_pct_variance = (cumulative_dollar_variance / cumulative_budget) * 100
            else:
                cumulative_pct_variance = 0.0

            # Calculate YTD percentage of budget
            if cumulative_budget != 0:
                ytd_pct_of_budget = (cumulative_actual / cumulative_budget) * 100
            else:
                ytd_pct_of_budget = 0.0

            # Determine if favorable
            is_favorable = self._is_favorable(section_name, cumulative_dollar_variance)

            # No flagging logic in this implementation (as per non_goals)
            is_flagged = False

            ytd_data[period] = {
                'cumulative_budget': cumulative_budget,
                'cumulative_actual': cumulative_actual,
                'cumulative_dollar_variance': cumulative_dollar_variance,
                'cumulative_pct_variance': cumulative_pct_variance,
                'ytd_pct_of_budget': ytd_pct_of_budget,
                'is_favorable': is_favorable,
                'is_flagged': is_flagged
            }

        return {
            'name': account_name,
            'values': ytd_data
        }

    def _is_favorable(self, section_name: str, cumulative_dollar_variance: float) -> bool:
        """
        Determine if cumulative variance is favorable based on section type.

        For Income: cumulative_actual > cumulative_budget (positive variance) is favorable
        For Expenses: cumulative_actual < cumulative_budget (negative variance) is favorable

        Args:
            section_name: Section name ('Income' or 'Expenses')
            cumulative_dollar_variance: Cumulative dollar variance (cumulative_actual - cumulative_budget)

        Returns:
            True if variance is favorable, False otherwise
        """
        if section_name == 'Income':
            return cumulative_dollar_variance > 0  # More revenue is good
        else:  # Expenses
            return cumulative_dollar_variance < 0  # Less expenses is good

    def _calculate_section_summaries(
        self,
        ytd_hierarchy: Dict[str, Any],
        ordered_periods: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate section-level YTD summaries for calculated_rows.

        Args:
            ytd_hierarchy: YTD hierarchy tree
            ordered_periods: List of period labels in fiscal year order

        Returns:
            Dict mapping section names to period dicts with aggregated YTD data
        """
        calculated_rows = {}

        # Calculate Income YTD summary
        income_summary = self._sum_section_ytd(ytd_hierarchy.get('Income', {}), ordered_periods)
        if income_summary:
            calculated_rows['income'] = income_summary

        # Calculate Expenses YTD summary
        expenses_summary = self._sum_section_ytd(ytd_hierarchy.get('Expenses', {}), ordered_periods)
        if expenses_summary:
            calculated_rows['expenses'] = expenses_summary

        return calculated_rows

    def _sum_section_ytd(
        self,
        section: Dict[str, Any],
        ordered_periods: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Sum all YTD values in a section across all accounts.

        Args:
            section: Section dict from YTD hierarchy
            ordered_periods: List of period labels in fiscal year order

        Returns:
            Dict mapping periods to aggregated cumulative YTD data
        """
        # Initialize period totals
        period_totals = {}
        for period in ordered_periods:
            period_totals[period] = {
                'cumulative_budget': 0.0,
                'cumulative_actual': 0.0,
                'cumulative_dollar_variance': 0.0,
                'cumulative_pct_variance': 0.0,
                'ytd_pct_of_budget': 0.0,
                'is_favorable': None,
                'is_flagged': False
            }

        def sum_node(node: Any) -> None:
            """Recursively sum YTD values."""
            if isinstance(node, dict):
                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            sum_node(child)
                    return

                # Sum leaf node values
                if 'values' in node and isinstance(node['values'], dict):
                    for period, ytd_data in node['values'].items():
                        if period in period_totals and isinstance(ytd_data, dict):
                            period_totals[period]['cumulative_budget'] += ytd_data.get('cumulative_budget', 0.0)
                            period_totals[period]['cumulative_actual'] += ytd_data.get('cumulative_actual', 0.0)
                            period_totals[period]['cumulative_dollar_variance'] += ytd_data.get('cumulative_dollar_variance', 0.0)

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        sum_node(child)

            elif isinstance(node, list):
                for item in node:
                    sum_node(item)

        sum_node(section)

        # Calculate percentage variance and ytd_pct_of_budget for totals
        for period in period_totals:
            cumulative_budget_total = period_totals[period]['cumulative_budget']
            cumulative_actual_total = period_totals[period]['cumulative_actual']
            cumulative_variance_total = period_totals[period]['cumulative_dollar_variance']

            if cumulative_budget_total != 0:
                period_totals[period]['cumulative_pct_variance'] = (
                    cumulative_variance_total / cumulative_budget_total
                ) * 100
                period_totals[period]['ytd_pct_of_budget'] = (
                    cumulative_actual_total / cumulative_budget_total
                ) * 100

        return period_totals if any(period_totals.values()) else {}

    def _extract_account_names(self, section: Dict[str, Any]) -> List[str]:
        """
        Extract all account names from a section hierarchy.

        Args:
            section: Section dict from hierarchy

        Returns:
            List of account names
        """
        names = []

        def traverse_node(node: Any) -> None:
            """Recursively extract account names."""
            if isinstance(node, dict):
                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            traverse_node(child)
                    return

                if 'name' in node and 'values' in node:
                    names.append(node['name'])

                if 'children' in node:
                    for child in node['children']:
                        traverse_node(child)

            elif isinstance(node, list):
                for item in node:
                    traverse_node(item)

        traverse_node(section)
        return names

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

    def _create_ytd_dataframe(self, ytd_hierarchy: Dict[str, Any]) -> pd.DataFrame:
        """
        Create DataFrame with YTD account metadata.

        Args:
            ytd_hierarchy: YTD hierarchy tree

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
        for section_name, section_data in ytd_hierarchy.items():
            extract_accounts(section_data, section_name)

        return pd.DataFrame(rows) if rows else pd.DataFrame()
