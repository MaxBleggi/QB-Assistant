"""
Metrics calculation package for revenue and margin analysis.

Provides calculators for revenue metrics and margin analysis using PLModel data.
"""
from .cash_flow_calculator import CashFlowCalculator
from .liquidity_calculator import LiquidityCalculator
from .margin_calculator import MarginCalculator
from .revenue_calculator import RevenueCalculator
from .exceptions import (
    CalculationError,
    MissingPeriodError,
    InvalidDataError,
    ZeroDivisionError,
)

__all__ = [
    'CashFlowCalculator',
    'LiquidityCalculator',
    'MarginCalculator',
    'RevenueCalculator',
    'CalculationError',
    'MissingPeriodError',
    'InvalidDataError',
    'ZeroDivisionError',
]
