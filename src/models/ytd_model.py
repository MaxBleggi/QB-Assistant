"""
YTDModel - Data model for year-to-date aggregation results.

Extends DataModel base class to provide structured storage for cumulative YTD data:
- Period-aware hierarchy tree with cumulative variance attributes per account
- Section-specific accessors (get_income_ytd, get_expenses_ytd)
- Metadata tracking (fiscal_year_start_month, aggregation_start_period)
- Serialization with hierarchy and calculated rows preservation
"""
from typing import Any, Dict, List

import pandas as pd

from .base import DataModel


class YTDModel(DataModel):
    """
    Data model for year-to-date aggregation with multi-period cumulative support.

    Stores:
    - Raw DataFrame (for tabular operations)
    - YTD hierarchy tree with cumulative_budget, cumulative_actual,
      cumulative_dollar_variance, cumulative_pct_variance, ytd_pct_of_budget,
      is_favorable, is_flagged per account/period
    - Calculated rows (section-level summaries)
    - Metadata (fiscal_year_start_month, aggregation_start_period)

    Provides convenient accessors for sections and YTD metadata.
    Mirrors BudgetModel/PLModel/VarianceModel structure for consistency.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        hierarchy: Dict[str, Any],
        calculated_rows: Dict[str, Any],
        fiscal_year_start_month: int,
        aggregation_start_period: str
    ):
        """
        Initialize model with DataFrame, hierarchy tree, calculated rows, and metadata.

        Args:
            df: Validated pandas DataFrame with account metadata
            hierarchy: Hierarchy tree dict with cumulative variance attributes per account/period
            calculated_rows: Dict of calculated section summaries with period data
            fiscal_year_start_month: Fiscal year start month (1=Jan, 7=Jul, etc.)
            aggregation_start_period: Earliest period in aggregation (e.g., '2024-07')
        """
        super().__init__(df)
        self._hierarchy = hierarchy
        self._calculated_rows = calculated_rows
        self._fiscal_year_start_month = fiscal_year_start_month
        self._aggregation_start_period = aggregation_start_period

    @property
    def hierarchy(self) -> Dict[str, Any]:
        """
        Get the YTD hierarchy tree.

        Returns:
            Hierarchy dict with sections as top-level keys, cumulative attributes at nodes
        """
        return self._hierarchy

    @property
    def calculated_rows(self) -> Dict[str, Any]:
        """
        Get the calculated rows (section-level summaries).

        Returns:
            Dict with section names as keys, period dicts as values
        """
        return self._calculated_rows

    @property
    def fiscal_year_start_month(self) -> int:
        """
        Get the fiscal year start month.

        Returns:
            Integer representing fiscal year start month (1-12)
        """
        return self._fiscal_year_start_month

    @property
    def aggregation_start_period(self) -> str:
        """
        Get the aggregation start period.

        Returns:
            Period label string representing earliest period in aggregation
        """
        return self._aggregation_start_period

    def get_income_ytd(self) -> Dict[str, Any]:
        """
        Get the Income section YTD data from hierarchy.

        Returns:
            Dict containing Income section tree with cumulative attributes, or empty dict if missing
        """
        return self._hierarchy.get('Income', {})

    def get_expenses_ytd(self) -> Dict[str, Any]:
        """
        Get the Expenses section YTD data from hierarchy.

        Returns:
            Dict containing Expenses section tree with cumulative attributes, or empty dict if missing
        """
        return self._hierarchy.get('Expenses', {})

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary including DataFrame, hierarchy, calculated rows, and metadata.

        Overrides base DataModel.to_dict() to include YTD-specific data.

        Args:
            orient: Format for DataFrame conversion (default: 'records')

        Returns:
            Dict with 'dataframe', 'hierarchy', 'calculated_rows',
            'fiscal_year_start_month', and 'aggregation_start_period' keys
        """
        return {
            'dataframe': self._df.to_dict(orient=orient),
            'hierarchy': self._hierarchy,
            'calculated_rows': self._calculated_rows,
            'fiscal_year_start_month': self._fiscal_year_start_month,
            'aggregation_start_period': self._aggregation_start_period
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'YTDModel':
        """
        Create YTDModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', 'calculated_rows',
                  'fiscal_year_start_month', and 'aggregation_start_period' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New YTDModel instance

        Raises:
            ValueError: If data is missing required keys
        """
        if 'dataframe' not in data:
            raise ValueError("Missing 'dataframe' key in data")
        if 'hierarchy' not in data:
            raise ValueError("Missing 'hierarchy' key in data")
        if 'calculated_rows' not in data:
            raise ValueError("Missing 'calculated_rows' key in data")
        if 'fiscal_year_start_month' not in data:
            raise ValueError("Missing 'fiscal_year_start_month' key in data")
        if 'aggregation_start_period' not in data:
            raise ValueError("Missing 'aggregation_start_period' key in data")

        # Reconstruct DataFrame
        if orient == 'records':
            df = pd.DataFrame(data['dataframe'])
        else:
            df = pd.DataFrame.from_dict(data['dataframe'], orient=orient)

        # Get hierarchy, calculated rows, and metadata
        hierarchy = data['hierarchy']
        calculated_rows = data['calculated_rows']
        fiscal_year_start_month = data['fiscal_year_start_month']
        aggregation_start_period = data['aggregation_start_period']

        return cls(
            df=df,
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            fiscal_year_start_month=fiscal_year_start_month,
            aggregation_start_period=aggregation_start_period
        )
