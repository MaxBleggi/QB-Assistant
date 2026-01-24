"""
Global configuration model for client-wide settings.

Extends ParameterModel to store global application settings such as forecast
horizon that apply uniformly across all scenarios.
"""
from typing import Any, Dict

from .parameters import ParameterModel


class GlobalConfigModel(ParameterModel):
    """
    Data model for global client-wide configuration settings.

    Extends ParameterModel to add forecast_horizon field with validation.
    The forecast horizon determines the time window for forecast calculations:
    - 6-month: For near-term operational liquidity planning
    - 12-month: For strategic expansion decisions and long-term planning

    Attributes:
        forecast_horizon: Integer value of 6 or 12 (months)
    """

    def __init__(self, parameters: Dict[str, Any] = None, forecast_horizon: int = 6):
        """
        Initialize global config model with forecast horizon.

        Args:
            parameters: Dictionary of parameter key-value pairs (default: empty dict)
            forecast_horizon: Forecast horizon in months, must be 6 or 12 (default: 6)

        Raises:
            ValueError: If forecast_horizon is not 6 or 12
        """
        super().__init__(parameters)

        # Validate and set forecast_horizon
        if forecast_horizon not in [6, 12]:
            raise ValueError(
                f"Invalid forecast_horizon value: {forecast_horizon}. "
                f"Must be 6 (near-term operational planning) or 12 (strategic expansion planning)."
            )
        self.forecast_horizon = forecast_horizon

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary for serialization.

        Args:
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            Dictionary with 'parameters' key containing forecast_horizon
        """
        base_dict = super().to_dict(orient)

        # Merge forecast_horizon into parameters
        base_dict['parameters']['forecast_horizon'] = self.forecast_horizon

        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'GlobalConfigModel':
        """
        Create GlobalConfigModel from dictionary.

        Args:
            data: Dictionary with 'parameters' key containing forecast_horizon
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            New GlobalConfigModel instance with forecast_horizon

        Raises:
            ValueError: If data is missing required keys or has invalid structure
        """
        if 'parameters' not in data:
            raise ValueError("Missing required key 'parameters' in data")

        params = data['parameters']
        if not isinstance(params, dict):
            raise ValueError(
                f"'parameters' must be a dict, got {type(params).__name__}"
            )

        # Extract forecast_horizon, default to 6 if not present
        forecast_horizon = params.get('forecast_horizon', 6)

        # Remove forecast_horizon from params dict to avoid duplication
        params_copy = params.copy()
        params_copy.pop('forecast_horizon', None)

        return cls(
            parameters=params_copy,
            forecast_horizon=forecast_horizon
        )
