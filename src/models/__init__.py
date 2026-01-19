"""
Data models for representing validated QuickBooks data.

Provides base DataModel wrapper and will include document-specific models
(BalanceSheetModel, PLModel, CashFlowModel) in future sprints.
"""
from .base import DataModel

__all__ = [
    'DataModel',
]
