"""
Unit tests for ConfigManager class.

Tests save/load operations, error handling, and path validation security.
"""
import json
import pytest
from pathlib import Path

from src.persistence.config_manager import ConfigManager
from src.models.parameters import ParameterModel


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project root with config directory."""
    project_root = tmp_path / 'test_project'
    project_root.mkdir()
    return str(project_root)


@pytest.fixture
def config_manager(temp_project_root):
    """Create ConfigManager instance with temporary project root."""
    return ConfigManager(temp_project_root)


@pytest.fixture
def sample_model():
    """Create sample ParameterModel for testing."""
    return ParameterModel(parameters={
        'revenue_growth_rate': 0.05,
        'expense_adjustment_factor': 1.1
    })


class TestConfigManager:
    """Test suite for ConfigManager class."""

    def test_initialization_creates_config_dir_reference(self, temp_project_root):
        """
        Given: Project root path
        When: ConfigManager instantiated
        Then: Config directory path is set correctly
        """
        manager = ConfigManager(temp_project_root)

        assert manager.config_dir == Path(temp_project_root) / 'config'
        assert manager.config_dir.is_absolute()

    def test_save_config_writes_json(self, config_manager, sample_model, temp_project_root):
        """
        Given: ParameterModel with data
        When: save_config called
        Then: JSON file created with correct content
        """
        filepath = 'test_params.json'
        config_manager.save_config(sample_model, filepath)

        # Verify file exists
        config_path = Path(temp_project_root) / 'config' / filepath
        assert config_path.exists()

        # Verify content
        with open(config_path, 'r') as f:
            data = json.load(f)

        assert 'parameters' in data
        assert data['parameters']['revenue_growth_rate'] == 0.05

    def test_load_config_reconstructs_model(self, config_manager, sample_model, temp_project_root):
        """
        Given: JSON file with parameter data
        When: load_config called
        Then: Returns ParameterModel with correct data
        """
        filepath = 'test_params.json'

        # Save first
        config_manager.save_config(sample_model, filepath)

        # Load and verify
        loaded_model = config_manager.load_config(filepath)

        assert isinstance(loaded_model, ParameterModel)
        assert loaded_model.get_parameter('revenue_growth_rate') == 0.05
        assert loaded_model.get_parameter('expense_adjustment_factor') == 1.1

    def test_round_trip_preserves_data(self, config_manager, sample_model):
        """
        Given: ParameterModel instance
        When: save_config then load_config called
        Then: Data is preserved exactly
        """
        filepath = 'round_trip.json'

        # Save
        config_manager.save_config(sample_model, filepath)

        # Load
        loaded_model = config_manager.load_config(filepath)

        # Verify
        assert loaded_model.parameters == sample_model.parameters

    def test_load_missing_file_returns_default(self, config_manager):
        """
        Given: JSON file does not exist
        When: load_config called
        Then: Returns ParameterModel with empty parameters
        """
        loaded_model = config_manager.load_config('non_existent.json')

        assert isinstance(loaded_model, ParameterModel)
        assert loaded_model.parameters == {}

    def test_save_creates_parent_directories(self, config_manager, sample_model, temp_project_root):
        """
        Given: Filepath with non-existent parent directories
        When: save_config called
        Then: Parent directories created and file saved
        """
        filepath = 'subdir/nested/params.json'
        config_manager.save_config(sample_model, filepath)

        # Verify file exists
        config_path = Path(temp_project_root) / 'config' / filepath
        assert config_path.exists()
        assert config_path.parent.exists()

    def test_path_validation_rejects_parent_directory_traversal(self, config_manager, sample_model):
        """
        Given: Filepath with '..' parent directory reference
        When: save_config or load_config called
        Then: Raises ValueError about invalid path
        """
        malicious_path = '../../../etc/passwd'

        with pytest.raises(ValueError) as exc_info:
            config_manager.save_config(sample_model, malicious_path)

        assert 'invalid path' in str(exc_info.value).lower()
        assert 'config directory' in str(exc_info.value).lower()

    def test_path_validation_rejects_absolute_path_outside_config(self, config_manager, sample_model):
        """
        Given: Absolute filepath outside config directory
        When: save_config or load_config called
        Then: Raises ValueError about invalid path
        """
        malicious_path = '/etc/passwd'

        with pytest.raises(ValueError) as exc_info:
            config_manager.save_config(sample_model, malicious_path)

        assert 'invalid path' in str(exc_info.value).lower()

    def test_path_validation_on_load_prevents_traversal(self, config_manager):
        """
        Given: Load attempt with directory traversal path
        When: load_config called
        Then: Raises ValueError before attempting file read
        """
        malicious_path = '../../sensitive_file.json'

        with pytest.raises(ValueError) as exc_info:
            config_manager.load_config(malicious_path)

        assert 'invalid path' in str(exc_info.value).lower()

    def test_invalid_json_raises_decode_error(self, config_manager, temp_project_root):
        """
        Given: JSON file with invalid syntax
        When: load_config called
        Then: Raises JSONDecodeError with line/column information
        """
        # Create invalid JSON file
        config_path = Path(temp_project_root) / 'config'
        config_path.mkdir(exist_ok=True)
        invalid_file = config_path / 'invalid.json'

        with open(invalid_file, 'w') as f:
            f.write('{invalid json syntax')

        # Attempt to load
        with pytest.raises(json.JSONDecodeError) as exc_info:
            config_manager.load_config('invalid.json')

        # Verify error message includes line/column info
        error_msg = str(exc_info.value)
        assert 'line' in error_msg.lower() or 'lineno' in error_msg.lower()

    def test_save_with_relative_path(self, config_manager, sample_model, temp_project_root):
        """
        Given: Relative filepath within config directory
        When: save_config called
        Then: File saved correctly in config directory
        """
        filepath = 'params.json'
        config_manager.save_config(sample_model, filepath)

        config_path = Path(temp_project_root) / 'config' / filepath
        assert config_path.exists()

    def test_json_formatting_is_human_readable(self, config_manager, sample_model, temp_project_root):
        """
        Given: ParameterModel
        When: save_config called
        Then: JSON file formatted with indentation (human-readable)
        """
        filepath = 'formatted.json'
        config_manager.save_config(sample_model, filepath)

        config_path = Path(temp_project_root) / 'config' / filepath

        # Read raw file content
        with open(config_path, 'r') as f:
            content = f.read()

        # Verify indentation exists (multiple spaces or tabs)
        assert '  ' in content or '\t' in content
        # Verify newlines exist (not minified)
        assert '\n' in content

    def test_empty_parameters_model_saves_and_loads(self, config_manager):
        """
        Given: ParameterModel with empty parameters
        When: save then load
        Then: Empty parameters preserved
        """
        empty_model = ParameterModel(parameters={})
        filepath = 'empty.json'

        config_manager.save_config(empty_model, filepath)
        loaded = config_manager.load_config(filepath)

        assert loaded.parameters == {}

    def test_parameters_with_various_types(self, config_manager, temp_project_root):
        """
        Given: ParameterModel with various Python types
        When: save then load
        Then: Types preserved correctly
        """
        model = ParameterModel(parameters={
            'string_param': 'test',
            'int_param': 42,
            'float_param': 3.14,
            'bool_param': True,
            'list_param': [1, 2, 3],
            'nested_dict': {'key': 'value'}
        })

        filepath = 'types.json'
        config_manager.save_config(model, filepath)
        loaded = config_manager.load_config(filepath)

        assert loaded.get_parameter('string_param') == 'test'
        assert loaded.get_parameter('int_param') == 42
        assert loaded.get_parameter('float_param') == 3.14
        assert loaded.get_parameter('bool_param') is True
        assert loaded.get_parameter('list_param') == [1, 2, 3]
        assert loaded.get_parameter('nested_dict') == {'key': 'value'}
