"""
Scenario list form for forecast scenario management.

Provides CRUD operations (Create, Read, Update, Delete) on forecast scenarios
with list view and navigation to detail form for parameter editing.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional

from ...models.forecast_scenario import ForecastScenarioModel, ForecastScenariosCollection
from ...services.forecast_templates import ForecastTemplateService


class ScenarioListForm(tk.Frame):
    """
    Form for managing forecast scenarios with CRUD operations.

    Displays scenario list in Listbox, provides buttons for Create/Edit/Delete,
    and navigates to ForecastParamsForm for parameter editing.
    """

    CONFIG_FILEPATH = 'config/forecast_scenarios.json'

    def __init__(self, parent):
        """
        Initialize scenario list form.

        Args:
            parent: Parent widget (should be App instance with get_config_manager and show_form methods)
        """
        super().__init__(parent)
        self.parent = parent

        # Storage for loaded scenarios collection
        self.scenarios_collection: Optional[ForecastScenariosCollection] = None

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Create title label
        title = tk.Label(
            self,
            text="Forecast Scenarios",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, columnspan=2, pady=20)

        # Create container for list and buttons
        container = tk.Frame(self)
        container.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=20, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)

        # Create listbox for scenarios (left side)
        list_frame = tk.LabelFrame(
            container,
            text="Scenarios",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        list_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        # Scrollbar for listbox
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox widget
        self.scenario_listbox = tk.Listbox(
            list_frame,
            width=30,
            height=15,
            font=('Arial', 10),
            yscrollcommand=scrollbar.set
        )
        self.scenario_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.scenario_listbox.yview)

        # Create buttons frame (right side)
        buttons_frame = tk.Frame(container)
        buttons_frame.grid(row=0, column=1, sticky='n')

        # Create Scenario button
        create_btn = tk.Button(
            buttons_frame,
            text="Create Scenario",
            command=self.on_create_clicked,
            width=18,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        create_btn.pack(pady=5)

        # Edit Scenario button
        edit_btn = tk.Button(
            buttons_frame,
            text="Edit Scenario",
            command=self.on_edit_clicked,
            width=18,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        edit_btn.pack(pady=5)

        # Delete Scenario button
        delete_btn = tk.Button(
            buttons_frame,
            text="Delete Scenario",
            command=self.on_delete_clicked,
            width=18,
            bg='#F44336',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        delete_btn.pack(pady=5)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=2, column=0, columnspan=2, pady=10)

        # Load scenarios on initialization
        self.load_scenarios()

    def load_scenarios(self) -> None:
        """
        Load scenarios from config file and populate listbox.

        Creates empty collection if file doesn't exist (first run).
        Displays error message if load fails.
        """
        try:
            # Load scenarios collection from config file
            config_mgr = self.parent.get_config_manager()

            # Load generic ParameterModel first
            loaded_model = config_mgr.load_config(self.CONFIG_FILEPATH)

            # Convert to ForecastScenariosCollection
            self.scenarios_collection = ForecastScenariosCollection.from_dict(loaded_model.to_dict())

        except FileNotFoundError:
            # First run - create empty collection
            self.scenarios_collection = ForecastScenariosCollection()
            self.status_label.config(text="No scenarios yet. Create your first scenario!", fg='#666')

        except Exception as e:
            # Unexpected error
            self.scenarios_collection = ForecastScenariosCollection()
            self.status_label.config(text=f"Load error: {str(e)}", fg='#F44336')
            messagebox.showerror("Error", f"Failed to load scenarios: {str(e)}")

        # Populate listbox with scenario names
        self.refresh_list()

    def refresh_list(self) -> None:
        """
        Refresh listbox with current scenarios from collection.

        Clears listbox and repopulates with scenario names.
        """
        # Clear listbox
        self.scenario_listbox.delete(0, tk.END)

        # Add scenario names to listbox
        if self.scenarios_collection:
            scenarios = self.scenarios_collection.list_scenarios()
            for scenario in scenarios:
                self.scenario_listbox.insert(tk.END, scenario.scenario_name)

            # Update status
            count = len(scenarios)
            if count > 0:
                self.status_label.config(text=f"{count} scenario(s) loaded", fg='#4CAF50')

    def on_create_clicked(self) -> None:
        """
        Handle Create Scenario button click.

        Opens dialog for scenario name and template selection, creates new scenario
        with template parameters, saves collection, and navigates to parameter form.
        """
        # Create custom dialog for scenario name and template selection
        dialog = ScenarioCreateDialog(self, ForecastTemplateService.list_templates())
        self.wait_window(dialog)

        # Check if dialog was cancelled
        if not dialog.result:
            return

        scenario_name, template_name = dialog.result

        try:
            # Get template parameters
            template_params = ForecastTemplateService.get_template(template_name)

            # Create new scenario with template
            new_scenario = ForecastScenarioModel(
                parameters=template_params,
                scenario_name=scenario_name,
                description=f"Created from {template_name} template"
            )

            # Add to collection
            self.scenarios_collection.add_scenario(new_scenario)

            # Save collection to file
            config_mgr = self.parent.get_config_manager()
            config_mgr.save_config(self.scenarios_collection, self.CONFIG_FILEPATH)

            # Update status
            self.status_label.config(
                text=f"Scenario '{scenario_name}' created successfully",
                fg='#4CAF50'
            )

            # Navigate to parameter form for editing
            from .forecast_params_form import ForecastParamsForm
            self.parent.show_form(ForecastParamsForm, scenario_id=new_scenario.scenario_id)

        except Exception as e:
            self.status_label.config(text=f"Create failed: {str(e)}", fg='#F44336')
            messagebox.showerror("Error", f"Failed to create scenario: {str(e)}")

    def on_edit_clicked(self) -> None:
        """
        Handle Edit Scenario button click.

        Gets selected scenario from listbox and navigates to parameter form.
        """
        # Get selected index
        selection = self.scenario_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a scenario to edit")
            return

        # Get scenario at selected index
        selected_index = selection[0]
        scenarios = self.scenarios_collection.list_scenarios()
        if selected_index >= len(scenarios):
            messagebox.showerror("Error", "Invalid scenario selection")
            return

        selected_scenario = scenarios[selected_index]

        # Navigate to parameter form with scenario_id
        from .forecast_params_form import ForecastParamsForm
        self.parent.show_form(ForecastParamsForm, scenario_id=selected_scenario.scenario_id)

    def on_delete_clicked(self) -> None:
        """
        Handle Delete Scenario button click.

        Shows confirmation dialog, removes scenario from collection, saves, and refreshes list.
        """
        # Get selected index
        selection = self.scenario_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a scenario to delete")
            return

        # Get scenario at selected index
        selected_index = selection[0]
        scenarios = self.scenarios_collection.list_scenarios()
        if selected_index >= len(scenarios):
            messagebox.showerror("Error", "Invalid scenario selection")
            return

        selected_scenario = scenarios[selected_index]

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete scenario '{selected_scenario.scenario_name}'?"
        )
        if not confirm:
            return

        try:
            # Remove scenario from collection
            self.scenarios_collection.remove_scenario(selected_scenario.scenario_id)

            # Save collection to file
            config_mgr = self.parent.get_config_manager()
            config_mgr.save_config(self.scenarios_collection, self.CONFIG_FILEPATH)

            # Refresh listbox
            self.refresh_list()

            # Update status
            self.status_label.config(
                text=f"Scenario '{selected_scenario.scenario_name}' deleted",
                fg='#4CAF50'
            )

        except Exception as e:
            self.status_label.config(text=f"Delete failed: {str(e)}", fg='#F44336')
            messagebox.showerror("Error", f"Failed to delete scenario: {str(e)}")


class ScenarioCreateDialog(tk.Toplevel):
    """
    Custom dialog for creating scenario with name and template selection.

    Provides entry field for scenario name and dropdown for template selection.
    """

    def __init__(self, parent, template_names):
        """
        Initialize create scenario dialog.

        Args:
            parent: Parent widget
            template_names: List of available template names
        """
        super().__init__(parent)
        self.title("Create New Scenario")
        self.geometry("400x250")
        self.resizable(False, False)

        # Center dialog on parent
        self.transient(parent)
        self.grab_set()

        # Result storage
        self.result = None

        # Scenario name entry
        name_label = tk.Label(self, text="Scenario Name:", font=('Arial', 10))
        name_label.pack(pady=(20, 5))

        self.name_entry = tk.Entry(self, width=40, font=('Arial', 10))
        self.name_entry.pack(pady=5)
        self.name_entry.focus()

        # Template selection dropdown
        template_label = tk.Label(self, text="Template:", font=('Arial', 10))
        template_label.pack(pady=(10, 5))

        self.template_var = tk.StringVar(value=template_names[0])
        template_dropdown = tk.OptionMenu(self, self.template_var, *template_names)
        template_dropdown.config(width=35)
        template_dropdown.pack(pady=5)

        # Buttons frame
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=20)

        # OK button
        ok_btn = tk.Button(
            buttons_frame,
            text="Create",
            command=self.on_ok,
            width=12,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        ok_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            buttons_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12,
            font=('Arial', 10)
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to OK
        self.bind('<Return>', lambda e: self.on_ok())
        self.bind('<Escape>', lambda e: self.on_cancel())

    def on_ok(self):
        """Handle OK button - validate and store result."""
        scenario_name = self.name_entry.get().strip()
        if not scenario_name:
            messagebox.showwarning("Invalid Input", "Please enter a scenario name")
            return

        template_name = self.template_var.get()
        self.result = (scenario_name, template_name)
        self.destroy()

    def on_cancel(self):
        """Handle Cancel button - close dialog without result."""
        self.result = None
        self.destroy()
