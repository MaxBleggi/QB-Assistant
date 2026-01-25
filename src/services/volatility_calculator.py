"""
VolatilityCalculator - Service for percentile-based volatility calculation with configurable confidence levels.

Computes historical volatility using month-over-month percent changes and percentile-based ratios.
Supports configurable confidence levels (50-95%), sparse data handling, and anomaly exclusion.
"""
from typing import Any, Dict, Optional

import pandas as pd

from src.services.anomaly_data_filter import AnomalyDataFilter


class VolatilityCalculator:
    """
    Calculator for historical volatility using percentile-based confidence intervals.

    Accepts historical values (pandas Series), confidence level, and optional anomaly annotations.
    Returns percentile ratios and metadata for use in forecast confidence interval calculations.
    """

    def __init__(
        self,
        historical_values: pd.Series,
        confidence_level: float = 0.80,
        anomaly_annotations: Optional[Any] = None
    ):
        """
        Initialize calculator with historical data, confidence level, and optional anomaly annotations.

        Args:
            historical_values: pandas Series with historical data (index = period names, values = amounts)
            confidence_level: Confidence level as decimal (0.50-0.95), default 0.80 for 80% confidence
            anomaly_annotations: Optional AnomalyAnnotationModel for 'volatility' exclusion

        Raises:
            ValueError: If confidence_level is outside valid range (0.50-0.95)
        """
        if not (0.50 <= confidence_level <= 0.95):
            raise ValueError(
                f"confidence_level must be between 0.50 and 0.95, got: {confidence_level}"
            )

        self.historical_values = historical_values
        self.confidence_level = confidence_level
        self.anomaly_annotations = anomaly_annotations
        self.warnings = []

    def calculate(self) -> Dict[str, Any]:
        """
        Calculate percentile-based volatility ratios and metadata.

        Process:
        1. Apply anomaly exclusion (if provided)
        2. Calculate month-over-month percent changes
        3. Check for sparse data (< 6 periods)
        4. Calculate percentile thresholds from confidence level
        5. Compute percentile ratios (percentile / median)
        6. Return ratios and metadata

        Returns:
            Dict with keys:
            - percentile_ratios: {'lower_ratio': float, 'upper_ratio': float}
            - metadata: {
                'sample_size': int,
                'percentile_values': {'lower': float|None, 'upper': float|None},
                'confidence_level': float,
                'excluded_period_count': int,
                'insufficient_data_flag': bool
              }
        """
        # Step 1: Apply anomaly exclusion
        filtered_values = self._apply_anomaly_exclusion()
        excluded_count = len(self.historical_values) - len(filtered_values)

        # Step 2: Calculate month-over-month percent changes
        # pct_change calculates (value[i] - value[i-1]) / value[i-1]
        mom_changes = filtered_values.pct_change().dropna()

        # Step 3: Check for sparse data
        sample_size = len(mom_changes)

        if sample_size < 6:
            # Insufficient data - use default ±25% bounds
            self.warnings.append(
                f'Insufficient historical data for volatility calculation ({sample_size} periods). Using default ±25% bounds.'
            )

            return {
                'percentile_ratios': {
                    'lower_ratio': 0.75,  # 1 - 0.25
                    'upper_ratio': 1.25   # 1 + 0.25
                },
                'metadata': {
                    'sample_size': sample_size,
                    'percentile_values': {'lower': None, 'upper': None},
                    'confidence_level': self.confidence_level,
                    'excluded_period_count': excluded_count,
                    'insufficient_data_flag': True
                }
            }

        # Step 4: Calculate percentile thresholds from confidence level
        # Formula: lower_percentile = (100 - confidence_level*100) / 200
        # Example: 80% confidence → (100-80)/200 = 0.10 → 10th percentile
        # Example: 95% confidence → (100-95)/200 = 0.025 → 2.5th percentile
        lower_percentile = (100 - self.confidence_level * 100) / 200 / 100
        upper_percentile = 1 - lower_percentile

        # Step 5: Compute percentile values and ratios
        percentile_lower = mom_changes.quantile(lower_percentile)
        percentile_upper = mom_changes.quantile(upper_percentile)
        median = filtered_values.median()

        # Avoid division by zero
        if median == 0:
            self.warnings.append(
                f'Cannot calculate volatility ratios with zero median. Using default ±25% bounds.'
            )

            return {
                'percentile_ratios': {
                    'lower_ratio': 0.75,
                    'upper_ratio': 1.25
                },
                'metadata': {
                    'sample_size': sample_size,
                    'percentile_values': {'lower': None, 'upper': None},
                    'confidence_level': self.confidence_level,
                    'excluded_period_count': excluded_count,
                    'insufficient_data_flag': True
                }
            }

        # Convert percentile changes to ratios relative to baseline
        # If percentile_lower = -0.15 (15% decline), ratio = 1 + (-0.15) = 0.85
        # If percentile_upper = 0.20 (20% increase), ratio = 1 + 0.20 = 1.20
        lower_ratio = 1 + percentile_lower
        upper_ratio = 1 + percentile_upper

        # Check for low variance (preserve existing functionality)
        variance_range = (percentile_upper - percentile_lower) / abs(median)
        if variance_range < 0.05:
            self.warnings.append(
                f'Low historical variance detected (range: {variance_range:.3f}). '
                'Confidence interval width may be artificially narrow.'
            )

        # Step 6: Return results
        return {
            'percentile_ratios': {
                'lower_ratio': lower_ratio,
                'upper_ratio': upper_ratio
            },
            'metadata': {
                'sample_size': sample_size,
                'percentile_values': {
                    'lower': percentile_lower,
                    'upper': percentile_upper
                },
                'confidence_level': self.confidence_level,
                'excluded_period_count': excluded_count,
                'insufficient_data_flag': False
            }
        }

    def _apply_anomaly_exclusion(self) -> pd.Series:
        """
        Filter historical values to exclude periods marked for 'volatility' exclusion.

        Returns:
            pandas Series with anomalous periods removed
        """
        if not self.anomaly_annotations:
            return self.historical_values

        # Get all annotations
        annotations = self.anomaly_annotations.get_annotations()

        if not annotations:
            return self.historical_values

        # Ensure datetime index for proper date range matching
        historical_with_datetime = self.historical_values.copy()
        if not isinstance(historical_with_datetime.index, pd.DatetimeIndex):
            # Try to convert index to datetime with format parameter for flexibility
            historical_with_datetime.index = pd.to_datetime(self.historical_values.index, format='%Y-%m', errors='coerce')

        # Apply filter with 'volatility' exclusion type
        filter_service = AnomalyDataFilter(
            historical_with_datetime,
            annotations,
            exclusion_type='volatility'
        )

        try:
            filter_result = filter_service.filter()
            filtered_series = filter_result['filtered_series']
            return filtered_series
        except ValueError:
            # If 100% of data would be excluded, fall back to original
            # (volatility calculation will handle insufficient data)
            return self.historical_values
