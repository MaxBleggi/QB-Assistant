"""
BalanceSheetParser - Two-pass parser for QuickBooks Balance Sheet CSV exports.

Key insight: QuickBooks format has NO visual indentation. Hierarchy is inferred from:
- Section markers: 'Assets', 'Liabilities and Equity' (empty value)
- Parent accounts: account name with empty value (not starting with 'Total for')
- Child accounts: account name with numeric value
- Total rows: account name starting with 'Total for X'

Two-pass approach:
1. _parse_raw_data(): Extract metadata DataFrame (account_name, raw_value, row_type)
2. _build_hierarchy(): Construct tree from metadata patterns
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Union

import pandas as pd

from ..loaders.file_loader import FileLoader
from ..models.balance_sheet import BalanceSheetModel


class BalanceSheetParser:
    """
    Parser for QuickBooks Balance Sheet CSV exports.

    Uses two-pass approach to separate data extraction from hierarchy construction,
    enabling independent testing and better error diagnostics.
    """

    # Known section markers in QuickBooks Balance Sheet
    # Only top-level sections - subsections like 'Current Assets' are parent accounts
    SECTION_MARKERS = {
        'Assets',
        'Liabilities and Equity',
        'Liabilities',
        'Equity'
    }

    # Footer pattern to detect and skip
    FOOTER_PATTERN = re.compile(r'Cash Basis.*GMT', re.IGNORECASE)

    def __init__(self, file_loader: FileLoader):
        """
        Initialize parser with FileLoader dependency.

        Args:
            file_loader: FileLoader instance for file I/O
        """
        self.file_loader = file_loader

    def parse(self, file_path: Union[str, Path]) -> BalanceSheetModel:
        """
        Parse Balance Sheet file and return BalanceSheetModel.

        Process:
        1. Load file via FileLoader
        2. Skip metadata rows (1-3) and footer
        3. Extract raw metadata (first pass)
        4. Build hierarchy tree (second pass)
        5. Return BalanceSheetModel with both DataFrame and hierarchy

        Args:
            file_path: Path to Balance Sheet CSV file

        Returns:
            BalanceSheetModel with raw DataFrame and hierarchy tree

        Raises:
            ValueError: If file structure is invalid (missing sections, malformed data)
        """
        # Load file
        df = self.file_loader.load(file_path)

        # Skip metadata rows (first 3 rows: title, company, date range)
        # Row 4 is typically blank, row 5 is column headers
        if len(df) < 5:
            raise ValueError(f"File too short - expected at least 5 rows, got {len(df)}")

        # Start from row 5 (index 4) which should be the column header
        df = df.iloc[2:].reset_index(drop=True)

        # Set column names (should be 'Distribution account', 'Total')
        if len(df.columns) < 2:
            raise ValueError(f"Expected at least 2 columns, got {len(df.columns)}")

        df.columns = ['account_name', 'value']

        # Skip the header row (index 0 after reset)
        df = df.iloc[1:].reset_index(drop=True)

        # Skip footer rows (detect timestamp pattern)
        clean_rows = []
        for idx, row in df.iterrows():
            account_name = str(row['account_name']).strip()
            # Skip empty rows and footer
            if not account_name or account_name.lower() == 'nan':
                continue
            if self.FOOTER_PATTERN.search(account_name):
                break  # Footer found, stop processing
            clean_rows.append(row)

        if not clean_rows:
            raise ValueError("No valid data rows found after skipping metadata and footer")

        df_clean = pd.DataFrame(clean_rows).reset_index(drop=True)

        # First pass: extract raw metadata
        metadata_df = self._parse_raw_data(df_clean)

        # Validate required sections exist
        self._validate_sections(metadata_df)

        # Second pass: build hierarchy tree
        hierarchy = self._build_hierarchy(metadata_df)

        # Return model with both raw DataFrame and hierarchy
        return BalanceSheetModel(df=metadata_df, hierarchy=hierarchy)

    def _parse_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        First pass: Extract metadata from raw DataFrame.

        For each row, determine:
        - account_name: The account/section name
        - raw_value: The value as string (to preserve formatting)
        - numeric_value: Parsed numeric value (None for non-numeric)
        - row_type: section/parent/child/total

        Args:
            df: Raw DataFrame with 'account_name' and 'value' columns

        Returns:
            DataFrame with metadata columns
        """
        rows = []

        for idx, row in df.iterrows():
            account_name = str(row['account_name']).strip()
            raw_value = str(row['value']).strip() if pd.notna(row['value']) else ''

            # Detect row type
            row_type = self._detect_row_type(account_name, raw_value)

            # Parse numeric value
            numeric_value = None
            if raw_value and raw_value.lower() != 'nan':
                try:
                    numeric_value = self._clean_currency(raw_value)
                except ValueError:
                    # Not a valid number - likely a section or parent
                    pass

            rows.append({
                'account_name': account_name,
                'raw_value': raw_value,
                'numeric_value': numeric_value,
                'row_type': row_type
            })

        return pd.DataFrame(rows)

    def _detect_row_type(self, account_name: str, raw_value: str) -> str:
        """
        Detect row type from account name and value patterns.

        Rules:
        - Section: account_name in SECTION_MARKERS AND empty value
        - Total: account_name starts with 'Total for '
        - Parent: empty value AND not a section AND not a total
        - Child: has numeric value

        Args:
            account_name: The account/section name
            raw_value: The raw value string

        Returns:
            Row type: 'section', 'parent', 'child', or 'total'
        """
        # Check if it's a total row
        if account_name.startswith('Total for '):
            return 'total'

        # Check if value is empty or nan
        is_empty_value = not raw_value or raw_value.lower() == 'nan'

        # Check if it's a section marker
        if account_name in self.SECTION_MARKERS and is_empty_value:
            return 'section'

        # If value is empty, it's a parent account
        if is_empty_value:
            return 'parent'

        # Has value, so it's a child account
        return 'child'

    def _clean_currency(self, value: str) -> float:
        """
        Clean currency string and convert to float.

        Handles formats: $2,001.00, 1,201.00, 800.00, -9,905.00
        Uses regex to strip currency symbols and commas, then float() conversion.
        Never uses eval() for security.

        Args:
            value: Currency string to clean

        Returns:
            Float value

        Raises:
            ValueError: If value cannot be parsed as numeric
        """
        # Strip whitespace
        cleaned = value.strip()

        # Remove dollar signs and commas using regex
        cleaned = re.sub(r'[$,]', '', cleaned)

        # Convert to float
        try:
            return float(cleaned)
        except ValueError:
            raise ValueError(f"Cannot parse currency value: {value}")

    def _validate_sections(self, df: pd.DataFrame) -> None:
        """
        Validate that required sections exist in the DataFrame.

        Required sections: Assets, Liabilities (or Liabilities and Equity), Equity

        Args:
            df: Metadata DataFrame

        Raises:
            ValueError: If required sections are missing
        """
        section_rows = df[df['row_type'] == 'section']
        found_sections = set(section_rows['account_name'].values)

        # Check for Assets
        if 'Assets' not in found_sections:
            raise ValueError("Missing required section: Assets")

        # Check for Liabilities (either 'Liabilities' or 'Liabilities and Equity')
        has_liabilities = ('Liabilities' in found_sections or
                          'Liabilities and Equity' in found_sections)
        if not has_liabilities:
            raise ValueError("Missing required section: Liabilities")

        # Check for Equity (might be under 'Liabilities and Equity')
        has_equity = 'Equity' in found_sections
        if not has_equity:
            raise ValueError("Missing required section: Equity")

    def _build_hierarchy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Second pass: Build hierarchy tree from metadata DataFrame.

        Tree structure:
        {
            'Assets': {
                'Current Assets': {
                    'children': [
                        {'name': 'Bank Accounts', 'parent': True, 'children': [
                            {'name': 'Checking', 'value': 1201.0},
                            {'name': 'Savings', 'value': 800.0}
                        ], 'total': 2001.0}
                    ]
                }
            },
            'Liabilities': {...},
            'Equity': {...}
        }

        Args:
            df: Metadata DataFrame from _parse_raw_data

        Returns:
            Hierarchy tree dict
        """
        hierarchy = {}
        current_section = None
        current_parent = None
        parent_stack = []  # Stack to handle nested parents

        for idx, row in df.iterrows():
            account_name = row['account_name']
            row_type = row['row_type']
            numeric_value = row['numeric_value']

            if row_type == 'section':
                # Start a new section
                current_section = account_name
                hierarchy[current_section] = {}
                parent_stack = []
                current_parent = None

            elif row_type == 'parent':
                # Parent account - create entry and add to stack
                parent_entry = {
                    'name': account_name,
                    'parent': True,
                    'children': [],
                    'total': None
                }

                if current_parent:
                    # Nested parent - add to current parent's children
                    current_parent['children'].append(parent_entry)
                    parent_stack.append(current_parent)
                else:
                    # Top-level parent under section
                    if current_section not in hierarchy:
                        hierarchy[current_section] = {}
                    if 'children' not in hierarchy[current_section]:
                        hierarchy[current_section]['children'] = []
                    hierarchy[current_section]['children'].append(parent_entry)

                current_parent = parent_entry

            elif row_type == 'child':
                # Child account - add to current parent
                child_entry = {
                    'name': account_name,
                    'value': numeric_value
                }

                if current_parent:
                    current_parent['children'].append(child_entry)
                else:
                    # Orphan child - add directly to section
                    if current_section not in hierarchy:
                        hierarchy[current_section] = {}
                    if 'children' not in hierarchy[current_section]:
                        hierarchy[current_section]['children'] = []
                    hierarchy[current_section]['children'].append(child_entry)

            elif row_type == 'total':
                # Total row - associate with parent
                # Extract parent name from "Total for X"
                parent_name = account_name.replace('Total for ', '')

                # Set total on current parent if name matches
                if current_parent and current_parent['name'] == parent_name:
                    current_parent['total'] = numeric_value
                    # Pop back to previous parent level
                    if parent_stack:
                        current_parent = parent_stack.pop()
                    else:
                        current_parent = None

        return hierarchy
