"""
AnomalyDataFilter - Centralized service for filtering historical data based on anomaly annotations.

Filters pandas Series data to exclude periods marked as anomalous, with support for different
exclusion types (baseline, volatility, both). Returns filtered data plus metadata for transparency.
"""
from typing import Dict, Any, List
import pandas as pd


class AnomalyDataFilter:
    """
    Centralized service for filtering historical data based on anomaly annotations.

    Implements date range filtering with pandas datetime operations, exclusion type matching,
    and metadata generation for forecast transparency. Validates data sufficiency after filtering.
    """

    def __init__(self, data: pd.Series, annotations: List[Dict[str, Any]], exclusion_type: str):
        """
        Initialize filter with data, annotations, and exclusion type.

        Args:
            data: pandas Series with datetime index containing historical values
            annotations: List of annotation dicts with start_date, end_date, reason, exclude_from
            exclusion_type: Type of exclusion to apply ('baseline', 'volatility', or 'both')

        Raises:
            ValueError: If exclusion_type is invalid
        """
        if exclusion_type not in ['baseline', 'volatility', 'both']:
            raise ValueError(
                f"exclusion_type must be 'baseline', 'volatility', or 'both', got: {exclusion_type}"
            )

        self.data = data
        self.annotations = annotations or []
        self.exclusion_type = exclusion_type

    def filter(self) -> Dict[str, Any]:
        """
        Filter data based on annotations and return filtered series with metadata.

        Returns:
            Dictionary with keys:
                - filtered_series: pandas Series with anomalous periods removed
                - metadata: dict with excluded_count, total_count, exclusion_percentage,
                           excluded_periods list, and warning flag

        Raises:
            ValueError: If 100% of data would be excluded (insufficient data)
        """
        # If no annotations, return original data
        if not self.annotations:
            return {
                'filtered_series': self.data,
                'metadata': {
                    'excluded_count': 0,
                    'total_count': len(self.data),
                    'exclusion_percentage': 0.0,
                    'excluded_periods': [],
                    'warning': False
                }
            }

        # Filter annotations by exclusion type
        # Match annotations where exclude_from == exclusion_type OR exclude_from == 'both'
        relevant_annotations = [
            ann for ann in self.annotations
            if ann.get('exclude_from') == self.exclusion_type or ann.get('exclude_from') == 'both'
        ]

        if not relevant_annotations:
            return {
                'filtered_series': self.data,
                'metadata': {
                    'excluded_count': 0,
                    'total_count': len(self.data),
                    'exclusion_percentage': 0.0,
                    'excluded_periods': [],
                    'warning': False
                }
            }

        # Ensure datetime index for date comparison
        if not isinstance(self.data.index, pd.DatetimeIndex):
            # Try to convert to datetime
            data_with_datetime = self.data.copy()
            data_with_datetime.index = pd.to_datetime(self.data.index)
        else:
            data_with_datetime = self.data

        # Create boolean mask for periods to keep (start as all True)
        mask = pd.Series([True] * len(data_with_datetime), index=data_with_datetime.index)

        # Build excluded_periods list for metadata
        excluded_periods = []

        # Apply each annotation's date range exclusion
        for ann in relevant_annotations:
            start_date = pd.to_datetime(ann.get('start_date'))
            end_date = pd.to_datetime(ann.get('end_date'))
            reason = ann.get('reason', 'No reason provided')

            # Mark periods within this range as False (to be excluded)
            # Date range filtering: index >= start_date AND index <= end_date
            exclusion_mask = (data_with_datetime.index >= start_date) & (data_with_datetime.index <= end_date)
            mask = mask & ~exclusion_mask

            # Add to excluded_periods metadata
            excluded_periods.append({
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'reason': reason
            })

        # Apply mask to filter data
        filtered_series = data_with_datetime[mask]

        # Calculate metadata
        total_count = len(self.data)
        excluded_count = total_count - len(filtered_series)
        exclusion_percentage = excluded_count / total_count if total_count > 0 else 0.0

        # Check for 100% exclusion (error condition)
        if excluded_count == total_count:
            raise ValueError(
                f'All {total_count} periods would be excluded. Cannot proceed with forecast. '
                f'Please review anomaly annotations.'
            )

        # Check for >50% exclusion (warning condition)
        warning = exclusion_percentage > 0.5

        metadata = {
            'excluded_count': excluded_count,
            'total_count': total_count,
            'exclusion_percentage': exclusion_percentage,
            'excluded_periods': excluded_periods,
            'warning': warning
        }

        return {
            'filtered_series': filtered_series,
            'metadata': metadata
        }
