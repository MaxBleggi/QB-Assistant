"""
Anomaly annotation data model for persistence of confirmed/dismissed anomalies.

Extends ParameterModel pattern to store anomaly annotations as configuration data,
enabling persistence across sessions for downstream baseline calculations.
"""
from typing import Any, Dict, List

from .parameters import ParameterModel


class AnomalyAnnotationModel(ParameterModel):
    """
    Data model for storing confirmed/dismissed anomaly annotations.

    Stores annotations as list of dicts in parameters, where each annotation
    contains: start_date, end_date, metric_name, reason, exclude_from_baseline,
    confirmed.

    Extends ParameterModel to maintain pattern consistency with other config models.
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize model with parameters dictionary.

        Args:
            parameters: Dictionary with 'annotations' key containing list of annotation dicts
                       (default: empty dict which initializes empty annotations list)
        """
        super().__init__(parameters)

        # Ensure annotations list exists
        if 'annotations' not in self._parameters:
            self._parameters['annotations'] = []

    def add_annotation(self, annotation_dict: Dict[str, Any]) -> None:
        """
        Add an anomaly annotation to the model.

        Args:
            annotation_dict: Dictionary with keys: start_date (str), end_date (str),
                           metric_name (str), reason (str), exclude_from_baseline (bool),
                           confirmed (bool)
        """
        if 'annotations' not in self._parameters:
            self._parameters['annotations'] = []

        self._parameters['annotations'].append(annotation_dict)

    def get_annotations(self) -> List[Dict[str, Any]]:
        """
        Get all anomaly annotations.

        Returns:
            List of annotation dicts (empty list if no annotations)
        """
        return self._parameters.get('annotations', [])
