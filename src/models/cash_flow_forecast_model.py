"""
CashFlowForecastModel - Data model for cash flow forecasts with confidence intervals.

Stores forecast output with three parallel value dictionaries (projected, lower_bound, upper_bound)
for each hierarchy node, comprehensive metadata including warnings and spillover tracking,
and calculated rows for beginning/ending cash positions.
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import DataModel


class CashFlowForecastModel(DataModel):
    """
    Data model for cash flow forecast output with confidence intervals.

    Stores:
    - Raw DataFrame (placeholder for compatibility)
    - Hierarchy tree with three parallel value dicts (projected, lower_bound, upper_bound)
    - Calculated rows (beginning_cash, ending_cash per month)
    - Metadata (confidence_level, forecast_horizon, excluded_periods, warnings, spillover)

    Provides convenient accessors for activity sections and value series.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        hierarchy: Dict[str, Any],
        calculated_rows: Dict[str, Any],
        metadata: Dict[str, Any]
    ):
        """
        Initialize model with DataFrame, hierarchy, calculated rows, and metadata.

        Args:
            df: Placeholder pandas DataFrame for compatibility
            hierarchy: Hierarchy tree with 'projected', 'lower_bound', 'upper_bound' value dicts
            calculated_rows: Dict with 'beginning_cash' and 'ending_cash' arrays for three series
            metadata: Dict with confidence_level, forecast_horizon, excluded_periods, warnings, spillover
        """
        super().__init__(df)
        self._hierarchy = hierarchy
        self._calculated_rows = calculated_rows
        self._metadata = metadata

    @property
    def hierarchy(self) -> Dict[str, Any]:
        """
        Get the hierarchy tree with three value dictionaries.

        Returns:
            Hierarchy dict with activity sections and three value series
        """
        return self._hierarchy

    @property
    def calculated_rows(self) -> Dict[str, Any]:
        """
        Get the calculated rows (beginning_cash, ending_cash arrays).

        Returns:
            Dict with keys 'beginning_cash' and 'ending_cash', each containing
            three sub-dicts: 'projected', 'lower_bound', 'upper_bound'
        """
        return self._calculated_rows

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the forecast.

        Returns:
            Metadata dict with confidence_level, forecast_horizon, excluded_periods,
            warnings array, and uncollected_spillover info
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
            List of investing activity items, or empty list if missing
        """
        return self._hierarchy.get('INVESTING ACTIVITIES', [])

    def get_financing(self) -> List[Dict[str, Any]]:
        """
        Get the Financing Activities section from hierarchy.

        Returns:
            List of financing activity items, or empty list if missing
        """
        return self._hierarchy.get('FINANCING ACTIVITIES', [])

    def get_projected_values(self, month: int, section: str = None) -> Optional[float]:
        """
        Get projected value for specific month and optional section.

        Args:
            month: 1-indexed month number (1 to forecast_horizon)
            section: Optional section name ('OPERATING ACTIVITIES', 'INVESTING ACTIVITIES', 'FINANCING ACTIVITIES')

        Returns:
            Projected value as float, or None if not found
        """
        if section:
            section_data = self._hierarchy.get(section, [])
            if section_data and len(section_data) > 0:
                projected = section_data[0].get('projected', {})
                return projected.get(month)
        return None

    def get_confidence_bounds(self, month: int, section: str = None) -> Optional[Dict[str, float]]:
        """
        Get lower and upper confidence bounds for specific month and optional section.

        Args:
            month: 1-indexed month number (1 to forecast_horizon)
            section: Optional section name

        Returns:
            Dict with 'lower' and 'upper' keys, or None if not found
        """
        if section:
            section_data = self._hierarchy.get(section, [])
            if section_data and len(section_data) > 0:
                lower_bound = section_data[0].get('lower_bound', {})
                upper_bound = section_data[0].get('upper_bound', {})
                return {
                    'lower': lower_bound.get(month),
                    'upper': upper_bound.get(month)
                }
        return None

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
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'CashFlowForecastModel':
        """
        Create CashFlowForecastModel from dictionary.

        Args:
            data: Dict with 'dataframe', 'hierarchy', 'calculated_rows', and 'metadata' keys
            orient: Format of DataFrame dict (default: 'records')

        Returns:
            New CashFlowForecastModel instance

        Raises:
            ValueError: If data is missing required keys
        """
        if 'dataframe' not in data:
            raise ValueError("Missing 'dataframe' key in data")
        if 'hierarchy' not in data:
            raise ValueError("Missing 'hierarchy' key in data")
        if 'calculated_rows' not in data:
            raise ValueError("Missing 'calculated_rows' key in data")
        if 'metadata' not in data:
            raise ValueError("Missing 'metadata' key in data")

        # Reconstruct DataFrame
        if orient == 'records':
            df = pd.DataFrame(data['dataframe'])
        else:
            df = pd.DataFrame.from_dict(data['dataframe'], orient=orient)

        # Get hierarchy, calculated rows, and metadata
        hierarchy = data['hierarchy']
        calculated_rows = data['calculated_rows']
        metadata = data['metadata']

        return cls(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows, metadata=metadata)
