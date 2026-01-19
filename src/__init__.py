"""
QB-Assistant: QuickBooks data parsing and analysis framework.

Provides file loading, validation, and data model abstractions for
working with QuickBooks exports (Balance Sheets, P&L, Cash Flow).
"""

__version__ = "0.1.0"
__description__ = "QuickBooks data parsing and analysis framework"

# Public API re-exports could go here in the future
# For now, users should import from specific subpackages:
# - from src.loaders import FileLoader
# - from src.validation import Validator, RequiredColumnsRule
# - from src.models import DataModel

__all__ = [
    '__version__',
    '__description__',
]
