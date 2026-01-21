"""
Forecast scenario data models.

Provides ForecastScenarioModel for individual scenarios with metadata and parameters,
and ForecastScenariosCollection wrapper for managing multiple scenarios in a single
configuration file.
"""
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from .parameters import ParameterModel


class ForecastScenarioModel(ParameterModel):
    """
    Data model for individual forecast scenario with metadata.

    Extends ParameterModel to add scenario-specific metadata (ID, name, description,
    created date) while maintaining parameter storage in self._parameters dict.
    """

    def __init__(
        self,
        parameters: Dict[str, Any] = None,
        scenario_id: str = None,
        scenario_name: str = "",
        description: str = "",
        created_date: str = None
    ):
        """
        Initialize forecast scenario model with metadata and parameters.

        Args:
            parameters: Dictionary of forecast parameter key-value pairs (default: empty dict)
            scenario_id: Unique scenario identifier (default: auto-generated UUID)
            scenario_name: Human-readable scenario name (default: empty string)
            description: Scenario description (default: empty string)
            created_date: ISO format creation timestamp (default: current timestamp)
        """
        super().__init__(parameters)

        # Scenario metadata
        self.scenario_id = scenario_id if scenario_id is not None else uuid.uuid4().hex
        self.scenario_name = scenario_name
        self.description = description
        self.created_date = created_date if created_date is not None else datetime.now().isoformat()

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert model to dictionary for serialization.

        Args:
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            Dictionary with metadata keys (scenario_id, scenario_name, description,
            created_date) and 'parameters' key containing parameter data
        """
        base_dict = super().to_dict(orient)

        # Merge metadata with base dict
        return {
            'scenario_id': self.scenario_id,
            'scenario_name': self.scenario_name,
            'description': self.description,
            'created_date': self.created_date,
            'parameters': base_dict['parameters']
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'ForecastScenarioModel':
        """
        Create ForecastScenarioModel from dictionary.

        Args:
            data: Dictionary with metadata keys and 'parameters' key
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            New ForecastScenarioModel instance with metadata and parameters

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

        return cls(
            parameters=params,
            scenario_id=data.get('scenario_id'),
            scenario_name=data.get('scenario_name', ''),
            description=data.get('description', ''),
            created_date=data.get('created_date')
        )


class ForecastScenariosCollection(ParameterModel):
    """
    Wrapper model for managing collection of forecast scenarios.

    Stores list of ForecastScenarioModel instances in self._parameters['scenarios']
    for ConfigManager compatibility. Provides CRUD operations on scenario collection.
    """

    def __init__(self, scenarios: List[ForecastScenarioModel] = None):
        """
        Initialize scenarios collection.

        Args:
            scenarios: List of ForecastScenarioModel instances (default: empty list)
        """
        # Store scenarios list in parameters dict for ConfigManager compatibility
        super().__init__(parameters={'scenarios': []})

        # Add scenarios if provided
        if scenarios:
            for scenario in scenarios:
                self.add_scenario(scenario)

    def add_scenario(self, scenario: ForecastScenarioModel) -> None:
        """
        Add scenario to collection.

        Args:
            scenario: ForecastScenarioModel instance to add
        """
        self._parameters['scenarios'].append(scenario)

    def remove_scenario(self, scenario_id: str) -> None:
        """
        Remove scenario from collection by ID.

        Args:
            scenario_id: Unique scenario identifier

        Raises:
            KeyError: If scenario with given ID not found
        """
        scenarios = self._parameters['scenarios']
        for i, scenario in enumerate(scenarios):
            if scenario.scenario_id == scenario_id:
                scenarios.pop(i)
                return

        raise KeyError(f"Scenario with id '{scenario_id}' not found")

    def get_scenario(self, scenario_id: str) -> ForecastScenarioModel:
        """
        Retrieve scenario by ID.

        Args:
            scenario_id: Unique scenario identifier

        Returns:
            ForecastScenarioModel instance with matching ID

        Raises:
            KeyError: If scenario with given ID not found
        """
        scenarios = self._parameters['scenarios']
        for scenario in scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario

        raise KeyError(f"Scenario with id '{scenario_id}' not found")

    def list_scenarios(self) -> List[ForecastScenarioModel]:
        """
        Get list of all scenarios in collection.

        Returns:
            List of ForecastScenarioModel instances
        """
        return self._parameters['scenarios']

    def to_dict(self, orient: str = 'records') -> Dict[str, Any]:
        """
        Convert collection to dictionary for serialization.

        Args:
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            Dictionary with 'parameters' key containing 'scenarios' list of scenario dicts
        """
        scenarios_dicts = [scenario.to_dict() for scenario in self._parameters['scenarios']]
        return {
            'parameters': {
                'scenarios': scenarios_dicts
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], orient: str = 'records') -> 'ForecastScenariosCollection':
        """
        Create ForecastScenariosCollection from dictionary.

        Args:
            data: Dictionary with 'parameters' key containing 'scenarios' list
            orient: Ignored (kept for signature compatibility with DataModel)

        Returns:
            New ForecastScenariosCollection instance with all scenarios reconstructed

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

        if 'scenarios' not in params:
            raise ValueError("Missing required key 'scenarios' in parameters")

        scenarios_data = params['scenarios']
        if not isinstance(scenarios_data, list):
            raise ValueError(
                f"'scenarios' must be a list, got {type(scenarios_data).__name__}"
            )

        # Reconstruct each scenario from dict
        scenarios = [ForecastScenarioModel.from_dict(scenario_dict) for scenario_dict in scenarios_data]

        return cls(scenarios=scenarios)
