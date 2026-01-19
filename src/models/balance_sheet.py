"""
BalanceSheetModel - Data model for Balance Sheet with hierarchy support.

Extends DataModel base class to add Balance Sheet-specific functionality:
- Hierarchy tree storage and access
- Section-specific accessors (get_assets, get_liabilities, get_equity)
- Account lookup by name
- Serialization with hierarchy preservation
"""
from typing import Any, Dict, Optional

import pandas as pd

from .base import DataModel


class BalanceSheetModel(DataModel):
    """
    Data model for QuickBooks Balance Sheet.

    Stores both raw DataFrame (for tabular operations) and hierarchy tree
    (for structural queries). Provides convenient accessors for sections
    and account lookup.
    """

    def __init__(self, df: pd.DataFrame, hierarchy: Dict[str, Any]):
        """
        Initialize model with DataFrame and hierarchy tree.

        Args:
            df: Validated pandas DataFrame with account metadata
            hierarchy: Hierarchy tree dict from parser
        """
        super().__init__(df)
        self._hierarchy = hierarchy

    @property
    def hierarchy(self) -> Dict[str, Any]:
        """
        Get the hierarchy tree.

        Returns:
            Hierarchy dict with sections as top-level keys
        """
        return self._hierarchy

    def get_assets(self) -> Dict[str, Any]:
        """
        Get the Assets section from hierarchy.

        Returns:
            Dict containing Assets section tree, or empty dict if missing
        """
        return self._hierarchy.get('Assets', {})

    def get_liabilities(self) -> Dict[str, Any]:
        """
        Get the Liabilities section from hierarchy.

        Handles both 'Liabilities' and 'Liabilities and Equity' section names.

        Returns:
            Dict containing Liabilities section tree, or empty dict if missing
        """
        # Try 'Liabilities' first, then 'Liabilities and Equity'
        liabilities = self._hierarchy.get('Liabilities', {})
        if not liabilities:
            # Check if it's under 'Liabilities and Equity'
            combined = self._hierarchy.get('Liabilities and Equity', {})
            if combined:
                # Extract just Liabilities from combined section
                # This is a simplified approach - actual structure may vary
                return combined.get('Liabilities', combined)
        return liabilities

    def get_equity(self) -> Dict[str, Any]:
        """
        Get the Equity section from hierarchy.

        Handles both standalone 'Equity' and when nested under 'Liabilities and Equity'.

        Returns:
            Dict containing Equity section tree, or empty dict if missing
        """
        # Try standalone 'Equity' first
        equity = self._hierarchy.get('Equity', {})
        if not equity:
            # Check if it's under 'Liabilities and Equity'
            combined = self._hierarchy.get('Liabilities and Equity', {})
            if combined:
                # Extract just Equity from combined section
                return combined.get('Equity', combined)
        return equity

    def get_account_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Search hierarchy tree for account by name.

        Performs recursive search through all sections and nested accounts.

        Args:
            name: Account name to search for

        Returns:
            Account dict if found, None otherwise
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
        Convert model to dictionary including both DataFrame and hierarchy.

        Overrides base DataModel.to_dict() to include hierarchy tree.

        Args:
            orient: Format for DataFrame conversion (default: 'records')

        Returns:
            Dict with 'dataframe' and 'hierarchy' keys
        """
        return {
            'dataframe': self._df.to_dict(orient=orient),
            'hierarchy': self._hierarchy
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'BalanceSheetModel':
        """
        Create BalanceSheetModel from dictionary.

        Args:
            data: Dict with 'dataframe' and 'hierarchy' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New BalanceSheetModel instance

        Raises:
            ValueError: If data is missing required keys
        """
        if 'dataframe' not in data:
            raise ValueError("Missing 'dataframe' key in data")
        if 'hierarchy' not in data:
            raise ValueError("Missing 'hierarchy' key in data")

        # Reconstruct DataFrame
        if orient == 'records':
            df = pd.DataFrame(data['dataframe'])
        else:
            df = pd.DataFrame.from_dict(data['dataframe'], orient=orient)

        # Get hierarchy
        hierarchy = data['hierarchy']

        return cls(df=df, hierarchy=hierarchy)
