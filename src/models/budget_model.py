"""
BudgetModel - Data model for budget projections with period-aware hierarchy support.

Extends DataModel base class to add budget-specific functionality:
- Period-aware hierarchy tree storage and access (mirroring PLModel structure)
- Section-specific accessors (get_income, get_expenses)
- Period utilities (get_period_column)
- Serialization with hierarchy and calculated rows preservation
"""
from typing import Any, Dict, List

import pandas as pd

from .base import DataModel


class BudgetModel(DataModel):
    """
    Data model for budget projections with multi-period support.

    Stores:
    - Raw DataFrame (for tabular operations)
    - Hierarchy tree with period-aware values (for structural queries)
    - Calculated rows (totals, subtotals)

    Provides convenient accessors for sections and periods.
    Mirrors PLModel structure for easy comparison between budgets and actuals.
    """

    def __init__(self, df: pd.DataFrame, hierarchy: Dict[str, Any], calculated_rows: List[Dict[str, Any]]):
        """
        Initialize model with DataFrame, hierarchy tree, and calculated rows.

        Args:
            df: Validated pandas DataFrame with account metadata
            hierarchy: Hierarchy tree dict with period-aware values
            calculated_rows: List of calculated row dicts (totals, subtotals)
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
        Get the calculated rows (totals, subtotals).

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

    def get_expenses(self) -> Dict[str, Any]:
        """
        Get the Expenses section from hierarchy.

        Returns:
            Dict containing Expenses section tree with period-aware values, or empty dict if missing
        """
        return self._hierarchy.get('Expenses', {})

    def get_period_column(self, period_index: int) -> str:
        """
        Get period column name for given period index.

        Extracts period labels from first account with values in hierarchy,
        then returns the column name at the specified index.

        Args:
            period_index: Zero-based index of period (0 = first period, 1 = second, etc.)

        Returns:
            Period column name (e.g., 'Jan 2024', 'Feb 2024')

        Raises:
            IndexError: If period_index is out of range
        """
        # Search hierarchy for first node with values dict
        def find_first_values(node: Any) -> Dict[str, float]:
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
            periods = list(first_values.keys())
            return periods[period_index]
        else:
            # Fallback: check calculated rows
            if self._calculated_rows:
                first_calc = self._calculated_rows[0]
                if 'values' in first_calc:
                    periods = list(first_calc['values'].keys())
                    return periods[period_index]

        raise IndexError(f"Period index {period_index} out of range - no periods found in hierarchy")

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
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'BudgetModel':
        """
        Create BudgetModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', and 'calculated_rows' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New BudgetModel instance

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
