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

        # Create navigation buttons container
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=2, column=0, pady=20)

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
        self.status_label.grid(row=3, column=0, pady=10)

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
