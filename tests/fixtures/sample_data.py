"""
Test data fixture utilities for creating sample CSV and Excel files.

Provides factory functions for generating test files with various scenarios
(valid data, missing columns, empty files, wrong types, etc.).
"""
import tempfile
from pathlib import Path
from typing import Dict, Any

import pandas as pd


def create_csv_file(data: Dict[str, Any], file_path: Path = None) -> Path:
    """
    Create a CSV file from dictionary data.

    Args:
        data: Dictionary of column_name -> list_of_values
        file_path: Optional path for the file. If None, creates temp file.

    Returns:
        Path to created CSV file
    """
    df = pd.DataFrame(data)

    if file_path is None:
        # Create temporary file
        temp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        file_path = Path(temp.name)
        temp.close()

    df.to_csv(file_path, index=False)
    return file_path


def create_excel_file(data: Dict[str, Any], file_path: Path = None) -> Path:
    """
    Create an Excel file from dictionary data.

    Args:
        data: Dictionary of column_name -> list_of_values
        file_path: Optional path for the file. If None, creates temp file.

    Returns:
        Path to created Excel file
    """
    df = pd.DataFrame(data)

    if file_path is None:
        # Create temporary file
        temp = tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False)
        file_path = Path(temp.name)
        temp.close()

    df.to_excel(file_path, index=False, engine='openpyxl')
    return file_path


def create_valid_sample() -> Dict[str, Any]:
    """
    Create a valid sample data structure simulating QuickBooks export.

    Returns:
        Dictionary with sample columns and data
    """
    return {
        'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'Account': ['Checking', 'Savings', 'Credit Card'],
        'Amount': [1000.50, 2500.00, -150.75],
        'Description': ['Initial deposit', 'Transfer', 'Payment']
    }


def create_empty_sample() -> Dict[str, Any]:
    """
    Create an empty data structure (no rows).

    Returns:
        Dictionary with column names but no data
    """
    return {
        'Date': [],
        'Account': [],
        'Amount': [],
        'Description': []
    }


def create_missing_columns_sample() -> Dict[str, Any]:
    """
    Create sample data missing some expected columns.

    Returns:
        Dictionary with incomplete column set
    """
    return {
        'Date': ['2025-01-01', '2025-01-02'],
        'Amount': [1000.50, 2500.00],
        # Missing 'Account' and 'Description' columns
    }


def create_wrong_types_sample() -> Dict[str, Any]:
    """
    Create sample data with incorrect data types.

    Returns:
        Dictionary with string data in numeric column
    """
    return {
        'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'Account': ['Checking', 'Savings', 'Credit Card'],
        'Amount': ['not a number', 'invalid', 'bad data'],  # Should be numeric
        'Description': ['Initial deposit', 'Transfer', 'Payment']
    }


def create_ragged_sample() -> Dict[str, Any]:
    """
    Create sample with inconsistent structure (for testing).

    Note: pandas DataFrames handle ragged data by filling with NaN,
    so this creates data with many NaN values to simulate ragged structure.

    Returns:
        Dictionary with inconsistent data
    """
    return {
        'Date': ['2025-01-01', None, '2025-01-03'],
        'Account': ['Checking', None, None],
        'Amount': [1000.50, None, None],
        'Description': ['Initial deposit', None, None]
    }
