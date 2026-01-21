"""
Tests for MainMenuForm navigation functionality.

Validates navigation buttons and back button functionality across all forms.
"""
import unittest
from unittest.mock import Mock, MagicMock
import tkinter as tk

from src.gui.forms.main_menu_form import MainMenuForm
from src.gui.forms.sample_params_form import SampleParamsForm
from src.gui.forms.budget_params_form import BudgetParamsForm
from src.gui.forms.scenario_list_form import ScenarioListForm


class TestMainMenuForm(unittest.TestCase):
    """Test suite for MainMenuForm navigation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.mock_parent = Mock()
        self.mock_parent.show_form = Mock()

    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()

    def test_main_menu_form_creation(self):
        """MainMenuForm instantiates correctly with parent parameter."""
        form = MainMenuForm(self.mock_parent)
        self.assertIsInstance(form, tk.Frame)
        self.assertEqual(form.parent, self.mock_parent)

    def test_navigation_buttons_exist(self):
        """All four navigation buttons present with correct labels."""
        form = MainMenuForm(self.mock_parent)

        # Get all children widgets
        button_texts = []
        for child in form.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, tk.Button):
                    button_texts.append(widget.cget('text'))

        # Verify exactly 3 navigation buttons exist (not 4 - no direct Forecast Parameters button)
        self.assertIn("Sample Parameters", button_texts)
        self.assertIn("Budget Parameters", button_texts)
        self.assertIn("Forecast Scenarios", button_texts)
        self.assertNotIn("Forecast Parameters", button_texts)

    def test_sample_params_navigation(self):
        """Sample Parameters button calls parent.show_form(SampleParamsForm)."""
        form = MainMenuForm(self.mock_parent)

        # Call navigation method directly
        form.on_sample_params_clicked()

        # Verify show_form called with correct form class
        self.mock_parent.show_form.assert_called_once()
        call_args = self.mock_parent.show_form.call_args[0]
        self.assertEqual(call_args[0], SampleParamsForm)

    def test_budget_params_navigation(self):
        """Budget Parameters button calls parent.show_form(BudgetParamsForm)."""
        form = MainMenuForm(self.mock_parent)

        # Call navigation method directly
        form.on_budget_params_clicked()

        # Verify show_form called with correct form class
        self.mock_parent.show_form.assert_called_once()
        call_args = self.mock_parent.show_form.call_args[0]
        self.assertEqual(call_args[0], BudgetParamsForm)

    def test_scenario_list_navigation(self):
        """Forecast Scenarios button calls parent.show_form(ScenarioListForm)."""
        form = MainMenuForm(self.mock_parent)

        # Call navigation method directly
        form.on_forecast_scenarios_clicked()

        # Verify show_form called with correct form class
        self.mock_parent.show_form.assert_called_once()
        call_args = self.mock_parent.show_form.call_args[0]
        self.assertEqual(call_args[0], ScenarioListForm)

    def test_no_direct_forecast_params_button(self):
        """No direct Forecast Parameters button exists (two-level nav required)."""
        form = MainMenuForm(self.mock_parent)

        # Get all button texts
        button_texts = []
        for child in form.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, tk.Button):
                    button_texts.append(widget.cget('text'))

        # Verify no "Forecast Parameters" button
        self.assertNotIn("Forecast Parameters", button_texts)

    def test_sample_params_back_button(self):
        """SampleParamsForm Back to Menu button navigates to MainMenuForm."""
        # Create mock config manager
        mock_config_mgr = Mock()
        self.mock_parent.get_config_manager = Mock(return_value=mock_config_mgr)

        # Create SampleParamsForm
        form = SampleParamsForm(self.mock_parent)

        # Call back button method directly
        form.on_back_to_menu_clicked()

        # Verify show_form called with MainMenuForm
        self.mock_parent.show_form.assert_called_once()
        call_args = self.mock_parent.show_form.call_args[0]
        self.assertEqual(call_args[0], MainMenuForm)

    def test_budget_params_back_button(self):
        """BudgetParamsForm Back to Menu button navigates to MainMenuForm."""
        # Create mock config manager
        mock_config_mgr = Mock()
        self.mock_parent.get_config_manager = Mock(return_value=mock_config_mgr)

        # Create BudgetParamsForm
        form = BudgetParamsForm(self.mock_parent)

        # Call back button method directly
        form.on_back_to_menu_clicked()

        # Verify show_form called with MainMenuForm
        self.mock_parent.show_form.assert_called_once()
        call_args = self.mock_parent.show_form.call_args[0]
        self.assertEqual(call_args[0], MainMenuForm)

    def test_scenario_list_back_button(self):
        """ScenarioListForm Back to Menu button navigates to MainMenuForm with width=18."""
        # Create mock config manager
        mock_config_mgr = Mock()
        mock_config_mgr.load_config = Mock(side_effect=FileNotFoundError)
        self.mock_parent.get_config_manager = Mock(return_value=mock_config_mgr)

        # Create ScenarioListForm
        form = ScenarioListForm(self.mock_parent)

        # Find Back to Menu button and verify width
        back_button = None
        for child in form.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, tk.Button) and widget.cget('text') == 'Back to Menu':
                    back_button = widget
                    break

        self.assertIsNotNone(back_button)
        self.assertEqual(back_button.cget('width'), 18)

        # Call back button method directly
        form.on_back_to_menu_clicked()

        # Verify show_form called with MainMenuForm
        self.mock_parent.show_form.assert_called_once()
        call_args = self.mock_parent.show_form.call_args[0]
        self.assertEqual(call_args[0], MainMenuForm)


if __name__ == '__main__':
    unittest.main()
