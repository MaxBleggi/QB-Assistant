"""
ScenarioForecastOrchestrator - Orchestrates multi-scenario forecast calculations.

Coordinates CashFlowForecastCalculator and PLForecastCalculator across multiple scenarios
(Conservative/Expected/Optimistic), enforces uniform horizon policy, and aggregates results
into MultiScenarioForecastResult for Epic 6 report generation.

Provides persistence integration via save_scenarios() and load_scenarios() methods
using ConfigManager to persist scenario definitions to client configuration directory.
"""
from typing import Optional
import copy
import logging
import os

from src.models.cash_flow_model import CashFlowModel
from src.models.pl_model import PLModel
from src.models.forecast_scenario import ForecastScenariosCollection
from src.models.anomaly_annotation import AnomalyAnnotationModel
from src.models.multi_scenario_forecast_result import MultiScenarioForecastResult
from src.models.forecast_validation import ValidationThresholds
from src.services.cash_flow_forecast_calculator import CashFlowForecastCalculator
from src.services.pl_forecast_calculator import PLForecastCalculator
from src.validators.forecast_validator import ForecastValidator
from src.persistence.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class ScenarioForecastOrchestrator:
    """
    Orchestrates multi-scenario forecast calculations with uniform horizon enforcement.

    Accepts CashFlowModel, PLModel, ForecastScenariosCollection, and global configuration.
    For each scenario: overrides horizon with global config, invokes both calculators,
    aggregates results into MultiScenarioForecastResult.
    """

    def __init__(
        self,
        cash_flow_model: CashFlowModel,
        pl_model: PLModel,
        scenarios_collection: ForecastScenariosCollection,
        global_config,
        anomaly_annotations: Optional[AnomalyAnnotationModel] = None
    ):
        """
        Initialize orchestrator with models, scenarios, and configuration.

        Args:
            cash_flow_model: CashFlowModel instance with historical cash flow data
            pl_model: PLModel instance with historical P&L data
            scenarios_collection: ForecastScenariosCollection with scenarios to process
            global_config: GlobalConfigModel instance with forecast_horizon setting
            anomaly_annotations: Optional AnomalyAnnotationModel for baseline exclusions
        """
        self.cash_flow_model = cash_flow_model
        self.pl_model = pl_model
        self.scenarios_collection = scenarios_collection
        self.global_config = global_config
        self.anomaly_annotations = anomaly_annotations

    def calculate_multi_scenario_forecasts(self) -> MultiScenarioForecastResult:
        """
        Calculate forecasts for all scenarios with uniform horizon enforcement.

        Process:
        1. Extract global forecast_horizon from config
        2. For each scenario in collection:
           a. Create deep copy of scenario to avoid mutation
           b. Override scenario.parameters['forecast_horizon'] with global horizon
           c. Invoke CashFlowForecastCalculator.calculate()
           d. Invoke PLForecastCalculator.calculate()
           e. Store results in aggregation dict
        3. Return MultiScenarioForecastResult with all scenario forecasts

        Returns:
            MultiScenarioForecastResult with scenario_forecasts dict mapping
            scenario names to {'cash_flow_forecast', 'pl_forecast'}

        Raises:
            ValueError: If any scenario calculation fails, with scenario name and error details
        """
        # Extract global forecast horizon (uniform policy enforcement)
        global_horizon = self.global_config.forecast_horizon

        logger.info(
            f"Starting multi-scenario forecast calculation with "
            f"global horizon={global_horizon} months"
        )

        # Aggregate results from all scenarios
        scenario_forecasts = {}

        # Get list of scenarios to process
        scenarios = self.scenarios_collection.list_scenarios()

        if not scenarios:
            logger.warning("Empty ForecastScenariosCollection - returning empty result")
            return MultiScenarioForecastResult(
                scenario_forecasts={},
                forecast_horizon=global_horizon,
                client_id=getattr(self.global_config, 'client_id', None)
            )

        # Process each scenario
        for scenario in scenarios:
            scenario_name = scenario.scenario_name
            logger.info(f"Processing scenario: {scenario_name}")

            try:
                # Create deep copy to avoid mutating original scenario
                scenario_copy = copy.deepcopy(scenario)

                # UNIFORM HORIZON ENFORCEMENT:
                # Override scenario's forecast_horizon with global config value
                scenario_copy.parameters['forecast_horizon'] = global_horizon

                logger.debug(
                    f"Scenario '{scenario_name}': Overriding horizon to {global_horizon}"
                )

                # Calculate Cash Flow forecast for this scenario
                cash_flow_calculator = CashFlowForecastCalculator(
                    cash_flow_model=self.cash_flow_model,
                    forecast_scenario=scenario_copy,
                    anomaly_annotations=self.anomaly_annotations
                )
                cash_flow_forecast = cash_flow_calculator.calculate()

                logger.debug(f"Scenario '{scenario_name}': Cash Flow forecast complete")

                # Calculate P&L forecast for this scenario
                pl_calculator = PLForecastCalculator(
                    pl_model=self.pl_model,
                    forecast_scenario=scenario_copy,
                    anomaly_annotations=self.anomaly_annotations
                )
                pl_forecast = pl_calculator.calculate()

                logger.debug(f"Scenario '{scenario_name}': P&L forecast complete")

                # Validate forecast results
                validation_result = None
                try:
                    thresholds = ValidationThresholds()
                    validator = ForecastValidator(
                        cash_flow_forecast=cash_flow_forecast,
                        pl_forecast=pl_forecast,
                        thresholds=thresholds
                    )
                    validation_result = validator.validate()
                    logger.debug(
                        f"Scenario '{scenario_name}': Validation complete - "
                        f"status={validation_result.validation_status}, "
                        f"warnings={len(validation_result.warnings)}"
                    )
                except Exception as validation_error:
                    # Log error but continue - validation failure shouldn't break forecasting
                    logger.error(
                        f"Scenario '{scenario_name}': Validation failed - {str(validation_error)}"
                    )
                    validation_result = None

                # Store results for this scenario
                scenario_forecasts[scenario_name] = {
                    'cash_flow_forecast': cash_flow_forecast,
                    'pl_forecast': pl_forecast,
                    'validation_result': validation_result
                }

                logger.info(
                    f"Scenario '{scenario_name}': Completed successfully "
                    f"(both forecasts generated with 3 series each)"
                )

            except Exception as e:
                # Re-raise with scenario context for debugging
                error_msg = (
                    f"Failed to calculate forecast for scenario '{scenario_name}': "
                    f"{type(e).__name__}: {str(e)}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e

        # Create multi-scenario result
        logger.info(
            f"Multi-scenario forecast calculation complete: "
            f"{len(scenario_forecasts)} scenarios processed"
        )

        return MultiScenarioForecastResult(
            scenario_forecasts=scenario_forecasts,
            forecast_horizon=global_horizon,
            client_id=getattr(self.global_config, 'client_id', None)
        )


def save_scenarios(
    scenarios_collection: ForecastScenariosCollection,
    client_config_path: str
) -> None:
    """
    Save ForecastScenariosCollection to client configuration directory.

    Uses ConfigManager to persist scenarios to 'scenarios.json' file in client config path.

    Args:
        scenarios_collection: ForecastScenariosCollection instance to persist
        client_config_path: Absolute path to client configuration directory

    Raises:
        ValueError: If filepath is invalid or outside config directory
        PermissionError: If insufficient permissions to write file
        OSError: If other file I/O error occurs
    """
    # ConfigManager expects project root, scenarios.json will be in config/ subdirectory
    # We need to determine project root from client_config_path
    # Assuming client_config_path is like /path/to/project/config/client_name
    # We need to go up to /path/to/project

    # If client_config_path ends with 'config', use parent; otherwise use it as-is
    config_path = os.path.abspath(client_config_path)

    # Determine project root (parent of config directory)
    if config_path.endswith('config') or '/config/' in config_path or '\\config\\' in config_path:
        # Extract project root (parent of config dir)
        parts = config_path.split(os.sep)
        if 'config' in parts:
            config_idx = parts.index('config')
            project_root = os.sep.join(parts[:config_idx])
        else:
            # Fallback: assume config_path IS the config directory
            project_root = os.path.dirname(config_path)
    else:
        # client_config_path is project root
        project_root = config_path

    # Initialize ConfigManager with project root
    config_manager = ConfigManager(project_root)

    # Determine relative path for scenarios.json
    # If client_config_path has subdirectory under config/, preserve it
    # Otherwise just use 'scenarios.json'
    relative_parts = config_path.replace(project_root, '').strip(os.sep).split(os.sep)

    if relative_parts[0] == 'config' and len(relative_parts) > 1:
        # Has client subdirectory like config/client_name
        # Save to config/client_name/scenarios.json
        relative_path = os.path.join(*relative_parts[1:], 'scenarios.json')
    else:
        # Direct config directory
        relative_path = 'scenarios.json'

    logger.info(f"Saving scenarios to {relative_path} in config directory")

    # Save using ConfigManager
    config_manager.save_config(scenarios_collection, relative_path)

    logger.info(f"Scenarios saved successfully to {relative_path}")


def load_scenarios(client_config_path: str) -> ForecastScenariosCollection:
    """
    Load ForecastScenariosCollection from client configuration directory.

    Uses ConfigManager to load scenarios from 'scenarios.json' file in client config path.
    Returns empty collection if file doesn't exist (first run).

    Args:
        client_config_path: Absolute path to client configuration directory

    Returns:
        ForecastScenariosCollection with scenarios reconstructed from file,
        or empty collection if file doesn't exist

    Raises:
        ValueError: If filepath is invalid or outside config directory
        JSONDecodeError: If file contains invalid JSON syntax
        PermissionError: If insufficient permissions to read file
    """
    # Same project root determination logic as save_scenarios
    config_path = os.path.abspath(client_config_path)

    if config_path.endswith('config') or '/config/' in config_path or '\\config\\' in config_path:
        parts = config_path.split(os.sep)
        if 'config' in parts:
            config_idx = parts.index('config')
            project_root = os.sep.join(parts[:config_idx])
        else:
            project_root = os.path.dirname(config_path)
    else:
        project_root = config_path

    # Initialize ConfigManager with project root
    config_manager = ConfigManager(project_root)

    # Determine relative path for scenarios.json
    relative_parts = config_path.replace(project_root, '').strip(os.sep).split(os.sep)

    if relative_parts[0] == 'config' and len(relative_parts) > 1:
        relative_path = os.path.join(*relative_parts[1:], 'scenarios.json')
    else:
        relative_path = 'scenarios.json'

    logger.info(f"Loading scenarios from {relative_path} in config directory")

    try:
        # Load using ConfigManager with ForecastScenariosCollection class
        scenarios_collection = config_manager.load_config(
            relative_path,
            model_class=ForecastScenariosCollection
        )
        logger.info(
            f"Scenarios loaded successfully: "
            f"{len(scenarios_collection.list_scenarios())} scenarios"
        )
        return scenarios_collection

    except FileNotFoundError:
        # First run - file doesn't exist yet
        logger.info(
            f"No scenarios file found at {relative_path} - returning empty collection"
        )
        return ForecastScenariosCollection()
    except Exception as e:
        # Re-raise other exceptions (JSON decode errors, permission errors, etc.)
        logger.error(f"Error loading scenarios from {relative_path}: {str(e)}")
        raise
