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


def create_balance_sheet_sample() -> pd.DataFrame:
    """
    Create a valid QuickBooks Balance Sheet sample.

    Matches real QuickBooks format with:
    - Metadata rows (title, company, date)
    - Column headers
    - All three sections: Assets, Liabilities, Equity
    - Parent accounts with empty values
    - Child accounts with numeric values
    - Total rows with 'Total for X' prefix
    - Mixed currency formats: $2,001.00, 1,201.00, 800.00, -9,905.00
    - Footer with timestamp

    Returns:
        DataFrame with QuickBooks Balance Sheet format
    """
    # Create list of rows matching QuickBooks format
    rows = [
        # Metadata rows (1-3)
        ['Balance Sheet', ''],
        ["Craig's Design and Landscaping Services", ''],
        ['As of December 31, 2025', ''],
        # Blank row
        ['', ''],
        # Column header
        ['Distribution account', 'Total'],
        # Assets section
        ['Assets', ''],
        ['Current Assets', ''],
        ['Bank Accounts', ''],
        ['Checking', '1,201.00'],
        ['Savings', '800.00'],
        ['Total for Bank Accounts', '$2,001.00'],
        ['Other Current Assets', ''],
        ['Undeposited Funds', '2,062.52'],
        ['Total for Other Current Assets', '$2,062.52'],
        ['Total for Current Assets', '$4,063.52'],
        ['Fixed Assets', ''],
        ['Truck', ''],
        ['Original Cost', '13,495.00'],
        ['Total for Truck', '$13,495.00'],
        ['Total for Fixed Assets', '$13,495.00'],
        ['Total for Assets', '$17,558.52'],
        # Liabilities and Equity section
        ['Liabilities and Equity', ''],
        ['Liabilities', ''],
        ['Current Liabilities', ''],
        ['Credit Cards', ''],
        ['Mastercard', '157.72'],
        ['Total for Credit Cards', '$157.72'],
        ['Other Current Liabilities', ''],
        ['Arizona Dept. of Revenue Payable', '0.00'],
        ['Board of Equalization Payable', '209.92'],
        ['Loan Payable', '4,000.00'],
        ['Total for Other Current Liabilities', '$4,209.92'],
        ['Total for Current Liabilities', '$4,367.64'],
        ['Long-term Liabilities', ''],
        ['Notes Payable', '25,000.00'],
        ['Total for Long-term Liabilities', '$25,000.00'],
        ['Total for Liabilities', '$29,367.64'],
        # Equity section
        ['Equity', ''],
        ['Opening Balance Equity', '-9,905.00'],
        ['Retained Earnings', ''],
        ['Net Income', '-1,904.12'],
        ['Total for Equity', '-$11,809.12'],
        ['Total for Liabilities and Equity', '$17,558.52'],
        # Blank rows
        ['', ''],
        ['', ''],
        # Footer
        ['Cash Basis Monday, January 19, 2026 04:25 PM GMTZ', ''],
    ]

    # Create DataFrame
    df = pd.DataFrame(rows)
    return df


def create_malformed_balance_sheet_sample(defect_type: str) -> pd.DataFrame:
    """
    Create malformed Balance Sheet sample with specific defect.

    Args:
        defect_type: Type of defect to introduce. Options:
                    'missing_section' - Remove Equity section
                    'invalid_currency' - Add unparseable currency value
                    'inconsistent_total' - Make total not match sum of children
                    'missing_header' - Remove column header row

    Returns:
        DataFrame with specified defect
    """
    if defect_type == 'missing_section':
        # Create sample without Equity section (but with complete Assets section)
        rows = [
            ['Balance Sheet', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['As of December 31, 2025', ''],
            ['', ''],
            ['Distribution account', 'Total'],
            # Complete Assets section
            ['Assets', ''],
            ['Current Assets', ''],
            ['Bank Accounts', ''],
            ['Checking', '1,201.00'],
            ['Savings', '800.00'],
            ['Total for Bank Accounts', '$2,001.00'],
            ['Other Current Assets', ''],
            ['Undeposited Funds', '2,062.52'],
            ['Total for Other Current Assets', '$2,062.52'],
            ['Total for Current Assets', '$4,063.52'],
            ['Fixed Assets', ''],
            ['Truck', ''],
            ['Original Cost', '13,495.00'],
            ['Total for Truck', '$13,495.00'],
            ['Total for Fixed Assets', '$13,495.00'],
            ['Total for Assets', '$17,558.52'],
            # Liabilities and Equity section (without Equity subsection)
            ['Liabilities and Equity', ''],
            ['Liabilities', ''],
            ['Current Liabilities', ''],
            ['Credit Cards', ''],
            ['Mastercard', '157.72'],
            ['Total for Credit Cards', '$157.72'],
            ['Other Current Liabilities', ''],
            ['Arizona Dept. of Revenue Payable', '0.00'],
            ['Board of Equalization Payable', '209.92'],
            ['Loan Payable', '4,000.00'],
            ['Total for Other Current Liabilities', '$4,209.92'],
            ['Total for Current Liabilities', '$4,367.64'],
            ['Long-term Liabilities', ''],
            ['Notes Payable', '25,000.00'],
            ['Total for Long-term Liabilities', '$25,000.00'],
            ['Total for Liabilities', '$29,367.64'],
            # Missing Equity section - only have Liabilities, no Equity
            ['Total for Liabilities and Equity', '$29,367.64'],
            ['', ''],
            ['Cash Basis Monday, January 19, 2026 04:25 PM GMTZ', ''],
        ]

    elif defect_type == 'invalid_currency':
        # Create sample with invalid currency value
        rows = [
            ['Balance Sheet', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['As of December 31, 2025', ''],
            ['', ''],
            ['Distribution account', 'Total'],
            ['Assets', ''],
            ['Current Assets', ''],
            ['Bank Accounts', ''],
            ['Checking', 'invalid'],  # Invalid currency
            ['Savings', '800.00'],
            ['Total for Bank Accounts', '$2,001.00'],
            ['Total for Current Assets', '$2,001.00'],
            ['Total for Assets', '$2,001.00'],
            ['Liabilities and Equity', ''],
            ['', ''],
            ['Cash Basis Monday, January 19, 2026 04:25 PM GMTZ', ''],
        ]

    elif defect_type == 'inconsistent_total':
        # Create sample where total doesn't match sum
        rows = [
            ['Balance Sheet', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['As of December 31, 2025', ''],
            ['', ''],
            ['Distribution account', 'Total'],
            ['Assets', ''],
            ['Current Assets', ''],
            ['Bank Accounts', ''],
            ['Checking', '1,201.00'],
            ['Savings', '800.00'],
            ['Total for Bank Accounts', '$5,000.00'],  # Wrong total (should be $2,001.00)
            ['Total for Current Assets', '$5,000.00'],
            ['Total for Assets', '$5,000.00'],
            ['Liabilities and Equity', ''],
            ['', ''],
            ['Cash Basis Monday, January 19, 2026 04:25 PM GMTZ', ''],
        ]

    elif defect_type == 'missing_header':
        # Create sample without column header row
        rows = [
            ['Balance Sheet', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['As of December 31, 2025', ''],
            ['', ''],
            # Missing header row
            ['Assets', ''],
            ['Current Assets', ''],
            ['Bank Accounts', ''],
            ['Checking', '1,201.00'],
            ['Total for Bank Accounts', '$1,201.00'],
            ['Total for Current Assets', '$1,201.00'],
            ['Total for Assets', '$1,201.00'],
            ['Liabilities and Equity', ''],
            ['', ''],
            ['Cash Basis Monday, January 19, 2026 04:25 PM GMTZ', ''],
        ]

    else:
        raise ValueError(f"Unknown defect type: {defect_type}")

    return pd.DataFrame(rows)
