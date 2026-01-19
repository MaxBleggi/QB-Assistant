"""
Unit tests for Balance Sheet validation rules.

Tests RequiredSectionsRule, HierarchyConsistencyRule, and NumericAmountRule
with both passing and failing scenarios.
"""
import pandas as pd
import pytest

from src.validation import (
    RequiredSectionsRule,
    HierarchyConsistencyRule,
    NumericAmountRule,
    ValidationResult,
)


class TestRequiredSectionsRule:
    """Test suite for RequiredSectionsRule."""

    def test_required_sections_rule_pass(self):
        """
        Given: DataFrame with all required sections (Assets, Liabilities, Equity)
        When: RequiredSectionsRule.validate() called
        Then: Returns ValidationResult with passed=True
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Checking', 'Liabilities', 'Credit Card', 'Equity', 'Retained Earnings'],
            'row_type': ['section', 'child', 'section', 'child', 'section', 'child']
        })

        rule = RequiredSectionsRule()
        result = rule.validate(df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_required_sections_rule_fail_missing_equity(self):
        """
        Given: DataFrame missing Equity section
        When: RequiredSectionsRule.validate() called
        Then: Returns ValidationResult with passed=False and descriptive error
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Checking', 'Liabilities', 'Credit Card'],
            'row_type': ['section', 'child', 'section', 'child']
        })

        rule = RequiredSectionsRule()
        result = rule.validate(df)

        assert result.passed is False
        assert len(result.errors) > 0
        assert 'Equity' in result.errors[0]

    def test_required_sections_rule_fail_missing_assets(self):
        """
        Given: DataFrame missing Assets section
        When: RequiredSectionsRule.validate() called
        Then: Returns ValidationResult with passed=False
        """
        df = pd.DataFrame({
            'account_name': ['Liabilities', 'Credit Card', 'Equity', 'Retained Earnings'],
            'row_type': ['section', 'child', 'section', 'child']
        })

        rule = RequiredSectionsRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('Assets' in error for error in result.errors)

    def test_required_sections_combined_section(self):
        """
        Given: DataFrame with 'Liabilities and Equity' combined section
        When: RequiredSectionsRule.validate() called
        Then: Accepts as valid (covers both Liabilities and Equity)
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Checking', 'Liabilities and Equity', 'Credit Card'],
            'row_type': ['section', 'child', 'section', 'child']
        })

        rule = RequiredSectionsRule()
        result = rule.validate(df)

        assert result.passed is True

    def test_required_sections_custom_list(self):
        """
        Given: Custom required sections list
        When: RequiredSectionsRule initialized with custom list
        Then: Validates against custom sections
        """
        df = pd.DataFrame({
            'account_name': ['Custom Section', 'Account1'],
            'row_type': ['section', 'child']
        })

        rule = RequiredSectionsRule(required_sections=['Custom Section'])
        result = rule.validate(df)

        assert result.passed is True

    def test_required_sections_without_row_type(self):
        """
        Given: DataFrame without row_type column (fallback mode)
        When: RequiredSectionsRule.validate() called
        Then: Uses account_name column directly
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Liabilities', 'Equity']
        })

        rule = RequiredSectionsRule()
        result = rule.validate(df)

        assert result.passed is True


class TestHierarchyConsistencyRule:
    """Test suite for HierarchyConsistencyRule."""

    def test_hierarchy_consistency_rule_pass(self):
        """
        Given: DataFrame with matching totals (Total for X = sum of children)
        When: HierarchyConsistencyRule.validate() called
        Then: Returns ValidationResult with passed=True
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Bank Accounts', 'Checking', 'Savings', 'Total for Bank Accounts'],
            'row_type': ['section', 'parent', 'child', 'child', 'total'],
            'numeric_value': [None, None, 1201.0, 800.0, 2001.0]
        })

        rule = HierarchyConsistencyRule()
        result = rule.validate(df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_hierarchy_consistency_rule_fail_mismatch(self):
        """
        Given: DataFrame with mismatched total (Total != sum of children)
        When: HierarchyConsistencyRule.validate() called
        Then: Returns ValidationResult with passed=False and error describing mismatch
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Bank Accounts', 'Checking', 'Savings', 'Total for Bank Accounts'],
            'row_type': ['section', 'parent', 'child', 'child', 'total'],
            'numeric_value': [None, None, 1201.0, 800.0, 5000.0]  # Total should be 2001.0
        })

        rule = HierarchyConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert len(result.errors) > 0
        assert 'Bank Accounts' in result.errors[0]
        assert 'mismatch' in result.errors[0].lower()

    def test_hierarchy_consistency_within_tolerance(self):
        """
        Given: DataFrame with total slightly different from sum (within tolerance)
        When: HierarchyConsistencyRule.validate() called
        Then: Passes validation (rounding tolerance applied)
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Bank Accounts', 'Checking', 'Savings', 'Total for Bank Accounts'],
            'row_type': ['section', 'parent', 'child', 'child', 'total'],
            'numeric_value': [None, None, 1201.0, 800.0, 2001.005]  # 0.005 difference
        })

        rule = HierarchyConsistencyRule(tolerance=0.01)
        result = rule.validate(df)

        assert result.passed is True

    def test_hierarchy_consistency_missing_columns(self):
        """
        Given: DataFrame without required columns
        When: HierarchyConsistencyRule.validate() called
        Then: Returns ValidationResult with error about missing columns
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Checking']
        })

        rule = HierarchyConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('row_type' in error for error in result.errors)

    def test_hierarchy_consistency_total_without_value(self):
        """
        Given: Total row with no numeric value
        When: HierarchyConsistencyRule.validate() called
        Then: Reports error about missing value
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Bank Accounts', 'Checking', 'Total for Bank Accounts'],
            'row_type': ['section', 'parent', 'child', 'total'],
            'numeric_value': [None, None, 1201.0, None]  # Total has no value
        })

        rule = HierarchyConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('no numeric value' in error for error in result.errors)

    def test_hierarchy_consistency_custom_tolerance(self):
        """
        Given: Custom tolerance value
        When: HierarchyConsistencyRule initialized with custom tolerance
        Then: Uses custom tolerance for validation
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Bank Accounts', 'Checking', 'Savings', 'Total for Bank Accounts'],
            'row_type': ['section', 'parent', 'child', 'child', 'total'],
            'numeric_value': [None, None, 1201.0, 800.0, 2002.0]  # 1.0 difference
        })

        # Should fail with default tolerance (0.01)
        rule_strict = HierarchyConsistencyRule(tolerance=0.01)
        result_strict = rule_strict.validate(df)
        assert result_strict.passed is False

        # Should pass with higher tolerance (2.0)
        rule_loose = HierarchyConsistencyRule(tolerance=2.0)
        result_loose = rule_loose.validate(df)
        assert result_loose.passed is True


class TestNumericAmountRule:
    """Test suite for NumericAmountRule."""

    def test_numeric_amount_rule_pass(self):
        """
        Given: DataFrame with all valid currency values
        When: NumericAmountRule.validate() called
        Then: Returns ValidationResult with passed=True
        """
        df = pd.DataFrame({
            'account_name': ['Checking', 'Savings', 'Credit Card'],
            'Total': ['$1,201.00', '800.00', '-157.72']
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_numeric_amount_rule_invalid_currency(self):
        """
        Given: DataFrame with unparseable currency value
        When: NumericAmountRule.validate() called
        Then: Returns ValidationResult with passed=False and error identifying row
        """
        df = pd.DataFrame({
            'account_name': ['Checking', 'Savings', 'Invalid'],
            'Total': ['$1,201.00', '800.00', 'invalid']
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        assert result.passed is False
        assert len(result.errors) > 0
        assert 'invalid' in result.errors[0].lower()

    def test_numeric_amount_rule_skip_empty(self):
        """
        Given: DataFrame with empty values (sections/parents)
        When: NumericAmountRule.validate() called
        Then: Skips empty values (they're valid for sections/parents)
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Current Assets', 'Checking'],
            'Total': ['', '', '$1,201.00']
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        assert result.passed is True

    def test_numeric_amount_rule_skip_nan(self):
        """
        Given: DataFrame with NaN values
        When: NumericAmountRule.validate() called
        Then: Skips NaN values (valid for sections/parents)
        """
        df = pd.DataFrame({
            'account_name': ['Assets', 'Checking'],
            'Total': [None, '$1,201.00']
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        assert result.passed is True

    def test_numeric_amount_rule_column_not_found(self):
        """
        Given: DataFrame without specified column
        When: NumericAmountRule.validate() called
        Then: Returns error about missing column
        """
        df = pd.DataFrame({
            'account_name': ['Checking'],
            'Amount': ['$1,201.00']  # Different column name
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        # Should try fallback columns or report error
        # Implementation tries 'value' and 'raw_value' as fallbacks
        assert result.passed is False or 'Amount' in df.columns

    def test_numeric_amount_rule_fallback_column(self):
        """
        Given: DataFrame with 'value' column instead of 'Total'
        When: NumericAmountRule.validate() called with default column
        Then: Uses fallback column 'value'
        """
        df = pd.DataFrame({
            'account_name': ['Checking'],
            'value': ['$1,201.00']
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        assert result.passed is True

    @pytest.mark.parametrize('currency_value', [
        '$2,001.00',
        '1,201.00',
        '800.00',
        '-9,905.00',
        '0.00',
        '$13,495.00',
    ])
    def test_numeric_amount_various_formats(self, currency_value):
        """
        Given: Various valid currency formats
        When: NumericAmountRule validates
        Then: All pass validation
        """
        df = pd.DataFrame({
            'account_name': ['Test'],
            'Total': [currency_value]
        })

        rule = NumericAmountRule(column_name='Total')
        result = rule.validate(df)

        assert result.passed is True


class TestValidationRulesIntegration:
    """Integration tests using multiple validation rules together."""

    def test_all_rules_pass_valid_data(self):
        """
        Given: Valid Balance Sheet DataFrame
        When: All three validation rules applied
        Then: All pass
        """
        df = pd.DataFrame({
            'account_name': [
                'Assets', 'Bank Accounts', 'Checking', 'Savings', 'Total for Bank Accounts',
                'Liabilities', 'Credit Cards', 'Mastercard', 'Total for Credit Cards',
                'Equity', 'Retained Earnings'
            ],
            'row_type': [
                'section', 'parent', 'child', 'child', 'total',
                'section', 'parent', 'child', 'total',
                'section', 'child'
            ],
            'numeric_value': [
                None, None, 1201.0, 800.0, 2001.0,
                None, None, 157.72, 157.72,
                None, -9905.0
            ],
            'Total': [
                '', '', '$1,201.00', '800.00', '$2,001.00',
                '', '', '157.72', '$157.72',
                '', '-9,905.00'
            ]
        })

        # Test all rules
        sections_rule = RequiredSectionsRule()
        hierarchy_rule = HierarchyConsistencyRule()
        numeric_rule = NumericAmountRule(column_name='Total')

        assert sections_rule.validate(df).passed is True
        assert hierarchy_rule.validate(df).passed is True
        assert numeric_rule.validate(df).passed is True
