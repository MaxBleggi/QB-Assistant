"""
MultiScenarioForecastResult - Data model for multi-scenario forecast results.

Stores results from multiple scenario forecasts (Conservative/Expected/Optimistic),
each containing Cash Flow and P&L forecasts with confidence intervals (3 series each).
Provides side-by-side comparison structure for Epic 6 report generation.
"""
from typing import Any, Dict, Optional
from datetime import datetime

from .cash_flow_forecast_model import CashFlowForecastModel
from .pl_forecast_model import PLForecastModel


class MultiScenarioForecastResult:
    """
    Data model for storing multi-scenario forecast results with side-by-side comparison structure.

    Stores dict mapping scenario_name to forecast results containing both Cash Flow and P&L forecasts.
    Each scenario produces 2 forecast types × 3 series = 6 data series (projected/lower/upper for each).
    Includes metadata for forecast horizon, timestamp, and client identification.
    """

    def __init__(
        self,
        scenario_forecasts: Dict[str, Dict[str, Any]] = None,
        forecast_horizon: int = 6,
        client_id: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        """
        Initialize multi-scenario forecast result.

        Args:
            scenario_forecasts: Dict mapping scenario_name to forecast results dict
                               Each forecast results dict contains:
                               - 'cash_flow_forecast': CashFlowForecastModel instance
                               - 'pl_forecast': PLForecastModel instance
            forecast_horizon: Forecast horizon in months (6 or 12)
            client_id: Client identifier for multi-tenant support
            created_at: ISO format timestamp (default: current timestamp)
        """
        self.scenario_forecasts = scenario_forecasts if scenario_forecasts is not None else {}
        self.forecast_horizon = forecast_horizon
        self.client_id = client_id
        self.created_at = created_at if created_at is not None else datetime.now().isoformat()

    def get_scenario_forecast(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """
        Get forecast results for specific scenario.

        Args:
            scenario_name: Name of scenario (e.g., 'Conservative', 'Expected', 'Optimistic')

        Returns:
            Dict with 'cash_flow_forecast' and 'pl_forecast' keys containing respective models,
            or None if scenario not found
        """
        return self.scenario_forecasts.get(scenario_name)

    def list_scenarios(self) -> list:
        """
        Get list of all scenario names in this result.

        Returns:
            List of scenario names (strings)
        """
        return list(self.scenario_forecasts.keys())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary for serialization.

        Returns:
            Dictionary with keys:
            - 'forecast_horizon': int
            - 'client_id': str or None
            - 'created_at': ISO timestamp string
            - 'scenario_forecasts': dict mapping scenario names to serialized forecast dicts
        """
        scenario_forecasts_dict = {}
        for scenario_name, forecasts in self.scenario_forecasts.items():
            scenario_forecasts_dict[scenario_name] = {
                'cash_flow_forecast': forecasts['cash_flow_forecast'].to_dict(),
                'pl_forecast': forecasts['pl_forecast'].to_dict()
            }

        return {
            'forecast_horizon': self.forecast_horizon,
            'client_id': self.client_id,
            'created_at': self.created_at,
            'scenario_forecasts': scenario_forecasts_dict
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiScenarioForecastResult':
        """
        Create MultiScenarioForecastResult from dictionary.

        Args:
            data: Dictionary with forecast_horizon, client_id, created_at, and scenario_forecasts

        Returns:
            New MultiScenarioForecastResult instance with CashFlowForecastModel and
            PLForecastModel objects reconstructed

        Raises:
            ValueError: If data is missing required keys or has invalid structure
        """
        if 'scenario_forecasts' not in data:
            raise ValueError("Missing required key 'scenario_forecasts' in data")

        scenario_forecasts_data = data['scenario_forecasts']
        if not isinstance(scenario_forecasts_data, dict):
            raise ValueError(
                f"'scenario_forecasts' must be a dict, got {type(scenario_forecasts_data).__name__}"
            )

        # Reconstruct forecast models for each scenario
        scenario_forecasts = {}
        for scenario_name, forecasts_dict in scenario_forecasts_data.items():
            if 'cash_flow_forecast' not in forecasts_dict:
                raise ValueError(
                    f"Scenario '{scenario_name}' missing 'cash_flow_forecast'"
                )
            if 'pl_forecast' not in forecasts_dict:
                raise ValueError(
                    f"Scenario '{scenario_name}' missing 'pl_forecast'"
                )

            scenario_forecasts[scenario_name] = {
                'cash_flow_forecast': CashFlowForecastModel.from_dict(
                    forecasts_dict['cash_flow_forecast']
                ),
                'pl_forecast': PLForecastModel.from_dict(
                    forecasts_dict['pl_forecast']
                )
            }

        return cls(
            scenario_forecasts=scenario_forecasts,
            forecast_horizon=data.get('forecast_horizon', 6),
            client_id=data.get('client_id'),
            created_at=data.get('created_at')
        )
