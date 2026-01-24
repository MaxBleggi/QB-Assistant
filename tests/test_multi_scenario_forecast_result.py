"""
Tests for MultiScenarioForecastResult data model.

Verifies initialization, accessors, serialization, and deserialization functionality.
"""
import pytest
from datetime import datetime

from src.models.multi_scenario_forecast_result import MultiScenarioForecastResult
from src.models.cash_flow_forecast_model import CashFlowForecastModel
from src.models.pl_forecast_model import PLForecastModel
import pandas as pd


@pytest.fixture
def mock_cash_flow_forecast():
    """Create mock CashFlowForecastModel for testing."""
    df = pd.DataFrame()
    hierarchy = {
        'OPERATING ACTIVITIES': {
            'projected': [100, 110, 120],
            'lower_bound': [90, 100, 110],
            'upper_bound': [110, 120, 130]
        }
    }
    calculated_rows = {
        'beginning_cash': {
            'projected': [1000, 1100, 1200],
            'lower_bound': [950, 1050, 1150],
            'upper_bound': [1050, 1150, 1250]
        },
        'ending_cash': {
            'projected': [1100, 1200, 1300],
            'lower_bound': [1050, 1150, 1250],
            'upper_bound': [1150, 1250, 1350]
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
    """Create mock PLForecastModel for testing."""
    hierarchy = {
        'Income': {
            'projected': [500, 550, 600],
            'lower_bound': [475, 525, 575],
            'upper_bound': [525, 575, 625]
        }
    }
    calculated_rows = {
        'gross_profit': {
            'projected': [200, 220, 240],
            'lower_bound': [190, 210, 230],
            'upper_bound': [210, 230, 250]
        }
    }
    metadata = {
        'confidence_level': 0.90,
        'forecast_horizon': 12,
        'excluded_periods': [],
        'warnings': []
    }
    return PLForecastModel(hierarchy, calculated_rows, metadata)


def test_multi_scenario_result_initialization(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify model can be initialized with valid data."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    result = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=12,
        client_id='test_client'
    )

    assert result.forecast_horizon == 12
    assert result.client_id == 'test_client'
    assert 'Conservative' in result.scenario_forecasts
    assert result.created_at is not None


def test_multi_scenario_result_get_scenario(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify get_scenario_forecast() returns correct forecast data."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        },
        'Expected': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    result = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=12
    )

    conservative = result.get_scenario_forecast('Conservative')
    assert conservative is not None
    assert 'cash_flow_forecast' in conservative
    assert 'pl_forecast' in conservative
    assert isinstance(conservative['cash_flow_forecast'], CashFlowForecastModel)
    assert isinstance(conservative['pl_forecast'], PLForecastModel)


def test_multi_scenario_result_missing_scenario(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify get_scenario_forecast() handles missing scenario gracefully."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    result = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=12
    )

    missing = result.get_scenario_forecast('NonExistent')
    assert missing is None


def test_multi_scenario_result_list_scenarios(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify list_scenarios() returns all scenario names."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        },
        'Expected': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        },
        'Optimistic': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    result = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=12
    )

    scenarios = result.list_scenarios()
    assert len(scenarios) == 3
    assert 'Conservative' in scenarios
    assert 'Expected' in scenarios
    assert 'Optimistic' in scenarios


def test_multi_scenario_result_metadata_fields(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify forecast_horizon, created_at, client_id stored correctly."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    test_timestamp = datetime.now().isoformat()
    result = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=6,
        client_id='client_123',
        created_at=test_timestamp
    )

    assert result.forecast_horizon == 6
    assert result.client_id == 'client_123'
    assert result.created_at == test_timestamp


def test_multi_scenario_result_serialization(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify to_dict() produces correct structure with metadata."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    result = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=12,
        client_id='test_client'
    )

    data = result.to_dict()

    assert 'forecast_horizon' in data
    assert 'client_id' in data
    assert 'created_at' in data
    assert 'scenario_forecasts' in data

    assert data['forecast_horizon'] == 12
    assert data['client_id'] == 'test_client'
    assert 'Conservative' in data['scenario_forecasts']

    conservative_data = data['scenario_forecasts']['Conservative']
    assert 'cash_flow_forecast' in conservative_data
    assert 'pl_forecast' in conservative_data


def test_multi_scenario_result_deserialization(mock_cash_flow_forecast, mock_pl_forecast):
    """Verify from_dict() reconstructs model objects correctly."""
    scenario_forecasts = {
        'Conservative': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        },
        'Expected': {
            'cash_flow_forecast': mock_cash_flow_forecast,
            'pl_forecast': mock_pl_forecast
        }
    }

    original = MultiScenarioForecastResult(
        scenario_forecasts=scenario_forecasts,
        forecast_horizon=12,
        client_id='test_client'
    )

    # Serialize then deserialize
    data = original.to_dict()
    reconstructed = MultiScenarioForecastResult.from_dict(data)

    # Verify metadata preserved
    assert reconstructed.forecast_horizon == original.forecast_horizon
    assert reconstructed.client_id == original.client_id
    assert reconstructed.created_at == original.created_at

    # Verify scenarios reconstructed
    assert len(reconstructed.list_scenarios()) == 2
    assert 'Conservative' in reconstructed.list_scenarios()
    assert 'Expected' in reconstructed.list_scenarios()

    # Verify forecast models are correct type
    conservative = reconstructed.get_scenario_forecast('Conservative')
    assert isinstance(conservative['cash_flow_forecast'], CashFlowForecastModel)
    assert isinstance(conservative['pl_forecast'], PLForecastModel)
