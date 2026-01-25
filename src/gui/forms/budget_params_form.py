"""
Budget parameters form with hierarchical sections.

Comprehensive form for capturing all budget parameters needed by Epic 3 (Budget System):
- Revenue section: overall growth rate, methodology, category-specific rates
- Expense section: adjustment factors
- Account overrides section: line-item overrides (placeholder for future)
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any

from ..components.form_fields import NumericEntry, LabeledDropdown
from ...models.parameters import ParameterModel
from ...services.budget_defaults import BudgetDefaultsService


class BudgetParamsForm(tk.Frame):
    """
    Form for editing budget parameters with hierarchical organization.

    Integrates with BudgetDefaultsService for intelligent defaults calculation
    from historical data. Saves parameters to config/budget_parameters.json
    via ConfigManager.
    """

    CONFIG_FILEPATH = 'config/budget_parameters.json'
    BUDGET_METHODOLOGIES = ['Growth from Prior Year', 'Historical Average', 'Zero-Based']

    def __init__(self, parent):
        """
        Initialize budget parameters form.

        Args:
            parent: Parent widget (should be App instance with get_config_manager method)
        """
        super().__init__(parent)
        self.parent = parent

        # Storage for dynamically created category fields
        self.category_fields: Dict[str, NumericEntry] = {}

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create title label
        title = tk.Label(
            self,
            text="Budget Parameters",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20)

        # Calculate defaults from BudgetDefaultsService
        defaults = self._get_defaults()

        # Create scrollable container for sections
        container = tk.Frame(self)
        container.grid(row=1, column=0, sticky='nsew', padx=20)

        # Revenue section
        self._create_revenue_section(container, defaults)

        # Expense section
        self._create_expense_section(container, defaults)

        # Account overrides section (placeholder)
        self._create_overrides_section(container)

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
            fg='black',
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
            fg='black',
            font=('Arial', 10, 'bold')
        )
        load_btn.pack(side=tk.LEFT, padx=10)

        # Back to Menu button
        back_btn = tk.Button(
            buttons_frame,
            text="Back to Menu",
            command=self.on_back_to_menu_clicked,
            width=20,
            bg='#9E9E9E',
            fg='black',
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
        self.status_label.grid(row=3, column=0, pady=10)

    def _get_defaults(self) -> Dict[str, Any]:
        """
        Calculate defaults using BudgetDefaultsService.

        Returns:
            Dict with default values, or fallback defaults if service fails
        """
        try:
            # Note: pl_model and bs_model will be None until Sprint 1.5 completes
            # BudgetDefaultsService handles None gracefully with fallback defaults
            defaults = BudgetDefaultsService.calculate_defaults(pl_model=None, bs_model=None)
            return defaults
        except Exception:
            # Graceful degradation: return fallback defaults if service fails
            return {
                'revenue_growth_rate': 0.05,
                'expense_adjustment': 1.0,
                'budget_methodology': 'Growth from Prior Year',
                'category_growth_rates': {}
            }

    def _create_revenue_section(self, parent: tk.Frame, defaults: Dict[str, Any]) -> None:
        """
        Create revenue section with growth rate and methodology fields.

        Args:
            parent: Parent frame to pack section into
            defaults: Dict with default values from BudgetDefaultsService
        """
        revenue_section = tk.LabelFrame(
            parent,
            text="Revenue Parameters",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        revenue_section.pack(fill=tk.X, expand=False, pady=10)

        # Overall revenue growth rate
        self.revenue_growth_field = NumericEntry(
            revenue_section,
            label_text="Overall Revenue Growth Rate:",
            default_value=defaults.get('revenue_growth_rate', 0.05),
            value_type=float
        )
        self.revenue_growth_field.pack(pady=5)

        # Budget methodology dropdown
        self.methodology_field = LabeledDropdown(
            revenue_section,
            label_text="Budget Methodology:",
            options=self.BUDGET_METHODOLOGIES,
            default_value=defaults.get('budget_methodology', 'Growth from Prior Year')
        )
        self.methodology_field.pack(pady=5)

        # Category-specific growth rates (dynamic)
        category_rates = defaults.get('category_growth_rates', {})
        if category_rates:
            # Add separator label
            category_label = tk.Label(
                revenue_section,
                text="Category-Specific Growth Rates:",
                font=('Arial', 10, 'italic')
            )
            category_label.pack(pady=(10, 5))

            # Create field for each category
            for category_name, default_rate in category_rates.items():
                category_field = NumericEntry(
                    revenue_section,
                    label_text=f"  {category_name}:",
                    default_value=default_rate,
                    value_type=float
                )
                category_field.pack(pady=3)
                self.category_fields[category_name] = category_field

    def _create_expense_section(self, parent: tk.Frame, defaults: Dict[str, Any]) -> None:
        """
        Create expense section with adjustment factor field.

        Args:
            parent: Parent frame to pack section into
            defaults: Dict with default values from BudgetDefaultsService
        """
        expense_section = tk.LabelFrame(
            parent,
            text="Expense Parameters",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        expense_section.pack(fill=tk.X, expand=False, pady=10)

        # Expense adjustment factor
        self.expense_adjustment_field = NumericEntry(
            expense_section,
            label_text="Expense Adjustment Factor:",
            default_value=defaults.get('expense_adjustment', 1.0),
            value_type=float
        )
        self.expense_adjustment_field.pack(pady=5)

        # Help text
        help_text = tk.Label(
            expense_section,
            text="(1.0 = no change, 1.1 = 10% increase, 0.9 = 10% decrease)",
            font=('Arial', 9, 'italic'),
            fg='#666'
        )
        help_text.pack(pady=2)

    def _create_overrides_section(self, parent: tk.Frame) -> None:
        """
        Create account overrides section (placeholder for future).

        Args:
            parent: Parent frame to pack section into
        """
        overrides_section = tk.LabelFrame(
            parent,
            text="Account-Level Overrides",
            font=('Arial', 12, 'bold'),
            padx=10,
            pady=10
        )
        overrides_section.pack(fill=tk.X, expand=False, pady=10)

        # Placeholder label
        placeholder_label = tk.Label(
            overrides_section,
            text="Account-level overrides will be available in a future release.",
            font=('Arial', 10, 'italic'),
            fg='#999'
        )
        placeholder_label.pack(pady=10)

    def on_save_clicked(self) -> None:
        """
        Handle save button click - collect field values and save to JSON.

        Collects values from all hierarchical sections (revenue, expense, overrides),
        creates ParameterModel, and saves to config/budget_parameters.json via ConfigManager.
        """
        try:
            # Collect revenue section values
            revenue_growth = self.revenue_growth_field.get_value()
            budget_methodology = self.methodology_field.get_value()

            # Collect category-specific growth rates
            category_rates = {}
            for category_name, field in self.category_fields.items():
                category_rates[category_name] = field.get_value()

            # Collect expense section values
            expense_adjustment = self.expense_adjustment_field.get_value()

            # Build parameters dict
            params = {
                'revenue_growth_rate': revenue_growth,
                'budget_methodology': budget_methodology,
                'category_growth_rates': category_rates,
                'expense_adjustment_factor': expense_adjustment
            }

            # Create ParameterModel
            model = ParameterModel(parameters=params)

            # Save to JSON via ConfigManager
            config_mgr = self.parent.get_config_manager()
            config_mgr.save_config(model, self.CONFIG_FILEPATH)

            # Display success message
            self.status_label.config(text="✓ Budget parameters saved successfully", fg='#4CAF50')
            messagebox.showinfo("Success", "Budget parameters saved successfully")

        except ValueError as e:
            # Validation error from NumericEntry.get_value
            self.status_label.config(text="✗ Validation error", fg='#F44336')
            messagebox.showerror("Invalid Input", str(e))

        except Exception as e:
            # File I/O or other errors
            self.status_label.config(text="✗ Save failed", fg='#F44336')
            messagebox.showerror("Error", f"Failed to save budget parameters: {str(e)}")

    def on_load_clicked(self) -> None:
        """
        Handle load button click - load from JSON and populate fields.

        Loads parameters from config/budget_parameters.json and populates all
        fields in all sections (revenue, expense, overrides).
        """
        try:
            # Load from JSON via ConfigManager
            config_mgr = self.parent.get_config_manager()
            model = config_mgr.load_config(self.CONFIG_FILEPATH)

            # Populate fields with loaded values
            params = model.parameters

            # Revenue section
            if 'revenue_growth_rate' in params:
                self.revenue_growth_field.set_value(str(params['revenue_growth_rate']))

            if 'budget_methodology' in params:
                self.methodology_field.set_value(params['budget_methodology'])

            # Category-specific rates
            if 'category_growth_rates' in params:
                loaded_category_rates = params['category_growth_rates']
                for category_name, field in self.category_fields.items():
                    if category_name in loaded_category_rates:
                        field.set_value(str(loaded_category_rates[category_name]))

            # Expense section
            if 'expense_adjustment_factor' in params:
                self.expense_adjustment_field.set_value(str(params['expense_adjustment_factor']))

            # Display success message
            loaded_count = len(params)
            self.status_label.config(
                text=f"✓ Loaded {loaded_count} parameter(s) successfully",
                fg='#4CAF50'
            )
            messagebox.showinfo("Success", f"Budget parameters loaded successfully ({loaded_count} parameter(s))")

        except Exception as e:
            # File I/O or JSON parsing errors
            self.status_label.config(text="✗ Load failed", fg='#F44336')
            messagebox.showerror("Error", f"Failed to load budget parameters: {str(e)}")

    def on_back_to_menu_clicked(self) -> None:
        """
        Handle Back to Menu button click - navigate to MainMenuForm.
        """
        from .main_menu_form import MainMenuForm
        self.parent.show_form(MainMenuForm)
