"""
Profit & Loss-specific validation rules.

Provides two validation rules for P&L data:
1. PLRequiredSectionsRule - Validates presence of Income and Expenses sections (COGS optional)
2. PLPeriodConsistencyRule - Validates that all child accounts have consistent period keys
"""
from typing import List

import pandas as pd

from .rules import ValidationRule, ValidationResult


class PLRequiredSectionsRule(ValidationRule):
    """
    Validates that all required sections exist in the Profit & Loss.

    Required sections: Income, Expenses
    Optional sections: Cost of Goods Sold, Other Expenses
    """

    def __init__(self, required_sections: List[str] = None):
        """
        Initialize rule with required sections.

        Args:
            required_sections: List of section names that must be present.
                             Default: ['Income', 'Expenses']
        """
        if required_sections is None:
            required_sections = ['Income', 'Expenses']
        self.required_sections = required_sections

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check that all required sections exist in the DataFrame.

        Looks for section markers (rows with row_type='section' and account_name
        matching required section names).

        Args:
            df: DataFrame with P&L data

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
            if section not in found_sections:
                errors.append(f"Missing required section: {section}")

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])


class PLPeriodConsistencyRule(ValidationRule):
    """
    Validates that all child accounts have the same set of period keys in their values dict.

    This ensures consistent time-series data for comparisons.
    Calculated rows are excluded from this check (they're summaries, not data points).
    """

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check that all child rows have consistent period keys.

        Process:
        1. Filter for row_type='child' (exclude sections, parents, totals, calculated)
        2. Extract values dict from each child row
        3. Compare period key sets across all children
        4. Report any inconsistencies

        Args:
            df: DataFrame with P&L data (should have row_type and values columns)

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Need row_type and values columns
        if 'row_type' not in df.columns:
            return ValidationResult(
                passed=False,
                errors=["DataFrame missing 'row_type' column - cannot validate period consistency"]
            )

        if 'values' not in df.columns:
            return ValidationResult(
                passed=False,
                errors=["DataFrame missing 'values' column - cannot validate periods"]
            )

        # Find all child rows (exclude calculated rows)
        child_rows = df[df['row_type'] == 'child']

        if len(child_rows) == 0:
            # No child rows to validate - pass by default
            return ValidationResult(passed=True, errors=[])

        # Extract period key sets from each child
        period_key_sets = []
        account_names = []

        for idx, row in child_rows.iterrows():
            account_name = row['account_name']
            values = row['values']

            # Values should be a dict
            if not isinstance(values, dict):
                errors.append(f"Account '{account_name}' has non-dict values: {type(values)}")
                continue

            # Get period keys
            period_keys = set(values.keys())
            period_key_sets.append(period_keys)
            account_names.append(account_name)

        # Check if all period key sets are identical
        if period_key_sets:
            first_period_set = period_key_sets[0]

            for i, period_set in enumerate(period_key_sets[1:], start=1):
                if period_set != first_period_set:
                    # Found inconsistency
                    missing_in_current = first_period_set - period_set
                    extra_in_current = period_set - first_period_set

                    error_msg = f"Period inconsistency for account '{account_names[i]}': "
                    if missing_in_current:
                        error_msg += f"missing periods {missing_in_current}, "
                    if extra_in_current:
                        error_msg += f"extra periods {extra_in_current}"

                    errors.append(error_msg.rstrip(', '))

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])
