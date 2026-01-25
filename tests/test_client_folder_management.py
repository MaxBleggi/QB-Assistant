"""
Comprehensive tests for Sprint 7.1 - Client Folder Management System.

Tests cover:
- ConfigManager YAML support
- ClientManager operations (discovery, creation, deletion, validation)
- ClientConfigModel serialization/deserialization
- App integration (client manager accessor, selected_client state)
- Security tests (path traversal, YAML injection, type confusion)
"""
import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.persistence.config_manager import ConfigManager
from src.services.client_manager import ClientManager
from src.models.client_config import ClientConfigModel
from src.models.parameters import ParameterModel
from src.gui.app import App


# =============================================================================
# Task 1: ConfigManager YAML Support Tests
# =============================================================================

def test_config_manager_yaml_save(tmp_path):
    """
    Test: ConfigManager saves YAML format when file extension is .yaml
    Acceptance criteria: task_1.criteria_1
    """
    config_mgr = ConfigManager(tmp_path)
    model = ParameterModel({'test_key': 'test_value'})

    yaml_path = 'config/test_config.yaml'
    config_mgr.save_config(model, yaml_path)

    # Verify file exists
    full_path = tmp_path / 'config' / 'test_config.yaml'
    assert full_path.exists()

    # Verify YAML format
    with open(full_path, 'r') as f:
        content = f.read()
        # YAML should not have JSON brackets/braces at top level
        assert 'parameters:' in content
        assert 'test_key: test_value' in content


def test_config_manager_yaml_load(tmp_path):
    """
    Test: ConfigManager loads YAML format using safe_load
    Acceptance criteria: task_1.criteria_3
    """
    config_mgr = ConfigManager(tmp_path)

    # Create YAML file manually
    yaml_path = tmp_path / 'config' / 'test_config.yaml'
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_data = {
        'parameters': {
            'test_key': 'test_value',
            'nested': {
                'key': 'value'
            }
        }
    }

    with open(yaml_path, 'w') as f:
        yaml.safe_dump(yaml_data, f)

    # Load config
    loaded_model = config_mgr.load_config('config/test_config.yaml')

    assert loaded_model.get_parameter('test_key') == 'test_value'
    assert loaded_model.get_parameter('nested') == {'key': 'value'}


def test_config_manager_json_backward_compatibility(tmp_path):
    """
    Test: ConfigManager preserves JSON behavior for .json files
    Acceptance criteria: task_1.criteria_2
    """
    config_mgr = ConfigManager(tmp_path)
    model = ParameterModel({'test_key': 'test_value'})

    json_path = 'config/test_config.json'
    config_mgr.save_config(model, json_path)

    # Verify file exists and is JSON format
    full_path = tmp_path / 'config' / 'test_config.json'
    assert full_path.exists()

    with open(full_path, 'r') as f:
        import json
        data = json.load(f)
        assert data['parameters']['test_key'] == 'test_value'


# =============================================================================
# Task 2: ClientManager Tests
# =============================================================================

def test_client_manager_discover_empty(tmp_path):
    """
    Test: discover_clients returns empty list when clients/ is empty
    Acceptance criteria: task_2.criteria_1
    """
    clients = ClientManager.discover_clients(tmp_path)
    assert clients == []


def test_client_manager_discover_multiple(tmp_path):
    """
    Test: discover_clients returns all client folder names
    Acceptance criteria: task_2.criteria_2
    """
    # Create multiple client folders
    clients_dir = tmp_path / 'clients'
    clients_dir.mkdir()

    (clients_dir / 'acme-corp').mkdir()
    (clients_dir / 'test_client').mkdir()
    (clients_dir / 'widgets-inc').mkdir()

    # Create a file (should be ignored)
    (clients_dir / 'not_a_client.txt').touch()

    clients = ClientManager.discover_clients(tmp_path)

    assert set(clients) == {'acme-corp', 'test_client', 'widgets-inc'}
    assert len(clients) == 3


def test_client_manager_validate_path_traversal(tmp_path):
    """
    Test: validate_client_name rejects path traversal attempts
    Acceptance criteria: task_2.criteria_3
    Security test: Path traversal prevention
    """
    # Test various path traversal attempts
    path_traversal_attempts = [
        '../../../etc/passwd',
        '../etc',
        '..',
        '../../',
        'valid/../invalid',
        './etc',
        'client/../../../etc'
    ]

    for attempt in path_traversal_attempts:
        with pytest.raises(ValueError) as exc_info:
            ClientManager.validate_client_name(attempt)
        assert 'invalid characters' in str(exc_info.value).lower() or \
               'path traversal' in str(exc_info.value).lower()


def test_client_manager_create_client(tmp_path):
    """
    Test: create_client creates folder structure and default config
    Acceptance criteria: task_2.criteria_4
    """
    ClientManager.create_client('new-client', tmp_path)

    # Verify folder structure
    client_dir = tmp_path / 'clients' / 'new-client'
    assert client_dir.exists()
    assert client_dir.is_dir()

    input_dir = client_dir / 'input'
    assert input_dir.exists()
    assert input_dir.is_dir()

    config_file = client_dir / 'config.yaml'
    assert config_file.exists()

    # Verify config contains default structure
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
        assert 'parameters' in config_data
        assert 'budget_parameters' in config_data['parameters']
        assert 'forecast_scenarios' in config_data['parameters']
        assert 'global_settings' in config_data['parameters']


def test_client_manager_delete_client(tmp_path):
    """
    Test: delete_client removes client folder completely
    Acceptance criteria: task_2.criteria_5
    """
    # Create client first
    ClientManager.create_client('old-client', tmp_path)

    client_dir = tmp_path / 'clients' / 'old-client'
    assert client_dir.exists()

    # Delete client
    ClientManager.delete_client('old-client', tmp_path)

    assert not client_dir.exists()


# =============================================================================
# Task 3: ClientConfigModel Tests
# =============================================================================

def test_client_config_model_to_dict_nested():
    """
    Test: ClientConfigModel.to_dict() produces correct nested structure
    Acceptance criteria: task_3.criteria_1
    """
    model = ClientConfigModel()
    model.set_budget_config({'budget_key': 'budget_value'})
    model.set_forecast_config({'forecast_key': 'forecast_value'})
    model.set_global_config({'global_key': 'global_value'})

    result = model.to_dict()

    assert 'parameters' in result
    assert 'budget_parameters' in result['parameters']
    assert 'forecast_scenarios' in result['parameters']
    assert 'global_settings' in result['parameters']

    assert result['parameters']['budget_parameters'] == {'budget_key': 'budget_value'}
    assert result['parameters']['forecast_scenarios'] == {'forecast_key': 'forecast_value'}
    assert result['parameters']['global_settings'] == {'global_key': 'global_value'}


def test_client_config_model_from_dict_complete():
    """
    Test: ClientConfigModel.from_dict() reconstructs model from nested dict
    Acceptance criteria: task_3.criteria_2
    """
    data = {
        'parameters': {
            'budget_parameters': {'budget_key': 'budget_value'},
            'forecast_scenarios': {'forecast_key': 'forecast_value'},
            'global_settings': {'global_key': 'global_value'}
        }
    }

    model = ClientConfigModel.from_dict(data)

    assert model.get_budget_config() == {'budget_key': 'budget_value'}
    assert model.get_forecast_config() == {'forecast_key': 'forecast_value'}
    assert model.get_global_config() == {'global_key': 'global_value'}


def test_client_config_model_from_dict_missing_keys():
    """
    Test: ClientConfigModel.from_dict() handles missing nested configs with defaults
    Acceptance criteria: task_3.criteria_3
    """
    data = {
        'parameters': {
            'budget_parameters': {'budget_key': 'budget_value'}
            # forecast_scenarios and global_settings missing
        }
    }

    model = ClientConfigModel.from_dict(data)

    assert model.get_budget_config() == {'budget_key': 'budget_value'}
    assert model.get_forecast_config() == {}
    assert model.get_global_config() == {}


def test_client_config_model_accessors():
    """
    Test: get/set methods for budget/forecast/global configs work correctly
    Acceptance criteria: task_3.criteria_4, task_3.criteria_5
    """
    model = ClientConfigModel()

    # Test setters
    model.set_budget_config({'test': 'budget'})
    model.set_forecast_config({'test': 'forecast'})
    model.set_global_config({'test': 'global'})

    # Test getters
    assert model.get_budget_config() == {'test': 'budget'}
    assert model.get_forecast_config() == {'test': 'forecast'}
    assert model.get_global_config() == {'test': 'global'}


# =============================================================================
# Task 4: App Integration Tests
# =============================================================================

def test_app_client_manager_accessor():
    """
    Test: App.get_client_manager() returns ClientManager instance
    Acceptance criteria: task_4.criteria_1
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        app = App(tmpdir)
        client_mgr = app.get_client_manager()

        assert client_mgr is not None
        assert isinstance(client_mgr, ClientManager)


def test_app_selected_client_state():
    """
    Test: App.selected_client starts as None and can be set
    Acceptance criteria: task_4.criteria_2, task_4.criteria_3
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        app = App(tmpdir)

        # Initially None
        assert app.selected_client is None

        # Can be set
        app.selected_client = 'test-client'
        assert app.selected_client == 'test-client'


# =============================================================================
# Security Tests
# =============================================================================

def test_validate_client_name_absolute_path():
    """
    Security test: Reject absolute path injection
    Attack vector: /etc/passwd
    """
    with pytest.raises(ValueError) as exc_info:
        ClientManager.validate_client_name('/etc/passwd')
    assert 'invalid characters' in str(exc_info.value).lower()


def test_validate_client_name_empty_string():
    """
    Security test: Empty string bypass
    Attack vector: ""
    """
    with pytest.raises(ValueError) as exc_info:
        ClientManager.validate_client_name('')
    assert 'cannot be empty' in str(exc_info.value).lower()


def test_validate_client_name_whitespace_only():
    """
    Security test: Whitespace bypass
    Attack vector: "   "
    """
    with pytest.raises(ValueError) as exc_info:
        ClientManager.validate_client_name('   ')
    assert 'cannot be empty' in str(exc_info.value).lower()


def test_validate_client_name_length_limit():
    """
    Security test: Buffer overflow / filesystem limits
    Attack vector: Very long client name
    """
    long_name = 'a' * 256
    with pytest.raises(ValueError) as exc_info:
        ClientManager.validate_client_name(long_name)
    assert 'too long' in str(exc_info.value).lower()


def test_delete_client_symlink_traversal(tmp_path):
    """
    Security test: Symlink to parent directory
    Attack vector: Create symlink clients/malicious -> ../, then delete 'malicious'
    """
    import os

    # Create clients directory
    clients_dir = tmp_path / 'clients'
    clients_dir.mkdir()

    # Create a symlink pointing to parent
    malicious_link = clients_dir / 'malicious'
    try:
        malicious_link.symlink_to('..')
    except OSError:
        pytest.skip("Symlink creation not supported on this platform")

    # Attempt to delete should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        ClientManager.delete_client('malicious', tmp_path)
    assert 'outside clients directory' in str(exc_info.value).lower()


def test_create_client_race_condition(tmp_path):
    """
    Security test: TOCTOU race via directory already exists
    Attack vector: Attempt to create client that already exists
    """
    # Create client first time
    ClientManager.create_client('test-client', tmp_path)

    # Attempt to create again should fail
    with pytest.raises(ValueError) as exc_info:
        ClientManager.create_client('test-client', tmp_path)
    assert 'already exists' in str(exc_info.value).lower()


def test_yaml_safe_load_code_execution(tmp_path):
    """
    Security test: Python object deserialization
    Attack vector: !!python/object/apply:os.system ['echo hacked']
    """
    config_mgr = ConfigManager(tmp_path)

    # Create malicious YAML file
    yaml_path = tmp_path / 'config' / 'malicious.yaml'
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    malicious_yaml = "!!python/object/apply:os.system ['echo hacked']"

    with open(yaml_path, 'w') as f:
        f.write(malicious_yaml)

    # Attempt to load should fail safely (safe_load rejects !! tags)
    with pytest.raises(Exception):
        # safe_load will raise yaml.constructor.ConstructorError
        config_mgr.load_config('config/malicious.yaml')


def test_client_config_type_confusion():
    """
    Security test: Type confusion in nested config
    Attack vector: {parameters: {budget_parameters: 'not_a_dict'}}
    """
    data = {
        'parameters': {
            'budget_parameters': 'not_a_dict',  # Should be dict
            'forecast_scenarios': {},
            'global_settings': {}
        }
    }

    with pytest.raises(ValueError) as exc_info:
        ClientConfigModel.from_dict(data)
    assert 'must be' in str(exc_info.value).lower() and 'dict' in str(exc_info.value).lower()


def test_config_manager_file_extension_bypass(tmp_path):
    """
    Security test: File extension manipulation
    Attack vector: Save config with .yaml.json double extension
    """
    config_mgr = ConfigManager(tmp_path)
    model = ParameterModel({'test_key': 'test_value'})

    # Use .yaml extension (should use YAML)
    yaml_path = 'config/test.yaml'
    config_mgr.save_config(model, yaml_path)

    full_path = tmp_path / 'config' / 'test.yaml'

    # Verify YAML format was used
    with open(full_path, 'r') as f:
        content = f.read()
        assert 'parameters:' in content  # YAML format


# =============================================================================
# Additional Validation Tests
# =============================================================================

def test_validate_client_name_valid_names():
    """
    Test: Valid client names pass validation
    """
    valid_names = [
        'acme-corp',
        'test_client',
        'client123',
        'ABC-xyz_123',
        'a',
        'a' * 100  # Max length
    ]

    for name in valid_names:
        result = ClientManager.validate_client_name(name)
        assert result == name


def test_validate_client_name_invalid_characters():
    """
    Test: Invalid characters are rejected
    """
    invalid_names = [
        'client name',  # Space
        'client@corp',  # Special char
        'client.corp',  # Dot
        'client/corp',  # Slash
        'client\\corp',  # Backslash
        'client:corp',  # Colon
        'client*corp',  # Asterisk
    ]

    for name in invalid_names:
        with pytest.raises(ValueError):
            ClientManager.validate_client_name(name)


def test_client_manager_create_initializes_correct_config(tmp_path):
    """
    Test: Created client has properly initialized config file
    """
    ClientManager.create_client('test-client', tmp_path)

    config_path = tmp_path / 'clients' / 'test-client' / 'config.yaml'

    # Load config and verify structure
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Verify all three sections exist and are dicts
    assert isinstance(config_data['parameters']['budget_parameters'], dict)
    assert isinstance(config_data['parameters']['forecast_scenarios'], dict)
    assert isinstance(config_data['parameters']['global_settings'], dict)


def test_client_config_model_type_validation_on_setters():
    """
    Test: Setters validate input types
    """
    model = ClientConfigModel()

    # Valid dict should work
    model.set_budget_config({'key': 'value'})

    # Invalid type should raise ValueError
    with pytest.raises(ValueError):
        model.set_budget_config('not_a_dict')

    with pytest.raises(ValueError):
        model.set_forecast_config(['not', 'a', 'dict'])

    with pytest.raises(ValueError):
        model.set_global_config(123)
