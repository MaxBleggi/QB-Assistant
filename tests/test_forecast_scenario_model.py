"""
Unit tests for ForecastScenarioModel and ForecastScenariosCollection.

Tests serialization, metadata preservation, collection CRUD operations,
and round-trip data integrity.
"""
import pytest

from src.models.forecast_scenario import ForecastScenarioModel, ForecastScenariosCollection


@pytest.fixture
def sample_parameters():
    """Create sample forecast parameter dictionary for testing."""
    return {
        'revenue_growth_rates': {
            'monthly_rate': 0.05,
            'use_averaged': True
        },
        'expense_trend_adjustments': {
            'cogs_trend': 0.03,
            'opex_trend': 0.02
        },
        'cash_flow_timing_params': {
            'collection_period_days': 45,
            'payment_terms_days': 30
        },
        'major_cash_events': {
            'planned_capex': [],
            'debt_payments': []
        }
    }


@pytest.fixture
def sample_scenario(sample_parameters):
    """Create ForecastScenarioModel instance with sample data."""
    return ForecastScenarioModel(
        parameters=sample_parameters,
        scenario_id='test-scenario-123',
        scenario_name='Test Scenario',
        description='Test description'
    )


class TestForecastScenarioModel:
    """Test suite for ForecastScenarioModel class."""

    def test_initialization_with_full_metadata(self, sample_parameters):
        """
        Given: Parameters and metadata
        When: ForecastScenarioModel instantiated with all fields
        Then: Model stores all metadata and parameters correctly
        """
        model = ForecastScenarioModel(
            parameters=sample_parameters,
            scenario_id='abc123',
            scenario_name='Q1 Forecast',
            description='First quarter forecast',
            created_date='2026-01-20T10:00:00'
        )

        assert model.scenario_id == 'abc123'
        assert model.scenario_name == 'Q1 Forecast'
        assert model.description == 'First quarter forecast'
        assert model.created_date == '2026-01-20T10:00:00'
        assert model.parameters == sample_parameters

    def test_initialization_with_defaults(self):
        """
        Given: No metadata provided
        When: ForecastScenarioModel instantiated
        Then: Model generates default scenario_id and created_date
        """
        model = ForecastScenarioModel()

        assert model.scenario_id is not None
        assert len(model.scenario_id) > 0  # UUID hex string
        assert model.scenario_name == ""
        assert model.description == ""
        assert model.created_date is not None
        assert model.parameters == {}

    def test_to_dict_includes_all_metadata_fields(self, sample_scenario):
        """
        Given: ForecastScenarioModel with metadata and parameters
        When: to_dict called
        Then: Returns dict with all metadata fields and parameters
        """
        result = sample_scenario.to_dict()

        assert 'scenario_id' in result
        assert 'scenario_name' in result
        assert 'description' in result
        assert 'created_date' in result
        assert 'parameters' in result

        assert result['scenario_id'] == 'test-scenario-123'
        assert result['scenario_name'] == 'Test Scenario'
        assert result['description'] == 'Test description'
        assert isinstance(result['parameters'], dict)

    def test_to_dict_includes_parameters_dict(self, sample_scenario):
        """
        Given: ForecastScenarioModel with parameters
        When: to_dict called
        Then: Returns dict with 'parameters' key containing parameter data
        """
        result = sample_scenario.to_dict()

        assert 'parameters' in result
        assert 'revenue_growth_rates' in result['parameters']
        assert result['parameters']['revenue_growth_rates']['monthly_rate'] == 0.05

    def test_from_dict_reconstructs_metadata_correctly(self, sample_parameters):
        """
        Given: Dictionary with metadata and parameters keys
        When: ForecastScenarioModel.from_dict called
        Then: Reconstructs model with all metadata intact
        """
        data = {
            'scenario_id': 'xyz789',
            'scenario_name': 'Q2 Forecast',
            'description': 'Second quarter',
            'created_date': '2026-02-01T12:00:00',
            'parameters': sample_parameters
        }

        model = ForecastScenarioModel.from_dict(data)

        assert model.scenario_id == 'xyz789'
        assert model.scenario_name == 'Q2 Forecast'
        assert model.description == 'Second quarter'
        assert model.created_date == '2026-02-01T12:00:00'

    def test_from_dict_reconstructs_parameters_correctly(self, sample_parameters):
        """
        Given: Dictionary with parameters key
        When: ForecastScenarioModel.from_dict called
        Then: Reconstructs model with all parameters intact
        """
        data = {
            'scenario_id': 'test123',
            'parameters': sample_parameters
        }

        model = ForecastScenarioModel.from_dict(data)

        assert model.parameters == sample_parameters
        assert model.get_parameter('revenue_growth_rates')['monthly_rate'] == 0.05

    def test_round_trip_preserves_all_data(self, sample_scenario):
        """
        Given: ForecastScenarioModel with metadata and parameters
        When: to_dict then from_dict called
        Then: Reconstructed model equals original (all fields match)
        """
        # Serialize to dict
        data = sample_scenario.to_dict()

        # Reconstruct from dict
        reconstructed = ForecastScenarioModel.from_dict(data)

        # Verify metadata matches
        assert reconstructed.scenario_id == sample_scenario.scenario_id
        assert reconstructed.scenario_name == sample_scenario.scenario_name
        assert reconstructed.description == sample_scenario.description
        assert reconstructed.created_date == sample_scenario.created_date

        # Verify parameters match
        assert reconstructed.parameters == sample_scenario.parameters

    def test_parameter_access_via_get_set(self, sample_scenario):
        """
        Given: ForecastScenarioModel instance
        When: get_parameter and set_parameter called
        Then: Inherited ParameterModel methods work correctly
        """
        # Get existing parameter
        revenue_params = sample_scenario.get_parameter('revenue_growth_rates')
        assert revenue_params['monthly_rate'] == 0.05

        # Set new parameter
        sample_scenario.set_parameter('new_param', 'test_value')
        assert sample_scenario.get_parameter('new_param') == 'test_value'


class TestForecastScenariosCollection:
    """Test suite for ForecastScenariosCollection class."""

    def test_initialization_with_scenarios(self, sample_scenario):
        """
        Given: List of scenarios
        When: ForecastScenariosCollection instantiated with scenarios
        Then: Collection contains all scenarios
        """
        scenario2 = ForecastScenarioModel(
            parameters={},
            scenario_id='scenario-2',
            scenario_name='Scenario 2'
        )

        collection = ForecastScenariosCollection(scenarios=[sample_scenario, scenario2])

        assert len(collection.list_scenarios()) == 2

    def test_initialization_empty(self):
        """
        Given: No scenarios provided
        When: ForecastScenariosCollection instantiated
        Then: Collection is empty
        """
        collection = ForecastScenariosCollection()

        assert len(collection.list_scenarios()) == 0

    def test_add_scenario_adds_to_internal_list(self, sample_scenario):
        """
        Given: ForecastScenariosCollection
        When: add_scenario called
        Then: Scenario added to internal list
        """
        collection = ForecastScenariosCollection()
        assert len(collection.list_scenarios()) == 0

        collection.add_scenario(sample_scenario)

        assert len(collection.list_scenarios()) == 1
        assert collection.list_scenarios()[0].scenario_id == 'test-scenario-123'

    def test_remove_scenario_removes_correct_scenario_by_id(self):
        """
        Given: ForecastScenariosCollection with 3 scenarios
        When: remove_scenario called with middle scenario id
        Then: Collection contains 2 scenarios, removed one not in list
        """
        scenario1 = ForecastScenarioModel(scenario_id='s1', scenario_name='Scenario 1')
        scenario2 = ForecastScenarioModel(scenario_id='s2', scenario_name='Scenario 2')
        scenario3 = ForecastScenarioModel(scenario_id='s3', scenario_name='Scenario 3')

        collection = ForecastScenariosCollection(scenarios=[scenario1, scenario2, scenario3])

        # Remove middle scenario
        collection.remove_scenario('s2')

        scenarios = collection.list_scenarios()
        assert len(scenarios) == 2
        assert scenarios[0].scenario_id == 's1'
        assert scenarios[1].scenario_id == 's3'

    def test_remove_scenario_raises_on_non_existent_id(self):
        """
        Given: ForecastScenariosCollection
        When: remove_scenario called with non-existent id
        Then: Raises KeyError
        """
        collection = ForecastScenariosCollection()

        with pytest.raises(KeyError) as exc_info:
            collection.remove_scenario('non-existent-id')

        assert 'non-existent-id' in str(exc_info.value)

    def test_get_scenario_returns_correct_scenario_by_id(self, sample_scenario):
        """
        Given: ForecastScenariosCollection with scenario_id='test-scenario-123'
        When: get_scenario('test-scenario-123') called
        Then: Returns ForecastScenarioModel instance with that scenario_id
        """
        collection = ForecastScenariosCollection(scenarios=[sample_scenario])

        retrieved = collection.get_scenario('test-scenario-123')

        assert retrieved.scenario_id == 'test-scenario-123'
        assert retrieved.scenario_name == 'Test Scenario'

    def test_get_scenario_raises_keyerror_for_non_existent_id(self):
        """
        Given: ForecastScenariosCollection
        When: get_scenario called with non-existent id
        Then: Raises KeyError with message indicating scenario not found
        """
        collection = ForecastScenariosCollection()

        with pytest.raises(KeyError) as exc_info:
            collection.get_scenario('xyz')

        assert 'xyz' in str(exc_info.value)

    def test_list_scenarios_returns_all_scenario_objects(self):
        """
        Given: ForecastScenariosCollection with scenarios
        When: list_scenarios called
        Then: Returns list of all ForecastScenarioModel instances
        """
        scenario1 = ForecastScenarioModel(scenario_id='s1', scenario_name='Scenario 1')
        scenario2 = ForecastScenarioModel(scenario_id='s2', scenario_name='Scenario 2')

        collection = ForecastScenariosCollection(scenarios=[scenario1, scenario2])

        scenarios = collection.list_scenarios()

        assert len(scenarios) == 2
        assert all(isinstance(s, ForecastScenarioModel) for s in scenarios)

    def test_to_dict_returns_correct_structure(self, sample_scenario):
        """
        Given: ForecastScenariosCollection with 3 scenarios
        When: to_dict called
        Then: Returns dict with 'parameters' key containing 'scenarios' list of 3 scenario dicts
        """
        scenario2 = ForecastScenarioModel(scenario_id='s2', scenario_name='S2')
        scenario3 = ForecastScenarioModel(scenario_id='s3', scenario_name='S3')

        collection = ForecastScenariosCollection(
            scenarios=[sample_scenario, scenario2, scenario3]
        )

        result = collection.to_dict()

        assert 'parameters' in result
        assert 'scenarios' in result['parameters']
        assert isinstance(result['parameters']['scenarios'], list)
        assert len(result['parameters']['scenarios']) == 3

    def test_from_dict_to_dict_round_trip_preserves_all_scenarios(self, sample_scenario):
        """
        Given: ForecastScenariosCollection serialized to dict and deserialized
        When: from_dict called
        Then: All scenarios reconstructed with correct metadata and parameters
        """
        scenario2 = ForecastScenarioModel(
            scenario_id='s2',
            scenario_name='Scenario 2',
            parameters={'test_param': 'test_value'}
        )

        collection = ForecastScenariosCollection(scenarios=[sample_scenario, scenario2])

        # Serialize
        data = collection.to_dict()

        # Deserialize
        reconstructed = ForecastScenariosCollection.from_dict(data)

        # Verify scenario count
        assert len(reconstructed.list_scenarios()) == 2

        # Verify first scenario
        s1 = reconstructed.get_scenario('test-scenario-123')
        assert s1.scenario_name == 'Test Scenario'
        assert s1.parameters == sample_scenario.parameters

        # Verify second scenario
        s2 = reconstructed.get_scenario('s2')
        assert s2.scenario_name == 'Scenario 2'
        assert s2.get_parameter('test_param') == 'test_value'
