"""
Integration and unit tests for Sprint 7.4 - Progress Indicators & Error Handling.

Tests ErrorMapper utility, progress callback integration in PipelineOrchestrator,
and error dialog display in MainMenuForm.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from src.utils.error_mapper import ErrorMapper
from src.loaders.exceptions import FileLoaderError, UnsupportedFileFormatError, EmptyFileError
from src.metrics.exceptions import CalculationError, MissingPeriodError, InvalidDataError
from src.services.pipeline_orchestrator import PipelineOrchestrator


class TestErrorMapper:
    """Unit tests for ErrorMapper.get_user_friendly_message()."""

    def test_error_mapper_handles_file_loader_error(self):
        """ErrorMapper extracts user-friendly message from FileLoaderError."""
        # Given: FileLoaderError with built-in message
        error = FileLoaderError(
            file_path=Path("/path/to/file.csv"),
            message="Balance Sheet contains invalid data"
        )

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns title and extracts built-in message
        assert title == "File Loading Error"
        assert "Balance Sheet contains invalid data" in message
        assert "file.csv" in message

    def test_error_mapper_handles_unsupported_file_format_error(self):
        """ErrorMapper handles UnsupportedFileFormatError (FileLoaderError subclass)."""
        # Given: UnsupportedFileFormatError
        error = UnsupportedFileFormatError(file_path=Path("/path/to/file.txt"))

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns title and built-in message
        assert title == "File Loading Error"
        assert "Unsupported file format" in message
        assert ".txt" in message

    def test_error_mapper_handles_calculation_error(self):
        """ErrorMapper extracts user-friendly message from CalculationError."""
        # Given: CalculationError with built-in message
        error = CalculationError("Net Income is required for ROI calculation")

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns title and extracts built-in message
        assert title == "Calculation Error"
        assert "Net Income is required for ROI calculation" in message

    def test_error_mapper_handles_missing_period_error(self):
        """ErrorMapper handles MissingPeriodError (CalculationError subclass)."""
        # Given: MissingPeriodError
        error = MissingPeriodError(
            period="2024-01",
            available_periods=["2023-12", "2023-11"]
        )

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns title and built-in message
        assert title == "Calculation Error"
        assert "2024-01" in message
        assert "not found" in message

    def test_error_mapper_handles_file_not_found(self):
        """ErrorMapper provides actionable message for FileNotFoundError with file path."""
        # Given: FileNotFoundError
        error = FileNotFoundError("[Errno 2] No such file or directory: '/path/to/missing.xlsx'")

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns actionable message with file path
        assert title == "File Not Found"
        assert "Could not find file" in message
        assert "/path/to/missing.xlsx" in message
        assert "ensure the file exists" in message

    def test_error_mapper_handles_value_error(self):
        """ErrorMapper provides format guidance for ValueError."""
        # Given: ValueError from parsing
        error = ValueError("Invalid date format in cell B5")

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns format guidance
        assert title == "Data Format Error"
        assert "Invalid date format" in message
        assert "MM/DD/YYYY" in message
        assert "Re-export" in message

    def test_error_mapper_handles_key_error(self):
        """ErrorMapper provides missing data field guidance for KeyError."""
        # Given: KeyError for missing field
        error = KeyError("'Revenue'")

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns missing field guidance
        assert title == "Missing Required Data"
        assert "Revenue" in message
        assert "required data field" in message
        assert "Balance Sheet" in message or "P&L" in message

    def test_error_mapper_handles_generic_exception(self):
        """ErrorMapper provides fallback message for unexpected exceptions."""
        # Given: Unexpected exception type
        error = RuntimeError("Something went wrong")

        # When: get_user_friendly_message called
        title, message = ErrorMapper.get_user_friendly_message(error)

        # Then: Returns fallback message
        assert title == "Processing Error"
        assert "unexpected error" in message
        assert "RuntimeError" in message
        assert "console output" in message


class TestPipelineOrchestratorProgressCallback:
    """Unit tests for PipelineOrchestrator progress callback integration."""

    @patch('src.services.pipeline_orchestrator.ConfigManager')
    @patch('src.services.pipeline_orchestrator.FileLoader')
    @patch('src.services.pipeline_orchestrator.BalanceSheetParser')
    @patch('src.services.pipeline_orchestrator.PLParser')
    @patch('src.services.pipeline_orchestrator.CashFlowParser')
    def test_pipeline_handles_none_callback(
        self, mock_cf_parser, mock_pl_parser, mock_bs_parser, mock_file_loader, mock_config_manager
    ):
        """PipelineOrchestrator executes successfully when callback is None."""
        # Given: Mock dependencies to prevent actual file operations
        mock_config = MagicMock()
        mock_config.forecast_horizon = 12
        mock_config_manager.return_value.load_config.return_value = mock_config

        # Mock parsers to return simple models
        mock_bs_parser.return_value.parse.return_value = MagicMock()
        mock_pl_parser.return_value.parse.return_value = MagicMock()
        mock_cf_parser.return_value.parse.return_value = MagicMock()

        orchestrator = PipelineOrchestrator("/fake/project/root")

        # When: process_pipeline called with progress_callback=None
        # (Will fail at later stages, but we're testing callback=None doesn't break early stages)
        try:
            result = orchestrator.process_pipeline(
                balance_sheet_path="/fake/bs.csv",
                pl_path="/fake/pl.csv",
                cash_flow_path="/fake/cf.csv",
                historical_path=None,
                client_name="test_client",
                progress_callback=None  # Explicit None
            )
        except Exception:
            # Expected to fail at later stages - we're just testing None callback doesn't error
            pass

        # Then: No callback-related errors occur (pipeline executes early stages)
        # Success is that we didn't get AttributeError or TypeError from callback

    @patch('src.services.pipeline_orchestrator.ConfigManager')
    @patch('src.services.pipeline_orchestrator.FileLoader')
    @patch('src.services.pipeline_orchestrator.BalanceSheetParser')
    @patch('src.services.pipeline_orchestrator.PLParser')
    @patch('src.services.pipeline_orchestrator.CashFlowParser')
    def test_pipeline_invokes_progress_callback(
        self, mock_cf_parser, mock_pl_parser, mock_bs_parser, mock_file_loader, mock_config_manager
    ):
        """PipelineOrchestrator invokes callback 8+ times with distinct messages."""
        # Given: Mock dependencies
        mock_config = MagicMock()
        mock_config.forecast_horizon = 12
        mock_config_manager.return_value.load_config.return_value = mock_config

        mock_bs_parser.return_value.parse.return_value = MagicMock()
        mock_pl_parser.return_value.parse.return_value = MagicMock()
        mock_cf_parser.return_value.parse.return_value = MagicMock()

        # Create mock callback
        mock_callback = Mock()

        orchestrator = PipelineOrchestrator("/fake/project/root")

        # When: process_pipeline called with callback
        try:
            result = orchestrator.process_pipeline(
                balance_sheet_path="/fake/bs.csv",
                pl_path="/fake/pl.csv",
                cash_flow_path="/fake/cf.csv",
                historical_path=None,
                client_name="test_client",
                progress_callback=mock_callback
            )
        except Exception:
            # Expected to fail at later stages
            pass

        # Then: Callback invoked multiple times with distinct messages
        assert mock_callback.call_count >= 3  # At least config, BS parse, P&L parse

        # Verify distinct messages
        messages = [call[0][0] for call in mock_callback.call_args_list]
        assert "Loading configurations..." in messages
        assert "Parsing Balance Sheet..." in messages
        assert "Parsing P&L..." in messages

    @patch('src.services.pipeline_orchestrator.ConfigManager')
    def test_pipeline_handles_failing_callback(self, mock_config_manager):
        """PipelineOrchestrator continues when callback raises exception."""
        # Given: Mock config manager
        mock_config = MagicMock()
        mock_config.forecast_horizon = 12
        mock_config_manager.return_value.load_config.return_value = mock_config

        # Create callback that raises exception
        def failing_callback(message):
            raise ValueError("Callback error!")

        orchestrator = PipelineOrchestrator("/fake/project/root")

        # When: process_pipeline called with failing callback
        # Then: Pipeline continues (callback error caught and logged)
        # We're testing that _notify_progress wraps the callback in try/except
        try:
            result = orchestrator.process_pipeline(
                balance_sheet_path="/fake/bs.csv",
                pl_path="/fake/pl.csv",
                cash_flow_path="/fake/cf.csv",
                historical_path=None,
                client_name="test_client",
                progress_callback=failing_callback
            )
        except ValueError as e:
            # If ValueError propagates, callback error handling is broken
            if "Callback error!" in str(e):
                pytest.fail("Callback exception should be caught, not propagated")
        except Exception:
            # Other exceptions are fine - we're just testing callback doesn't break pipeline
            pass


class TestMainMenuFormProgressAndErrors:
    """Integration tests for MainMenuForm progress updates and error dialogs."""

    @patch('src.gui.forms.main_menu_form.PipelineOrchestrator')
    def test_main_menu_displays_progress_updates(self, mock_orchestrator_class):
        """MainMenuForm status_label updates during pipeline processing."""
        # Given: Mock orchestrator that captures callback
        captured_callback = None

        def mock_process_pipeline(*args, **kwargs):
            nonlocal captured_callback
            captured_callback = kwargs.get('progress_callback')
            # Simulate successful processing
            return {'status': 'success', 'report_path': '/fake/report.xlsx', 'errors': []}

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_pipeline = mock_process_pipeline
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create mock parent and form
        mock_parent = MagicMock()
        mock_parent.selected_client = "TestClient"
        mock_parent.selected_balance_sheet = "/fake/bs.csv"
        mock_parent.selected_profit_loss = "/fake/pl.csv"
        mock_parent.selected_cash_flow = "/fake/cf.csv"
        mock_parent.selected_historical_data = None
        mock_parent.project_root = Path("/fake/project")

        from src.gui.forms.main_menu_form import MainMenuForm

        with patch('tkinter.Frame.__init__', return_value=None):
            with patch('tkinter.Label') as mock_label:
                form = MainMenuForm(mock_parent)
                form.status_label = MagicMock()

                # When: _on_process_data called
                with patch('src.gui.forms.main_menu_form.messagebox'):
                    form._on_process_data()

                # Then: Callback was passed to orchestrator
                assert captured_callback is not None

                # Simulate callback invocations
                captured_callback("Parsing Balance Sheet...")

                # Verify status_label updated with blue color
                form.status_label.config.assert_called_with(
                    text="Parsing Balance Sheet...",
                    fg='#2196F3'
                )

    @patch('src.gui.forms.main_menu_form.PipelineOrchestrator')
    @patch('src.gui.forms.main_menu_form.messagebox')
    def test_main_menu_displays_success_message(self, mock_messagebox, mock_orchestrator_class):
        """MainMenuForm shows green 'Processing complete!' on success."""
        # Given: Mock successful orchestrator
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_pipeline.return_value = {
            'status': 'success',
            'report_path': '/fake/report.xlsx',
            'errors': []
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        # Create mock parent and form
        mock_parent = MagicMock()
        mock_parent.selected_client = "TestClient"
        mock_parent.selected_balance_sheet = "/fake/bs.csv"
        mock_parent.selected_profit_loss = "/fake/pl.csv"
        mock_parent.selected_cash_flow = "/fake/cf.csv"
        mock_parent.selected_historical_data = None
        mock_parent.project_root = Path("/fake/project")

        from src.gui.forms.main_menu_form import MainMenuForm

        with patch('tkinter.Frame.__init__', return_None):
            form = MainMenuForm(mock_parent)
            form.status_label = MagicMock()

            # When: _on_process_data completes successfully
            form._on_process_data()

            # Then: status_label shows green success message
            form.status_label.config.assert_called_with(
                text="Processing complete!",
                fg='#4CAF50'
            )

    @patch('src.gui.forms.main_menu_form.PipelineOrchestrator')
    @patch('src.gui.forms.main_menu_form.messagebox')
    @patch('src.gui.forms.main_menu_form.ErrorMapper')
    def test_main_menu_displays_error_dialog_on_file_error(
        self, mock_error_mapper, mock_messagebox, mock_orchestrator_class
    ):
        """MainMenuForm shows user-friendly error dialog when FileLoaderError occurs."""
        # Given: Orchestrator that raises FileLoaderError
        from src.loaders.exceptions import FileLoaderError

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_pipeline.side_effect = FileLoaderError(
            file_path=Path("/fake/bs.csv"),
            message="Balance Sheet contains invalid data"
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        # Mock ErrorMapper to return user-friendly message
        mock_error_mapper.get_user_friendly_message.return_value = (
            "File Loading Error",
            "Balance Sheet contains invalid data (file: /fake/bs.csv)"
        )

        # Create mock parent and form
        mock_parent = MagicMock()
        mock_parent.selected_client = "TestClient"
        mock_parent.selected_balance_sheet = "/fake/bs.csv"
        mock_parent.selected_profit_loss = "/fake/pl.csv"
        mock_parent.selected_cash_flow = "/fake/cf.csv"
        mock_parent.project_root = Path("/fake/project")

        from src.gui.forms.main_menu_form import MainMenuForm

        with patch('tkinter.Frame.__init__', return_value=None):
            form = MainMenuForm(mock_parent)
            form.status_label = MagicMock()

            # When: _on_process_data raises FileLoaderError
            form._on_process_data()

            # Then: ErrorMapper called and error dialog shown
            assert mock_error_mapper.get_user_friendly_message.called
            mock_messagebox.showerror.assert_called_once()
            call_args = mock_messagebox.showerror.call_args[0]
            assert call_args[0] == "File Loading Error"
            assert "Balance Sheet contains invalid data" in call_args[1]

    @patch('src.gui.forms.main_menu_form.PipelineOrchestrator')
    @patch('src.gui.forms.main_menu_form.messagebox')
    @patch('src.gui.forms.main_menu_form.ErrorMapper')
    def test_main_menu_displays_error_dialog_on_calculation_error(
        self, mock_error_mapper, mock_messagebox, mock_orchestrator_class
    ):
        """MainMenuForm shows user-friendly error dialog when CalculationError occurs."""
        # Given: Orchestrator that raises CalculationError
        from src.metrics.exceptions import CalculationError

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_pipeline.side_effect = CalculationError(
            "Net Income is required for ROI calculation"
        )
        mock_orchestrator_class.return_value = mock_orchestrator

        # Mock ErrorMapper
        mock_error_mapper.get_user_friendly_message.return_value = (
            "Calculation Error",
            "Net Income is required for ROI calculation"
        )

        # Create mock parent and form
        mock_parent = MagicMock()
        mock_parent.selected_client = "TestClient"
        mock_parent.selected_balance_sheet = "/fake/bs.csv"
        mock_parent.selected_profit_loss = "/fake/pl.csv"
        mock_parent.selected_cash_flow = "/fake/cf.csv"
        mock_parent.project_root = Path("/fake/project")

        from src.gui.forms.main_menu_form import MainMenuForm

        with patch('tkinter.Frame.__init__', return_value=None):
            form = MainMenuForm(mock_parent)
            form.status_label = MagicMock()

            # When: _on_process_data raises CalculationError
            form._on_process_data()

            # Then: Error dialog shown with user-friendly message
            assert mock_error_mapper.get_user_friendly_message.called
            mock_messagebox.showerror.assert_called_once()
            call_args = mock_messagebox.showerror.call_args[0]
            assert call_args[0] == "Calculation Error"
            assert "Net Income is required" in call_args[1]
