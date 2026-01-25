"""
Client configuration model for aggregated client settings.

Provides unified configuration storage for budget parameters, forecast scenarios,
and global settings in a single client-specific config.yaml file.
"""
from typing import Any, Dict

from .parameters import ParameterModel


class ClientConfigModel(ParameterModel):
    """
    Data model for aggregated client configuration.

    Extends ParameterModel to store nested configuration for:
    - budget_parameters: Budget defaults and overrides
    - forecast_scenarios: Forecast scenario collection
    - global_settings: Client-wide global configuration

    Attributes:
        budget_parameters: Dictionary of budget parameter key-value pairs
        forecast_scenarios: Dictionary of forecast scenario configurations
        global_settings: Dictionary of global settings (e.g., forecast_horizon)
    """

    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize client config model with nested configuration structure.

        Args:
            parameters: Dictionary of parameter key-value pairs (default: empty dict)
        """
        super().__init__(parameters)

        # Initialize nested config sections if not present
        if 'budget_parameters' not in self._parameters:
            self._parameters['budget_parameters'] = {}
        if 'forecast_scenarios' not in self._parameters:
            self._parameters['forecast_scenarios'] = {}
        if 'global_settings' not in self._parameters:
            self._parameters['global_settings'] = {}

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary for serialization.

        Args:
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            Dictionary with 'parameters' key containing nested config structure
        """
        return super().to_dict(orient)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'ClientConfigModel':
        """
        Reconstruct model from nested dictionary with validation.

        Args:
            data: Dictionary from YAML deserialization
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            ClientConfigModel instance

        Raises:
            ValueError: If data structure is invalid
        """
        instance = cls()

        # Extract parameters dict (top-level key)
        params = data.get('parameters', {})

        if not isinstance(params, dict):
            raise ValueError(
                f"Invalid config structure: 'parameters' must be dict, "
                f"got {type(params).__name__}"
            )

        # Extract and validate nested configs
        budget = params.get('budget_parameters', {})
        forecast = params.get('forecast_scenarios', {})
        global_cfg = params.get('global_settings', {})

        # Type validation for security
        if not isinstance(budget, dict):
            raise ValueError("budget_parameters must be a dictionary")
        if not isinstance(forecast, dict):
            raise ValueError("forecast_scenarios must be a dictionary")
        if not isinstance(global_cfg, dict):
            raise ValueError("global_settings must be a dictionary")

        # Set validated values
        instance._parameters['budget_parameters'] = budget
        instance._parameters['forecast_scenarios'] = forecast
        instance._parameters['global_settings'] = global_cfg

        return instance

    def get_budget_config(self) -> Dict[str, Any]:
        """
        Get budget parameters configuration.

        Returns:
            Dictionary of budget parameter key-value pairs
        """
        return self._parameters['budget_parameters']

    def get_forecast_config(self) -> Dict[str, Any]:
        """
        Get forecast scenarios configuration.

        Returns:
            Dictionary of forecast scenario configurations
        """
        return self._parameters['forecast_scenarios']

    def get_global_config(self) -> Dict[str, Any]:
        """
        Get global settings configuration.

        Returns:
            Dictionary of global settings
        """
        return self._parameters['global_settings']

    def set_budget_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Update budget parameters configuration.

        Args:
            config_dict: Dictionary of budget parameter key-value pairs
        """
        if not isinstance(config_dict, dict):
            raise ValueError("config_dict must be a dictionary")
        self._parameters['budget_parameters'] = config_dict

    def set_forecast_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Update forecast scenarios configuration.

        Args:
            config_dict: Dictionary of forecast scenario configurations
        """
        if not isinstance(config_dict, dict):
            raise ValueError("config_dict must be a dictionary")
        self._parameters['forecast_scenarios'] = config_dict

    def set_global_config(self, config_dict: Dict[str, Any]) -> None:
        """
        Update global settings configuration.

        Args:
            config_dict: Dictionary of global settings
        """
        if not isinstance(config_dict, dict):
            raise ValueError("config_dict must be a dictionary")
        self._parameters['global_settings'] = config_dict
