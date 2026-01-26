"""
FileLoader for automatic CSV/Excel file detection and loading.

Uses pandas for format-agnostic data loading with comprehensive error handling.
"""
from pathlib import Path
from typing import Union

import pandas as pd

from .exceptions import (
    CorruptedFileError,
    EmptyFileError,
    UnsupportedFileFormatError,
)


class FileLoader:
    """
    Loads CSV and Excel files with automatic format detection.

    Detects file format based on extension and delegates to appropriate pandas reader.
    Provides comprehensive error handling for common failure modes.
    """

    SUPPORTED_FORMATS = {'.csv', '.xlsx'}

    def load(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load file and return pandas DataFrame.

        Args:
            file_path: Path to CSV or Excel file (absolute or relative)

        Returns:
            pandas DataFrame containing file data

        Raises:
            FileNotFoundError: If file does not exist
            UnsupportedFileFormatError: If file format is not CSV or Excel
            EmptyFileError: If file exists but contains no data rows
            CorruptedFileError: If file cannot be parsed
        """
        # Convert to Path for consistent handling
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check format is supported
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise UnsupportedFileFormatError(path)

        # Load based on format
        try:
            if suffix == '.csv':
                # Try standard CSV reading first
                try:
                    df = pd.read_csv(path)
                except pd.errors.ParserError as e:
                    # If error is about mismatched field counts (QuickBooks CSVs have variable columns),
                    # retry with forced column count to handle variable-width rows
                    if "Expected" in str(e) and "saw" in str(e):
                        # Extract the maximum column count from error message
                        # Error format: "Expected X fields in line Y, saw Z"
                        import re
                        match = re.search(r'saw (\d+)', str(e))
                        if match:
                            max_cols = int(match.group(1))
                            # Generate column names for the maximum width
                            column_names = [f'col_{i}' for i in range(max_cols)]
                            # Read with forced columns - short rows will be padded with NaN
                            df = pd.read_csv(path, header=None, names=column_names)
                        else:
                            raise
                    else:
                        raise
            elif suffix == '.xlsx':
                df = pd.read_excel(path, engine='openpyxl')
            else:
                # Should never reach here due to format check above
                raise UnsupportedFileFormatError(path)

        except pd.errors.EmptyDataError as e:
            raise CorruptedFileError(path, original_error=e)
        except pd.errors.ParserError as e:
            # Re-raise ParserError that wasn't handled above
            raise CorruptedFileError(path, original_error=e)
        except Exception as e:
            # Catch other pandas exceptions (malformed Excel, etc.)
            if "corrupted" in str(e).lower() or "invalid" in str(e).lower():
                raise CorruptedFileError(path, original_error=e)
            # Re-raise unexpected exceptions
            raise

        # Check for empty data
        if df.empty:
            raise EmptyFileError(path)

        return df
