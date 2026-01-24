"""
PLForecastModel - Data model for P&L forecasts with confidence intervals.

Stores forecast output with three parallel value dictionaries (projected, lower_bound, upper_bound)
for each P&L section, comprehensive metadata including warnings, and calculated rows for margins
and net income.
"""
from typing import Any, Dict, Optional

import pandas as pd

from .base import DataModel


class PLForecastModel(DataModel):
    """
    Data model for P&L forecast output with confidence intervals.

    Stores:
    - Raw DataFrame (placeholder for compatibility)
    - Hierarchy tree with three parallel value dicts (projected, lower_bound, upper_bound)
    - Calculated rows (gross_profit, gross_margin_pct, operating_income, operating_margin_pct, net_income)
    - Metadata (confidence_level, forecast_horizon, excluded_periods, warnings)

    Provides convenient accessors for P&L sections and margin metrics.
    """

    def __init__(
        self,
        hierarchy: Dict[str, Any],
        calculated_rows: Dict[str, Any],
        metadata: Dict[str, Any],
        df: Optional[pd.DataFrame] = None
    ):
        """
        Initialize model with hierarchy, calculated rows, and metadata.

        Args:
            hierarchy: Hierarchy tree with 'projected', 'lower_bound', 'upper_bound' value dicts
            calculated_rows: Dict with margin metrics, each containing three value dicts
            metadata: Dict with confidence_level, forecast_horizon, excluded_periods, warnings
            df: Optional placeholder pandas DataFrame for compatibility (default: empty DataFrame)
        """
        if df is None:
            df = pd.DataFrame()
        super().__init__(df)

        # Validate required fields
        if not hierarchy:
            raise ValueError("hierarchy is required and cannot be empty")
        if calculated_rows is None:
            raise ValueError("calculated_rows is required")
        if not metadata:
            raise ValueError("metadata is required and cannot be empty")

        self._hierarchy = hierarchy
        self._calculated_rows = calculated_rows
        self._metadata = metadata

    @property
    def hierarchy(self) -> Dict[str, Any]:
        """
        Get the hierarchy tree with three value dictionaries.

        Returns:
            Hierarchy dict with P&L sections and three value series
        """
        return self._hierarchy

    @property
    def calculated_rows(self) -> Dict[str, Any]:
        """
        Get the calculated rows (margin metrics).

        Returns:
            Dict with keys for margin metrics (gross_profit, gross_margin_pct,
            operating_income, operating_margin_pct, net_income), each containing
            three sub-dicts: 'projected', 'lower_bound', 'upper_bound'
        """
        return self._calculated_rows

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the forecast.

        Returns:
            Metadata dict with confidence_level, forecast_horizon, excluded_periods,
            warnings array
        """
        return self._metadata

    def get_income(self) -> Optional[Dict[str, Any]]:
        """
        Get the Income section from hierarchy.

        Returns:
            Income section dict with projected/lower_bound/upper_bound value dicts,
            or None if missing
        """
        income_list = self._hierarchy.get('Income', [])
        if income_list and len(income_list) > 0:
            return income_list[0]
        return None

    def get_expenses(self) -> Optional[Dict[str, Any]]:
        """
        Get the Expenses section from hierarchy.

        Returns:
            Expenses section dict with projected/lower_bound/upper_bound value dicts,
            or None if missing
        """
        expenses_list = self._hierarchy.get('Expenses', [])
        if expenses_list and len(expenses_list) > 0:
            return expenses_list[0]
        return None

    def get_margins(self) -> Dict[str, Any]:
        """
        Get all margin metrics from calculated_rows.

        Returns:
            Dict with margin metrics (gross_profit, gross_margin_pct, operating_income,
            operating_margin_pct, net_income)
        """
        return self._calculated_rows

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary including DataFrame, hierarchy, calculated rows, and metadata.

        Overrides base DataModel.to_dict() to include all forecast components.

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
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'PLForecastModel':
        """
        Create PLForecastModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', 'calculated_rows', and 'metadata' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New PLForecastModel instance

        Raises:
            ValueError: If data is missing required keys
        """
        if 'hierarchy' not in data:
            raise ValueError("Missing 'hierarchy' key in data")
        if 'calculated_rows' not in data:
            raise ValueError("Missing 'calculated_rows' key in data")
        if 'metadata' not in data:
            raise ValueError("Missing 'metadata' key in data")

        # Reconstruct DataFrame (optional)
        df = None
        if 'dataframe' in data:
            if orient == 'records':
                df = pd.DataFrame(data['dataframe'])
            else:
                df = pd.DataFrame.from_dict(data['dataframe'], orient=orient)

        # Get hierarchy, calculated rows, and metadata
        hierarchy = data['hierarchy']
        calculated_rows = data['calculated_rows']
        metadata = data['metadata']

        return cls(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata,
            df=df
        )
