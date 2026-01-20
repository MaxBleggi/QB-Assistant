"""
Unit tests for parameter validation rules.

Tests type validation, range validation, and required key validation.
"""
import pytest

from src.validation.parameter_rules import (
    RangeValidationRule,
    TypeValidationRule,
    RequiredParametersRule
)


class TestRangeValidationRule:
    """Test suite for RangeValidationRule."""

    def test_accepts_value_within_range(self):
        """
        Given: RangeValidationRule with min=0, max=1
        When: validate called with value 0.5
        Then: Returns passed=True
        """
        rule = RangeValidationRule('revenue_growth_rate', 0.0, 1.0)
        result = rule.validate({'revenue_growth_rate': 0.5})

        assert result.passed is True
        assert len(result.errors) == 0

    def test_accepts_value_at_min_boundary(self):
        """
        Given: RangeValidationRule with min=0, max=1
        When: validate called with value 0 (min boundary)
        Then: Returns passed=True
        """
        rule = RangeValidationRule('param', 0.0, 1.0)
        result = rule.validate({'param': 0.0})

        assert result.passed is True

    def test_accepts_value_at_max_boundary(self):
        """
        Given: RangeValidationRule with min=0, max=1
        When: validate called with value 1 (max boundary)
        Then: Returns passed=True
        """
        rule = RangeValidationRule('param', 0.0, 1.0)
        result = rule.validate({'param': 1.0})

        assert result.passed is True

    def test_rejects_value_below_min(self):
        """
        Given: RangeValidationRule with min=0, max=1
        When: validate called with value -0.5
        Then: Returns passed=False with error message
        """
        rule = RangeValidationRule('revenue_growth_rate', 0.0, 1.0)
        result = rule.validate({'revenue_growth_rate': -0.5})

        assert result.passed is False
        assert len(result.errors) == 1
        assert 'revenue_growth_rate' in result.errors[0]
        assert '0.0' in result.errors[0]
        assert '1.0' in result.errors[0]

    def test_rejects_value_above_max(self):
        """
        Given: RangeValidationRule with min=0, max=1
        When: validate called with value 1.5
        Then: Returns passed=False with error message
        """
        rule = RangeValidationRule('revenue_growth_rate', 0.0, 1.0)
        result = rule.validate({'revenue_growth_rate': 1.5})

        assert result.passed is False
        assert len(result.errors) == 1
        assert 'between' in result.errors[0].lower()

    def test_rejects_non_numeric_value(self):
        """
        Given: RangeValidationRule expecting numeric value
        When: validate called with string value
        Then: Returns passed=False with type error
        """
        rule = RangeValidationRule('param', 0.0, 1.0)
        result = rule.validate({'param': 'not_a_number'})

        assert result.passed is False
        assert 'numeric' in result.errors[0].lower()

    def test_passes_when_parameter_missing(self):
        """
        Given: RangeValidationRule for 'param_a'
        When: validate called with dict not containing 'param_a'
        Then: Returns passed=True (not rule's responsibility to check existence)
        """
        rule = RangeValidationRule('param_a', 0.0, 1.0)
        result = rule.validate({'param_b': 0.5})

        assert result.passed is True

    def test_accepts_negative_range(self):
        """
        Given: RangeValidationRule with negative range (min=-1, max=0)
        When: validate called with value -0.5
        Then: Returns passed=True
        """
        rule = RangeValidationRule('adjustment', -1.0, 0.0)
        result = rule.validate({'adjustment': -0.5})

        assert result.passed is True

    def test_accepts_integer_values(self):
        """
        Given: RangeValidationRule for integer range
        When: validate called with integer value in range
        Then: Returns passed=True
        """
        rule = RangeValidationRule('count', 1, 100)
        result = rule.validate({'count': 50})

        assert result.passed is True


class TestTypeValidationRule:
    """Test suite for TypeValidationRule."""

    def test_accepts_correct_type_float(self):
        """
        Given: TypeValidationRule expecting float
        When: validate called with float value
        Then: Returns passed=True
        """
        rule = TypeValidationRule('growth_rate', float)
        result = rule.validate({'growth_rate': 0.05})

        assert result.passed is True
        assert len(result.errors) == 0

    def test_accepts_correct_type_int(self):
        """
        Given: TypeValidationRule expecting int
        When: validate called with int value
        Then: Returns passed=True
        """
        rule = TypeValidationRule('count', int)
        result = rule.validate({'count': 42})

        assert result.passed is True

    def test_accepts_correct_type_string(self):
        """
        Given: TypeValidationRule expecting str
        When: validate called with string value
        Then: Returns passed=True
        """
        rule = TypeValidationRule('name', str)
        result = rule.validate({'name': 'test'})

        assert result.passed is True

    def test_accepts_correct_type_bool(self):
        """
        Given: TypeValidationRule expecting bool
        When: validate called with boolean value
        Then: Returns passed=True
        """
        rule = TypeValidationRule('enabled', bool)
        result = rule.validate({'enabled': True})

        assert result.passed is True

    def test_rejects_incorrect_type(self):
        """
        Given: TypeValidationRule expecting int
        When: validate called with string value
        Then: Returns passed=False with type error
        """
        rule = TypeValidationRule('count', int)
        result = rule.validate({'count': 'not_int'})

        assert result.passed is False
        assert len(result.errors) == 1
        assert 'count' in result.errors[0]
        assert 'int' in result.errors[0].lower()

    def test_rejects_float_when_expecting_int(self):
        """
        Given: TypeValidationRule expecting int
        When: validate called with float value
        Then: Returns passed=False (strict type checking)
        """
        rule = TypeValidationRule('count', int)
        result = rule.validate({'count': 42.5})

        assert result.passed is False

    def test_passes_when_parameter_missing(self):
        """
        Given: TypeValidationRule for 'param_a'
        When: validate called with dict not containing 'param_a'
        Then: Returns passed=True (not rule's responsibility)
        """
        rule = TypeValidationRule('param_a', str)
        result = rule.validate({'param_b': 'value'})

        assert result.passed is True

    def test_error_message_includes_expected_and_actual_type(self):
        """
        Given: TypeValidationRule expecting int
        When: validate called with string value
        Then: Error message includes both expected and actual type
        """
        rule = TypeValidationRule('value', int)
        result = rule.validate({'value': 'string'})

        assert result.passed is False
        error = result.errors[0].lower()
        assert 'int' in error
        assert 'str' in error


class TestRequiredParametersRule:
    """Test suite for RequiredParametersRule."""

    def test_accepts_dict_with_all_required_keys(self):
        """
        Given: RequiredParametersRule with keys ['a', 'b']
        When: validate called with dict containing both keys
        Then: Returns passed=True
        """
        rule = RequiredParametersRule(['revenue_growth_rate', 'expense_adjustment'])
        result = rule.validate({
            'revenue_growth_rate': 0.05,
            'expense_adjustment': 1.1
        })

        assert result.passed is True
        assert len(result.errors) == 0

    def test_accepts_dict_with_extra_keys(self):
        """
        Given: RequiredParametersRule with keys ['a', 'b']
        When: validate called with dict containing a, b, and extra keys
        Then: Returns passed=True
        """
        rule = RequiredParametersRule(['a', 'b'])
        result = rule.validate({'a': 1, 'b': 2, 'c': 3, 'd': 4})

        assert result.passed is True

    def test_rejects_dict_missing_one_key(self):
        """
        Given: RequiredParametersRule with keys ['a', 'b']
        When: validate called with dict missing 'b'
        Then: Returns passed=False with error listing missing key
        """
        rule = RequiredParametersRule(['revenue_growth_rate', 'expense_adjustment'])
        result = rule.validate({'revenue_growth_rate': 0.05})

        assert result.passed is False
        assert len(result.errors) == 1
        assert 'expense_adjustment' in result.errors[0]
        assert 'missing' in result.errors[0].lower()

    def test_rejects_dict_missing_multiple_keys(self):
        """
        Given: RequiredParametersRule with keys ['a', 'b', 'c']
        When: validate called with dict missing 'b' and 'c'
        Then: Returns passed=False with errors for both missing keys
        """
        rule = RequiredParametersRule(['a', 'b', 'c'])
        result = rule.validate({'a': 1})

        assert result.passed is False
        assert len(result.errors) == 2
        # Check both missing keys are mentioned
        errors_text = ' '.join(result.errors)
        assert 'b' in errors_text
        assert 'c' in errors_text

    def test_rejects_empty_dict_when_keys_required(self):
        """
        Given: RequiredParametersRule with keys ['a', 'b']
        When: validate called with empty dict
        Then: Returns passed=False with errors for all missing keys
        """
        rule = RequiredParametersRule(['a', 'b'])
        result = rule.validate({})

        assert result.passed is False
        assert len(result.errors) == 2

    def test_accepts_empty_dict_when_no_keys_required(self):
        """
        Given: RequiredParametersRule with empty required keys list
        When: validate called with empty dict
        Then: Returns passed=True
        """
        rule = RequiredParametersRule([])
        result = rule.validate({})

        assert result.passed is True

    def test_error_messages_include_parameter_names(self):
        """
        Given: RequiredParametersRule with keys ['revenue_growth_rate']
        When: validate called with dict missing that key
        Then: Error message includes parameter name
        """
        rule = RequiredParametersRule(['revenue_growth_rate'])
        result = rule.validate({})

        assert result.passed is False
        assert 'revenue_growth_rate' in result.errors[0]
