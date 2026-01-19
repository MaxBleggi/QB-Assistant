"""
Unit tests for validation framework.

Tests individual validation rules and Validator composition.
"""
import pandas as pd
import pytest

from src.validation import (
    DataTypeRule,
    NonEmptyRule,
    RequiredColumnsRule,
    StructuralConsistencyRule,
    ValidationReport,
    ValidationResult,
    Validator,
)


class TestRequiredColumnsRule:
    """Test suite for RequiredColumnsRule."""

    def test_required_columns_rule_pass(self):
        """Test that rule passes when all required columns are present."""
        df = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02'],
            'Amount': [100, 200]
        })

        rule = RequiredColumnsRule(['Date', 'Amount'])
        result = rule.validate(df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_required_columns_rule_fail(self):
        """Test that rule fails when columns are missing."""
        df = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02']
        })

        rule = RequiredColumnsRule(['Date', 'Amount'])
        result = rule.validate(df)

        assert result.passed is False
        assert len(result.errors) == 1
        assert 'Amount' in result.errors[0]

    def test_required_columns_multiple_missing(self):
        """Test that rule identifies multiple missing columns."""
        df = pd.DataFrame({
            'Date': ['2025-01-01']
        })

        rule = RequiredColumnsRule(['Date', 'Amount', 'Account', 'Description'])
        result = rule.validate(df)

        assert result.passed is False
        assert 'Amount' in result.errors[0]
        assert 'Account' in result.errors[0]
        assert 'Description' in result.errors[0]


class TestDataTypeRule:
    """Test suite for DataTypeRule."""

    def test_data_type_rule_numeric(self):
        """Test numeric type validation."""
        df = pd.DataFrame({
            'Amount': [100, 200, 300]
        })

        rule = DataTypeRule({'Amount': 'numeric'})
        result = rule.validate(df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_data_type_rule_string(self):
        """Test string type validation."""
        df = pd.DataFrame({
            'Account': ['Checking', 'Savings', 'Credit']
        })

        rule = DataTypeRule({'Account': 'string'})
        result = rule.validate(df)

        assert result.passed is True

    def test_data_type_rule_fail(self):
        """Test that rule fails when type is incorrect."""
        df = pd.DataFrame({
            'Amount': ['not', 'a', 'number']
        })

        rule = DataTypeRule({'Amount': 'numeric'})
        result = rule.validate(df)

        assert result.passed is False
        assert 'Amount' in result.errors[0]
        assert 'incorrect type' in result.errors[0].lower()

    def test_data_type_rule_missing_column(self):
        """Test that rule fails gracefully when column doesn't exist."""
        df = pd.DataFrame({
            'Date': ['2025-01-01']
        })

        rule = DataTypeRule({'Amount': 'numeric'})
        result = rule.validate(df)

        assert result.passed is False
        assert 'not found' in result.errors[0]

    @pytest.mark.parametrize("dtype,values,expected_pass", [
        ('numeric', [1, 2, 3], True),
        ('numeric', [1.5, 2.5, 3.5], True),
        ('numeric', ['a', 'b', 'c'], False),
        ('string', ['a', 'b', 'c'], True),
        ('string', [1, 2, 3], False),
    ])
    def test_data_type_variations(self, dtype, values, expected_pass):
        """Test various data type scenarios."""
        df = pd.DataFrame({'col': values})
        rule = DataTypeRule({'col': dtype})
        result = rule.validate(df)

        assert result.passed == expected_pass


class TestNonEmptyRule:
    """Test suite for NonEmptyRule."""

    def test_non_empty_rule_pass(self):
        """Test that rule passes with non-empty DataFrame."""
        df = pd.DataFrame({
            'Date': ['2025-01-01'],
            'Amount': [100]
        })

        rule = NonEmptyRule()
        result = rule.validate(df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_non_empty_rule_fail(self):
        """Test that rule fails with empty DataFrame."""
        df = pd.DataFrame()

        rule = NonEmptyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert 'empty' in result.errors[0].lower()

    def test_non_empty_rule_no_rows(self):
        """Test that rule fails when DataFrame has columns but no rows."""
        df = pd.DataFrame(columns=['Date', 'Amount'])

        rule = NonEmptyRule()
        result = rule.validate(df)

        assert result.passed is False


class TestStructuralConsistencyRule:
    """Test suite for StructuralConsistencyRule."""

    def test_structural_consistency_pass(self):
        """Test that rule passes with consistent structure."""
        df = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'Amount': [100, 200, 300]
        })

        rule = StructuralConsistencyRule()
        result = rule.validate(df)

        assert result.passed is True

    def test_structural_consistency_ragged_data(self):
        """Test that rule detects rows with excessive null values."""
        df = pd.DataFrame({
            'Date': ['2025-01-01', None, '2025-01-03'],
            'Account': ['Checking', None, None],
            'Amount': [100, None, None],
            'Description': ['Valid', None, None]
        })

        rule = StructuralConsistencyRule()
        result = rule.validate(df)

        # Rows 1 and 2 have >50% null values
        assert result.passed is False
        assert any('Row' in error for error in result.errors)

    def test_structural_consistency_no_columns(self):
        """Test that rule fails with DataFrame that has no columns."""
        df = pd.DataFrame()

        rule = StructuralConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False


class TestValidator:
    """Test suite for Validator class."""

    def test_validator_all_rules_pass(self):
        """Test that Validator returns valid=True when all rules pass."""
        df = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02'],
            'Amount': [100, 200]
        })

        rules = [
            RequiredColumnsRule(['Date', 'Amount']),
            NonEmptyRule(),
            DataTypeRule({'Amount': 'numeric'})
        ]

        validator = Validator(rules)
        report = validator.validate(df)

        assert report.valid is True
        assert len(report.errors) == 0

    def test_validator_collect_errors(self):
        """Test that Validator collects errors from multiple failed rules."""
        df = pd.DataFrame({
            'Date': ['2025-01-01']
            # Missing 'Amount' column, which will fail multiple rules
        })

        rules = [
            RequiredColumnsRule(['Date', 'Amount']),
            DataTypeRule({'Amount': 'numeric'})
        ]

        validator = Validator(rules)
        report = validator.validate(df, fail_fast=False)

        assert report.valid is False
        assert len(report.errors) >= 2  # At least one error from each rule

    def test_validator_fail_fast(self):
        """Test that Validator stops at first failure when fail_fast=True."""
        df = pd.DataFrame({
            'Date': ['2025-01-01']
            # Missing 'Amount' column
        })

        rules = [
            RequiredColumnsRule(['Date', 'Amount']),  # This will fail
            DataTypeRule({'Amount': 'numeric'}),       # This would also fail
            NonEmptyRule()                              # This would pass
        ]

        validator = Validator(rules)
        report = validator.validate(df, fail_fast=True)

        assert report.valid is False
        # Should only have errors from first failed rule
        assert all('RequiredColumnsRule' in error for error in report.errors)

    def test_validator_empty_rules(self):
        """Test that Validator with no rules returns valid=True."""
        df = pd.DataFrame({
            'Date': ['2025-01-01']
        })

        validator = Validator([])
        report = validator.validate(df)

        assert report.valid is True
        assert len(report.errors) == 0

    def test_validator_error_prefixing(self):
        """Test that errors are prefixed with rule name."""
        df = pd.DataFrame({
            'Date': ['2025-01-01']
        })

        rules = [
            RequiredColumnsRule(['Date', 'Amount'])
        ]

        validator = Validator(rules)
        report = validator.validate(df)

        assert report.valid is False
        assert any('RequiredColumnsRule' in error for error in report.errors)

    def test_validator_integration(self):
        """Integration test with multiple rules on realistic data."""
        df = pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'Account': ['Checking', 'Savings', 'Credit Card'],
            'Amount': [1000.50, 2500.00, -150.75],
            'Description': ['Deposit', 'Transfer', 'Payment']
        })

        rules = [
            RequiredColumnsRule(['Date', 'Account', 'Amount', 'Description']),
            NonEmptyRule(),
            DataTypeRule({'Amount': 'numeric', 'Account': 'string'}),
            StructuralConsistencyRule()
        ]

        validator = Validator(rules)
        report = validator.validate(df)

        assert report.valid is True
        assert len(report.errors) == 0
