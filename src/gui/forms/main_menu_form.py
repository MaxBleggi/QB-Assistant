"""
Main menu form for QB-Assistant parameter configuration tools.

Provides central navigation hub to access all parameter configuration tools:
- Sample Parameters
- Budget Parameters
- Forecast Scenarios
"""
import tkinter as tk
from tkinter import messagebox

from ...services.pipeline_orchestrator import PipelineOrchestrator
from ...loaders.exceptions import FileLoaderError
from ...metrics.exceptions import CalculationError
from ...utils.error_mapper import ErrorMapper


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

        # Create client context section
        self._create_client_context()

        # Create forecast settings section
        self._create_forecast_settings()

        # Create navigation buttons container
        nav_frame = tk.Frame(self)
        nav_frame.grid(row=4, column=0, pady=20)

        # Sample Parameters button
        sample_btn = tk.Button(
            nav_frame,
            text="Sample Parameters",
            command=self.on_sample_params_clicked,
            width=30,
            bg='#4CAF50',
            fg='black',
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
            fg='black',
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
            fg='black',
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
            fg='black',
            font=('Arial', 10, 'bold')
        )
        anomaly_btn.pack(pady=10)

        # Select Input Files button
        file_selection_btn = tk.Button(
            nav_frame,
            text="Select Input Files",
            command=self._on_file_selection,
            width=30,
            bg='#4CAF50',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        file_selection_btn.pack(pady=10)

        # Process Data button
        process_data_btn = tk.Button(
            nav_frame,
            text="Process Data",
            command=self._on_process_data,
            width=30,
            bg='#4CAF50',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        process_data_btn.pack(pady=10)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=5, column=0, pady=10)

    def _create_client_context(self) -> None:
        """
        Create client context section showing current client and change button.

        Displays current client name and provides button to navigate back to
        client selection.
        """
        # Create client context container frame
        client_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1, padx=15, pady=10)
        client_frame.grid(row=2, column=0, pady=(0, 10))

        # Client label
        client_label = tk.Label(
            client_frame,
            text="Current Client:",
            font=('Arial', 10, 'bold')
        )
        client_label.pack(side=tk.LEFT, padx=(0, 10))

        # Client name display
        client_name = self.parent.selected_client or "None"
        client_name_label = tk.Label(
            client_frame,
            text=client_name,
            font=('Arial', 10),
            fg='#2196F3'
        )
        client_name_label.pack(side=tk.LEFT, padx=(0, 20))

        # Change Client button
        change_btn = tk.Button(
            client_frame,
            text="Change Client",
            command=self.on_change_client_clicked,
            bg='#9E9E9E',
            fg='black',
            font=('Arial', 9, 'bold')
        )
        change_btn.pack(side=tk.LEFT)

    def _create_forecast_settings(self) -> None:
        """
        Create forecast settings section with horizon selector.

        Adds radio buttons for 6-month/12-month forecast horizon selection,
        help text explaining the options, and persistence via global config.
        """
        # Create settings container frame
        settings_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1, padx=15, pady=10)
        settings_frame.grid(row=3, column=0, pady=(0, 10))

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

    def _update_progress_status(self, message: str) -> None:
        """
        Update progress status in GUI during pipeline processing.

        Displays in-progress message in blue color to indicate active processing.

        Args:
            message: Progress message to display (e.g., 'Parsing Balance Sheet...')
        """
        self.status_label.config(text=message, fg='#2196F3')

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

    def on_change_client_clicked(self) -> None:
        """
        Handle Change Client button click - navigate to ClientSelectionForm.
        """
        from .client_selection_form import ClientSelectionForm
        self.parent.show_form(ClientSelectionForm)

    def _on_file_selection(self) -> None:
        """
        Handle Select Input Files button click - navigate to FileSelectionForm.
        """
        from .file_selection_form import FileSelectionForm
        self.parent.show_form(FileSelectionForm)

    def _on_process_data(self) -> None:
        """
        Handle Process Data button click - validate selections and trigger pipeline.

        Validates that required files are selected, then invokes PipelineOrchestrator
        to execute the complete processing workflow. Shows success/error messages
        based on pipeline results.
        """
        # Get reference to app for cleaner code
        app = self.parent

        # Validate required files are selected
        if app.selected_client is None:
            messagebox.showerror(
                "Missing Client",
                "Please select a client before processing data."
            )
            return

        if app.selected_balance_sheet is None:
            messagebox.showerror(
                "Missing File",
                "Please select a balance sheet file."
            )
            return

        if app.selected_profit_loss is None:
            messagebox.showerror(
                "Missing File",
                "Please select a profit & loss file."
            )
            return

        if app.selected_cash_flow is None:
            messagebox.showerror(
                "Missing File",
                "Please select a cash flow file."
            )
            return

        # Historical data is optional - don't block if missing
        # (Pipeline will handle None gracefully)

        # All required validations passed - execute pipeline
        try:
            # Instantiate orchestrator with project root
            orchestrator = PipelineOrchestrator(str(app.project_root))

            # Call process_pipeline with all file paths and client name
            result = orchestrator.process_pipeline(
                balance_sheet_path=app.selected_balance_sheet,
                pl_path=app.selected_profit_loss,
                cash_flow_path=app.selected_cash_flow,
                historical_path=app.selected_historical_data,  # May be None
                client_name=app.selected_client,
                progress_callback=self._update_progress_status
            )

            # Handle result based on status
            if result['status'] == 'success':
                # Update status label to green success message
                self.status_label.config(text="Processing complete!", fg='#4CAF50')
                messagebox.showinfo(
                    "Processing Complete",
                    f"Data processed successfully!\n\nReport saved to:\n{result['report_path']}"
                )
            elif result['status'] == 'partial':
                # Some stages failed but report was generated
                error_summary = result['errors'][0] if result['errors'] else "Unknown error"
                messagebox.showwarning(
                    "Processing Completed with Warnings",
                    f"Report generated but some stages encountered errors:\n\n{error_summary}\n\nReport saved to:\n{result['report_path']}"
                )
            else:
                # Failed - no report generated
                error_summary = result['errors'][0] if result['errors'] else "Unknown error"
                messagebox.showerror(
                    "Processing Failed",
                    f"Data processing failed:\n\n{error_summary}"
                )

        except FileLoaderError as e:
            # File loading errors - use ErrorMapper for user-friendly message
            title, message = ErrorMapper.get_user_friendly_message(e)
            self.status_label.config(text="", fg='#666')  # Reset status label
            messagebox.showerror(title, message)
            print(f"File loading error: {e}")

        except CalculationError as e:
            # Calculation errors - use ErrorMapper for user-friendly message
            title, message = ErrorMapper.get_user_friendly_message(e)
            self.status_label.config(text="", fg='#666')  # Reset status label
            messagebox.showerror(title, message)
            print(f"Calculation error: {e}")

        except FileNotFoundError as e:
            # File not found - use ErrorMapper for user-friendly message
            title, message = ErrorMapper.get_user_friendly_message(e)
            self.status_label.config(text="", fg='#666')  # Reset status label
            messagebox.showerror(title, message)
            print(f"File not found: {e}")

        except ValueError as e:
            # Value/format errors - use ErrorMapper for user-friendly message
            title, message = ErrorMapper.get_user_friendly_message(e)
            self.status_label.config(text="", fg='#666')  # Reset status label
            messagebox.showerror(title, message)
            print(f"Data format error: {e}")

        except KeyError as e:
            # Missing data field errors - use ErrorMapper for user-friendly message
            title, message = ErrorMapper.get_user_friendly_message(e)
            self.status_label.config(text="", fg='#666')  # Reset status label
            messagebox.showerror(title, message)
            print(f"Missing data field: {e}")

        except Exception as e:
            # Generic fallback for unexpected exceptions
            title, message = ErrorMapper.get_user_friendly_message(e)
            self.status_label.config(text="", fg='#666')  # Reset status label
            messagebox.showerror(title, message)
            print(f"Exception during pipeline execution: {e}")
            import traceback
            traceback.print_exc()
