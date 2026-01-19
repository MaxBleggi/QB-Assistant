"""
Unit tests for P&L validation rules.

Tests PLRequiredSectionsRule and PLPeriodConsistencyRule with various configurations.
"""
import pandas as pd
import pytest

from src.validation import PLRequiredSectionsRule, PLPeriodConsistencyRule, ValidationResult


class TestPLRequiredSectionsRule:
    """Test suite for PLRequiredSectionsRule."""

    @pytest.fixture
    def valid_pl_dataframe(self):
        """Create DataFrame with Income and Expenses sections."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Design income', 'values': {'Nov 2025': 637.50}, 'row_type': 'child'},
            {'account_name': 'Cost of Goods Sold', 'values': {}, 'row_type': 'section'},
            {'account_name': 'COGS', 'values': {'Nov 2025': 100.00}, 'row_type': 'child'},
            {'account_name': 'Expenses', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Rent', 'values': {'Nov 2025': 900.00}, 'row_type': 'child'},
        ])

    @pytest.fixture
    def pl_without_cogs(self):
        """Create DataFrame without COGS section."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Design income', 'values': {'Nov 2025': 637.50}, 'row_type': 'child'},
            {'account_name': 'Expenses', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Rent', 'values': {'Nov 2025': 900.00}, 'row_type': 'child'},
        ])

    @pytest.fixture
    def pl_missing_income(self):
        """Create DataFrame missing Income section."""
        return pd.DataFrame([
            {'account_name': 'Expenses', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Rent', 'values': {'Nov 2025': 900.00}, 'row_type': 'child'},
        ])

    @pytest.fixture
    def pl_missing_expenses(self):
        """Create DataFrame missing Expenses section."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Design income', 'values': {'Nov 2025': 637.50}, 'row_type': 'child'},
        ])

    def test_required_sections_valid(self, valid_pl_dataframe):
        """
        Given: DataFrame with Income and Expenses sections
        When: PLRequiredSectionsRule.validate() called
        Then: ValidationResult.passed = True
        """
        rule = PLRequiredSectionsRule()
        result = rule.validate(valid_pl_dataframe)

        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_required_sections_missing_income(self, pl_missing_income):
        """
        Given: DataFrame missing Income section
        When: PLRequiredSectionsRule.validate() called
        Then: ValidationResult.passed = False, error mentions 'Income'
        """
        rule = PLRequiredSectionsRule()
        result = rule.validate(pl_missing_income)

        assert result.passed is False
        assert len(result.errors) > 0
        assert any('Income' in error for error in result.errors)

    def test_required_sections_missing_expenses(self, pl_missing_expenses):
        """
        Given: DataFrame missing Expenses section
        When: PLRequiredSectionsRule.validate() called
        Then: ValidationResult.passed = False, error mentions 'Expenses'
        """
        rule = PLRequiredSectionsRule()
        result = rule.validate(pl_missing_expenses)

        assert result.passed is False
        assert len(result.errors) > 0
        assert any('Expenses' in error for error in result.errors)

    def test_optional_cogs_section(self, pl_without_cogs):
        """
        Given: DataFrame with Income and Expenses but no COGS
        When: PLRequiredSectionsRule.validate() called
        Then: ValidationResult.passed = True (COGS optional)
        """
        rule = PLRequiredSectionsRule()
        result = rule.validate(pl_without_cogs)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_custom_required_sections(self):
        """
        Given: Custom required sections list
        When: Rule initialized with custom list
        Then: Validates against custom list
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Custom Section', 'values': {}, 'row_type': 'section'},
        ])

        # Require custom section
        rule = PLRequiredSectionsRule(required_sections=['Income', 'Custom Section'])
        result = rule.validate(df)

        assert result.passed is True

    def test_without_row_type_column(self):
        """
        Given: DataFrame without 'row_type' column
        When: validate() called
        Then: Falls back to account_name matching
        """
        df = pd.DataFrame([
            {'account_name': 'Income'},
            {'account_name': 'Design income'},
            {'account_name': 'Expenses'},
            {'account_name': 'Rent'},
        ])

        rule = PLRequiredSectionsRule()
        result = rule.validate(df)

        # Should find sections by name alone
        assert result.passed is True


class TestPLPeriodConsistencyRule:
    """Test suite for PLPeriodConsistencyRule."""

    @pytest.fixture
    def consistent_periods_df(self):
        """Create DataFrame where all child rows have periods ['A', 'B']."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Sales', 'values': {'Period A': 100.0, 'Period B': 200.0}, 'row_type': 'child'},
            {'account_name': 'Services', 'values': {'Period A': 150.0, 'Period B': 250.0}, 'row_type': 'child'},
            {'account_name': 'Expenses', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Rent', 'values': {'Period A': 50.0, 'Period B': 50.0}, 'row_type': 'child'},
        ])

    @pytest.fixture
    def inconsistent_periods_df(self):
        """Create DataFrame where one child has ['A'] and others have ['A', 'B']."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Sales', 'values': {'Period A': 100.0, 'Period B': 200.0}, 'row_type': 'child'},
            {'account_name': 'Services', 'values': {'Period A': 150.0}, 'row_type': 'child'},  # Missing Period B
            {'account_name': 'Rent', 'values': {'Period A': 50.0, 'Period B': 50.0}, 'row_type': 'child'},
        ])

    @pytest.fixture
    def with_calculated_row_df(self):
        """Create DataFrame with calculated row having different periods than children."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Sales', 'values': {'Period A': 100.0, 'Period B': 200.0}, 'row_type': 'child'},
            {'account_name': 'Services', 'values': {'Period A': 150.0, 'Period B': 250.0}, 'row_type': 'child'},
            # Calculated row with different periods (should be ignored)
            {'account_name': 'Gross Profit', 'values': {'Period A': 250.0, 'Period C': 450.0}, 'row_type': 'calculated'},
        ])

    def test_period_consistency_valid(self, consistent_periods_df):
        """
        Given: DataFrame where all child rows have periods ['A', 'B']
        When: PLPeriodConsistencyRule.validate() called
        Then: ValidationResult.passed = True
        """
        rule = PLPeriodConsistencyRule()
        result = rule.validate(consistent_periods_df)

        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_period_consistency_invalid(self, inconsistent_periods_df):
        """
        Given: DataFrame where one child has ['A'] and others have ['A', 'B']
        When: PLPeriodConsistencyRule.validate() called
        Then: ValidationResult.passed = False, error lists inconsistent account
        """
        rule = PLPeriodConsistencyRule()
        result = rule.validate(inconsistent_periods_df)

        assert result.passed is False
        assert len(result.errors) > 0
        # Should mention the inconsistent account
        assert any('Services' in error for error in result.errors)

    def test_calculated_rows_ignored(self, with_calculated_row_df):
        """
        Given: DataFrame with calculated row having different periods than children
        When: PLPeriodConsistencyRule.validate() called
        Then: ValidationResult.passed = True (calculated rows ignored)
        """
        rule = PLPeriodConsistencyRule()
        result = rule.validate(with_calculated_row_df)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_empty_dataframe(self):
        """
        Given: Empty DataFrame
        When: validate() called
        Then: passes (no children to validate)
        """
        df = pd.DataFrame(columns=['account_name', 'values', 'row_type'])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is True

    def test_no_child_rows(self):
        """
        Given: DataFrame with only sections and parents (no children)
        When: validate() called
        Then: passes (no children to validate)
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Operating Expenses', 'values': {}, 'row_type': 'parent'},
        ])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is True

    def test_missing_row_type_column(self):
        """
        Given: DataFrame missing 'row_type' column
        When: validate() called
        Then: returns validation error
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'values': {}},
            {'account_name': 'Sales', 'values': {'Period A': 100.0}},
        ])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('row_type' in error for error in result.errors)

    def test_missing_values_column(self):
        """
        Given: DataFrame missing 'values' column
        When: validate() called
        Then: returns validation error
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'row_type': 'section'},
            {'account_name': 'Sales', 'row_type': 'child'},
        ])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('values' in error for error in result.errors)

    def test_non_dict_values(self):
        """
        Given: DataFrame where values column contains non-dict
        When: validate() called
        Then: reports error for non-dict values
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Sales', 'values': 'not a dict', 'row_type': 'child'},  # Invalid
        ])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('Sales' in error and 'non-dict' in error for error in result.errors)

    def test_extra_periods_detected(self):
        """
        Given: One child has extra period not in others
        When: validate() called
        Then: reports inconsistency with extra periods
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Sales', 'values': {'Period A': 100.0, 'Period B': 200.0}, 'row_type': 'child'},
            {'account_name': 'Services', 'values': {'Period A': 150.0, 'Period B': 250.0, 'Period C': 300.0}, 'row_type': 'child'},  # Extra period
        ])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is False
        assert any('Services' in error and 'extra periods' in error for error in result.errors)

    def test_single_child_row(self):
        """
        Given: DataFrame with only one child row
        When: validate() called
        Then: passes (no comparison needed)
        """
        df = pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Sales', 'values': {'Period A': 100.0, 'Period B': 200.0}, 'row_type': 'child'},
        ])

        rule = PLPeriodConsistencyRule()
        result = rule.validate(df)

        assert result.passed is True
