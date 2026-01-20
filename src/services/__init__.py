"""
Services for business logic and defaults calculation.

Services provide separation between GUI presentation layer and business logic,
enabling independent testing and reusability.
"""
from .budget_defaults import BudgetDefaultsService

__all__ = [
    'BudgetDefaultsService',
]
