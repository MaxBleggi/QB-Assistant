"""
Custom exception hierarchy for file loading errors.

Provides actionable error messages to help users diagnose and fix file loading issues.
"""
from pathlib import Path
from typing import Optional


class FileLoaderError(Exception):
    """Base exception for all file loading errors."""

    def __init__(self, file_path: Path, message: str):
        self.file_path = file_path
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} (file: {self.file_path})"


class UnsupportedFileFormatError(FileLoaderError):
    """Raised when file format is not supported (not CSV or Excel)."""

    def __init__(self, file_path: Path, message: Optional[str] = None):
        if message is None:
            suffix = file_path.suffix.lower()
            message = (
                f"Unsupported file format '{suffix}'. "
                f"Supported formats: .csv, .xlsx. "
                f"Please export your QuickBooks data as CSV or Excel format."
            )
        super().__init__(file_path, message)


class EmptyFileError(FileLoaderError):
    """Raised when file exists but contains no data rows."""

    def __init__(self, file_path: Path, message: Optional[str] = None):
        if message is None:
            message = (
                "File is empty or contains no data rows. "
                "Please ensure the file contains valid QuickBooks data with at least one row."
            )
        super().__init__(file_path, message)


class CorruptedFileError(FileLoaderError):
    """Raised when file cannot be parsed due to corruption or invalid format."""

    def __init__(self, file_path: Path, original_error: Optional[Exception] = None, message: Optional[str] = None):
        self.original_error = original_error

        if message is None:
            message = "File appears to be corrupted or has an invalid structure."
            if original_error:
                message += f" Original error: {str(original_error)}"
            message += " Please try re-exporting from QuickBooks."

        super().__init__(file_path, message)
