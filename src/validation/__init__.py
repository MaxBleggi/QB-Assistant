"""
Validation framework for DataFrame structure and content validation.

Provides composable validation rules and orchestration via Validator class.
"""
from .rules import (
    DataTypeRule,
    NonEmptyRule,
    RequiredColumnsRule,
    StructuralConsistencyRule,
    ValidationResult,
    ValidationRule,
)
from .validator import ValidationReport, Validator

__all__ = [
    'Validator',
    'ValidationRule',
    'ValidationResult',
    'ValidationReport',
    'RequiredColumnsRule',
    'DataTypeRule',
    'NonEmptyRule',
    'StructuralConsistencyRule',
]
