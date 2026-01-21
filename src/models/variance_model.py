"""
VarianceModel - Data model for budget vs actual variance analysis results.

Extends DataModel base class to provide structured storage for variance calculations:
- Period-aware hierarchy tree with variance attributes per account
- Section-specific accessors (get_income_variances, get_expense_variances)
- Tracking of unmatched accounts (budget without actual, actual without budget)
- Serialization with hierarchy and calculated rows preservation
"""
from typing import Any, Dict, List

import pandas as pd

from .base import DataModel


class VarianceModel(DataModel):
    """
    Data model for budget vs actual variance analysis with multi-period support.

    Stores:
    - Raw DataFrame (for tabular operations)
    - Variance hierarchy tree with budget_value, actual_value, dollar_variance,
      pct_variance, is_favorable, is_flagged per account/period
    - Calculated rows (totals, subtotals)
    - Unmatched accounts (budget without actual, actual without budget)

    Provides convenient accessors for sections and unmatched tracking.
    Mirrors BudgetModel/PLModel structure for consistency.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        hierarchy: Dict[str, Any],
        calculated_rows: List[Dict[str, Any]],
        unmatched_budget_accounts: List[str] = None,
        unmatched_actual_accounts: List[str] = None
    ):
        """
        Initialize model with DataFrame, hierarchy tree, calculated rows, and unmatched lists.

        Args:
            df: Validated pandas DataFrame with account metadata
            hierarchy: Hierarchy tree dict with variance attributes per account/period
            calculated_rows: List of calculated row dicts (totals, subtotals)
            unmatched_budget_accounts: List of budget account names without matching actuals
            unmatched_actual_accounts: List of actual account names without matching budget
        """
        super().__init__(df)
        self._hierarchy = hierarchy
        self._calculated_rows = calculated_rows
        self._unmatched_budget_accounts = unmatched_budget_accounts if unmatched_budget_accounts is not None else []
        self._unmatched_actual_accounts = unmatched_actual_accounts if unmatched_actual_accounts is not None else []

    @property
    def hierarchy(self) -> Dict[str, Any]:
        """
        Get the variance hierarchy tree.

        Returns:
            Hierarchy dict with sections as top-level keys, variance attributes at nodes
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

    @property
    def unmatched_budget_accounts(self) -> List[str]:
        """
        Get list of budget accounts without matching actuals.

        Returns:
            List of budget account names that had no corresponding actual accounts
        """
        return self._unmatched_budget_accounts

    @property
    def unmatched_actual_accounts(self) -> List[str]:
        """
        Get list of actual accounts without matching budget.

        Returns:
            List of actual account names that had no corresponding budget accounts
        """
        return self._unmatched_actual_accounts

    def get_income_variances(self) -> Dict[str, Any]:
        """
        Get the Income section variance data from hierarchy.

        Returns:
            Dict containing Income section tree with variance attributes, or empty dict if missing
        """
        return self._hierarchy.get('Income', {})

    def get_expense_variances(self) -> Dict[str, Any]:
        """
        Get the Expenses section variance data from hierarchy.

        Returns:
            Dict containing Expenses section tree with variance attributes, or empty dict if missing
        """
        return self._hierarchy.get('Expenses', {})

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary including DataFrame, hierarchy, calculated rows, and unmatched lists.

        Overrides base DataModel.to_dict() to include variance-specific data.

        Args:
            orient: Format for DataFrame conversion (default: 'records')

        Returns:
            Dict with 'dataframe', 'hierarchy', 'calculated_rows', 'unmatched_budget_accounts',
            and 'unmatched_actual_accounts' keys
        """
        return {
            'dataframe': self._df.to_dict(orient=orient),
            'hierarchy': self._hierarchy,
            'calculated_rows': self._calculated_rows,
            'unmatched_budget_accounts': self._unmatched_budget_accounts,
            'unmatched_actual_accounts': self._unmatched_actual_accounts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'VarianceModel':
        """
        Create VarianceModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', 'calculated_rows',
                  'unmatched_budget_accounts', and 'unmatched_actual_accounts' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New VarianceModel instance

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

        # Get unmatched lists (optional - default to empty if missing)
        unmatched_budget = data.get('unmatched_budget_accounts', [])
        unmatched_actual = data.get('unmatched_actual_accounts', [])

        return cls(
            df=df,
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            unmatched_budget_accounts=unmatched_budget,
            unmatched_actual_accounts=unmatched_actual
        )
