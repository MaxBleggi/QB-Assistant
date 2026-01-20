"""
Persistence layer for parameter configuration.

Provides JSON-based configuration file management with error handling.
"""
from .config_manager import ConfigManager

__all__ = [
    'ConfigManager',
]
