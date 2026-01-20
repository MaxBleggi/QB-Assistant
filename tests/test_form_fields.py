"""
Unit tests for reusable form field components.

Tests data binding (get_value/set_value) and validation for GUI components.
"""
import pytest
import tkinter as tk

from src.gui.components.form_fields import LabeledEntry, NumericEntry, LabeledDropdown


@pytest.fixture
def tk_root():
    """Create Tk root for GUI tests."""
    root = tk.Tk()
    yield root
    root.destroy()


class TestLabeledEntry:
    """Test suite for LabeledEntry component."""

    def test_initialization_creates_widgets(self, tk_root):
        """
        Given: Parent widget and label text
        When: LabeledEntry instantiated
        Then: Label and entry widgets created
        """
        entry = LabeledEntry(tk_root, label_text="Test Label", default_value="")

        assert entry.label is not None
        assert entry.entry is not None
        assert entry.label['text'] == "Test Label"

    def test_get_value_returns_entry_text(self, tk_root):
        """
        Given: LabeledEntry with text in entry field
        When: get_value called
        Then: Returns entry text
        """
        entry = LabeledEntry(tk_root, label_text="Test", default_value="initial")

        value = entry.get_value()

        assert value == "initial"

    def test_set_value_updates_entry_text(self, tk_root):
        """
        Given: LabeledEntry instance
        When: set_value called with new text
        Then: Entry field updated with new text
        """
        entry = LabeledEntry(tk_root, label_text="Test", default_value="initial")

        entry.set_value("updated")
        value = entry.get_value()

        assert value == "updated"

    def test_round_trip_get_set_value(self, tk_root):
        """
        Given: LabeledEntry instance
        When: set_value then get_value called
        Then: Value preserved exactly
        """
        entry = LabeledEntry(tk_root, label_text="Test")

        test_value = "test_123"
        entry.set_value(test_value)
        retrieved = entry.get_value()

        assert retrieved == test_value

    def test_empty_default_value(self, tk_root):
        """
        Given: LabeledEntry with no default value
        When: get_value called
        Then: Returns empty string
        """
        entry = LabeledEntry(tk_root, label_text="Test")

        value = entry.get_value()

        assert value == ""

    def test_set_value_replaces_existing_text(self, tk_root):
        """
        Given: LabeledEntry with existing text
        When: set_value called with different text
        Then: Old text replaced with new text
        """
        entry = LabeledEntry(tk_root, label_text="Test", default_value="old")

        entry.set_value("new")

        assert entry.get_value() == "new"
        assert "old" not in entry.get_value()


class TestNumericEntry:
    """Test suite for NumericEntry component."""

    def test_initialization_with_float_type(self, tk_root):
        """
        Given: Float value type
        When: NumericEntry instantiated
        Then: Component created with float validation
        """
        entry = NumericEntry(tk_root, label_text="Growth Rate", value_type=float)

        assert entry.value_type == float

    def test_initialization_with_int_type(self, tk_root):
        """
        Given: Int value type
        When: NumericEntry instantiated
        Then: Component created with int validation
        """
        entry = NumericEntry(tk_root, label_text="Count", value_type=int)

        assert entry.value_type == int

    def test_get_value_returns_float(self, tk_root):
        """
        Given: NumericEntry with value_type=float and valid numeric input
        When: get_value called
        Then: Returns float value
        """
        entry = NumericEntry(tk_root, label_text="Rate", default_value="0.05", value_type=float)

        value = entry.get_value()

        assert isinstance(value, float)
        assert value == 0.05

    def test_get_value_returns_int(self, tk_root):
        """
        Given: NumericEntry with value_type=int and valid numeric input
        When: get_value called
        Then: Returns int value
        """
        entry = NumericEntry(tk_root, label_text="Count", default_value="42", value_type=int)

        value = entry.get_value()

        assert isinstance(value, int)
        assert value == 42

    def test_get_value_raises_on_invalid_float(self, tk_root):
        """
        Given: NumericEntry with value_type=float and non-numeric input
        When: get_value called
        Then: Raises ValueError with descriptive message
        """
        entry = NumericEntry(tk_root, label_text="Rate", value_type=float)
        entry.set_value("not_a_number")

        with pytest.raises(ValueError) as exc_info:
            entry.get_value()

        error_msg = str(exc_info.value).lower()
        assert 'invalid' in error_msg or 'numeric' in error_msg

    def test_get_value_raises_on_invalid_int(self, tk_root):
        """
        Given: NumericEntry with value_type=int and non-integer input
        When: get_value called
        Then: Raises ValueError
        """
        entry = NumericEntry(tk_root, label_text="Count", value_type=int)
        entry.set_value("3.14")

        with pytest.raises(ValueError) as exc_info:
            entry.get_value()

        assert 'invalid' in str(exc_info.value).lower()

    def test_get_value_raises_on_empty_input(self, tk_root):
        """
        Given: NumericEntry with empty entry field
        When: get_value called
        Then: Raises ValueError about empty value
        """
        entry = NumericEntry(tk_root, label_text="Rate", value_type=float)
        entry.set_value("")

        with pytest.raises(ValueError) as exc_info:
            entry.get_value()

        assert 'empty' in str(exc_info.value).lower()

    def test_accepts_negative_float(self, tk_root):
        """
        Given: NumericEntry with value_type=float
        When: get_value called with negative number string
        Then: Returns negative float
        """
        entry = NumericEntry(tk_root, label_text="Rate", value_type=float)
        entry.set_value("-0.5")

        value = entry.get_value()

        assert value == -0.5

    def test_accepts_negative_int(self, tk_root):
        """
        Given: NumericEntry with value_type=int
        When: get_value called with negative integer string
        Then: Returns negative int
        """
        entry = NumericEntry(tk_root, label_text="Adjustment", value_type=int)
        entry.set_value("-10")

        value = entry.get_value()

        assert value == -10

    def test_default_value_numeric_conversion(self, tk_root):
        """
        Given: NumericEntry with numeric default value
        When: get_value called
        Then: Returns correct numeric type
        """
        entry = NumericEntry(tk_root, label_text="Rate", default_value=0.05, value_type=float)

        value = entry.get_value()

        assert isinstance(value, float)
        assert value == 0.05

    def test_set_value_accepts_string(self, tk_root):
        """
        Given: NumericEntry instance
        When: set_value called with string representation of number
        Then: Value stored and retrievable as numeric type
        """
        entry = NumericEntry(tk_root, label_text="Rate", value_type=float)
        entry.set_value("1.23")

        value = entry.get_value()

        assert value == 1.23


class TestLabeledDropdown:
    """Test suite for LabeledDropdown component."""

    def test_initialization_creates_widgets(self, tk_root):
        """
        Given: Options list
        When: LabeledDropdown instantiated
        Then: Label and dropdown widgets created
        """
        dropdown = LabeledDropdown(tk_root, label_text="Select Option", options=["A", "B"])

        assert dropdown.label is not None
        assert dropdown.dropdown is not None

    def test_get_value_returns_selected_option(self, tk_root):
        """
        Given: LabeledDropdown with options
        When: get_value called
        Then: Returns currently selected option
        """
        dropdown = LabeledDropdown(
            tk_root,
            label_text="Select",
            options=["Option A", "Option B"],
            default_value="Option A"
        )

        value = dropdown.get_value()

        assert value == "Option A"

    def test_set_value_changes_selected_option(self, tk_root):
        """
        Given: LabeledDropdown with options
        When: set_value called with different option
        Then: Selected option changes
        """
        dropdown = LabeledDropdown(
            tk_root,
            label_text="Select",
            options=["Option A", "Option B"],
            default_value="Option A"
        )

        dropdown.set_value("Option B")
        value = dropdown.get_value()

        assert value == "Option B"

    def test_default_value_when_not_specified(self, tk_root):
        """
        Given: LabeledDropdown with no default value specified
        When: get_value called
        Then: Returns first option
        """
        dropdown = LabeledDropdown(
            tk_root,
            label_text="Select",
            options=["First", "Second", "Third"]
        )

        value = dropdown.get_value()

        assert value == "First"

    def test_default_value_when_specified(self, tk_root):
        """
        Given: LabeledDropdown with default_value specified
        When: initialized
        Then: default_value is selected
        """
        dropdown = LabeledDropdown(
            tk_root,
            label_text="Select",
            options=["A", "B", "C"],
            default_value="B"
        )

        value = dropdown.get_value()

        assert value == "B"

    def test_round_trip_set_get_value(self, tk_root):
        """
        Given: LabeledDropdown instance
        When: set_value then get_value called
        Then: Value preserved
        """
        dropdown = LabeledDropdown(
            tk_root,
            label_text="Select",
            options=["Alpha", "Beta", "Gamma"]
        )

        dropdown.set_value("Gamma")
        value = dropdown.get_value()

        assert value == "Gamma"
