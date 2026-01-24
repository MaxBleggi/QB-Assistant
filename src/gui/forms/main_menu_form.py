"""
Main menu form for QB-Assistant parameter configuration tools.

Provides central navigation hub to access all parameter configuration tools:
- Sample Parameters
- Budget Parameters
- Forecast Scenarios
"""
import tkinter as tk


class MainMenuForm(tk.Frame):
    """
    Main menu form providing navigation to all parameter configuration tools.

    Serves as the entry point for the QB-Assistant GUI application, with
    navigation buttons to each configuration tool.
    """

    def __init__(self, parent):
        """
        Initialize main menu form.

        Args:
            parent: Parent widget (should be App instance with show_form method)
        """
        super().__init__(parent)
        self.parent = parent

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create title label
        title = tk.Label(
            self,
            text="QB-Assistant Parameter Configuration",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20)

        # Create subtitle/description
        subtitle = tk.Label(
            self,
            text="Select a parameter configuration tool to begin",
            font=('Arial', 12),
            fg='#666'
        )
        subtitle.grid(row=1, column=0, pady=(0, 20))

        # Create forecast settings section
        self._create_forecast_settings()

        # Create navigation buttons container
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=3, column=0, pady=20)

        # Sample Parameters button
        sample_btn = tk.Button(
            nav_frame,
            text="Sample Parameters",
            command=self.on_sample_params_clicked,
            width=30,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        sample_btn.pack(pady=10)

        # Budget Parameters button
        budget_btn = tk.Button(
            nav_frame,
            text="Budget Parameters",
            command=self.on_budget_params_clicked,
            width=30,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        budget_btn.pack(pady=10)

        # Forecast Scenarios button
        scenarios_btn = tk.Button(
            nav_frame,
            text="Forecast Scenarios",
            command=self.on_forecast_scenarios_clicked,
            width=30,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        scenarios_btn.pack(pady=10)

        # Historical Data Anomaly Review button
        anomaly_btn = tk.Button(
            nav_frame,
            text="Historical Data Anomaly Review",
            command=self.on_anomaly_review_clicked,
            width=30,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        anomaly_btn.pack(pady=10)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=4, column=0, pady=10)

    def _create_forecast_settings(self) -> None:
        """
        Create forecast settings section with horizon selector.

        Adds radio buttons for 6-month/12-month forecast horizon selection,
        help text explaining the options, and persistence via global config.
        """
        # Create settings container frame
        settings_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1, padx=15, pady=10)
        settings_frame.grid(row=2, column=0, pady=(0, 10))

        # Section header
        header = tk.Label(
            settings_frame,
            text="Forecast Settings",
            font=('Arial', 11, 'bold')
        )
        header.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 5))

        # Horizon selector label
        horizon_label = tk.Label(
            settings_frame,
            text="Forecast Horizon:",
            font=('Arial', 10)
        )
        horizon_label.grid(row=1, column=0, sticky='w', pady=5)

        # Load current horizon from global config
        global_config = self.parent.get_global_config()
        current_horizon = global_config.forecast_horizon

        # Create StringVar for radio button state
        self.horizon_var = tk.StringVar(value=str(current_horizon))

        # Create radio buttons frame
        radio_frame = tk.Frame(settings_frame)
        radio_frame.grid(row=1, column=1, sticky='w', pady=5)

        # 6-month radio button
        radio_6 = tk.Radiobutton(
            radio_frame,
            text="6 months",
            variable=self.horizon_var,
            value="6",
            command=self._on_horizon_changed,
            font=('Arial', 10)
        )
        radio_6.pack(side=tk.LEFT, padx=(0, 15))

        # 12-month radio button
        radio_12 = tk.Radiobutton(
            radio_frame,
            text="12 months",
            variable=self.horizon_var,
            value="12",
            command=self._on_horizon_changed,
            font=('Arial', 10)
        )
        radio_12.pack(side=tk.LEFT)

        # Help text explaining the options
        help_text = tk.Label(
            settings_frame,
            text="6-month for near-term liquidity planning, 12-month for strategic expansion decisions",
            font=('Arial', 9),
            fg='#666',
            wraplength=600,
            justify='left'
        )
        help_text.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0))

    def _on_horizon_changed(self) -> None:
        """
        Handle forecast horizon selection change.

        Updates global configuration and persists to config/global_settings.json.
        """
        # Get selected horizon value
        new_horizon = int(self.horizon_var.get())

        # Update global config
        global_config = self.parent.get_global_config()
        global_config.forecast_horizon = new_horizon

        # Save to file
        config_manager = self.parent.get_config_manager()
        config_manager.save_config(global_config, 'config/global_settings.json')

        # Update status label
        self.status_label.config(
            text=f"Forecast horizon updated to {new_horizon} months",
            fg='#4CAF50'
        )

    def on_sample_params_clicked(self) -> None:
        """
        Handle Sample Parameters button click - navigate to SampleParamsForm.
        """
        from .sample_params_form import SampleParamsForm
        self.parent.show_form(SampleParamsForm)

    def on_budget_params_clicked(self) -> None:
        """
        Handle Budget Parameters button click - navigate to BudgetParamsForm.
        """
        from .budget_params_form import BudgetParamsForm
        self.parent.show_form(BudgetParamsForm)

    def on_forecast_scenarios_clicked(self) -> None:
        """
        Handle Forecast Scenarios button click - navigate to ScenarioListForm.
        """
        from .scenario_list_form import ScenarioListForm
        self.parent.show_form(ScenarioListForm)

    def on_anomaly_review_clicked(self) -> None:
        """
        Handle Historical Data Anomaly Review button click - navigate to AnomalyAnnotationForm.
        """
        from .anomaly_annotation_form import AnomalyAnnotationForm
        self.parent.show_form(AnomalyAnnotationForm)
