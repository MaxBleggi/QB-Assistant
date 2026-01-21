"""
BudgetCalculator service for generating budget projections from historical data.

Applies user-defined parameters (growth rates, adjustments, overrides) to historical
P&L data to generate current year budgets. Supports multiple budget methodologies:
- Growth from prior year (apply percentage to last period)
- Historical average (average across all periods)
- Zero-based (start from zero)
"""
from typing import Any, Dict
import copy

import pandas as pd

from src.models import PLModel, ParameterModel, BudgetModel


class BudgetCalculator:
    """
    Calculator for budget projections based on historical data and parameters.

    Accepts PLModel (historical) and ParameterModel (budget params) as inputs,
    applies methodology and parameters in defined order, returns BudgetModel.
    """

    def __init__(self, pl_model: PLModel, param_model: ParameterModel):
        """
        Initialize calculator with historical data and budget parameters.

        Args:
            pl_model: PLModel instance with historical P&L data
            param_model: ParameterModel instance with budget parameters
        """
        self.pl_model = pl_model
        self.param_model = param_model

    def calculate(self) -> BudgetModel:
        """
        Calculate budget projections by applying parameters to historical data.

        Process:
        1. Apply base methodology (growth_from_prior_year, historical_average, or zero_based)
        2. Apply percentage growth rates (revenue_growth_rate, category_growth_rates)
        3. Apply absolute adjustments (expense_adjustment_factor)
        4. Apply account overrides (account_overrides)

        Returns:
            BudgetModel instance with budget projections in same structure as PLModel
        """
        # Deep copy hierarchy to avoid mutating historical data
        budget_hierarchy = copy.deepcopy(self.pl_model.hierarchy)

        # Get methodology from parameters
        methodology = self.param_model.parameters.get('budget_methodology', 'growth_from_prior_year')

        # Get all periods from historical data
        periods = self.pl_model.get_periods()

        # Step 1: Apply base methodology
        self._apply_base_methodology(budget_hierarchy, methodology, periods)

        # Step 2: Apply percentage growth rates
        self._apply_percentage_growth(budget_hierarchy, periods)

        # Step 3: Apply absolute adjustments
        self._apply_absolute_adjustments(budget_hierarchy, periods)

        # Step 4: Apply account overrides
        self._apply_account_overrides(budget_hierarchy, periods)

        # Create DataFrame for BudgetModel (placeholder with account names)
        df = self._create_budget_dataframe(budget_hierarchy, periods)

        # Calculate budget totals/subtotals for calculated_rows
        calculated_rows = self._calculate_totals(budget_hierarchy, periods)

        return BudgetModel(df=df, hierarchy=budget_hierarchy, calculated_rows=calculated_rows)

    def _apply_base_methodology(self, hierarchy: Dict[str, Any], methodology: str, periods: list) -> None:
        """
        Apply base budget methodology to all accounts in hierarchy.

        Args:
            hierarchy: Budget hierarchy tree (modified in place)
            methodology: Methodology name ('growth_from_prior_year', 'historical_average', 'zero_based')
            periods: List of period labels
        """
        def process_node(node: Any) -> None:
            """Recursively process hierarchy nodes."""
            if isinstance(node, dict):
                # Skip parent nodes - only process leaf accounts
                if node.get('parent', False):
                    # Still traverse children
                    if 'children' in node:
                        for child in node['children']:
                            process_node(child)
                    return

                # Process leaf node with values
                if 'values' in node and isinstance(node['values'], dict):
                    historical_values = node['values']
                    budget_values = {}

                    if methodology == 'growth_from_prior_year':
                        # Use last period value for all budget periods
                        if historical_values:
                            last_period_value = list(historical_values.values())[-1]
                            for period in periods:
                                budget_values[period] = last_period_value
                        else:
                            for period in periods:
                                budget_values[period] = 0.0

                    elif methodology == 'historical_average':
                        # Calculate average across all historical periods
                        if historical_values:
                            avg_value = sum(historical_values.values()) / len(historical_values)
                            for period in periods:
                                budget_values[period] = avg_value
                        else:
                            for period in periods:
                                budget_values[period] = 0.0

                    elif methodology == 'zero_based':
                        # Set all values to zero
                        for period in periods:
                            budget_values[period] = 0.0

                    else:
                        # Default to growth_from_prior_year
                        if historical_values:
                            last_period_value = list(historical_values.values())[-1]
                            for period in periods:
                                budget_values[period] = last_period_value
                        else:
                            for period in periods:
                                budget_values[period] = 0.0

                    # Update node values with budget values
                    node['values'] = budget_values

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        process_node(child)

                # Traverse all dict values
                for key, value in node.items():
                    if key not in ['values', 'children', 'name', 'parent', 'total']:
                        process_node(value)

            elif isinstance(node, list):
                for item in node:
                    process_node(item)

        # Process entire hierarchy
        process_node(hierarchy)

    def _apply_percentage_growth(self, hierarchy: Dict[str, Any], periods: list) -> None:
        """
        Apply percentage growth rates to budget values.

        Args:
            hierarchy: Budget hierarchy tree (modified in place)
            periods: List of period labels
        """
        # Get growth rates from parameters
        revenue_growth_rate = self.param_model.parameters.get('revenue_growth_rate', 0.0)
        category_growth_rates = self.param_model.parameters.get('category_growth_rates', {})

        def process_node(node: Any, section_name: str = None, account_name: str = None) -> None:
            """Recursively apply growth rates."""
            if isinstance(node, dict):
                # Track section and account names for category-specific rates
                current_section = section_name
                current_account = account_name

                if 'name' in node:
                    current_account = node['name']

                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            process_node(child, current_section, current_account)
                    return

                # Apply growth rate to leaf node values
                if 'values' in node and isinstance(node['values'], dict):
                    # Determine which growth rate to use
                    growth_rate = 0.0

                    # Check if category-specific rate exists
                    if current_account and current_account in category_growth_rates:
                        growth_rate = category_growth_rates[current_account]
                    # Apply revenue growth to Income section
                    elif current_section == 'Income':
                        growth_rate = revenue_growth_rate

                    # Apply growth rate to all periods
                    if growth_rate != 0.0:
                        for period in node['values']:
                            node['values'][period] *= (1 + growth_rate)

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        process_node(child, current_section, current_account)

            elif isinstance(node, list):
                for item in node:
                    process_node(item, section_name, account_name)

        # Process each top-level section
        for section_name, section_data in hierarchy.items():
            process_node(section_data, section_name=section_name)

    def _apply_absolute_adjustments(self, hierarchy: Dict[str, Any], periods: list) -> None:
        """
        Apply absolute dollar adjustments to budget values.

        Args:
            hierarchy: Budget hierarchy tree (modified in place)
            periods: List of period labels
        """
        # Get expense adjustment factors from parameters
        expense_adjustments = self.param_model.parameters.get('expense_adjustment_factor', {})

        if not expense_adjustments:
            return

        def process_node(node: Any) -> None:
            """Recursively apply absolute adjustments."""
            if isinstance(node, dict):
                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            process_node(child)
                    return

                # Apply adjustment if account name matches
                if 'name' in node and node['name'] in expense_adjustments:
                    adjustment = expense_adjustments[node['name']]

                    if 'values' in node and isinstance(node['values'], dict):
                        # Add adjustment to each period
                        for period in node['values']:
                            node['values'][period] += adjustment

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        process_node(child)

                # Traverse dict values
                for key, value in node.items():
                    if key not in ['values', 'children', 'name', 'parent', 'total']:
                        process_node(value)

            elif isinstance(node, list):
                for item in node:
                    process_node(item)

        # Process entire hierarchy
        process_node(hierarchy)

    def _apply_account_overrides(self, hierarchy: Dict[str, Any], periods: list) -> None:
        """
        Apply account-level overrides, creating new accounts if needed.

        Args:
            hierarchy: Budget hierarchy tree (modified in place)
            periods: List of period labels
        """
        # Get account overrides from parameters
        account_overrides = self.param_model.parameters.get('account_overrides', {})

        if not account_overrides:
            return

        for account_name, override_values in account_overrides.items():
            # Find account in hierarchy
            account_node = self._find_account_by_name(hierarchy, account_name)

            if account_node:
                # Account exists - replace values with overrides
                if isinstance(override_values, dict):
                    account_node['values'] = override_values.copy()
            else:
                # Account doesn't exist - create new leaf node
                # Add to Income section as default (new revenue line)
                if 'Income' not in hierarchy:
                    hierarchy['Income'] = {'children': []}

                if 'children' not in hierarchy['Income']:
                    hierarchy['Income']['children'] = []

                # Create new account node
                new_account = {
                    'name': account_name,
                    'values': override_values.copy() if isinstance(override_values, dict) else {}
                }

                hierarchy['Income']['children'].append(new_account)

    def _find_account_by_name(self, hierarchy: Dict[str, Any], account_name: str) -> Dict[str, Any]:
        """
        Search hierarchy for account by name.

        Args:
            hierarchy: Hierarchy tree to search
            account_name: Account name to find

        Returns:
            Account node dict if found, None otherwise
        """
        def search_node(node: Any) -> Dict[str, Any]:
            """Recursively search for account."""
            if isinstance(node, dict):
                # Check if this node matches
                if node.get('name') == account_name:
                    return node

                # Search children
                if 'children' in node:
                    for child in node['children']:
                        result = search_node(child)
                        if result:
                            return result

                # Search dict values
                for key, value in node.items():
                    if key != 'name':
                        result = search_node(value)
                        if result:
                            return result

            elif isinstance(node, list):
                for item in node:
                    result = search_node(item)
                    if result:
                        return result

            return None

        return search_node(hierarchy)

    def _create_budget_dataframe(self, hierarchy: Dict[str, Any], periods: list) -> pd.DataFrame:
        """
        Create DataFrame with budget account metadata.

        Args:
            hierarchy: Budget hierarchy tree
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

    def _calculate_totals(self, hierarchy: Dict[str, Any], periods: list) -> list:
        """
        Calculate budget totals and subtotals for calculated_rows.

        Args:
            hierarchy: Budget hierarchy tree
            periods: List of period labels

        Returns:
            List of calculated row dicts
        """
        calculated_rows = []

        # Calculate Income total
        income_total = self._sum_section_values(hierarchy.get('Income', {}), periods)
        if income_total:
            calculated_rows.append({
                'account_name': 'Total Income',
                'values': income_total
            })

        # Calculate Expenses total
        expenses_total = self._sum_section_values(hierarchy.get('Expenses', {}), periods)
        if expenses_total:
            calculated_rows.append({
                'account_name': 'Total Expenses',
                'values': expenses_total
            })

        # Calculate Net Income (Income - Expenses)
        if income_total and expenses_total:
            net_income = {}
            for period in periods:
                net_income[period] = income_total.get(period, 0.0) - expenses_total.get(period, 0.0)

            calculated_rows.append({
                'account_name': 'Net Income',
                'values': net_income
            })

        return calculated_rows

    def _sum_section_values(self, section: Dict[str, Any], periods: list) -> Dict[str, float]:
        """
        Sum all leaf node values in a section.

        Args:
            section: Section dict from hierarchy
            periods: List of period labels

        Returns:
            Dict mapping periods to summed values
        """
        period_totals = {period: 0.0 for period in periods}

        def sum_node(node: Any) -> None:
            """Recursively sum leaf node values."""
            if isinstance(node, dict):
                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            sum_node(child)
                    return

                # Sum leaf node values
                if 'values' in node and isinstance(node['values'], dict):
                    for period, value in node['values'].items():
                        if period in period_totals:
                            period_totals[period] += value

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        sum_node(child)

            elif isinstance(node, list):
                for item in node:
                    sum_node(item)

        sum_node(section)
        return period_totals
