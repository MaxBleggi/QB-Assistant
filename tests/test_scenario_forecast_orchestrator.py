"""
Tests for ScenarioForecastOrchestrator service.

Verifies uniform horizon enforcement, multi-scenario calculation, template instantiation,
exception handling, and persistence integration.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.services.scenario_forecast_orchestrator import (
    ScenarioForecastOrchestrator,
    save_scenarios,
    load_scenarios
)
from src.models.forecast_scenario import ForecastScenarioModel, ForecastScenariosCollection
from src.models.cash_flow_model import CashFlowModel
from src.models.pl_model import PLModel
from src.models.cash_flow_forecast_model import CashFlowForecastModel
from src.models.pl_forecast_model import PLForecastModel
from src.models.multi_scenario_forecast_result import MultiScenarioForecastResult
from src.services.forecast_templates import ForecastTemplateService


@pytest.fixture
def mock_cash_flow_model():
    """Create mock CashFlowModel for testing."""
    df = pd.DataFrame({
        'Operating Activities': [100, 110, 120],
        'Investing Activities': [50, 55, 60],
        'Financing Activities': [30, 33, 36]
    })
    return CashFlowModel(df, hierarchy={}, calculated_rows=[], metadata={})


@pytest.fixture
def mock_pl_model():
    """Create mock PLModel for testing."""
    df = pd.DataFrame({
        'Income': [500, 550, 600],
        'COGS': [200, 220, 240],
        'Operating Expenses': [150, 165, 180]
    })
    return PLModel(df, hierarchy={}, calculated_rows=[])


@pytest.fixture
def mock_forecast_scenarios_collection():
    """Create mock ForecastScenariosCollection with 3 scenarios."""
    scenarios = [
        ForecastScenarioModel(
            parameters={'forecast_horizon': 6, 'monthly_rate': 0.02},
            scenario_name='Conservative',
            description='Conservative growth scenario'
        ),
        ForecastScenarioModel(
            parameters={'forecast_horizon': 6, 'monthly_rate': 0.05},
            scenario_name='Expected',
            description='Expected growth scenario'
        ),
        ForecastScenarioModel(
            parameters={'forecast_horizon': 6, 'monthly_rate': 0.10},
            scenario_name='Optimistic',
            description='Optimistic growth scenario'
        )
    ]
    return ForecastScenariosCollection(scenarios=scenarios)


@pytest.fixture
def mock_global_config_model():
    """Create mock GlobalConfigModel with forecast_horizon=12."""
    config = Mock()
    config.forecast_horizon = 12
    config.client_id = 'test_client_123'
    return config


@pytest.fixture
def mock_anomaly_annotations():
    """Create mock AnomalyAnnotationModel for testing."""
    return None  # Simplified for testing


@pytest.fixture
def mock_cash_flow_forecast():
    """Create mock CashFlowForecastModel."""
    df = pd.DataFrame()
    hierarchy = {
        'OPERATING ACTIVITIES': {
            'projected': [100] * 12,
            'lower_bound': [90] * 12,
            'upper_bound': [110] * 12
        }
    }
    calculated_rows = {
        'beginning_cash': {
            'projected': [1000] * 12,
            'lower_bound': [950] * 12,
            'upper_bound': [1050] * 12
        },
        'ending_cash': {
            'projected': [1100] * 12,
            'lower_bound': [1050] * 12,
            'upper_bound': [1150] * 12
        }
    }
    metadata = {
        'confidence_level': 0.90,
        'forecast_horizon': 12,
        'excluded_periods': [],
        'warnings': []
    }
    return CashFlowForecastModel(df, hierarchy, calculated_rows, metadata)


@pytest.fixture
def mock_pl_forecast():
    """Create mock PLForecastModel."""
    hierarchy = {
        'Income': {
            'projected': [500] * 12,
            'lower_bound': [475] * 12,
            'upper_bound': [525] * 12
        }
    }
    calculated_rows = {
        'gross_profit': {
            'projected': [200] * 12,
            'lower_bound': [190] * 12,
            'upper_bound': [210] * 12
        }
    }
    metadata = {
        'confidence_level': 0.90,
        'forecast_horizon': 12,
        'excluded_periods': [],
        'warnings': []
    }
    return PLForecastModel(hierarchy, calculated_rows, metadata)


def test_orchestrator_uniform_horizon_enforcement(
    mock_cash_flow_model,
    mock_pl_model,
    mock_forecast_scenarios_collection,
    mock_global_config_model,
    mock_cash_flow_forecast,
    mock_pl_forecast
):
    """Verify scenario horizon is overridden by global config before calculator invocation."""
    orchestrator = ScenarioForecastOrchestrator(
        cash_flow_model=mock_cash_flow_model,
        pl_model=mock_pl_model,
        scenarios_collection=mock_forecast_scenarios_collection,
        global_config=mock_global_config_model
    )

    # Mock the calculators
    with patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator') as MockCFCalc, \
         patch('src.services.scenario_forecast_orchestrator.PLForecastCalculator') as MockPLCalc:

        # Set up mocks to return forecast models
        mock_cf_instance = MockCFCalc.return_value
        mock_cf_instance.calculate.return_value = mock_cash_flow_forecast

        mock_pl_instance = MockPLCalc.return_value
        mock_pl_instance.calculate.return_value = mock_pl_forecast

        # Execute
        result = orchestrator.calculate_multi_scenario_forecasts()

        # Verify global horizon was used
        assert result.forecast_horizon == 12

        # Verify calculators were called with scenarios having overridden horizon
        # Check that the scenario passed to calculator had horizon=12
        for call in MockCFCalc.call_args_list:
            _, kwargs = call
            scenario = kwargs.get('forecast_scenario') or call[0][1]
            assert scenario.parameters['forecast_horizon'] == 12


def test_orchestrator_multi_scenario_calculation(
    mock_cash_flow_model,
    mock_pl_model,
    mock_forecast_scenarios_collection,
    mock_global_config_model,
    mock_cash_flow_forecast,
    mock_pl_forecast
):
    """Verify all scenarios are processed and results aggregated correctly."""
    orchestrator = ScenarioForecastOrchestrator(
        cash_flow_model=mock_cash_flow_model,
        pl_model=mock_pl_model,
        scenarios_collection=mock_forecast_scenarios_collection,
        global_config=mock_global_config_model
    )

    with patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator') as MockCFCalc, \
         patch('src.services.scenario_forecast_orchestrator.PLForecastCalculator') as MockPLCalc:

        mock_cf_instance = MockCFCalc.return_value
        mock_cf_instance.calculate.return_value = mock_cash_flow_forecast

        mock_pl_instance = MockPLCalc.return_value
        mock_pl_instance.calculate.return_value = mock_pl_forecast

        result = orchestrator.calculate_multi_scenario_forecasts()

        # Verify result is MultiScenarioForecastResult
        assert isinstance(result, MultiScenarioForecastResult)

        # Verify 3 scenarios were processed
        assert len(result.list_scenarios()) == 3
        assert 'Conservative' in result.list_scenarios()
        assert 'Expected' in result.list_scenarios()
        assert 'Optimistic' in result.list_scenarios()

        # Verify forecast_horizon is set
        assert result.forecast_horizon == 12


def test_orchestrator_three_series_per_scenario(
    mock_cash_flow_model,
    mock_pl_model,
    mock_forecast_scenarios_collection,
    mock_global_config_model,
    mock_cash_flow_forecast,
    mock_pl_forecast
):
    """Verify each scenario's forecasts contain projected/lower_bound/upper_bound series."""
    orchestrator = ScenarioForecastOrchestrator(
        cash_flow_model=mock_cash_flow_model,
        pl_model=mock_pl_model,
        scenarios_collection=mock_forecast_scenarios_collection,
        global_config=mock_global_config_model
    )

    with patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator') as MockCFCalc, \
         patch('src.services.scenario_forecast_orchestrator.PLForecastCalculator') as MockPLCalc:

        mock_cf_instance = MockCFCalc.return_value
        mock_cf_instance.calculate.return_value = mock_cash_flow_forecast

        mock_pl_instance = MockPLCalc.return_value
        mock_pl_instance.calculate.return_value = mock_pl_forecast

        result = orchestrator.calculate_multi_scenario_forecasts()

        # Check each scenario has both forecasts
        for scenario_name in result.list_scenarios():
            forecasts = result.get_scenario_forecast(scenario_name)
            assert 'cash_flow_forecast' in forecasts
            assert 'pl_forecast' in forecasts

            # Verify cash flow forecast has 3 series
            cf_forecast = forecasts['cash_flow_forecast']
            assert 'projected' in cf_forecast.hierarchy['OPERATING ACTIVITIES']
            assert 'lower_bound' in cf_forecast.hierarchy['OPERATING ACTIVITIES']
            assert 'upper_bound' in cf_forecast.hierarchy['OPERATING ACTIVITIES']

            # Verify PL forecast has 3 series
            pl_forecast = forecasts['pl_forecast']
            assert 'projected' in pl_forecast.hierarchy['Income']
            assert 'lower_bound' in pl_forecast.hierarchy['Income']
            assert 'upper_bound' in pl_forecast.hierarchy['Income']


def test_orchestrator_calculator_exception_handling(
    mock_cash_flow_model,
    mock_pl_model,
    mock_forecast_scenarios_collection,
    mock_global_config_model
):
    """Verify calculator exceptions are caught and re-raised with scenario context."""
    orchestrator = ScenarioForecastOrchestrator(
        cash_flow_model=mock_cash_flow_model,
        pl_model=mock_pl_model,
        scenarios_collection=mock_forecast_scenarios_collection,
        global_config=mock_global_config_model
    )

    with patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator') as MockCFCalc:
        # Make calculator raise an exception
        mock_cf_instance = MockCFCalc.return_value
        mock_cf_instance.calculate.side_effect = ValueError("Invalid parameter")

        # Verify exception is raised with scenario context
        with pytest.raises(ValueError) as exc_info:
            orchestrator.calculate_multi_scenario_forecasts()

        # Verify error message includes scenario name
        assert 'Conservative' in str(exc_info.value)
        assert 'Invalid parameter' in str(exc_info.value)


def test_orchestrator_empty_scenarios_collection(
    mock_cash_flow_model,
    mock_pl_model,
    mock_global_config_model
):
    """Verify empty collection returns empty result without errors."""
    # Create empty scenarios collection
    empty_collection = ForecastScenariosCollection()

    orchestrator = ScenarioForecastOrchestrator(
        cash_flow_model=mock_cash_flow_model,
        pl_model=mock_pl_model,
        scenarios_collection=empty_collection,
        global_config=mock_global_config_model
    )

    result = orchestrator.calculate_multi_scenario_forecasts()

    # Verify empty result
    assert isinstance(result, MultiScenarioForecastResult)
    assert len(result.list_scenarios()) == 0
    assert result.forecast_horizon == 12


def test_template_to_scenario_flattening():
    """Verify nested template structure is flattened to ForecastScenarioModel parameters format."""
    scenario = ForecastTemplateService.create_scenario_from_template(
        template_name='Conservative',
        scenario_name='Test Conservative',
        overrides=None
    )

    # Verify scenario created
    assert scenario.scenario_name == 'Test Conservative'
    assert 'Conservative template' in scenario.description

    # Verify nested structure was flattened
    # Original template has {'revenue_growth_rates': {'monthly_rate': 0.02}}
    # Should be flattened to {'monthly_rate': 0.02}
    assert 'monthly_rate' in scenario.parameters
    assert scenario.parameters['monthly_rate'] == 0.02


def test_template_to_scenario_override_merge():
    """Verify user overrides are merged correctly with template defaults."""
    scenario = ForecastTemplateService.create_scenario_from_template(
        template_name='Expected',
        scenario_name='Custom Expected',
        overrides={'monthly_rate': 0.08}
    )

    # Verify override was applied
    assert scenario.parameters['monthly_rate'] == 0.08

    # Verify other template defaults preserved
    assert 'use_averaged' in scenario.parameters
    assert scenario.parameters['use_averaged'] is True


def test_template_to_scenario_invalid_template():
    """Verify ValueError raised for non-existent template."""
    with pytest.raises(ValueError) as exc_info:
        ForecastTemplateService.create_scenario_from_template(
            template_name='InvalidTemplate',
            scenario_name='Test',
            overrides=None
        )

    assert 'InvalidTemplate' in str(exc_info.value)
    assert 'Valid templates' in str(exc_info.value)


def test_template_to_scenario_partial_overrides():
    """Verify partial overrides keep template defaults for non-overridden params."""
    scenario = ForecastTemplateService.create_scenario_from_template(
        template_name='Optimistic',
        scenario_name='Custom Optimistic',
        overrides={'monthly_rate': 0.12}  # Override only monthly_rate
    )

    # Verify override applied
    assert scenario.parameters['monthly_rate'] == 0.12

    # Verify other parameters kept template defaults
    assert scenario.parameters['cogs_trend'] == 0.05  # From Optimistic template
    assert scenario.parameters['opex_trend'] == 0.04  # From Optimistic template
    assert scenario.parameters['collection_period_days'] == 30  # From Optimistic template


def test_save_scenarios_creates_file():
    """Verify save_scenarios() creates scenarios.json with correct data."""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, 'config')
        os.makedirs(config_dir)

        # Create scenarios collection
        scenarios = [
            ForecastScenarioModel(
                parameters={'monthly_rate': 0.02},
                scenario_name='Conservative'
            ),
            ForecastScenarioModel(
                parameters={'monthly_rate': 0.05},
                scenario_name='Expected'
            )
        ]
        collection = ForecastScenariosCollection(scenarios=scenarios)

        # Save scenarios
        save_scenarios(collection, config_dir)

        # Verify file created
        scenarios_file = os.path.join(config_dir, 'scenarios.json')
        assert os.path.exists(scenarios_file)

        # Verify content
        with open(scenarios_file, 'r') as f:
            data = json.load(f)

        assert 'parameters' in data
        assert 'scenarios' in data['parameters']
        assert len(data['parameters']['scenarios']) == 2


def test_load_scenarios_reads_file():
    """Verify load_scenarios() reconstructs collection from scenarios.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, 'config')
        os.makedirs(config_dir)

        # Create and save scenarios
        scenarios = [
            ForecastScenarioModel(
                parameters={'monthly_rate': 0.02},
                scenario_name='Conservative'
            )
        ]
        collection = ForecastScenariosCollection(scenarios=scenarios)
        save_scenarios(collection, config_dir)

        # Load scenarios
        loaded_collection = load_scenarios(config_dir)

        # Verify reconstruction
        assert isinstance(loaded_collection, ForecastScenariosCollection)
        loaded_scenarios = loaded_collection.list_scenarios()
        assert len(loaded_scenarios) == 1
        assert loaded_scenarios[0].scenario_name == 'Conservative'
        assert loaded_scenarios[0].parameters['monthly_rate'] == 0.02


def test_load_scenarios_missing_file():
    """Verify load_scenarios() returns empty collection when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, 'config')
        os.makedirs(config_dir)

        # Load from non-existent file
        loaded_collection = load_scenarios(config_dir)

        # Verify empty collection returned
        assert isinstance(loaded_collection, ForecastScenariosCollection)
        assert len(loaded_collection.list_scenarios()) == 0


def test_load_scenarios_corrupted_file():
    """Verify load_scenarios() raises clear error for corrupted JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = os.path.join(tmpdir, 'config')
        os.makedirs(config_dir)

        # Write corrupted JSON
        scenarios_file = os.path.join(config_dir, 'scenarios.json')
        with open(scenarios_file, 'w') as f:
            f.write("{ invalid json }")

        # Verify exception raised
        with pytest.raises(Exception):  # JSONDecodeError or similar
            load_scenarios(config_dir)
