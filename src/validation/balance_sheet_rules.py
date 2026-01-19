"""
Balance Sheet-specific validation rules.

Provides three validation rules for Balance Sheet data:
1. RequiredSectionsRule - Validates presence of Assets, Liabilities, Equity sections
2. HierarchyConsistencyRule - Validates that totals match sum of children
3. NumericAmountRule - Validates that currency values are parseable
"""
import re
from typing import List

import pandas as pd

from .rules import ValidationRule, ValidationResult


class RequiredSectionsRule(ValidationRule):
    """
    Validates that all required sections exist in the Balance Sheet.

    Default required sections: Assets, Liabilities (or Liabilities and Equity), Equity
    """

    def __init__(self, required_sections: List[str] = None):
        """
        Initialize rule with required sections.

        Args:
            required_sections: List of section names that must be present.
                             Default: ['Assets', 'Liabilities', 'Equity']
        """
        if required_sections is None:
            required_sections = ['Assets', 'Liabilities', 'Equity']
        self.required_sections = required_sections

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check that all required sections exist in the DataFrame.

        Looks for section markers (rows with row_type='section' if available,
        or rows where account_name matches section names).

        Args:
            df: DataFrame with Balance Sheet data

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Extract section names from DataFrame
        # Check if 'row_type' column exists (from parser output)
        if 'row_type' in df.columns:
            section_rows = df[df['row_type'] == 'section']
            found_sections = set(section_rows['account_name'].values)
        else:
            # Fallback: look for account names that match known sections
            account_names = df['account_name'].values if 'account_name' in df.columns else []
            found_sections = set(account_names)

        # Check each required section
        for section in self.required_sections:
            # Special handling for Liabilities - accept 'Liabilities and Equity' as alternative
            if section == 'Liabilities':
                has_section = (section in found_sections or
                             'Liabilities and Equity' in found_sections)
            elif section == 'Equity':
                # Equity might be standalone or under 'Liabilities and Equity'
                has_section = (section in found_sections or
                             'Liabilities and Equity' in found_sections)
            else:
                has_section = section in found_sections

            if not has_section:
                errors.append(f"Missing required section: {section}")

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])


class HierarchyConsistencyRule(ValidationRule):
    """
    Validates that 'Total for X' rows match the sum of children under parent X.

    Uses tolerance for floating-point comparison to handle rounding errors.
    """

    def __init__(self, tolerance: float = 0.01):
        """
        Initialize rule with comparison tolerance.

        Args:
            tolerance: Maximum allowed difference between total and sum (default: 0.01)
        """
        self.tolerance = tolerance

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check that totals match sum of children.

        Process:
        1. Find all 'Total for X' rows
        2. For each total, find parent X and its children
        3. Sum children values and compare to total
        4. Report mismatches exceeding tolerance

        Args:
            df: DataFrame with Balance Sheet data (should have row_type and numeric_value)

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Need row_type and numeric_value columns
        if 'row_type' not in df.columns:
            return ValidationResult(
                passed=False,
                errors=["DataFrame missing 'row_type' column - cannot validate hierarchy"]
            )

        if 'numeric_value' not in df.columns:
            return ValidationResult(
                passed=False,
                errors=["DataFrame missing 'numeric_value' column - cannot validate totals"]
            )

        # Find all total rows
        total_rows = df[df['row_type'] == 'total']

        for idx, total_row in total_rows.iterrows():
            account_name = total_row['account_name']
            total_value = total_row['numeric_value']

            if pd.isna(total_value):
                errors.append(f"Total row '{account_name}' has no numeric value")
                continue

            # Extract parent name from 'Total for X'
            if not account_name.startswith('Total for '):
                errors.append(f"Total row '{account_name}' does not start with 'Total for '")
                continue

            parent_name = account_name.replace('Total for ', '')

            # Find parent row
            parent_rows = df[(df['account_name'] == parent_name) & (df['row_type'] == 'parent')]

            if len(parent_rows) == 0:
                # Parent might not exist if it's a direct section total
                # Try to find children between previous section/parent and this total
                continue

            # Find children: rows between parent and total with row_type='child'
            parent_idx = parent_rows.index[0]
            total_idx = idx

            # Get rows between parent and total
            between_rows = df.loc[parent_idx+1:total_idx-1]
            child_rows = between_rows[between_rows['row_type'] == 'child']

            # Sum children values
            children_sum = child_rows['numeric_value'].sum()

            # Compare with tolerance
            diff = abs(total_value - children_sum)
            if diff > self.tolerance:
                errors.append(
                    f"Total mismatch for '{parent_name}': "
                    f"total={total_value:.2f}, sum of children={children_sum:.2f}, "
                    f"difference={diff:.2f}"
                )

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])


class NumericAmountRule(ValidationRule):
    """
    Validates that currency values in specified column are parseable as numbers.

    Skips empty values (parents and sections legitimately have no value).
    Uses same currency cleaning logic as parser.
    """

    def __init__(self, column_name: str = 'Total'):
        """
        Initialize rule with column to validate.

        Args:
            column_name: Name of column containing currency values (default: 'Total')
        """
        self.column_name = column_name

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check that all non-empty values in column are valid currency amounts.

        Args:
            df: DataFrame with Balance Sheet data

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Check if column exists
        if self.column_name not in df.columns:
            # Try alternative column names
            if 'value' in df.columns:
                column_name = 'value'
            elif 'raw_value' in df.columns:
                column_name = 'raw_value'
            else:
                return ValidationResult(
                    passed=False,
                    errors=[f"Column '{self.column_name}' not found in DataFrame"]
                )
        else:
            column_name = self.column_name

        # Check each non-empty value
        for idx, row in df.iterrows():
            value = row[column_name]

            # Skip empty/NaN values (valid for sections and parents)
            if pd.isna(value) or value == '' or str(value).strip() == '':
                continue

            # Try to parse as currency
            try:
                self._clean_currency(str(value))
            except ValueError:
                errors.append(
                    f"Row {idx}: Cannot parse currency value '{value}' in column '{column_name}'"
                )

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])

    def _clean_currency(self, value: str) -> float:
        """
        Clean currency string and convert to float.

        Same logic as BalanceSheetParser._clean_currency().

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
