"""
Parameter validation rules for type checking, range validation, and required keys.

Adapts ValidationRule pattern for dict-based validation (parameters are key-value
pairs, not tabular DataFrame data).
"""
from typing import Any, Dict, List, Type

from .rules import ValidationResult, ValidationRule


class RangeValidationRule(ValidationRule):
    """
    Validates that a numeric parameter is within specified min/max bounds.

    Used for parameters like percentages (0-1), growth rates (-1 to 1), etc.
    """

    def __init__(self, param_name: str, min_value: float, max_value: float):
        """
        Initialize range validation rule.

        Args:
            param_name: Name of parameter to validate
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
        """
        self.param_name = param_name
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate parameter is within range.

        Args:
            data: Dictionary of parameters (not DataFrame)

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Check if parameter exists in data
        if self.param_name not in data:
            # Parameter doesn't exist - not this rule's responsibility
            # (RequiredParametersRule should catch this)
            return ValidationResult(passed=True, errors=[])

        value = data[self.param_name]

        # Validate value is numeric
        if not isinstance(value, (int, float)):
            errors.append(
                f"{self.param_name}: must be numeric, got {type(value).__name__}"
            )
            return ValidationResult(passed=False, errors=errors)

        # Check range bounds
        if value < self.min_value or value > self.max_value:
            errors.append(
                f"{self.param_name}: must be between {self.min_value} and {self.max_value}, got {value}"
            )

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])


class TypeValidationRule(ValidationRule):
    """
    Validates that a parameter matches the expected Python type.

    Used to ensure parameters are correct type (int, float, str, bool, etc.)
    before use in calculations or business logic.
    """

    def __init__(self, param_name: str, expected_type: Type):
        """
        Initialize type validation rule.

        Args:
            param_name: Name of parameter to validate
            expected_type: Expected Python type (e.g., int, float, str, bool)
        """
        self.param_name = param_name
        self.expected_type = expected_type

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate parameter has correct type.

        Args:
            data: Dictionary of parameters (not DataFrame)

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Check if parameter exists in data
        if self.param_name not in data:
            # Parameter doesn't exist - not this rule's responsibility
            return ValidationResult(passed=True, errors=[])

        value = data[self.param_name]

        # Validate type
        if not isinstance(value, self.expected_type):
            errors.append(
                f"{self.param_name}: must be {self.expected_type.__name__}, got {type(value).__name__}"
            )

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])


class RequiredParametersRule(ValidationRule):
    """
    Validates that all required parameter keys exist in the data dictionary.

    Used to ensure mandatory parameters are present before processing.
    """

    def __init__(self, required_keys: List[str]):
        """
        Initialize required parameters rule.

        Args:
            required_keys: List of parameter names that must be present
        """
        self.required_keys = required_keys

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate all required keys exist in data.

        Args:
            data: Dictionary of parameters (not DataFrame)

        Returns:
            ValidationResult with pass/fail status and errors
        """
        errors = []

        # Check each required key
        for key in self.required_keys:
            if key not in data:
                errors.append(f"Required parameter missing: {key}")

        if errors:
            return ValidationResult(passed=False, errors=errors)

        return ValidationResult(passed=True, errors=[])
