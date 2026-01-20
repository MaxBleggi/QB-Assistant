"""
Metrics calculation package for revenue and margin analysis.

Provides calculators for revenue metrics and margin analysis using PLModel data.
"""
from .revenue_calculator import RevenueCalculator
from .margin_calculator import MarginCalculator
from .exceptions import (
    CalculationError,
    MissingPeriodError,
    InvalidDataError,
    ZeroDivisionError,
)

__all__ = [
    'RevenueCalculator',
    'MarginCalculator',
    'CalculationError',
    'MissingPeriodError',
    'InvalidDataError',
    'ZeroDivisionError',
]
