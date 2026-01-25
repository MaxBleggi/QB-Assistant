"""
ErrorMapper utility for translating technical exceptions to user-friendly error messages.

Provides centralized mapping from exception types to actionable error dialogs that
help users understand what went wrong and how to fix it.
"""
from typing import Tuple

from ..loaders.exceptions import FileLoaderError
from ..metrics.exceptions import CalculationError


class ErrorMapper:
    """
    Static utility for mapping exceptions to user-friendly error messages.

    Handles both custom exceptions (FileLoaderError, CalculationError hierarchies)
    which have built-in user-friendly messages, and stdlib exceptions which need
    custom context-specific messages.
    """

    @staticmethod
    def get_user_friendly_message(exception: Exception) -> Tuple[str, str]:
        """
        Translate exception to user-friendly error dialog title and message.

        Custom exceptions (FileLoaderError, CalculationError) have built-in
        user-friendly messages that are extracted. Stdlib exceptions get
        context-specific messages with actionable guidance.

        Args:
            exception: Exception instance to translate

        Returns:
            Tuple of (title, message) for error dialog display
        """
        # Custom exception hierarchies - extract built-in messages
        if isinstance(exception, FileLoaderError):
            return ("File Loading Error", str(exception))

        if isinstance(exception, CalculationError):
            return ("Calculation Error", str(exception))

        # Stdlib exceptions - provide custom context-specific messages
        if isinstance(exception, FileNotFoundError):
            file_path = str(exception).split("'")[1] if "'" in str(exception) else "unknown"
            message = (
                f"Could not find file: {file_path}\n\n"
                f"Please check the file path and ensure the file exists.\n"
                f"Tip: Use the 'Select Input Files' button to choose the correct file."
            )
            return ("File Not Found", message)

        if isinstance(exception, ValueError):
            # ValueError often occurs during parsing - provide format guidance
            error_detail = str(exception)
            message = (
                f"Data format error: {error_detail}\n\n"
                f"This usually indicates invalid data in your input files.\n"
                f"Please check:\n"
                f"  - Date formats are consistent (MM/DD/YYYY)\n"
                f"  - Numeric values don't contain invalid characters\n"
                f"  - All required columns are present\n\n"
                f"Tip: Re-export from QuickBooks if data appears corrupted."
            )
            return ("Data Format Error", message)

        if isinstance(exception, KeyError):
            # KeyError during processing means missing required data field
            missing_key = str(exception).strip("'\"")
            message = (
                f"Missing required data field: {missing_key}\n\n"
                f"This field is required for processing but was not found in your data.\n"
                f"Please ensure your input files contain all required sections:\n"
                f"  - Balance Sheet: Assets, Liabilities, Equity\n"
                f"  - P&L: Revenue, Expenses, Net Income\n"
                f"  - Cash Flow: Operating, Investing, Financing activities\n\n"
                f"Tip: Use QuickBooks standard report templates to ensure all required fields are included."
            )
            return ("Missing Required Data", message)

        # Generic fallback for unexpected exceptions
        exception_type = type(exception).__name__
        error_detail = str(exception)
        message = (
            f"An unexpected error occurred during processing:\n\n"
            f"{exception_type}: {error_detail}\n\n"
            f"This is an unexpected error that should not normally occur.\n"
            f"Please check the console output for detailed technical information.\n\n"
            f"Tip: If this error persists, try:\n"
            f"  1. Re-exporting your data from QuickBooks\n"
            f"  2. Verifying all input files are valid\n"
            f"  3. Restarting the application"
        )
        return ("Processing Error", message)
