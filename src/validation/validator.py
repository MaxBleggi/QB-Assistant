"""
Validator for composing and executing multiple validation rules.

Provides orchestration for running multiple validation rules and aggregating results.
"""
from dataclasses import dataclass
from typing import List

import pandas as pd

from .rules import ValidationRule


@dataclass
class ValidationReport:
    """Aggregated validation results from multiple rules."""
    valid: bool
    errors: List[str]


class Validator:
    """
    Orchestrates execution of multiple validation rules.

    Can be subclassed by document-specific validators (e.g., BalanceSheetValidator)
    to add domain-specific rules on top of base validation.
    """

    def __init__(self, rules: List[ValidationRule]):
        """
        Initialize validator with a list of rules.

        Args:
            rules: List of ValidationRule instances to execute
        """
        self.rules = rules

    def validate(self, df: pd.DataFrame, fail_fast: bool = False) -> ValidationReport:
        """
        Execute all validation rules and aggregate results.

        Args:
            df: DataFrame to validate
            fail_fast: If True, stop at first failure. If False, collect all errors.

        Returns:
            ValidationReport with overall validity and aggregated errors
        """
        all_errors = []

        for rule in self.rules:
            # Get rule name for error context
            rule_name = rule.__class__.__name__

            # Execute rule
            result = rule.validate(df)

            # If rule failed, collect errors
            if not result.passed:
                # Prefix errors with rule name for clarity
                prefixed_errors = [
                    f"[{rule_name}] {error}"
                    for error in result.errors
                ]
                all_errors.extend(prefixed_errors)

                # Stop if fail_fast is enabled
                if fail_fast:
                    break

        # Determine overall validity
        valid = len(all_errors) == 0

        return ValidationReport(valid=valid, errors=all_errors)
