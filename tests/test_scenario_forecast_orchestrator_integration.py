"""
Integration tests for ScenarioForecastOrchestrator validation flow.

Tests orchestrator invokes validator for all scenarios and handles errors gracefully.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.scenario_forecast_orchestrator import ScenarioForecastOrchestrator
from src.models.forecast_validation import ForecastValidationResult


@pytest.fixture
def mock_global_config():
    """Fixture for mock global configuration."""
    config = Mock()
    config.forecast_horizon = 6
    config.client_id = 'test_client'
    return config


@pytest.fixture
def mock_cash_flow_model():
    """Fixture for mock CashFlowModel."""
    return Mock()


@pytest.fixture
def mock_pl_model():
    """Fixture for mock PLModel."""
    return Mock()


@pytest.fixture
def mock_scenarios_collection():
    """Fixture for mock ForecastScenariosCollection with three scenarios."""
    scenarios_collection = Mock()

    # Create three mock scenarios
    optimistic = Mock()
    optimistic.scenario_name = 'Optimistic'
    optimistic.parameters = {'forecast_horizon': 6, 'monthly_rate': 0.05}

    base = Mock()
    base.scenario_name = 'Base'
    base.parameters = {'forecast_horizon': 6, 'monthly_rate': 0.02}

    pessimistic = Mock()
    pessimistic.scenario_name = 'Pessimistic'
    pessimistic.parameters = {'forecast_horizon': 6, 'monthly_rate': -0.01}

    scenarios_collection.list_scenarios = Mock(return_value=[optimistic, base, pessimistic])

    return scenarios_collection


@pytest.fixture
def mock_forecast_models():
    """Fixture for mock forecast model outputs."""
    def _create_forecasts():
        cf_forecast = Mock()
        cf_forecast.calculated_rows = {
            'ending_cash': {
                'projected': {1: 10000, 2: 9000, 3: 8000},
                'lower_bound': {1: 8000, 2: 7000, 3: 6000},
                'upper_bound': {1: 12000, 2: 11000, 3: 10000}
            }
        }
        cf_forecast.metadata = {'forecast_horizon': 6, 'excluded_periods': 0}

        pl_forecast = Mock()
        pl_forecast.get_income = Mock(return_value={
            'projected': {1: 50000, 2: 52000, 3: 54000},
            'lower_bound': {1: 45000, 2: 47000, 3: 49000},
            'upper_bound': {1: 55000, 2: 57000, 3: 59000}
        })
        pl_forecast.get_expenses = Mock(return_value={
            'projected': {1: 30000, 2: 31000, 3: 32000},
            'lower_bound': {1: 28000, 2: 29000, 3: 30000},
            'upper_bound': {1: 32000, 2: 33000, 3: 34000}
        })
        pl_forecast.calculated_rows = {
            'operating_margin_pct': {
                'projected': {1: 25.0, 2: 24.0, 3: 23.0},
                'lower_bound': {},
                'upper_bound': {}
            },
            'net_income': {
                'projected': {},
                'lower_bound': {},
                'upper_bound': {}
            }
        }
        pl_forecast.metadata = {'forecast_horizon': 6, 'excluded_periods': 0}

        return cf_forecast, pl_forecast

    return _create_forecasts


class TestOrchestratorValidationIntegration:
    """Integration tests for orchestrator validation flow."""

    @patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator')
    @patch('src.services.scenario_forecast_orchestrator.PLForecastCalculator')
    def test_orchestrator_validates_all_scenarios(
        self,
        mock_pl_calculator_class,
        mock_cf_calculator_class,
        mock_cash_flow_model,
        mock_pl_model,
        mock_scenarios_collection,
        mock_global_config,
        mock_forecast_models
    ):
        """
        Given: Orchestrator runs with three scenarios
        When: calculate_multi_scenario_forecasts() called
        Then: All three scenarios have validation_result in output
        """
        # Setup calculator mocks to return forecast models
        cf_forecast, pl_forecast = mock_forecast_models()

        mock_cf_calculator = Mock()
        mock_cf_calculator.calculate = Mock(return_value=cf_forecast)
        mock_cf_calculator_class.return_value = mock_cf_calculator

        mock_pl_calculator = Mock()
        mock_pl_calculator.calculate = Mock(return_value=pl_forecast)
        mock_pl_calculator_class.return_value = mock_pl_calculator

        # Create orchestrator and run
        orchestrator = ScenarioForecastOrchestrator(
            cash_flow_model=mock_cash_flow_model,
            pl_model=mock_pl_model,
            scenarios_collection=mock_scenarios_collection,
            global_config=mock_global_config
        )

        result = orchestrator.calculate_multi_scenario_forecasts()

        # Verify all three scenarios have validation results
        assert 'Optimistic' in result.scenario_forecasts
        assert 'Base' in result.scenario_forecasts
        assert 'Pessimistic' in result.scenario_forecasts

        for scenario_name in ['Optimistic', 'Base', 'Pessimistic']:
            scenario_data = result.scenario_forecasts[scenario_name]
            assert 'validation_result' in scenario_data

            # Validation result should be ForecastValidationResult or None (if error)
            validation_result = scenario_data['validation_result']
            if validation_result is not None:
                assert isinstance(validation_result, ForecastValidationResult)
                assert hasattr(validation_result, 'validation_status')
                assert hasattr(validation_result, 'warnings')
                assert hasattr(validation_result, 'quality_level')

    @patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator')
    @patch('src.services.scenario_forecast_orchestrator.PLForecastCalculator')
    def test_scenario_specific_validation_warnings(
        self,
        mock_pl_calculator_class,
        mock_cf_calculator_class,
        mock_cash_flow_model,
        mock_pl_model,
        mock_scenarios_collection,
        mock_global_config
    ):
        """
        Given: Base scenario forecast with cash runway < threshold
        When: Orchestrator completes
        Then: Base scenario validation_result contains CASH_RUNWAY warning
        """
        # Create scenario-specific forecast models
        # Base scenario has cash runway issue
        base_cf_forecast = Mock()
        base_cf_forecast.calculated_rows = {
            'ending_cash': {
                'projected': {1: 10000, 2: -5000, 3: -8000},  # Negative in month 2
                'lower_bound': {1: 8000, 2: -7000, 3: -10000},
                'upper_bound': {1: 12000, 2: -3000, 3: -6000}
            }
        }
        base_cf_forecast.metadata = {'forecast_horizon': 6, 'excluded_periods': 0}

        base_pl_forecast = Mock()
        base_pl_forecast.get_income = Mock(return_value={
            'projected': {1: 50000, 2: 52000, 3: 54000},
            'lower_bound': {1: 45000, 2: 47000, 3: 49000},
            'upper_bound': {1: 55000, 2: 57000, 3: 59000}
        })
        base_pl_forecast.get_expenses = Mock(return_value={
            'projected': {1: 30000, 2: 31000, 3: 32000},
            'lower_bound': {},
            'upper_bound': {}
        })
        base_pl_forecast.calculated_rows = {
            'operating_margin_pct': {
                'projected': {1: 25.0, 2: 24.0, 3: 23.0},
                'lower_bound': {},
                'upper_bound': {}
            },
            'net_income': {
                'projected': {},
                'lower_bound': {},
                'upper_bound': {}
            }
        }
        base_pl_forecast.metadata = {'forecast_horizon': 6, 'excluded_periods': 0}

        # Other scenarios have positive cash
        other_cf_forecast = Mock()
        other_cf_forecast.calculated_rows = {
            'ending_cash': {
                'projected': {1: 50000, 2: 48000, 3: 46000},
                'lower_bound': {},
                'upper_bound': {}
            }
        }
        other_cf_forecast.metadata = {'forecast_horizon': 6, 'excluded_periods': 0}

        other_pl_forecast = Mock()
        other_pl_forecast.get_income = Mock(return_value={
            'projected': {1: 50000, 2: 52000, 3: 54000},
            'lower_bound': {},
            'upper_bound': {}
        })
        other_pl_forecast.get_expenses = Mock(return_value={
            'projected': {1: 30000, 2: 31000, 3: 32000},
            'lower_bound': {},
            'upper_bound': {}
        })
        other_pl_forecast.calculated_rows = {
            'operating_margin_pct': {
                'projected': {1: 25.0, 2: 24.0, 3: 23.0},
                'lower_bound': {},
                'upper_bound': {}
            },
            'net_income': {
                'projected': {},
                'lower_bound': {},
                'upper_bound': {}
            }
        }
        other_pl_forecast.metadata = {'forecast_horizon': 6, 'excluded_periods': 0}

        # Setup calculators to return different forecasts per scenario
        def cf_calculator_side_effect(*args, **kwargs):
            calc = Mock()
            scenario = kwargs.get('forecast_scenario') or args[1]
            if scenario.scenario_name == 'Base':
                calc.calculate = Mock(return_value=base_cf_forecast)
            else:
                calc.calculate = Mock(return_value=other_cf_forecast)
            return calc

        def pl_calculator_side_effect(*args, **kwargs):
            calc = Mock()
            scenario = kwargs.get('forecast_scenario') or args[1]
            if scenario.scenario_name == 'Base':
                calc.calculate = Mock(return_value=base_pl_forecast)
            else:
                calc.calculate = Mock(return_value=other_pl_forecast)
            return calc

        mock_cf_calculator_class.side_effect = cf_calculator_side_effect
        mock_pl_calculator_class.side_effect = pl_calculator_side_effect

        # Create orchestrator and run
        orchestrator = ScenarioForecastOrchestrator(
            cash_flow_model=mock_cash_flow_model,
            pl_model=mock_pl_model,
            scenarios_collection=mock_scenarios_collection,
            global_config=mock_global_config
        )

        result = orchestrator.calculate_multi_scenario_forecasts()

        # Check Base scenario has cash runway warning
        base_validation = result.scenario_forecasts['Base']['validation_result']
        assert base_validation is not None

        cash_warnings = [w for w in base_validation.warnings if w['type'] == 'CASH_RUNWAY']
        assert len(cash_warnings) >= 1
        assert cash_warnings[0]['runway_months'] == 2

        # Other scenarios should not have cash runway warnings
        for scenario_name in ['Optimistic', 'Pessimistic']:
            scenario_validation = result.scenario_forecasts[scenario_name]['validation_result']
            if scenario_validation is not None:
                cash_warnings = [w for w in scenario_validation.warnings if w['type'] == 'CASH_RUNWAY']
                assert len(cash_warnings) == 0

    @patch('src.services.scenario_forecast_orchestrator.CashFlowForecastCalculator')
    @patch('src.services.scenario_forecast_orchestrator.PLForecastCalculator')
    @patch('src.services.scenario_forecast_orchestrator.ForecastValidator')
    def test_validation_error_handling(
        self,
        mock_validator_class,
        mock_pl_calculator_class,
        mock_cf_calculator_class,
        mock_cash_flow_model,
        mock_pl_model,
        mock_scenarios_collection,
        mock_global_config,
        mock_forecast_models
    ):
        """
        Given: Validator raises ValueError during validation
        When: Orchestrator validation step runs
        Then: Error logged, validation_result=None, orchestrator continues
        """
        # Setup calculator mocks
        cf_forecast, pl_forecast = mock_forecast_models()

        mock_cf_calculator = Mock()
        mock_cf_calculator.calculate = Mock(return_value=cf_forecast)
        mock_cf_calculator_class.return_value = mock_cf_calculator

        mock_pl_calculator = Mock()
        mock_pl_calculator.calculate = Mock(return_value=pl_forecast)
        mock_pl_calculator_class.return_value = mock_pl_calculator

        # Setup validator to raise exception
        mock_validator = Mock()
        mock_validator.validate = Mock(side_effect=ValueError("Validation failed"))
        mock_validator_class.return_value = mock_validator

        # Create orchestrator and run
        orchestrator = ScenarioForecastOrchestrator(
            cash_flow_model=mock_cash_flow_model,
            pl_model=mock_pl_model,
            scenarios_collection=mock_scenarios_collection,
            global_config=mock_global_config
        )

        # Should not raise exception despite validator error
        result = orchestrator.calculate_multi_scenario_forecasts()

        # Verify all scenarios completed
        assert len(result.scenario_forecasts) == 3

        # All validation results should be None due to error
        for scenario_name in ['Optimistic', 'Base', 'Pessimistic']:
            scenario_data = result.scenario_forecasts[scenario_name]
            assert scenario_data['validation_result'] is None
