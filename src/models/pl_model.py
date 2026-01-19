"""
PLModel - Data model for Profit & Loss with period-aware hierarchy support.

Extends DataModel base class to add P&L-specific functionality:
- Period-aware hierarchy tree storage and access
- Section-specific accessors (get_income, get_cogs, get_expenses, get_other_expenses)
- Period utilities (get_periods)
- Calculated row access (get_calculated_row)
- Account lookup by name with period data
- Serialization with hierarchy and calculated rows preservation
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import DataModel


class PLModel(DataModel):
    """
    Data model for QuickBooks Profit & Loss with multi-period support.

    Stores:
    - Raw DataFrame (for tabular operations)
    - Hierarchy tree with period-aware values (for structural queries)
    - Calculated rows (Gross Profit, Net Income, etc.)

    Provides convenient accessors for sections, periods, and account lookup.
    """

    def __init__(self, df: pd.DataFrame, hierarchy: Dict[str, Any], calculated_rows: List[Dict[str, Any]]):
        """
        Initialize model with DataFrame, hierarchy tree, and calculated rows.

        Args:
            df: Validated pandas DataFrame with account metadata
            hierarchy: Hierarchy tree dict from parser with period-aware values
            calculated_rows: List of calculated row dicts (Gross Profit, Net Income, etc.)
        """
        super().__init__(df)
        self._hierarchy = hierarchy
        self._calculated_rows = calculated_rows

    @property
    def hierarchy(self) -> Dict[str, Any]:
        """
        Get the hierarchy tree.

        Returns:
            Hierarchy dict with sections as top-level keys, period-aware values at nodes
        """
        return self._hierarchy

    @property
    def calculated_rows(self) -> List[Dict[str, Any]]:
        """
        Get the calculated rows (Gross Profit, Net Income, etc.).

        Returns:
            List of dicts with 'account_name' and 'values' (period dict) keys
        """
        return self._calculated_rows

    def get_income(self) -> Dict[str, Any]:
        """
        Get the Income section from hierarchy.

        Returns:
            Dict containing Income section tree with period-aware values, or empty dict if missing
        """
        return self._hierarchy.get('Income', {})

    def get_cogs(self) -> Optional[Dict[str, Any]]:
        """
        Get the Cost of Goods Sold section from hierarchy.

        COGS is optional in P&L (service businesses may not have COGS).

        Returns:
            Dict containing COGS section tree with period-aware values, or None if not present
        """
        cogs = self._hierarchy.get('Cost of Goods Sold')
        return cogs if cogs else None

    def get_expenses(self) -> Dict[str, Any]:
        """
        Get the Expenses section from hierarchy.

        Returns:
            Dict containing Expenses section tree with period-aware values, or empty dict if missing
        """
        return self._hierarchy.get('Expenses', {})

    def get_other_expenses(self) -> Optional[Dict[str, Any]]:
        """
        Get the Other Expenses section from hierarchy.

        Other Expenses is optional in P&L.

        Returns:
            Dict containing Other Expenses section tree with period-aware values, or None if not present
        """
        other = self._hierarchy.get('Other Expenses')
        return other if other else None

    def get_periods(self) -> List[str]:
        """
        Get list of all period labels available in the dataset.

        Extracts period labels from the first account with values in the hierarchy.

        Returns:
            List of period label strings (e.g., ['Nov 1 - Nov 30 2025', 'Nov 1 - Nov 30 2024 (PY)'])
            Returns empty list if no periods found
        """
        # Search hierarchy for first node with values dict
        def find_first_values(node: Any) -> Optional[Dict[str, float]]:
            """Recursively search tree for first values dict."""
            if isinstance(node, dict):
                # Check if this node has values dict
                if 'values' in node and isinstance(node['values'], dict):
                    return node['values']

                # Search children if present
                if 'children' in node:
                    for child in node['children']:
                        result = find_first_values(child)
                        if result:
                            return result

                # Search all values in dict
                for key, value in node.items():
                    if key != 'values':  # Avoid redundant check
                        result = find_first_values(value)
                        if result:
                            return result

            elif isinstance(node, list):
                # Search each item in list
                for item in node:
                    result = find_first_values(item)
                    if result:
                        return result

            return None

        # Find first values dict in hierarchy
        first_values = find_first_values(self._hierarchy)

        if first_values:
            return list(first_values.keys())
        else:
            # Fallback: check calculated rows
            if self._calculated_rows:
                first_calc = self._calculated_rows[0]
                if 'values' in first_calc:
                    return list(first_calc['values'].keys())

        return []

    def get_calculated_row(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a calculated row by name (e.g., 'Net Income', 'Gross Profit').

        Args:
            name: Account name of calculated row

        Returns:
            Dict with 'account_name' and 'values' (period dict), or None if not found
        """
        for row in self._calculated_rows:
            if row.get('account_name') == name:
                return row
        return None

    def get_account_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Search hierarchy tree for account by name.

        Performs recursive search through all sections and nested accounts.
        Returns accounts with period-aware values dict.

        Args:
            name: Account name to search for

        Returns:
            Account dict with 'values' period dict if found, None otherwise
        """
        def search_tree(node: Any, target: str) -> Optional[Dict[str, Any]]:
            """Recursively search tree for account name."""
            if isinstance(node, dict):
                # Check if this node has a name that matches
                if node.get('name') == target:
                    return node

                # Search children if present
                if 'children' in node:
                    for child in node['children']:
                        result = search_tree(child, target)
                        if result:
                            return result

                # Search all values in dict
                for key, value in node.items():
                    if key != 'name':  # Avoid redundant check
                        result = search_tree(value, target)
                        if result:
                            return result

            elif isinstance(node, list):
                # Search each item in list
                for item in node:
                    result = search_tree(item, target)
                    if result:
                        return result

            return None

        # Search entire hierarchy tree
        return search_tree(self._hierarchy, name)

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary including DataFrame, hierarchy, and calculated rows.

        Overrides base DataModel.to_dict() to include hierarchy tree and calculated rows.

        Args:
            orient: Format for DataFrame conversion (default: 'records')

        Returns:
            Dict with 'dataframe', 'hierarchy', and 'calculated_rows' keys
        """
        return {
            'dataframe': self._df.to_dict(orient=orient),
            'hierarchy': self._hierarchy,
            'calculated_rows': self._calculated_rows
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'PLModel':
        """
        Create PLModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', and 'calculated_rows' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New PLModel instance

        Raises:
            ValueError: If data is missing required keys
        """
        if 'dataframe' not in data:
            raise ValueError("Missing 'dataframe' key in data")
        if 'hierarchy' not in data:
            raise ValueError("Missing 'hierarchy' key in data")
        if 'calculated_rows' not in data:
            raise ValueError("Missing 'calculated_rows' key in data")

        # Reconstruct DataFrame
        if orient == 'records':
            df = pd.DataFrame(data['dataframe'])
        else:
            df = pd.DataFrame.from_dict(data['dataframe'], orient=orient)

        # Get hierarchy and calculated rows
        hierarchy = data['hierarchy']
        calculated_rows = data['calculated_rows']

        return cls(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows)
