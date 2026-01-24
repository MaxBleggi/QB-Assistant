"""
Statistical anomaly detection service using 2-sigma threshold.

Implements conservative anomaly detection to minimize false positives,
flagging values that deviate >2σ from the historical mean.
"""
import math
from typing import List, Tuple


class AnomalyDetector:
    """
    Service for detecting statistical anomalies in time-series data.

    Uses 2-sigma threshold: flags values where |value - μ| > 2σ
    """

    @staticmethod
    def detect_anomalies(values: List[float]) -> List[Tuple[int, float, float]]:
        """
        Detect anomalies in time-series data using 2-sigma threshold.

        Args:
            values: List of numeric values (time-series data)

        Returns:
            List of tuples: [(period_index, value, deviation_magnitude), ...]
            where deviation_magnitude is |value - μ| / σ

            Returns empty list if:
            - Less than 3 periods (insufficient for std dev calculation)
            - Standard deviation is 0 (all values identical)
            - No values exceed 2σ threshold
        """
        # Edge case: insufficient data for standard deviation
        if len(values) < 3:
            return []

        # Calculate mean: μ = sum(values) / n
        n = len(values)
        mean = sum(values) / n

        # Calculate sample standard deviation: σ = sqrt(sum((value - μ)²) / (n - 1))
        variance = sum((value - mean) ** 2 for value in values) / (n - 1)
        std_dev = math.sqrt(variance)

        # Edge case: zero standard deviation (all values identical)
        if std_dev == 0:
            return []

        # Detect anomalies: flag values where |value - μ| > 2σ
        anomalies = []
        for idx, value in enumerate(values):
            deviation = abs(value - mean)
            if deviation > 2 * std_dev:
                # Calculate deviation magnitude (how many sigmas away)
                deviation_magnitude = deviation / std_dev
                anomalies.append((idx, value, deviation_magnitude))

        return anomalies
