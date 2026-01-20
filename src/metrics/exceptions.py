"""
Custom exception hierarchy for calculation errors.

Provides actionable error messages to help users diagnose and fix calculation issues.
"""
from typing import List, Optional

from src.models import PLModel


class CalculationError(Exception):
    """Base exception for all calculation errors."""

    def __init__(self, message: str, pl_model: Optional[PLModel] = None):
        self.message = message
        self.pl_model = pl_model
        super().__init__(self.message)

    def __str__(self):
        return self.message


class MissingPeriodError(CalculationError):
    """Raised when requested period is not found in PLModel."""

    def __init__(self, period: str, available_periods: List[str], pl_model: Optional[PLModel] = None):
        self.period = period
        self.available_periods = available_periods

        message = (
            f"Period '{period}' not found in P&L data. "
            f"Available periods: {', '.join(available_periods)}. "
            f"Please ensure the requested period exists in your data."
        )
        super().__init__(message, pl_model)


class InvalidDataError(CalculationError):
    """Raised when required data is missing for calculation."""

    def __init__(self, data_type: str, calculation_type: str, pl_model: Optional[PLModel] = None):
        self.data_type = data_type
        self.calculation_type = calculation_type

        message = (
            f"{data_type} is required for {calculation_type} calculation but is not present in P&L data. "
            f"Please ensure your P&L statement includes {data_type} section."
        )
        super().__init__(message, pl_model)


class ZeroDivisionError(CalculationError):
    """Raised when denominator is zero in calculation."""

    def __init__(self, denominator_type: str, calculation_type: str, period: Optional[str] = None, pl_model: Optional[PLModel] = None):
        self.denominator_type = denominator_type
        self.calculation_type = calculation_type
        self.period = period

        period_info = f" for period '{period}'" if period else ""
        message = (
            f"Cannot calculate {calculation_type}: {denominator_type} is zero{period_info}. "
            f"Division by zero is undefined. Please review your data to ensure {denominator_type} is non-zero."
        )
        super().__init__(message, pl_model)
