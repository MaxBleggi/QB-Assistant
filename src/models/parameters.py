"""
Parameter data model for configuration storage.

Extends DataModel pattern but stores parameters as dict (configuration data)
instead of DataFrame (tabular data). Provides serialization and parameter access.
"""
from typing import Any, Dict
import pandas as pd

from .base import DataModel


class ParameterModel(DataModel):
    """
    Data model for parameter configuration storage.

    Stores parameters as key-value pairs (dict) rather than tabular data.
    Extends DataModel to maintain pattern consistency with BalanceSheetModel,
    PLModel, CashFlowModel, but uses dict storage semantics.
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize model with parameter dictionary.

        Args:
            parameters: Dictionary of parameter key-value pairs (default: empty dict)
        """
        # Pass empty DataFrame to satisfy DataModel inheritance contract
        super().__init__(pd.DataFrame())

        # Store parameters as dict (actual data storage)
        self._parameters = parameters if parameters is not None else {}

    @property
    def parameters(self) -> Dict[str, Any]:
        """
        Get parameters dictionary.

        Returns:
            Dictionary of parameter key-value pairs
        """
        return self._parameters

    def get_parameter(self, key: str) -> Any:
        """
        Retrieve parameter value by key.

        Args:
            key: Parameter name to retrieve

        Returns:
            Parameter value

        Raises:
            KeyError: If parameter key does not exist
        """
        if key not in self._parameters:
            raise KeyError(f"Parameter '{key}' not found")
        return self._parameters[key]

    def set_parameter(self, key: str, value: Any) -> None:
        """
        Set parameter value by key.

        Args:
            key: Parameter name to set
            value: Parameter value to store
        """
        self._parameters[key] = value

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary for serialization.

        Args:
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            Dictionary with 'parameters' key containing parameter data
        """
        return {
            'parameters': self._parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'ParameterModel':
        """
        Create ParameterModel from dictionary.

        Args:
            data: Dictionary with 'parameters' key
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            New ParameterModel instance

        Raises:
            ValueError: If data is missing required 'parameters' key or 'parameters' is not a dict
        """
        if 'parameters' not in data:
            raise ValueError("Missing required key 'parameters' in data")

        params = data['parameters']
        if not isinstance(params, dict):
            raise ValueError(
                f"'parameters' must be a dict, got {type(params).__name__}"
            )

        return cls(parameters=params)
