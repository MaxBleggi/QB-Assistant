"""
CashFlowParser - Two-pass parser for QuickBooks Cash Flow Statement CSV exports.

Key insight: Cash flow statements follow same structure as Balance Sheet/P&L but with:
- Three activity sections: OPERATING, INVESTING, FINANCING (all caps)
- Calculated summary rows (6 total) that are NOT hierarchy nodes
- Beginning/ending cash positions that are calculated fields, not activities
- Single period (unlike P&L which can have multiple periods)

Hierarchy is inferred from:
- Section markers: 'OPERATING ACTIVITIES', 'INVESTING ACTIVITIES', 'FINANCING ACTIVITIES' (empty values)
- Parent accounts: account name with empty value (e.g., 'Adjustments to reconcile...')
- Child accounts: account name with numeric value
- Total rows: account name starting with 'Total for X'
- Calculated rows: special summary rows (Net cash provided by..., NET CASH INCREASE, Cash at beginning/end)

Two-pass approach:
1. _parse_raw_data(): Extract metadata DataFrame (account_name, raw_value, row_type)
2. _build_hierarchy(): Construct tree from metadata patterns, excluding calculated rows
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Union

import pandas as pd

from ..loaders.file_loader import FileLoader
from ..models.cash_flow_model import CashFlowModel


class CashFlowParser:
    """
    Parser for QuickBooks Cash Flow Statement CSV exports.

    Uses two-pass approach to separate data extraction from hierarchy construction.
    Calculated rows (cash positions, net changes) stored separately from hierarchy tree.
    """

    # Known section markers in QuickBooks Cash Flow (all caps)
    SECTION_MARKERS = {
        'OPERATING ACTIVITIES',
        'INVESTING ACTIVITIES',
        'FINANCING ACTIVITIES'
    }

    # Calculated rows that are summaries, not hierarchy nodes
    CALCULATED_ROWS = {
        'Net cash provided by operating activities',
        'Net cash provided by investing activities',
        'Net cash provided by financing activities',
        'NET CASH INCREASE FOR PERIOD',
        'Cash at beginning of period',
        'CASH AT END OF PERIOD'
    }

    # Footer pattern to detect and skip
    FOOTER_PATTERN = re.compile(r'GMT', re.IGNORECASE)

    def __init__(self, file_loader: FileLoader):
        """
        Initialize parser with FileLoader dependency.

        Args:
            file_loader: FileLoader instance for file I/O
        """
        self.file_loader = file_loader

    def parse(self, file_path: Union[str, Path]) -> CashFlowModel:
        """
        Parse Cash Flow Statement file and return CashFlowModel.

        Process:
        1. Load file via FileLoader
        2. Skip metadata rows (1-3) and footer
        3. Extract raw metadata (first pass)
        4. Validate required sections exist
        5. Build hierarchy tree with calculated rows separated (second pass)
        6. Return CashFlowModel with DataFrame, hierarchy, and calculated rows

        Args:
            file_path: Path to Cash Flow Statement CSV file

        Returns:
            CashFlowModel with raw DataFrame, hierarchy tree, and calculated rows

        Raises:
            ValueError: If file structure is invalid (missing sections, malformed data)
        """
        # Load file
        df = self.file_loader.load(file_path)

        # Skip metadata rows (first 3 rows: title, company, date range)
        # Row 4 is typically blank, row 5 is column headers
        if len(df) < 5:
            raise ValueError(f"File too short - expected at least 5 rows, got {len(df)}")

        # Start from row 2 (index 2) to skip first 3 metadata rows
        df = df.iloc[2:].reset_index(drop=True)

        # Set column names (should be 'Full name', 'Total')
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

        # Second pass: build hierarchy tree and extract calculated rows
        hierarchy, calculated_rows = self._build_hierarchy(metadata_df)

        # Extract metadata for model
        metadata = {
            'total_rows': len(metadata_df),
            'sections': list(self.SECTION_MARKERS)
        }

        # Return model with DataFrame, hierarchy, calculated rows, and metadata
        return CashFlowModel(df=metadata_df, hierarchy=hierarchy,
                           calculated_rows=calculated_rows, metadata=metadata)

    def _parse_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        First pass: Extract metadata from raw DataFrame.

        For each row, determine:
        - account_name: The account/section name
        - raw_value: The value as string (to preserve formatting)
        - numeric_value: Parsed numeric value (None for non-numeric)
        - row_type: section/parent/child/total/calculated

        Args:
            df: Raw DataFrame with 'account_name' and 'value' columns

        Returns:
            DataFrame with metadata columns
        """
        rows = []

        for idx, row in df.iterrows():
            account_name = str(row['account_name']).strip()
            raw_value = str(row['value']).strip() if pd.notna(row['value']) else ''

            # Detect row type (calculated rows checked FIRST)
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

        Rules (in priority order):
        1. Calculated: account_name in CALCULATED_ROWS (checked FIRST to override child)
        2. Total: account_name starts with 'Total for '
        3. Section: account_name in SECTION_MARKERS AND empty value
        4. Parent: empty value AND not a section AND not a total AND not calculated
        5. Child: has numeric value

        Args:
            account_name: The account/section name
            raw_value: The raw value string

        Returns:
            Row type: 'section', 'parent', 'child', 'total', or 'calculated'
        """
        # Check if it's a calculated row FIRST (has priority over child type)
        if account_name in self.CALCULATED_ROWS:
            return 'calculated'

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

        Handles formats: $1,887.47, 1,481.28, -2,853.02, -$2,832.50
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

        Required sections: OPERATING ACTIVITIES, INVESTING ACTIVITIES, FINANCING ACTIVITIES

        Note: INVESTING and FINANCING may have no children (empty sections), but the
        section markers must still be present.

        Args:
            df: Metadata DataFrame

        Raises:
            ValueError: If required sections are missing
        """
        section_rows = df[df['row_type'] == 'section']
        found_sections = set(section_rows['account_name'].values)

        # Check for all three required sections
        for required in self.SECTION_MARKERS:
            if required not in found_sections:
                raise ValueError(f"Missing required section: {required}")

    def _build_hierarchy(self, df: pd.DataFrame) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Second pass: Build hierarchy tree from metadata DataFrame.

        Tree structure:
        {
            'OPERATING ACTIVITIES': [
                {'name': 'Net Income', 'value': 1481.28},
                {'name': 'Adjustments to reconcile...', 'parent': True, 'children': [
                    {'name': 'Accounts Payable (A/P)', 'value': -369.72},
                    {'name': 'Accounts Receivable (A/R)', 'value': -2853.02},
                    ...
                ], 'total': 406.19}
            ],
            'INVESTING ACTIVITIES': [],  # May be empty
            'FINANCING ACTIVITIES': [
                {'name': 'Notes Payable', 'value': 25000.00},
                {'name': 'Opening Balance Equity', 'value': -27832.50}
            ]
        }

        Calculated rows (excluded from hierarchy):
        [
            {'account_name': 'Net cash provided by operating activities', 'value': 1887.47},
            {'account_name': 'NET CASH INCREASE FOR PERIOD', 'value': -945.03},
            {'account_name': 'Cash at beginning of period', 'value': 5008.55},
            {'account_name': 'CASH AT END OF PERIOD', 'value': 4063.52}
        ]

        Args:
            df: Metadata DataFrame from _parse_raw_data

        Returns:
            Tuple of (hierarchy tree dict, calculated rows list)
        """
        hierarchy = {}
        calculated_rows = []
        current_section = None
        current_parent = None
        parent_stack = []  # Stack to handle nested parents

        for idx, row in df.iterrows():
            account_name = row['account_name']
            row_type = row['row_type']
            numeric_value = row['numeric_value']

            if row_type == 'calculated':
                # Store calculated row separately, not in hierarchy
                calculated_rows.append({
                    'account_name': account_name,
                    'value': numeric_value
                })
                continue

            if row_type == 'section':
                # Start a new section - initialize with empty list
                current_section = account_name
                hierarchy[current_section] = []
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
                    if current_section and current_section in hierarchy:
                        hierarchy[current_section].append(parent_entry)

                current_parent = parent_entry

            elif row_type == 'child':
                # Child account - add to current parent or section
                child_entry = {
                    'name': account_name,
                    'value': numeric_value
                }

                if current_parent:
                    current_parent['children'].append(child_entry)
                else:
                    # Orphan child - add directly to section
                    if current_section and current_section in hierarchy:
                        hierarchy[current_section].append(child_entry)

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

        return hierarchy, calculated_rows
