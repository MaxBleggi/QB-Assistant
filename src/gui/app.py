"""
Main application window for QB-Assistant parameter configuration.

Provides window management, form navigation framework, and shared services
(ConfigManager access) for parameter forms.
"""
import tkinter as tk
from typing import Optional, Type
from pathlib import Path

from ..persistence.config_manager import ConfigManager
from ..services.client_manager import ClientManager


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

        # Store project root as Path object
        self.project_root = Path(project_root).resolve()

        # Window configuration
        self.title("QB-Assistant Parameter Configuration")
        self.geometry("800x600")

        # Initialize services
        self._config_manager = ConfigManager(project_root)
        self._client_manager = ClientManager()

        # Track current form for lifecycle management
        self.current_form: Optional[tk.Frame] = None

        # Cache for global configuration (lazy loaded)
        self._global_config = None

        # Track selected client (None until user selects)
        self.selected_client: Optional[str] = None

        # Track selected input files for processing pipeline (None until user selects)
        self.selected_balance_sheet: Optional[str] = None
        self.selected_profit_loss: Optional[str] = None
        self.selected_cash_flow: Optional[str] = None
        self.selected_historical_data: Optional[str] = None

    def show_form(self, form_class: Type[tk.Frame], **kwargs) -> None:
        """
        Switch active form by destroying current and creating new form.

        Args:
            form_class: Form class to instantiate and display (must accept parent as first arg)
            **kwargs: Additional keyword arguments to pass to form constructor
        """
        # Destroy current form if exists
        if self.current_form is not None:
            self.current_form.destroy()

        # Create new form instance with optional kwargs
        self.current_form = form_class(self, **kwargs)

        # Pack form to fill window
        self.current_form.pack(fill='both', expand=True)

    def get_config_manager(self) -> ConfigManager:
        """
        Get shared ConfigManager instance.

        Returns:
            ConfigManager for parameter persistence
        """
        return self._config_manager

    def get_client_manager(self) -> ClientManager:
        """
        Get shared ClientManager instance.

        Returns:
            ClientManager for client folder operations
        """
        return self._client_manager

    def get_global_config(self):
        """
        Get global configuration singleton.

        Loads GlobalConfigModel from config/global_settings.json on first call,
        returns cached instance on subsequent calls. Creates default config
        with 6-month forecast horizon if file does not exist.

        Returns:
            GlobalConfigModel instance with global application settings
        """
        # Return cached instance if available
        if self._global_config is not None:
            return self._global_config

        # Import here to avoid circular dependency
        from ..models.global_config import GlobalConfigModel

        # Load global config from file
        config_path = 'config/global_settings.json'
        try:
            self._global_config = self._config_manager.load_config(
                config_path,
                model_class=GlobalConfigModel
            )
        except Exception:
            # File doesn't exist or is invalid - create default config
            self._global_config = GlobalConfigModel(forecast_horizon=6)
            # Save default config to file
            self._config_manager.save_config(self._global_config, config_path)

        return self._global_config

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
