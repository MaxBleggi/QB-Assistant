"""
Reusable GUI form field components for parameter input.

Provides labeled entry fields, numeric entry with validation, and dropdown fields
with consistent layout and data binding interface.
"""
import tkinter as tk
from tkinter import ttk
from typing import Any, List, Union


class LabeledEntry(tk.Frame):
    """
    Entry field with label for text input.

    Packs label and entry widget horizontally, provides get_value/set_value
    interface for data binding.
    """

    def __init__(self, parent: tk.Widget, label_text: str, default_value: str = ""):
        """
        Initialize labeled entry field.

        Args:
            parent: Parent tkinter widget
            label_text: Text to display in label
            default_value: Initial value for entry field (default: empty string)
        """
        super().__init__(parent)

        # Create label widget
        self.label = tk.Label(self, text=label_text, width=25, anchor='w')
        self.label.pack(side=tk.LEFT, padx=5, pady=5)

        # Create entry widget
        self.entry = tk.Entry(self, width=30)
        self.entry.pack(side=tk.LEFT, padx=5, pady=5)

        # Set default value
        if default_value:
            self.entry.insert(0, default_value)

    def get_value(self) -> str:
        """
        Get current value from entry field.

        Returns:
            String value from entry widget
        """
        return self.entry.get()

    def set_value(self, value: str) -> None:
        """
        Set value in entry field.

        Args:
            value: String value to set
        """
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)


class NumericEntry(LabeledEntry):
    """
    Numeric entry field with type validation.

    Extends LabeledEntry to validate numeric input (float or int) on get_value.
    Validation occurs on retrieval, not on keystroke, to avoid disrupting user input.
    """

    def __init__(self, parent: tk.Widget, label_text: str, default_value: Union[str, float, int] = "", value_type: type = float):
        """
        Initialize numeric entry field.

        Args:
            parent: Parent tkinter widget
            label_text: Text to display in label
            default_value: Initial numeric value (default: empty string)
            value_type: Expected numeric type (float or int, default: float)
        """
        # Convert numeric default to string for entry widget
        default_str = str(default_value) if default_value != "" else ""
        super().__init__(parent, label_text, default_str)

        self.value_type = value_type

    def get_value(self) -> Union[float, int]:
        """
        Get current value as numeric type.

        Returns:
            Numeric value (float or int based on value_type)

        Raises:
            ValueError: If entry contains non-numeric or invalid input
        """
        text_value = self.entry.get().strip()

        if not text_value:
            raise ValueError(f"{self.label['text']}: value cannot be empty")

        try:
            if self.value_type == int:
                return int(text_value)
            elif self.value_type == float:
                return float(text_value)
            else:
                raise ValueError(f"Unsupported value_type: {self.value_type}")
        except ValueError:
            raise ValueError(
                f"{self.label['text']}: invalid numeric input '{text_value}'"
            )


class LabeledDropdown(tk.Frame):
    """
    Dropdown/combobox field with label for option selection.

    Packs label and dropdown widget horizontally, provides get_value/set_value
    interface for data binding.
    """

    def __init__(self, parent: tk.Widget, label_text: str, options: List[str], default_value: str = None):
        """
        Initialize labeled dropdown field.

        Args:
            parent: Parent tkinter widget
            label_text: Text to display in label
            options: List of option strings for dropdown
            default_value: Initial selected value (default: first option)
        """
        super().__init__(parent)

        # Create label widget
        self.label = tk.Label(self, text=label_text, width=25, anchor='w')
        self.label.pack(side=tk.LEFT, padx=5, pady=5)

        # Create StringVar to track selected value
        self.selected_value = tk.StringVar()

        # Set default value
        if default_value and default_value in options:
            self.selected_value.set(default_value)
        elif options:
            self.selected_value.set(options[0])

        # Create dropdown widget using OptionMenu
        self.dropdown = tk.OptionMenu(self, self.selected_value, *options)
        self.dropdown.config(width=27)
        self.dropdown.pack(side=tk.LEFT, padx=5, pady=5)

    def get_value(self) -> str:
        """
        Get currently selected option.

        Returns:
            Selected option string
        """
        return self.selected_value.get()

    def set_value(self, value: str) -> None:
        """
        Set selected option.

        Args:
            value: Option string to select
        """
        self.selected_value.set(value)
