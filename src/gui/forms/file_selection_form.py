"""
File selection form for QuickBooks input file selection.

Provides file picker dialogs for the 4 required QuickBooks input files
(Balance Sheet, Profit & Loss, Cash Flow Statement, Historical Data CSV).
Validates all 4 files are selected before proceeding to main menu.
"""
import tkinter as tk
from tkinter import filedialog
from pathlib import Path


class FileSelectionForm(tk.Frame):
    """
    Form for selecting required QuickBooks input files.

    Displays 4 file picker buttons (Balance Sheet, P&L, Cash Flow, Historical Data),
    validates all files are selected, and navigates to MainMenuForm after selection.
    """

    def __init__(self, parent):
        """
        Initialize file selection form.

        Args:
            parent: Parent widget (should be App instance with file path attributes and show_form method)
        """
        super().__init__(parent)
        self.parent = parent

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create title label
        title = tk.Label(
            self,
            text="File Selection",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20)

        # Create subtitle/description
        subtitle = tk.Label(
            self,
            text="Select the 4 required QuickBooks input files",
            font=('Arial', 12),
            fg='#666'
        )
        subtitle.grid(row=1, column=0, pady=(0, 20))

        # Create container for file pickers
        container = tk.LabelFrame(
            self,
            text="Required Input Files",
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=20
        )
        container.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        container.grid_columnconfigure(1, weight=1)

        # Balance Sheet row
        tk.Label(
            container,
            text="Balance Sheet (.xlsx):",
            font=('Arial', 10),
            anchor='w'
        ).grid(row=0, column=0, sticky='w', pady=10, padx=(0, 10))

        self.balance_sheet_label = tk.Label(
            container,
            text="No file selected",
            font=('Arial', 10),
            fg='#666',
            anchor='w'
        )
        self.balance_sheet_label.grid(row=0, column=1, sticky='w', pady=10, padx=(0, 10))

        tk.Button(
            container,
            text="Browse...",
            command=self._on_browse_balance_sheet,
            width=18,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=0, column=2, pady=10)

        # Profit & Loss row
        tk.Label(
            container,
            text="Profit & Loss (.xlsx):",
            font=('Arial', 10),
            anchor='w'
        ).grid(row=1, column=0, sticky='w', pady=10, padx=(0, 10))

        self.profit_loss_label = tk.Label(
            container,
            text="No file selected",
            font=('Arial', 10),
            fg='#666',
            anchor='w'
        )
        self.profit_loss_label.grid(row=1, column=1, sticky='w', pady=10, padx=(0, 10))

        tk.Button(
            container,
            text="Browse...",
            command=self._on_browse_profit_loss,
            width=18,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=1, column=2, pady=10)

        # Cash Flow Statement row
        tk.Label(
            container,
            text="Cash Flow Statement (.xlsx):",
            font=('Arial', 10),
            anchor='w'
        ).grid(row=2, column=0, sticky='w', pady=10, padx=(0, 10))

        self.cash_flow_label = tk.Label(
            container,
            text="No file selected",
            font=('Arial', 10),
            fg='#666',
            anchor='w'
        )
        self.cash_flow_label.grid(row=2, column=1, sticky='w', pady=10, padx=(0, 10))

        tk.Button(
            container,
            text="Browse...",
            command=self._on_browse_cash_flow,
            width=18,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=2, column=2, pady=10)

        # Historical Data row
        tk.Label(
            container,
            text="Historical Data (.csv):",
            font=('Arial', 10),
            anchor='w'
        ).grid(row=3, column=0, sticky='w', pady=10, padx=(0, 10))

        self.historical_data_label = tk.Label(
            container,
            text="No file selected",
            font=('Arial', 10),
            fg='#666',
            anchor='w'
        )
        self.historical_data_label.grid(row=3, column=1, sticky='w', pady=10, padx=(0, 10))

        tk.Button(
            container,
            text="Browse...",
            command=self._on_browse_historical_data,
            width=18,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        ).grid(row=3, column=2, pady=10)

        # Create buttons frame
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=3, column=0, pady=20)

        # Proceed button (initially disabled)
        self.proceed_btn = tk.Button(
            buttons_frame,
            text="Proceed",
            command=self._on_proceed,
            width=18,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10, 'bold'),
            state='disabled'
        )
        self.proceed_btn.pack(side=tk.LEFT, padx=5)

        # Clear Selections button
        clear_btn = tk.Button(
            buttons_frame,
            text="Clear Selections",
            command=self._on_clear_selections,
            width=18,
            bg='#9E9E9E',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Status message label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=4, column=0, pady=10)

        # Initialize UI based on current state
        self._refresh_ui()

    def _on_browse_balance_sheet(self) -> None:
        """Handle Balance Sheet browse button click."""
        filepath = filedialog.askopenfilename(
            title="Select Balance Sheet",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filepath:
            self.parent.selected_balance_sheet = filepath
            self.balance_sheet_label.config(text=Path(filepath).name)
            self._validate_selections()

    def _on_browse_profit_loss(self) -> None:
        """Handle Profit & Loss browse button click."""
        filepath = filedialog.askopenfilename(
            title="Select Profit & Loss",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filepath:
            self.parent.selected_profit_loss = filepath
            self.profit_loss_label.config(text=Path(filepath).name)
            self._validate_selections()

    def _on_browse_cash_flow(self) -> None:
        """Handle Cash Flow Statement browse button click."""
        filepath = filedialog.askopenfilename(
            title="Select Cash Flow Statement",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filepath:
            self.parent.selected_cash_flow = filepath
            self.cash_flow_label.config(text=Path(filepath).name)
            self._validate_selections()

    def _on_browse_historical_data(self) -> None:
        """Handle Historical Data browse button click."""
        filepath = filedialog.askopenfilename(
            title="Select Historical Data",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            self.parent.selected_historical_data = filepath
            self.historical_data_label.config(text=Path(filepath).name)
            self._validate_selections()

    def _validate_selections(self) -> None:
        """
        Validate all 4 files are selected and enable/disable proceed button.

        Enables proceed button only when all 4 file path attributes are not None.
        """
        all_selected = (
            self.parent.selected_balance_sheet is not None and
            self.parent.selected_profit_loss is not None and
            self.parent.selected_cash_flow is not None and
            self.parent.selected_historical_data is not None
        )

        if all_selected:
            self.proceed_btn.config(state='normal', bg='#2196F3')
            self.status_label.config(text="All files selected - ready to proceed", fg='#4CAF50')
        else:
            self.proceed_btn.config(state='disabled', bg='#CCCCCC')
            self.status_label.config(text="", fg='#666')

    def _on_clear_selections(self) -> None:
        """
        Handle Clear Selections button click.

        Resets all 4 file path attributes to None and updates UI.
        """
        self.parent.selected_balance_sheet = None
        self.parent.selected_profit_loss = None
        self.parent.selected_cash_flow = None
        self.parent.selected_historical_data = None

        self.balance_sheet_label.config(text="No file selected")
        self.profit_loss_label.config(text="No file selected")
        self.cash_flow_label.config(text="No file selected")
        self.historical_data_label.config(text="No file selected")

        self._validate_selections()
        self.status_label.config(text="Selections cleared", fg='#666')

    def _on_proceed(self) -> None:
        """
        Handle Proceed button click.

        Validates all 4 files are selected (defensive check) and navigates
        to MainMenuForm.
        """
        # Defensive validation check
        all_selected = (
            self.parent.selected_balance_sheet is not None and
            self.parent.selected_profit_loss is not None and
            self.parent.selected_cash_flow is not None and
            self.parent.selected_historical_data is not None
        )

        if not all_selected:
            self.status_label.config(text="Please select all 4 required files", fg='#F44336')
            return

        # Navigate to main menu
        from .main_menu_form import MainMenuForm
        self.parent.show_form(MainMenuForm)

    def _refresh_ui(self) -> None:
        """
        Refresh UI to reflect current state of file selections.

        Updates filename labels and validation status based on App state.
        """
        # Update Balance Sheet label
        if self.parent.selected_balance_sheet:
            self.balance_sheet_label.config(text=Path(self.parent.selected_balance_sheet).name)

        # Update Profit & Loss label
        if self.parent.selected_profit_loss:
            self.profit_loss_label.config(text=Path(self.parent.selected_profit_loss).name)

        # Update Cash Flow label
        if self.parent.selected_cash_flow:
            self.cash_flow_label.config(text=Path(self.parent.selected_cash_flow).name)

        # Update Historical Data label
        if self.parent.selected_historical_data:
            self.historical_data_label.config(text=Path(self.parent.selected_historical_data).name)

        # Validate selections to update proceed button state
        self._validate_selections()
