"""
AnomalyValidator - Validates anomaly annotation date ranges.

Checks date ordering (start < end), bounds validation (within historical data range),
and overlap detection. Follows ForecastValidator pattern for consistency.
"""
from typing import Dict, Any, List
import pandas as pd


class AnomalyValidator:
    """
    Standalone validator for anomaly annotation date range validation.

    Validates annotations for date ordering, bounds checking, and overlap detection
    before filtering occurs. Returns validation result with errors and warnings.
    """

    def __init__(self, annotations: List[Dict[str, Any]], earliest_date: str, latest_date: str):
        """
        Initialize validator with annotations and historical bounds.

        Args:
            annotations: List of annotation dicts with start_date, end_date, exclude_from, reason
            earliest_date: Earliest date in historical data (string format YYYY-MM-DD)
            latest_date: Latest date in historical data (string format YYYY-MM-DD)
        """
        self.annotations = annotations or []
        self.earliest_date = pd.to_datetime(earliest_date)
        self.latest_date = pd.to_datetime(latest_date)

    def validate(self) -> Dict[str, Any]:
        """
        Validate all annotations and return result.

        Returns:
            Dictionary with keys:
                - valid: bool (False if any errors exist, True otherwise)
                - errors: list of error messages
                - warnings: list of warning messages
        """
        errors = []
        warnings = []

        # Run all validation checks
        errors.extend(self._validate_ordering())
        errors.extend(self._validate_bounds())
        errors.extend(self._validate_overlaps())
        warnings.extend(self._validate_single_day())

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _validate_ordering(self) -> List[str]:
        """
        Check that start_date < end_date for each annotation.

        Returns:
            List of error messages for ordering violations
        """
        errors = []
        for i, ann in enumerate(self.annotations):
            start_date = pd.to_datetime(ann.get('start_date'))
            end_date = pd.to_datetime(ann.get('end_date'))

            if start_date > end_date:
                errors.append(
                    f"Annotation {i}: Date ordering violation - start_date ({start_date.date()}) "
                    f"must be before end_date ({end_date.date()})"
                )

        return errors

    def _validate_bounds(self) -> List[str]:
        """
        Check that annotation dates fall within historical data bounds.

        Returns:
            List of error messages for bounds violations
        """
        errors = []
        for i, ann in enumerate(self.annotations):
            start_date = pd.to_datetime(ann.get('start_date'))
            end_date = pd.to_datetime(ann.get('end_date'))

            if start_date < self.earliest_date:
                errors.append(
                    f"Annotation {i}: start_date ({start_date.date()}) is before earliest "
                    f"historical date ({self.earliest_date.date()})"
                )

            if end_date > self.latest_date:
                errors.append(
                    f"Annotation {i}: end_date ({end_date.date()}) is after latest "
                    f"historical date ({self.latest_date.date()})"
                )

        return errors

    def _validate_overlaps(self) -> List[str]:
        """
        Check for overlapping annotation date ranges.

        Uses overlap formula: A.start <= B.end AND B.start <= A.end

        Returns:
            List of error messages for overlapping ranges
        """
        errors = []

        # Check each pair of annotations for overlap
        for i in range(len(self.annotations)):
            for j in range(i + 1, len(self.annotations)):
                ann_a = self.annotations[i]
                ann_b = self.annotations[j]

                start_a = pd.to_datetime(ann_a.get('start_date'))
                end_a = pd.to_datetime(ann_a.get('end_date'))
                start_b = pd.to_datetime(ann_b.get('start_date'))
                end_b = pd.to_datetime(ann_b.get('end_date'))

                # Overlap formula: A.start <= B.end AND B.start <= A.end
                if start_a <= end_b and start_b <= end_a:
                    errors.append(
                        f"Annotations {i} and {j} overlap: "
                        f"[{start_a.date()} to {end_a.date()}] overlaps with "
                        f"[{start_b.date()} to {end_b.date()}]"
                    )

        return errors

    def _validate_single_day(self) -> List[str]:
        """
        Warn about single-day exclusions (start_date == end_date).

        This is unusual but valid, so return as warning not error.

        Returns:
            List of warning messages for single-day exclusions
        """
        warnings = []
        for i, ann in enumerate(self.annotations):
            start_date = pd.to_datetime(ann.get('start_date'))
            end_date = pd.to_datetime(ann.get('end_date'))

            if start_date == end_date:
                warnings.append(
                    f"Annotation {i}: Single-day exclusion ({start_date.date()}) - "
                    f"this is unusual but valid"
                )

        return warnings
