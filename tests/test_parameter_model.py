"""
Unit tests for ParameterModel class.

Tests serialization, parameter access, and error handling.
"""
import pytest

from src.models.parameters import ParameterModel


@pytest.fixture
def sample_parameters():
    """Create sample parameter dictionary for testing."""
    return {
        'revenue_growth_rate': 0.05,
        'expense_adjustment_factor': 1.1,
        'discount_rate': 0.15
    }


@pytest.fixture
def sample_parameter_model(sample_parameters):
    """Create ParameterModel instance with sample data."""
    return ParameterModel(parameters=sample_parameters)


class TestParameterModel:
    """Test suite for ParameterModel class."""

    def test_initialization_with_parameters(self, sample_parameters):
        """
        Given: Parameter dictionary
        When: ParameterModel instantiated with parameters
        Then: Model stores parameters correctly
        """
        model = ParameterModel(parameters=sample_parameters)

        assert model.parameters == sample_parameters
        assert len(model.parameters) == 3

    def test_initialization_without_parameters(self):
        """
        Given: No parameters provided
        When: ParameterModel instantiated
        Then: Model initialized with empty dict
        """
        model = ParameterModel()

        assert model.parameters == {}
        assert len(model.parameters) == 0

    def test_get_parameter_returns_value(self, sample_parameter_model):
        """
        Given: ParameterModel with parameters
        When: get_parameter called with existing key
        Then: Returns correct value
        """
        value = sample_parameter_model.get_parameter('revenue_growth_rate')

        assert value == 0.05

    def test_get_parameter_raises_on_missing_key(self, sample_parameter_model):
        """
        Given: ParameterModel with parameters
        When: get_parameter called with non-existent key
        Then: Raises KeyError with descriptive message
        """
        with pytest.raises(KeyError) as exc_info:
            sample_parameter_model.get_parameter('non_existent_key')

        assert 'non_existent_key' in str(exc_info.value)

    def test_set_parameter_stores_value(self, sample_parameter_model):
        """
        Given: ParameterModel instance
        When: set_parameter called with key and value
        Then: Parameter is stored and retrievable
        """
        sample_parameter_model.set_parameter('new_parameter', 100)

        assert sample_parameter_model.get_parameter('new_parameter') == 100
        assert 'new_parameter' in sample_parameter_model.parameters

    def test_set_parameter_overwrites_existing(self, sample_parameter_model):
        """
        Given: ParameterModel with existing parameter
        When: set_parameter called with same key and different value
        Then: Parameter value is updated
        """
        original_value = sample_parameter_model.get_parameter('revenue_growth_rate')
        assert original_value == 0.05

        sample_parameter_model.set_parameter('revenue_growth_rate', 0.10)

        assert sample_parameter_model.get_parameter('revenue_growth_rate') == 0.10

    def test_to_dict_returns_correct_structure(self, sample_parameter_model):
        """
        Given: ParameterModel with parameters
        When: to_dict called
        Then: Returns dict with 'parameters' key
        """
        result = sample_parameter_model.to_dict()

        assert 'parameters' in result
        assert isinstance(result['parameters'], dict)
        assert result['parameters']['revenue_growth_rate'] == 0.05

    def test_from_dict_reconstructs_model(self, sample_parameters):
        """
        Given: Dictionary with 'parameters' key
        When: ParameterModel.from_dict called
        Then: Returns ParameterModel with correct parameters
        """
        data = {'parameters': sample_parameters}
        model = ParameterModel.from_dict(data)

        assert isinstance(model, ParameterModel)
        assert model.parameters == sample_parameters
        assert model.get_parameter('revenue_growth_rate') == 0.05

    def test_round_trip_preserves_data(self, sample_parameter_model):
        """
        Given: ParameterModel instance
        When: to_dict then from_dict called
        Then: Data is preserved exactly
        """
        # Serialize to dict
        data = sample_parameter_model.to_dict()

        # Reconstruct from dict
        reconstructed = ParameterModel.from_dict(data)

        # Verify data matches
        assert reconstructed.parameters == sample_parameter_model.parameters
        assert reconstructed.get_parameter('revenue_growth_rate') == 0.05
        assert reconstructed.get_parameter('expense_adjustment_factor') == 1.1

    def test_from_dict_raises_on_missing_parameters_key(self):
        """
        Given: Dictionary without 'parameters' key
        When: ParameterModel.from_dict called
        Then: Raises ValueError with descriptive message
        """
        invalid_data = {'other_key': 'some_value'}

        with pytest.raises(ValueError) as exc_info:
            ParameterModel.from_dict(invalid_data)

        assert 'parameters' in str(exc_info.value).lower()
        assert 'missing' in str(exc_info.value).lower()

    def test_from_dict_raises_on_non_dict_parameters(self):
        """
        Given: Dictionary with 'parameters' key but non-dict value
        When: ParameterModel.from_dict called
        Then: Raises ValueError about type mismatch
        """
        invalid_data = {'parameters': 'not_a_dict'}

        with pytest.raises(ValueError) as exc_info:
            ParameterModel.from_dict(invalid_data)

        assert 'dict' in str(exc_info.value).lower()

    def test_from_dict_with_list_as_parameters(self):
        """
        Given: Dictionary with 'parameters' as list instead of dict
        When: ParameterModel.from_dict called
        Then: Raises ValueError about type mismatch
        """
        invalid_data = {'parameters': ['item1', 'item2']}

        with pytest.raises(ValueError) as exc_info:
            ParameterModel.from_dict(invalid_data)

        assert 'dict' in str(exc_info.value).lower()
