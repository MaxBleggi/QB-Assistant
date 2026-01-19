"""
PLParser - Two-pass parser for QuickBooks Profit & Loss CSV exports with multi-period support.

Key insight: P&L has same hierarchical structure as Balance Sheet but with multiple period columns
and calculated summary rows (Gross Profit, Net Income).

Hierarchy is inferred from:
- Section markers: 'Income', 'Cost of Goods Sold', 'Expenses', 'Other Expenses' (empty values)
- Parent accounts: account name with empty values for all periods (not starting with 'Total for')
- Child accounts: account name with numeric values for at least one period
- Total rows: account name starting with 'Total for X'
- Calculated rows: special summary rows like 'Gross Profit', 'Net Income'

Two-pass approach with period awareness:
1. _parse_raw_data(): Extract metadata DataFrame with period-aware values dict
2. _build_hierarchy(): Construct tree from metadata patterns, preserving period data at each node
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Union

import pandas as pd

from ..loaders.file_loader import FileLoader
from ..models.pl_model import PLModel


class PLParser:
    """
    Parser for QuickBooks Profit & Loss CSV exports with multi-period support.

    Uses two-pass approach to separate data extraction from hierarchy construction.
    Period data stored as dict {period_label: numeric_value} at each hierarchy node.
    """

    # Known section markers in QuickBooks P&L
    SECTION_MARKERS = {
        'Income',
        'Cost of Goods Sold',
        'Expenses',
        'Other Expenses'
    }

    # Calculated rows that are summaries, not hierarchy nodes
    CALCULATED_ROWS = {
        'Gross Profit',
        'Net Operating Income',
        'Net Other Income',
        'Net Income'
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

    def parse(self, file_path: Union[str, Path]) -> PLModel:
        """
        Parse Profit & Loss file and return PLModel.

        Process:
        1. Load file via FileLoader
        2. Skip metadata rows (1-3) and footer
        3. Parse period headers from row 6 (index 5)
        4. Extract raw metadata with period-aware values (first pass)
        5. Build hierarchy tree with period preservation (second pass)
        6. Return PLModel with DataFrame, hierarchy, and calculated rows

        Args:
            file_path: Path to Profit & Loss CSV file

        Returns:
            PLModel with raw DataFrame, hierarchy tree, and calculated rows

        Raises:
            ValueError: If file structure is invalid (missing sections, malformed data)
        """
        # Load file
        df = self.file_loader.load(file_path)

        # Skip metadata rows (first 3 rows: title, company, date range)
        # Row 4 is blank, row 5 is column headers, row 6 is period headers
        if len(df) < 6:
            raise ValueError(f"File too short - expected at least 6 rows, got {len(df)}")

        # Start from row 2 (index 2) to skip first 3 metadata rows
        df = df.iloc[2:].reset_index(drop=True)

        # Row 0 is now blank, row 1 is column headers ("Distribution account", "Total", "")
        # Row 2 is blank row with period headers
        # Row 3+ is actual data

        # Extract period headers from row 3 (after skipping first 3 rows, this is index 3)
        # Period headers are in row 6 of original file = index 3 after skipping first 3
        period_row_idx = 1
        if len(df) <= period_row_idx:
            raise ValueError("File missing period header row")

        # Parse period headers to get period_columns mapping
        period_columns = self._parse_period_headers(df.iloc[period_row_idx])

        # Now skip to data rows (after period header row)
        df = df.iloc[period_row_idx + 1:].reset_index(drop=True)

        # Set column names - first column is account name, rest are period values
        column_names = ['account_name'] + [f'period_{i}' for i in range(len(df.columns) - 1)]
        df.columns = column_names

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

        # First pass: extract raw metadata with period-aware values
        metadata_df = self._parse_raw_data(df_clean, period_columns)

        # Validate required sections exist
        self._validate_sections(metadata_df)

        # Second pass: build hierarchy tree with period data
        hierarchy, calculated_rows = self._build_hierarchy(metadata_df)

        # Return model with DataFrame, hierarchy, and calculated rows
        return PLModel(df=metadata_df, hierarchy=hierarchy, calculated_rows=calculated_rows)

    def _parse_period_headers(self, period_row: pd.Series) -> Dict[int, str]:
        """
        Parse period headers from row 6 to create column index mapping.

        Period headers appear in row 6 with format like:
        - "Nov 1 - Nov 30 2025"
        - "Nov 1 - Nov 30 2024 (PY)"

        Args:
            period_row: Row 6 Series with period labels in columns 1+

        Returns:
            Dict mapping column index to period label string
        """
        period_columns = {}

        # Iterate over columns starting from index 1 (skip account_name column)
        for idx in range(1, len(period_row)):
            period_label = str(period_row.iloc[idx]).strip()

            # Skip empty or NaN values
            if period_label and period_label.lower() != 'nan':
                period_columns[idx] = period_label

        return period_columns

    def _parse_raw_data(self, df: pd.DataFrame, period_columns: Dict[int, str]) -> pd.DataFrame:
        """
        First pass: Extract metadata from raw DataFrame with period-aware values.

        For each row, determine:
        - account_name: The account/section name
        - values: Dict of {period_label: numeric_value} for all periods
        - row_type: section/parent/child/total/calculated

        Args:
            df: Raw DataFrame with account_name and period columns
            period_columns: Mapping of column index to period label

        Returns:
            DataFrame with metadata columns including period-aware values dict
        """
        rows = []

        for idx, row in df.iterrows():
            account_name = str(row['account_name']).strip()

            # Extract values for each period
            values = {}
            for col_idx, period_label in period_columns.items():
                # Get value from corresponding column
                col_name = f'period_{col_idx - 1}'  # Adjust for 0-based indexing
                if col_name in df.columns:
                    raw_value = str(row[col_name]).strip() if pd.notna(row[col_name]) else ''

                    # Parse numeric value if present
                    if raw_value and raw_value.lower() != 'nan':
                        try:
                            numeric_value = self._clean_currency(raw_value)
                            values[period_label] = numeric_value
                        except ValueError:
                            # Not a valid number - skip this period
                            pass

            # Detect row type based on account name and values
            row_type = self._detect_row_type(account_name, values)

            rows.append({
                'account_name': account_name,
                'values': values,
                'row_type': row_type
            })

        return pd.DataFrame(rows)

    def _detect_row_type(self, account_name: str, values: Dict[str, float]) -> str:
        """
        Detect row type from account name and values patterns.

        Rules:
        - Calculated: account_name in CALCULATED_ROWS (checked first to override child)
        - Section: account_name in SECTION_MARKERS AND empty values
        - Total: account_name starts with 'Total for '
        - Parent: empty values AND not a section AND not a total AND not calculated
        - Child: has at least one numeric value in values dict

        Args:
            account_name: The account/section name
            values: Dict of period values

        Returns:
            Row type: 'section', 'parent', 'child', 'total', or 'calculated'
        """
        # Check if it's a calculated row (has priority over child type)
        if account_name in self.CALCULATED_ROWS:
            return 'calculated'

        # Check if it's a total row
        if account_name.startswith('Total for '):
            return 'total'

        # Check if values dict is empty
        is_empty_values = len(values) == 0

        # Check if it's a section marker
        if account_name in self.SECTION_MARKERS and is_empty_values:
            return 'section'

        # If values empty, it's a parent account
        if is_empty_values:
            return 'parent'

        # Has values, so it's a child account
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

        Required sections: Income, Expenses
        Optional sections: Cost of Goods Sold, Other Expenses

        Args:
            df: Metadata DataFrame

        Raises:
            ValueError: If required sections are missing
        """
        section_rows = df[df['row_type'] == 'section']
        found_sections = set(section_rows['account_name'].values)

        # Check for Income
        if 'Income' not in found_sections:
            raise ValueError("Missing required section: Income")

        # Check for Expenses
        if 'Expenses' not in found_sections:
            raise ValueError("Missing required section: Expenses")

        # COGS and Other Expenses are optional - no validation needed

    def _build_hierarchy(self, df: pd.DataFrame) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Second pass: Build hierarchy tree from metadata DataFrame with period preservation.

        Tree structure (period-aware):
        {
            'Income': {
                'children': [
                    {'name': 'Design income', 'values': {'Nov 1 - Nov 30 2025': 637.50}},
                    {'name': 'Landscaping Services', 'parent': True, 'children': [
                        {'name': 'Job Materials', 'parent': True, 'children': [
                            {'name': 'Fountains and Garden Lighting', 'values': {...}},
                            {'name': 'Plants and Soil', 'values': {...}}
                        ], 'total': {...}}
                    ]}
                ]
            },
            'Cost of Goods Sold': {...},  # Optional
            'Expenses': {...},
            'Other Expenses': {...}  # Optional
        }

        Calculated rows (excluded from hierarchy):
        [
            {'account_name': 'Gross Profit', 'values': {'Nov 1 - Nov 30 2025': 3652.63}},
            {'account_name': 'Net Income', 'values': {...}}
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
            values = row['values']

            if row_type == 'calculated':
                # Store calculated row separately, not in hierarchy
                calculated_rows.append({
                    'account_name': account_name,
                    'values': values
                })
                continue

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
                # Child account - add to current parent with period-aware values
                child_entry = {
                    'name': account_name,
                    'values': values
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
                # Total row - associate with parent (period-aware)
                # Extract parent name from "Total for X"
                parent_name = account_name.replace('Total for ', '')

                # Set total on current parent if name matches
                if current_parent and current_parent['name'] == parent_name:
                    current_parent['total'] = values
                    # Pop back to previous parent level
                    if parent_stack:
                        current_parent = parent_stack.pop()
                    else:
                        current_parent = None

        return hierarchy, calculated_rows
