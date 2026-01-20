"""
CashFlowModel - Data model for Cash Flow Statement with activity section support.

Extends DataModel base class to add Cash Flow-specific functionality:
- Hierarchy tree storage with three activity sections (Operating, Investing, Financing)
- Activity section accessors (get_operating, get_investing, get_financing)
- Beginning and ending cash position properties
- Calculated rows storage for cash position markers
- Serialization with hierarchy and calculated rows preservation
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import DataModel


class CashFlowModel(DataModel):
    """
    Data model for QuickBooks Cash Flow Statement.

    Stores:
    - Raw DataFrame (for tabular operations)
    - Hierarchy tree with three activity sections
    - Calculated rows (cash positions, net changes)

    Provides convenient accessors for activity sections and cash positions.
    """

    def __init__(self, df: pd.DataFrame, hierarchy: Dict[str, List],
                 calculated_rows: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """
        Initialize model with DataFrame, hierarchy tree, and calculated rows.

        Args:
            df: Validated pandas DataFrame with account metadata
            hierarchy: Hierarchy tree dict with activity sections as keys
            calculated_rows: List of calculated row dicts (cash positions, net changes)
            metadata: Optional metadata dict
        """
        super().__init__(df)
        self._hierarchy = hierarchy
        self._calculated_rows = calculated_rows
        self._metadata = metadata or {}

    @property
    def hierarchy(self) -> Dict[str, List]:
        """
        Get the hierarchy tree.

        Returns:
            Hierarchy dict with activity sections as top-level keys
        """
        return self._hierarchy

    @property
    def calculated_rows(self) -> List[Dict[str, Any]]:
        """
        Get the calculated rows (cash positions, net changes).

        Returns:
            List of dicts with 'account_name' and 'value' keys
        """
        return self._calculated_rows

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the cash flow statement.

        Returns:
            Metadata dict with info about sections, rows, etc.
        """
        return self._metadata

    def get_operating(self) -> List[Dict[str, Any]]:
        """
        Get the Operating Activities section from hierarchy.

        Returns:
            List of operating activity items, or empty list if missing
        """
        return self._hierarchy.get('OPERATING ACTIVITIES', [])

    def get_investing(self) -> List[Dict[str, Any]]:
        """
        Get the Investing Activities section from hierarchy.

        Returns:
            List of investing activity items, or empty list if missing/empty
        """
        return self._hierarchy.get('INVESTING ACTIVITIES', [])

    def get_financing(self) -> List[Dict[str, Any]]:
        """
        Get the Financing Activities section from hierarchy.

        Returns:
            List of financing activity items, or empty list if missing
        """
        return self._hierarchy.get('FINANCING ACTIVITIES', [])

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

    @property
    def beginning_cash(self) -> Optional[float]:
        """
        Get the beginning cash position from calculated rows.

        Searches for 'Cash at beginning of period' in calculated_rows.

        Returns:
            Beginning cash value as float, or None if not found
        """
        for row in self._calculated_rows:
            if row.get('account_name') == 'Cash at beginning of period':
                return row.get('value')
        return None

    @property
    def ending_cash(self) -> Optional[float]:
        """
        Get the ending cash position from calculated rows.

        Searches for 'CASH AT END OF PERIOD' in calculated_rows.

        Returns:
            Ending cash value as float, or None if not found
        """
        for row in self._calculated_rows:
            if row.get('account_name') == 'CASH AT END OF PERIOD':
                return row.get('value')
        return None

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary including DataFrame, hierarchy, and calculated rows.

        Overrides base DataModel.to_dict() to include hierarchy tree and calculated rows.

        Args:
            orient: Format for DataFrame conversion (default: 'records')

        Returns:
            Dict with 'dataframe', 'hierarchy', 'calculated_rows', and 'metadata' keys
        """
        return {
            'dataframe': self._df.to_dict(orient=orient),
            'hierarchy': self._hierarchy,
            'calculated_rows': self._calculated_rows,
            'metadata': self._metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'CashFlowModel':
        """
        Create CashFlowModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', and 'calculated_rows' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New CashFlowModel instance

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

        # Get hierarchy, calculated rows, and metadata
        hierarchy = data['hierarchy']
        calculated_rows = data['calculated_rows']
        metadata = data.get('metadata', {})

        return cls(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows,
                  metadata=metadata)
