"""
Forecast parameters form for detailed scenario parameter editing.

Provides hierarchical sections for revenue growth rates, expense trend adjustments,
cash flow timing parameters, and major cash events. Loads specific scenario by ID
and saves changes back to scenarios collection.
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any

from ..components.form_fields import NumericEntry, LabeledEntry, LabeledDropdown
from ...models.forecast_scenario import ForecastScenariosCollection


class ForecastParamsForm(tk.Frame):
    """
    Form for editing detailed forecast parameters for a specific scenario.

    Organizes parameters into four hierarchical sections matching Epic 4 requirements.
    Loads scenario by ID, populates fields, and saves changes to collection.
    """

    CONFIG_FILEPATH = 'config/forecast_scenarios.json'

    def __init__(self, parent, scenario_id: str):
        """
        Initialize forecast parameters form for specific scenario.

        Args:
            parent: Parent widget (should be App instance with get_config_manager and show_form methods)
            scenario_id: Unique identifier of scenario to edit
        """
        super().__init__(parent)
        self.parent = parent
        self.scenario_id = scenario_id

        # Storage for field references (for easy value collection)
        self.fields: Dict[str, Any] = {}

        # Load scenario from collection
        self.scenarios_collection = None
        self.current_scenario = None
        self._load_scenario()

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create title with scenario name
        title_text = f"Forecast Parameters: {self.current_scenario.scenario_name if self.current_scenario else 'Unknown'}"
        title = tk.Label(
            self,
            text=title_text,
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20)

        # Create scrollable container for sections
        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky='nsew', padx=20)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.grid_rowconfigure(1, weight=1)

        # Create parameter sections
        if self.current_scenario:
            params = self.current_scenario.parameters
            self._create_revenue_section(scrollable_frame, params.get('revenue_growth_rates', {}))
            self._create_expense_section(scrollable_frame, params.get('expense_trend_adjustments', {}))
            self._create_cash_flow_section(scrollable_frame, params.get('cash_flow_timing_params', {}))
            self._create_major_events_section(scrollable_frame, params.get('major_cash_events', {}))
            self._create_external_events_section(scrollable_frame, params.get('external_events', {}))

        # Create buttons container
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=20)

        # Save button
        save_btn = tk.Button(
            buttons_frame,
            text="Save Changes",
            command=self.on_save_clicked,
            width=20,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        save_btn.pack(side=tk.LEFT, padx=10)

        # Back button
        back_btn = tk.Button(
            buttons_frame,
            text="Back to Scenarios",
            command=self.on_back_clicked,
            width=20,
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        back_btn.pack(side=tk.LEFT, padx=10)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

    def _load_scenario(self) -> None:
        """
        Load scenarios collection and retrieve specific scenario by ID.

        Sets self.current_scenario to loaded scenario, or None if error occurs.
        Displays error message if load fails.
        """
        try:
            # Load scenarios collection from config file
            config_mgr = self.parent.get_config_manager()
            self.scenarios_collection = config_mgr.load_config(
                self.CONFIG_FILEPATH,
                model_class=ForecastScenariosCollection
            )

            # Get specific scenario by ID
            self.current_scenario = self.scenarios_collection.get_scenario(self.scenario_id)

        except Exception as e:
            self.current_scenario = None
            messagebox.showerror("Error", f"Failed to load scenario: {str(e)}")

    def _create_revenue_section(self, parent: tk.Frame, params: Dict[str, Any]) -> None:
        """
        Create revenue growth rates section with fields.

        Args:
            parent: Parent frame to pack section into
            params: Dictionary with revenue parameter values
        """
        revenue_section = tk.LabelFrame(
            parent,
            text="Revenue Growth Rates",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        revenue_section.pack(fill=tk.X, expand=False, pady=10)

        # Monthly rate field
        monthly_rate_field = NumericEntry(
            revenue_section,
            label_text="Monthly Growth Rate:",
            default_value=params.get('monthly_rate', 0.05),
            value_type=float
        )
        monthly_rate_field.pack(pady=5)
        self.fields['monthly_rate'] = monthly_rate_field

        # Use averaged checkbox
        use_averaged_var = tk.IntVar(value=1 if params.get('use_averaged', True) else 0)
        use_averaged_check = tk.Checkbutton(
            revenue_section,
            text="Use Averaged Growth Rate",
            variable=use_averaged_var,
            font=('Arial', 10)
        )
        use_averaged_check.pack(pady=5)
        self.fields['use_averaged'] = use_averaged_var

        # Help text
        help_text = tk.Label(
            revenue_section,
            text="(Monthly rate as decimal: 0.05 = 5% growth)",
            font=('Arial', 9, 'italic'),
            fg='#666'
        )
        help_text.pack(pady=2)

    def _create_expense_section(self, parent: tk.Frame, params: Dict[str, Any]) -> None:
        """
        Create expense trend adjustments section with fields.

        Args:
            parent: Parent frame to pack section into
            params: Dictionary with expense parameter values
        """
        expense_section = tk.LabelFrame(
            parent,
            text="Expense Trend Adjustments",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        expense_section.pack(fill=tk.X, expand=False, pady=10)

        # COGS trend field
        cogs_trend_field = NumericEntry(
            expense_section,
            label_text="COGS Trend Rate:",
            default_value=params.get('cogs_trend', 0.03),
            value_type=float
        )
        cogs_trend_field.pack(pady=5)
        self.fields['cogs_trend'] = cogs_trend_field

        # OpEx trend field
        opex_trend_field = NumericEntry(
            expense_section,
            label_text="OpEx Trend Rate:",
            default_value=params.get('opex_trend', 0.02),
            value_type=float
        )
        opex_trend_field.pack(pady=5)
        self.fields['opex_trend'] = opex_trend_field

        # Help text
        help_text = tk.Label(
            expense_section,
            text="(Trend rate as decimal: 0.03 = 3% increase)",
            font=('Arial', 9, 'italic'),
            fg='#666'
        )
        help_text.pack(pady=2)

    def _create_cash_flow_section(self, parent: tk.Frame, params: Dict[str, Any]) -> None:
        """
        Create cash flow timing parameters section with fields.

        Args:
            parent: Parent frame to pack section into
            params: Dictionary with cash flow parameter values
        """
        cash_flow_section = tk.LabelFrame(
            parent,
            text="Cash Flow Timing Parameters",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        cash_flow_section.pack(fill=tk.X, expand=False, pady=10)

        # Collection period field
        collection_period_field = NumericEntry(
            cash_flow_section,
            label_text="Collection Period (days):",
            default_value=params.get('collection_period_days', 45),
            value_type=int
        )
        collection_period_field.pack(pady=5)
        self.fields['collection_period_days'] = collection_period_field

        # Payment terms field
        payment_terms_field = NumericEntry(
            cash_flow_section,
            label_text="Payment Terms (days):",
            default_value=params.get('payment_terms_days', 30),
            value_type=int
        )
        payment_terms_field.pack(pady=5)
        self.fields['payment_terms_days'] = payment_terms_field

        # Help text
        help_text = tk.Label(
            cash_flow_section,
            text="(Number of days for collections and payments)",
            font=('Arial', 9, 'italic'),
            fg='#666'
        )
        help_text.pack(pady=2)

    def _create_major_events_section(self, parent: tk.Frame, params: Dict[str, Any]) -> None:
        """
        Create major cash events section with fields.

        Args:
            parent: Parent frame to pack section into
            params: Dictionary with major cash event parameter values
        """
        events_section = tk.LabelFrame(
            parent,
            text="Major Cash Events",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        events_section.pack(fill=tk.X, expand=False, pady=10)

        # Planned CapEx field (text entry for now, can be enhanced later)
        planned_capex = params.get('planned_capex', [])
        capex_text = ', '.join(str(item) for item in planned_capex) if planned_capex else ""

        capex_field = LabeledEntry(
            events_section,
            label_text="Planned Capital Expenditures:",
            default_value=capex_text
        )
        capex_field.pack(pady=5)
        self.fields['planned_capex'] = capex_field

        # Debt payments field
        debt_payments = params.get('debt_payments', [])
        debt_text = ', '.join(str(item) for item in debt_payments) if debt_payments else ""

        debt_field = LabeledEntry(
            events_section,
            label_text="Debt Payments:",
            default_value=debt_text
        )
        debt_field.pack(pady=5)
        self.fields['debt_payments'] = debt_field

        # Help text
        help_text = tk.Label(
            events_section,
            text="(Comma-separated values for planned events)",
            font=('Arial', 9, 'italic'),
            fg='#666'
        )
        help_text.pack(pady=2)

    def _create_external_events_section(self, parent: tk.Frame, params: Dict[str, Any]) -> None:
        """
        Create external economic events section with list-based UI for add/delete operations.

        Args:
            parent: Parent frame to pack section into
            params: Dictionary with external events parameter values
        """
        events_section = tk.LabelFrame(
            parent,
            text="External Economic Events",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        events_section.pack(fill=tk.X, expand=False, pady=10)

        # Help text to distinguish from major_cash_events
        help_text = tk.Label(
            events_section,
            text="(Forward-looking external events: tariffs, policy changes, economic shocks - distinct from internal major cash events)",
            font=('Arial', 9, 'italic'),
            fg='#666',
            wraplength=600,
            justify=tk.LEFT
        )
        help_text.pack(pady=(0, 10))

        # Form fields frame
        form_frame = tk.Frame(events_section)
        form_frame.pack(fill=tk.X, pady=5)

        # Month field (1-12)
        self.external_event_month_field = NumericEntry(
            form_frame,
            label_text="Month (1-12):",
            default_value="",
            value_type=int
        )
        self.external_event_month_field.pack(pady=5)

        # Impact type dropdown
        impact_type_options = [
            'Revenue Reduction',
            'Revenue Increase',
            'Cost Increase',
            'Cost Reduction',
            'Other'
        ]
        self.external_event_impact_type_field = LabeledDropdown(
            form_frame,
            label_text="Impact Type:",
            options=impact_type_options,
            default_value='Revenue Reduction'
        )
        self.external_event_impact_type_field.pack(pady=5)

        # Magnitude field (percentage)
        self.external_event_magnitude_field = NumericEntry(
            form_frame,
            label_text="Magnitude (%):",
            default_value="",
            value_type=float
        )
        self.external_event_magnitude_field.pack(pady=5)

        # Description field
        self.external_event_description_field = LabeledEntry(
            form_frame,
            label_text="Description:",
            default_value=""
        )
        self.external_event_description_field.pack(pady=5)

        # Buttons frame
        buttons_frame = tk.Frame(events_section)
        buttons_frame.pack(pady=10)

        # Add button
        add_btn = tk.Button(
            buttons_frame,
            text="Add Event",
            command=self._on_add_external_event_clicked,
            width=15,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        add_btn.pack(side=tk.LEFT, padx=5)

        # Delete button
        delete_btn = tk.Button(
            buttons_frame,
            text="Delete Selected",
            command=self._on_delete_external_event_clicked,
            width=15,
            bg='#F44336',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        delete_btn.pack(side=tk.LEFT, padx=5)

        # Listbox for saved events
        list_frame = tk.Frame(events_section)
        list_frame.pack(fill=tk.X, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.external_events_listbox = tk.Listbox(
            list_frame,
            width=80,
            height=6,
            yscrollcommand=scrollbar.set,
            font=('Courier', 9)
        )
        self.external_events_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.external_events_listbox.yview)

        # Initialize events list storage
        self.external_events_list = []

        # Load existing events from params
        existing_events = params.get('events', [])
        for event in existing_events:
            self.external_events_list.append(event)

        # Refresh display
        self._refresh_external_events_listbox()

    def _on_add_external_event_clicked(self) -> None:
        """
        Handle add external event button click.

        Validates fields, appends to events list, refreshes display, and clears form.
        """
        try:
            # Get and validate month (1-12)
            month = self.external_event_month_field.get_value()
            if month < 1 or month > 12:
                messagebox.showerror(
                    "Invalid Input",
                    "Month must be between 1 and 12 (forecast periods)."
                )
                return

            # Get other fields
            impact_type = self.external_event_impact_type_field.get_value()
            magnitude = self.external_event_magnitude_field.get_value()
            description = self.external_event_description_field.get_value()

            if not description.strip():
                messagebox.showerror(
                    "Invalid Input",
                    "Description cannot be empty."
                )
                return

            # Create event dict
            event = {
                'month': month,
                'impact_type': impact_type,
                'magnitude': magnitude,
                'description': description
            }

            # Add to list
            self.external_events_list.append(event)

            # Refresh listbox
            self._refresh_external_events_listbox()

            # Clear form fields
            self.external_event_month_field.set_value("")
            self.external_event_magnitude_field.set_value("")
            self.external_event_description_field.set_value("")

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

    def _on_delete_external_event_clicked(self) -> None:
        """
        Handle delete external event button click.

        Removes selected event from list after confirmation and refreshes display.
        """
        # Get selected index
        selection = self.external_events_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to delete.")
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this event?"
        )
        if not confirm:
            return

        # Remove from list
        index = selection[0]
        del self.external_events_list[index]

        # Refresh listbox
        self._refresh_external_events_listbox()

    def _refresh_external_events_listbox(self) -> None:
        """
        Refresh external events listbox with current events list.

        Formats each event as: 'Month X | impact_type | magnitude% | description'
        """
        # Clear listbox
        self.external_events_listbox.delete(0, tk.END)

        # Add each event
        for event in self.external_events_list:
            month = event['month']
            impact_type = event['impact_type']
            magnitude = event['magnitude']
            description = event['description']

            # Format display string
            display_text = f"Month {month} | {impact_type} | {magnitude}% | {description}"
            self.external_events_listbox.insert(tk.END, display_text)

    def on_save_clicked(self) -> None:
        """
        Handle save button click - collect field values and save to collection.

        Collects values from all sections, updates scenario in collection,
        and saves collection to config file.
        """
        try:
            # Reload collection to prevent overwriting concurrent changes
            config_mgr = self.parent.get_config_manager()
            self.scenarios_collection = config_mgr.load_config(
                self.CONFIG_FILEPATH,
                model_class=ForecastScenariosCollection
            )

            # Get current scenario from reloaded collection
            scenario = self.scenarios_collection.get_scenario(self.scenario_id)

            # Collect revenue section values
            revenue_params = {
                'monthly_rate': self.fields['monthly_rate'].get_value(),
                'use_averaged': bool(self.fields['use_averaged'].get())
            }

            # Collect expense section values
            expense_params = {
                'cogs_trend': self.fields['cogs_trend'].get_value(),
                'opex_trend': self.fields['opex_trend'].get_value()
            }

            # Collect cash flow section values
            cash_flow_params = {
                'collection_period_days': int(self.fields['collection_period_days'].get_value()),
                'payment_terms_days': int(self.fields['payment_terms_days'].get_value())
            }

            # Collect major events section values
            capex_text = self.fields['planned_capex'].get_value()
            debt_text = self.fields['debt_payments'].get_value()

            # Parse comma-separated values (simple parsing for now)
            planned_capex = [item.strip() for item in capex_text.split(',') if item.strip()]
            debt_payments = [item.strip() for item in debt_text.split(',') if item.strip()]

            major_events_params = {
                'planned_capex': planned_capex,
                'debt_payments': debt_payments
            }

            # Collect external events section values
            external_events_params = {
                'events': self.external_events_list
            }

            # Update scenario parameters
            scenario.set_parameter('revenue_growth_rates', revenue_params)
            scenario.set_parameter('expense_trend_adjustments', expense_params)
            scenario.set_parameter('cash_flow_timing_params', cash_flow_params)
            scenario.set_parameter('major_cash_events', major_events_params)
            scenario.set_parameter('external_events', external_events_params)

            # Save collection to file
            config_mgr.save_config(self.scenarios_collection, self.CONFIG_FILEPATH)

            # Display success message
            self.status_label.config(text="Parameters saved successfully", fg='#4CAF50')
            messagebox.showinfo("Success", "Forecast parameters saved successfully")

        except ValueError as e:
            # Validation error from NumericEntry.get_value
            self.status_label.config(text="Validation error", fg='#F44336')
            messagebox.showerror("Invalid Input", str(e))

        except Exception as e:
            # File I/O or other errors
            self.status_label.config(text="Save failed", fg='#F44336')
            messagebox.showerror("Error", f"Failed to save parameters: {str(e)}")

    def on_back_clicked(self) -> None:
        """
        Handle back button click - navigate to scenario list form.

        Returns to ScenarioListForm without saving changes.
        """
        from .scenario_list_form import ScenarioListForm
        self.parent.show_form(ScenarioListForm)
