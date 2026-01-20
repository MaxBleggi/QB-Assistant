"""
Sample parameter form for revenue growth rate and expense adjustment factor.

Demonstrates end-to-end workflow: display parameters → user edits → save to JSON
→ load from JSON → display in form.
"""
import tkinter as tk
from tkinter import messagebox

from ..components.form_fields import NumericEntry
from ...models.parameters import ParameterModel


class SampleParamsForm(tk.Frame):
    """
    Form for editing sample parameters with save/load functionality.

    Provides two numeric fields (revenue_growth_rate, expense_adjustment_factor)
    and integrates with ConfigManager for JSON persistence.
    """

    CONFIG_FILEPATH = 'config/default_parameters.json'

    def __init__(self, parent):
        """
        Initialize sample parameter form.

        Args:
            parent: Parent widget (should be App instance)
        """
        super().__init__(parent)
        self.parent = parent

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create title label
        title = tk.Label(
            self,
            text="Sample Parameters",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20)

        # Create form fields container
        fields_frame = tk.Frame(self)
        fields_frame.grid(row=1, column=0, pady=10)

        # Revenue growth rate field
        self.revenue_growth_field = NumericEntry(
            fields_frame,
            label_text="Revenue Growth Rate:",
            default_value="0.05",
            value_type=float
        )
        self.revenue_growth_field.pack(pady=5)

        # Expense adjustment factor field
        self.expense_adjustment_field = NumericEntry(
            fields_frame,
            label_text="Expense Adjustment Factor:",
            default_value="1.0",
            value_type=float
        )
        self.expense_adjustment_field.pack(pady=5)

        # Create buttons container
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=2, column=0, pady=20)

        # Save button
        save_btn = tk.Button(
            buttons_frame,
            text="Save Parameters",
            command=self.on_save_clicked,
            width=20,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        save_btn.pack(side=tk.LEFT, padx=10)

        # Load button
        load_btn = tk.Button(
            buttons_frame,
            text="Load Parameters",
            command=self.on_load_clicked,
            width=20,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        load_btn.pack(side=tk.LEFT, padx=10)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=3, column=0, pady=10)

    def on_save_clicked(self) -> None:
        """
        Handle save button click - collect field values and save to JSON.

        Catches validation errors and file I/O errors, displays user-friendly
        error messages via messagebox.
        """
        try:
            # Collect field values (raises ValueError if invalid)
            revenue_growth = self.revenue_growth_field.get_value()
            expense_adjustment = self.expense_adjustment_field.get_value()

            # Create parameters dict
            params = {
                'revenue_growth_rate': revenue_growth,
                'expense_adjustment_factor': expense_adjustment
            }

            # Create ParameterModel
            model = ParameterModel(parameters=params)

            # Save to JSON via ConfigManager
            config_mgr = self.parent.get_config_manager()
            config_mgr.save_config(model, self.CONFIG_FILEPATH)

            # Display success message
            self.status_label.config(text="✓ Parameters saved successfully", fg='#4CAF50')
            messagebox.showinfo("Success", "Parameters saved successfully")

        except ValueError as e:
            # Validation error from NumericEntry.get_value
            self.status_label.config(text="✗ Validation error", fg='#F44336')
            messagebox.showerror("Invalid Input", str(e))

        except Exception as e:
            # File I/O or other errors
            self.status_label.config(text="✗ Save failed", fg='#F44336')
            messagebox.showerror("Error", f"Failed to save parameters: {str(e)}")

    def on_load_clicked(self) -> None:
        """
        Handle load button click - load from JSON and populate fields.

        Catches file I/O errors and JSON parsing errors, displays user-friendly
        error messages via messagebox.
        """
        try:
            # Load from JSON via ConfigManager
            config_mgr = self.parent.get_config_manager()
            model = config_mgr.load_config(self.CONFIG_FILEPATH)

            # Populate fields with loaded values
            params = model.parameters

            if 'revenue_growth_rate' in params:
                self.revenue_growth_field.set_value(str(params['revenue_growth_rate']))

            if 'expense_adjustment_factor' in params:
                self.expense_adjustment_field.set_value(str(params['expense_adjustment_factor']))

            # Display success message
            loaded_count = len(params)
            self.status_label.config(
                text=f"✓ Loaded {loaded_count} parameter(s) successfully",
                fg='#4CAF50'
            )
            messagebox.showinfo("Success", f"Parameters loaded successfully ({loaded_count} parameter(s))")

        except Exception as e:
            # File I/O or JSON parsing errors
            self.status_label.config(text="✗ Load failed", fg='#F44336')
            messagebox.showerror("Error", f"Failed to load parameters: {str(e)}")
