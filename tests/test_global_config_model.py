"""
Unit tests for GlobalConfigModel and related components.

Tests global configuration model validation, serialization, ConfigManager
integration with model_class parameter, and App singleton accessor.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.models.global_config import GlobalConfigModel
from src.models.parameters import ParameterModel
from src.persistence.config_manager import ConfigManager


class TestGlobalConfigModel(unittest.TestCase):
    """Test GlobalConfigModel class."""

    def test_global_config_default_values(self):
        """
        GlobalConfigModel instantiated with no args has forecast_horizon=6.

        Maps to acceptance criteria: task_1.criteria_1
        """
        model = GlobalConfigModel()
        self.assertEqual(model.forecast_horizon, 6)

    def test_global_config_to_dict(self):
        """
        GlobalConfigModel.to_dict() returns correct structure with forecast_horizon.

        Maps to acceptance criteria: task_1.criteria_2
        """
        model = GlobalConfigModel(forecast_horizon=12)
        result = model.to_dict()

        self.assertIn('parameters', result)
        self.assertIn('forecast_horizon', result['parameters'])
        self.assertEqual(result['parameters']['forecast_horizon'], 12)

    def test_global_config_from_dict(self):
        """
        GlobalConfigModel.from_dict() reconstructs model with forecast_horizon.

        Maps to acceptance criteria: task_1.criteria_3
        """
        data = {'parameters': {'forecast_horizon': 6}}
        model = GlobalConfigModel.from_dict(data)

        self.assertIsInstance(model, GlobalConfigModel)
        self.assertEqual(model.forecast_horizon, 6)

    def test_global_config_validation_invalid_horizon(self):
        """
        Setting forecast_horizon to invalid value (e.g., 18) raises ValueError.

        Maps to acceptance criteria: task_1.criteria_4
        """
        with self.assertRaises(ValueError) as context:
            GlobalConfigModel(forecast_horizon=18)

        self.assertIn("Invalid forecast_horizon value", str(context.exception))
        self.assertIn("Must be 6", str(context.exception))
        self.assertIn("or 12", str(context.exception))

    def test_global_config_validation_invalid_horizon_3(self):
        """Test validation with another invalid value (3)."""
        with self.assertRaises(ValueError) as context:
            GlobalConfigModel(forecast_horizon=3)

        self.assertIn("Invalid forecast_horizon value: 3", str(context.exception))

    def test_global_config_custom_parameters(self):
        """Test that GlobalConfigModel can store additional parameters."""
        model = GlobalConfigModel(
            parameters={'custom_key': 'custom_value'},
            forecast_horizon=12
        )
        self.assertEqual(model.parameters['custom_key'], 'custom_value')
        self.assertEqual(model.forecast_horizon, 12)

    def test_global_config_from_dict_default_horizon(self):
        """Test from_dict uses default horizon=6 if not provided."""
        data = {'parameters': {}}
        model = GlobalConfigModel.from_dict(data)
        self.assertEqual(model.forecast_horizon, 6)


class TestConfigManagerModelClass(unittest.TestCase):
    """Test ConfigManager.load_config with model_class parameter."""

    def setUp(self):
        """Create temporary config directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_config_manager_load_with_model_class(self):
        """
        ConfigManager.load_config with model_class=GlobalConfigModel returns GlobalConfigModel.

        Maps to acceptance criteria: task_2.criteria_2
        """
        # Create config file
        config_path = Path(self.temp_dir) / 'config' / 'test_global.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump({'parameters': {'forecast_horizon': 12}}, f)

        # Load with model_class
        model = self.config_manager.load_config(
            'config/test_global.json',
            model_class=GlobalConfigModel
        )

        self.assertIsInstance(model, GlobalConfigModel)
        self.assertEqual(model.forecast_horizon, 12)

    def test_config_manager_backward_compatibility(self):
        """
        ConfigManager.load_config without model_class returns ParameterModel.

        Maps to acceptance criteria: task_2.criteria_1
        """
        # Create config file
        config_path = Path(self.temp_dir) / 'config' / 'test_params.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump({'parameters': {'key': 'value'}}, f)

        # Load without model_class
        model = self.config_manager.load_config('config/test_params.json')

        self.assertIsInstance(model, ParameterModel)
        self.assertEqual(model.parameters['key'], 'value')

    def test_config_manager_missing_file_with_model_class(self):
        """Test load_config with model_class when file doesn't exist."""
        model = self.config_manager.load_config(
            'config/nonexistent.json',
            model_class=GlobalConfigModel
        )

        self.assertIsInstance(model, GlobalConfigModel)
        self.assertEqual(model.forecast_horizon, 6)  # Default value

    def test_config_manager_invalid_json_with_model_class(self):
        """Test load_config with model_class when JSON is invalid."""
        # Create invalid JSON file
        config_path = Path(self.temp_dir) / 'config' / 'invalid.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            f.write('{invalid json}')

        with self.assertRaises(json.JSONDecodeError):
            self.config_manager.load_config(
                'config/invalid.json',
                model_class=GlobalConfigModel
            )

    def test_config_manager_save_global_config(self):
        """Test save_config works with GlobalConfigModel."""
        model = GlobalConfigModel(forecast_horizon=12)
        self.config_manager.save_config(model, 'config/test_save.json')

        # Verify file was created and contains correct data
        config_path = Path(self.temp_dir) / 'config' / 'test_save.json'
        self.assertTrue(config_path.exists())

        with open(config_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['parameters']['forecast_horizon'], 12)


class TestAppGlobalConfig(unittest.TestCase):
    """Test App.get_global_config() singleton accessor."""

    def setUp(self):
        """Create temporary project directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_app_get_global_config_singleton(self):
        """
        App.get_global_config() returns same instance on multiple calls.

        Maps to acceptance criteria: task_3.criteria_2
        """
        from src.gui.app import App

        # Create app instance (in test mode without running mainloop)
        app = App(self.temp_dir)

        # Get global config twice
        config1 = app.get_global_config()
        config2 = app.get_global_config()

        # Should be same instance (singleton)
        self.assertIs(config1, config2)

        # Clean up
        app.destroy()

    def test_app_get_global_config_creates_default(self):
        """
        App.get_global_config() creates default config if file missing.

        Maps to acceptance criteria: task_3.criteria_3
        """
        from src.gui.app import App

        # Create app instance
        app = App(self.temp_dir)

        # Config file should not exist yet
        config_path = Path(self.temp_dir) / 'config' / 'global_settings.json'
        self.assertFalse(config_path.exists())

        # Get global config (should create default)
        config = app.get_global_config()

        # Verify default values
        self.assertIsInstance(config, GlobalConfigModel)
        self.assertEqual(config.forecast_horizon, 6)

        # Verify file was created
        self.assertTrue(config_path.exists())

        # Clean up
        app.destroy()

    def test_app_get_global_config_loads_existing(self):
        """Test get_global_config loads existing config file."""
        from src.gui.app import App

        # Create config file before app initialization
        config_path = Path(self.temp_dir) / 'config' / 'global_settings.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump({'parameters': {'forecast_horizon': 12}}, f)

        # Create app and load config
        app = App(self.temp_dir)
        config = app.get_global_config()

        # Should load 12-month horizon from file
        self.assertEqual(config.forecast_horizon, 12)

        # Clean up
        app.destroy()


class TestMainMenuFormHorizonSelector(unittest.TestCase):
    """Test MainMenuForm forecast horizon selector integration."""

    def setUp(self):
        """Create temporary project directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_main_menu_form_horizon_default_display(self):
        """
        MainMenuForm displays 6-month selected by default.

        Maps to acceptance criteria: task_4.criteria_1

        Note: GUI test - manual verification recommended.
        """
        from src.gui.app import App
        from src.gui.forms.main_menu_form import MainMenuForm

        # Create app
        app = App(self.temp_dir)

        # Create main menu form
        form = MainMenuForm(app)

        # Verify horizon_var is set to "6" (default)
        self.assertEqual(form.horizon_var.get(), "6")

        # Clean up
        form.destroy()
        app.destroy()

    def test_main_menu_form_horizon_selection_persists(self):
        """
        Changing horizon to 12-month updates config and persists across sessions.

        Maps to acceptance criteria: task_4.criteria_2, task_4.criteria_3

        Note: GUI test - manual verification recommended for full session persistence.
        """
        from src.gui.app import App
        from src.gui.forms.main_menu_form import MainMenuForm

        # Create app
        app = App(self.temp_dir)
        form = MainMenuForm(app)

        # Simulate changing horizon to 12 months
        form.horizon_var.set("12")
        form._on_horizon_changed()

        # Verify global config was updated
        global_config = app.get_global_config()
        self.assertEqual(global_config.forecast_horizon, 12)

        # Verify config file was saved
        config_path = Path(self.temp_dir) / 'config' / 'global_settings.json'
        self.assertTrue(config_path.exists())

        with open(config_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data['parameters']['forecast_horizon'], 12)

        # Clean up first session
        form.destroy()
        app.destroy()

        # Create new app session (simulates restart)
        app2 = App(self.temp_dir)
        form2 = MainMenuForm(app2)

        # Verify horizon is still 12 months (persisted)
        self.assertEqual(form2.horizon_var.get(), "12")

        # Clean up
        form2.destroy()
        app2.destroy()

    def test_main_menu_form_help_text_present(self):
        """Test that help text is present in the form."""
        from src.gui.app import App
        from src.gui.forms.main_menu_form import MainMenuForm

        # Create app and form
        app = App(self.temp_dir)
        form = MainMenuForm(app)

        # Search for widgets containing help text
        help_text_found = False
        for widget in form.winfo_children():
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if isinstance(child, __import__('tkinter').Label):
                        text = child.cget('text')
                        if 'near-term liquidity' in text and 'strategic expansion' in text:
                            help_text_found = True
                            break

        self.assertTrue(help_text_found, "Help text not found in MainMenuForm")

        # Clean up
        form.destroy()
        app.destroy()


if __name__ == '__main__':
    unittest.main()
