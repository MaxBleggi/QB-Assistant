"""
Main application window for QB-Assistant parameter configuration.

Provides window management, form navigation framework, and shared services
(ConfigManager access) for parameter forms.
"""
import tkinter as tk
from typing import Optional, Type

from ..persistence.config_manager import ConfigManager


class App(tk.Tk):
    """
    Main application window with form navigation and lifecycle management.

    Manages window-level configuration (title, size), dynamic form switching,
    and provides shared services to forms (ConfigManager access).
    """

    def __init__(self, project_root: str):
        """
        Initialize application window.

        Args:
            project_root: Absolute path to project root directory
        """
        super().__init__()

        # Window configuration
        self.title("QB-Assistant Parameter Configuration")
        self.geometry("800x600")

        # Initialize services
        self._config_manager = ConfigManager(project_root)

        # Track current form for lifecycle management
        self.current_form: Optional[tk.Frame] = None

    def show_form(self, form_class: Type[tk.Frame]) -> None:
        """
        Switch active form by destroying current and creating new form.

        Args:
            form_class: Form class to instantiate and display (must accept parent as first arg)
        """
        # Destroy current form if exists
        if self.current_form is not None:
            self.current_form.destroy()

        # Create new form instance
        self.current_form = form_class(self)

        # Pack form to fill window
        self.current_form.pack(fill='both', expand=True)

    def get_config_manager(self) -> ConfigManager:
        """
        Get shared ConfigManager instance.

        Returns:
            ConfigManager for parameter persistence
        """
        return self._config_manager

    def quit(self) -> None:
        """
        Cleanup resources and close application.

        Override to add cleanup logic before window destruction.
        """
        # Cleanup current form
        if self.current_form is not None:
            self.current_form.destroy()

        # Call parent quit to close window
        super().quit()
