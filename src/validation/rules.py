"""
Validation rules for DataFrame structure and content validation.

Provides composable, stateless validation rules for checking required columns,
data types, and structural consistency.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype, is_datetime64_any_dtype


@dataclass
class ValidationResult:
    """Result of a single validation rule execution."""
    passed: bool
    errors: List[str]


class ValidationRule(ABC):
    """Abstract base class for validation rules."""

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate the DataFrame against this rule.

        Args:
            df: DataFrame to validate

        Returns:
            ValidationResult with pass/fail status and error messages
        """
        pass


class RequiredColumnsRule(ValidationRule):
    """Validates that all required columns exist in the DataFrame."""

    def __init__(self, required_columns: List[str]):
        """
        Initialize rule with required column names.

        Args:
            required_columns: List of column names that must be present
        """
        self.required_columns = required_columns

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Check that all required columns exist."""
        actual_columns = set(df.columns)
        required_set = set(self.required_columns)
        missing = required_set - actual_columns

        if missing:
            missing_list = sorted(list(missing))
            error_msg = f"Missing required columns: {', '.join(missing_list)}"
            return ValidationResult(passed=False, errors=[error_msg])

        return ValidationResult(passed=True, errors=[])


class DataTypeRule(ValidationRule):
    """Validates that columns have expected data types."""

    def __init__(self, column_types: Dict[str, str]):
        """
        Initialize rule with expected column types.

        Args:
            column_types: Dict mapping column names to expected types
                         Supported types: 'numeric', 'string', 'datetime'
        """
        self.column_types = column_types
        self.type_checkers = {
            'numeric': is_numeric_dtype,
            'string': is_string_dtype,
            'datetime': is_datetime64_any_dtype,
        }

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Check that columns have expected types."""
        errors = []

        for column, expected_type in self.column_types.items():
            # Check column exists
            if column not in df.columns:
                errors.append(f"Column '{column}' not found for type validation")
                continue

            # Check type
            if expected_type not in self.type_checkers:
                errors.append(f"Unknown type '{expected_type}' for column '{column}'")
                continue

            type_checker = self.type_checkers[expected_type]
            if not type_checker(df[column]):
                actual_type = df[column].dtype
                errors.append(
                    f"Column '{column}' has incorrect type. "
                    f"Expected: {expected_type}, Got: {actual_type}"
                )

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])


class NonEmptyRule(ValidationRule):
    """Validates that DataFrame has at least one data row."""

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Check that DataFrame is not empty."""
        if df.empty or len(df) == 0:
            return ValidationResult(
                passed=False,
                errors=["DataFrame is empty - no data rows found"]
            )

        return ValidationResult(passed=True, errors=[])


class StructuralConsistencyRule(ValidationRule):
    """Validates that all rows have consistent structure (no ragged data)."""

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Check that all rows have same number of columns."""
        # In pandas DataFrame, all rows have same number of columns by construction,
        # but we can check for rows with all NaN values which might indicate ragged data
        errors = []

        # Check for rows where majority of values are NaN (potential ragged data)
        for idx, row in df.iterrows():
            null_count = row.isna().sum()
            total_cols = len(row)

            # If more than 50% of columns are null, flag as potential structural issue
            if null_count > total_cols * 0.5:
                errors.append(
                    f"Row {idx} has {null_count}/{total_cols} null values - "
                    f"possible structural inconsistency"
                )

        # Also check if column count is consistent with header
        expected_cols = len(df.columns)
        # This is implicitly validated by pandas structure, but we document it
        if expected_cols == 0:
            errors.append("DataFrame has no columns - structural issue")

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])
