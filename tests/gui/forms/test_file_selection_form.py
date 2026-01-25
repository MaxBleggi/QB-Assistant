"""
Unit tests for FileSelectionForm.

Tests file selection, validation, clear selections, and navigation behavior.
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, patch

from src.gui.forms.file_selection_form import FileSelectionForm


@pytest.fixture
def tk_root():
    """Create Tk root for GUI tests."""
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def mock_parent(tk_root):
    """Create mock parent with required attributes and methods."""
    parent = tk_root
    parent.get_config_manager = Mock()
    parent.show_form = Mock()

    # Initialize file path attributes to None
    parent.selected_balance_sheet = None
    parent.selected_profit_loss = None
    parent.selected_cash_flow = None
    parent.selected_historical_data = None

    return parent


@pytest.fixture
def form(mock_parent):
    """Create FileSelectionForm instance."""
    return FileSelectionForm(mock_parent)


class TestInitialState:
    """Test suite for initial form state."""

    def test_initial_state(self, form):
        """
        Given: FileSelectionForm is displayed
        When: No files are selected
        Then: All filename labels show 'No file selected' and proceed button is disabled
        """
        assert form.balance_sheet_label.cget('text') == 'No file selected'
        assert form.profit_loss_label.cget('text') == 'No file selected'
        assert form.cash_flow_label.cget('text') == 'No file selected'
        assert form.historical_data_label.cget('text') == 'No file selected'
        assert form.proceed_btn.cget('state') == 'disabled'


class TestFileSelection:
    """Test suite for individual file selection."""

    @patch('tkinter.filedialog.askopenfilename')
    def test_select_balance_sheet_file(self, mock_filedialog, form, mock_parent):
        """
        Given: User clicks Balance Sheet browse button
        When: User selects /test/balance_sheet.xlsx in file dialog
        Then: App.selected_balance_sheet is set to full path and filename label shows 'balance_sheet.xlsx'
        """
        mock_filedialog.return_value = '/test/balance_sheet.xlsx'

        form._on_browse_balance_sheet()

        assert mock_parent.selected_balance_sheet == '/test/balance_sheet.xlsx'
        assert form.balance_sheet_label.cget('text') == 'balance_sheet.xlsx'

    @patch('tkinter.filedialog.askopenfilename')
    def test_select_profit_loss_file(self, mock_filedialog, form, mock_parent):
        """
        Given: User clicks Profit & Loss browse button
        When: User selects /test/profit_loss.xlsx in file dialog
        Then: App.selected_profit_loss is set to full path and filename label shows 'profit_loss.xlsx'
        """
        mock_filedialog.return_value = '/test/profit_loss.xlsx'

        form._on_browse_profit_loss()

        assert mock_parent.selected_profit_loss == '/test/profit_loss.xlsx'
        assert form.profit_loss_label.cget('text') == 'profit_loss.xlsx'

    @patch('tkinter.filedialog.askopenfilename')
    def test_select_cash_flow_file(self, mock_filedialog, form, mock_parent):
        """
        Given: User clicks Cash Flow browse button
        When: User selects /test/cash_flow.xlsx in file dialog
        Then: App.selected_cash_flow is set to full path and filename label shows 'cash_flow.xlsx'
        """
        mock_filedialog.return_value = '/test/cash_flow.xlsx'

        form._on_browse_cash_flow()

        assert mock_parent.selected_cash_flow == '/test/cash_flow.xlsx'
        assert form.cash_flow_label.cget('text') == 'cash_flow.xlsx'

    @patch('tkinter.filedialog.askopenfilename')
    def test_select_historical_data_file(self, mock_filedialog, form, mock_parent):
        """
        Given: User clicks Historical Data browse button
        When: User selects /test/historical.csv in file dialog
        Then: App.selected_historical_data is set to full path and filename label shows 'historical.csv'
        """
        mock_filedialog.return_value = '/test/historical.csv'

        form._on_browse_historical_data()

        assert mock_parent.selected_historical_data == '/test/historical.csv'
        assert form.historical_data_label.cget('text') == 'historical.csv'

    @patch('tkinter.filedialog.askopenfilename')
    def test_cancel_filedialog_does_not_update_state(self, mock_filedialog, form, mock_parent):
        """
        Given: User clicks browse button
        When: User cancels file dialog (returns empty string)
        Then: State unchanged and label remains 'No file selected'
        """
        mock_filedialog.return_value = ''

        form._on_browse_balance_sheet()

        assert mock_parent.selected_balance_sheet is None
        assert form.balance_sheet_label.cget('text') == 'No file selected'


class TestValidation:
    """Test suite for file selection validation."""

    @patch('tkinter.filedialog.askopenfilename')
    def test_all_files_selected_enables_proceed(self, mock_filedialog, form, mock_parent):
        """
        Given: User has selected all 4 files
        When: _validate_selections() is called after 4th file
        Then: Proceed button becomes enabled with blue styling
        """
        # Select all 4 files
        mock_filedialog.return_value = '/test/balance_sheet.xlsx'
        form._on_browse_balance_sheet()

        mock_filedialog.return_value = '/test/profit_loss.xlsx'
        form._on_browse_profit_loss()

        mock_filedialog.return_value = '/test/cash_flow.xlsx'
        form._on_browse_cash_flow()

        mock_filedialog.return_value = '/test/historical.csv'
        form._on_browse_historical_data()

        # Verify proceed button enabled
        assert form.proceed_btn.cget('state') == 'normal'
        assert form.proceed_btn.cget('bg') == '#2196F3'

    @patch('tkinter.filedialog.askopenfilename')
    def test_three_files_selected_keeps_proceed_disabled(self, mock_filedialog, form):
        """
        Given: User has selected only 3 files
        When: _validate_selections() is called
        Then: Proceed button remains disabled
        """
        # Select only 3 files
        mock_filedialog.return_value = '/test/balance_sheet.xlsx'
        form._on_browse_balance_sheet()

        mock_filedialog.return_value = '/test/profit_loss.xlsx'
        form._on_browse_profit_loss()

        mock_filedialog.return_value = '/test/cash_flow.xlsx'
        form._on_browse_cash_flow()

        # Verify proceed button still disabled
        assert form.proceed_btn.cget('state') == 'disabled'


class TestClearSelections:
    """Test suite for clear selections functionality."""

    @patch('tkinter.filedialog.askopenfilename')
    def test_clear_selections_resets_state(self, mock_filedialog, form, mock_parent):
        """
        Given: User has selected some files
        When: User clicks Clear Selections button
        Then: All 4 App file attributes reset to None and labels show 'No file selected'
        """
        # Select 2 files first
        mock_filedialog.return_value = '/test/balance_sheet.xlsx'
        form._on_browse_balance_sheet()

        mock_filedialog.return_value = '/test/profit_loss.xlsx'
        form._on_browse_profit_loss()

        # Clear selections
        form._on_clear_selections()

        # Verify all attributes reset
        assert mock_parent.selected_balance_sheet is None
        assert mock_parent.selected_profit_loss is None
        assert mock_parent.selected_cash_flow is None
        assert mock_parent.selected_historical_data is None

        # Verify labels reset
        assert form.balance_sheet_label.cget('text') == 'No file selected'
        assert form.profit_loss_label.cget('text') == 'No file selected'
        assert form.cash_flow_label.cget('text') == 'No file selected'
        assert form.historical_data_label.cget('text') == 'No file selected'

        # Verify proceed button disabled
        assert form.proceed_btn.cget('state') == 'disabled'


class TestNavigation:
    """Test suite for navigation to MainMenuForm."""

    @patch('tkinter.filedialog.askopenfilename')
    def test_proceed_navigates_to_main_menu(self, mock_filedialog, form, mock_parent):
        """
        Given: All 4 files are selected and proceed button is clicked
        When: _on_proceed() is called
        Then: parent.show_form called with MainMenuForm
        """
        # Select all 4 files
        mock_filedialog.return_value = '/test/balance_sheet.xlsx'
        form._on_browse_balance_sheet()

        mock_filedialog.return_value = '/test/profit_loss.xlsx'
        form._on_browse_profit_loss()

        mock_filedialog.return_value = '/test/cash_flow.xlsx'
        form._on_browse_cash_flow()

        mock_filedialog.return_value = '/test/historical.csv'
        form._on_browse_historical_data()

        # Click proceed
        form._on_proceed()

        # Verify navigation
        from src.gui.forms.main_menu_form import MainMenuForm
        mock_parent.show_form.assert_called_once()
        assert mock_parent.show_form.call_args[0][0] == MainMenuForm

    def test_proceed_without_all_files_shows_error(self, form, mock_parent):
        """
        Given: Proceed button clicked but validation fails (not all files selected)
        When: _on_proceed() is called
        Then: Status label shows error message and navigation does not occur
        """
        # Don't select any files, call proceed directly (edge case)
        form._on_proceed()

        # Verify error shown
        assert 'Please select all 4 required files' in form.status_label.cget('text')

        # Verify no navigation
        mock_parent.show_form.assert_not_called()


class TestMainMenuNavigation:
    """Test suite for MainMenuForm navigation button."""

    def test_main_menu_navigation_button(self, tk_root):
        """
        Given: MainMenuForm is displayed
        When: User clicks 'Select Input Files' button
        Then: FileSelectionForm is displayed via parent.show_form()
        """
        from src.gui.forms.main_menu_form import MainMenuForm

        # Create mock parent
        parent = tk_root
        parent.get_config_manager = Mock()
        parent.get_global_config = Mock()
        parent.show_form = Mock()
        parent.selected_client = "TestClient"

        # Mock global config
        mock_global_config = Mock()
        mock_global_config.forecast_horizon = 6
        parent.get_global_config.return_value = mock_global_config

        # Create MainMenuForm
        main_menu = MainMenuForm(parent)

        # Call file selection navigation
        main_menu._on_file_selection()

        # Verify navigation
        parent.show_form.assert_called_once()
        assert parent.show_form.call_args[0][0] == FileSelectionForm
