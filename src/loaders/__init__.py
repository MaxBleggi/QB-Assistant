"""
File loading module for QuickBooks data.

Provides automatic CSV/Excel format detection and comprehensive error handling.
"""
from .exceptions import (
    CorruptedFileError,
    EmptyFileError,
    FileLoaderError,
    UnsupportedFileFormatError,
)
from .file_loader import FileLoader

__all__ = [
    'FileLoader',
    'FileLoaderError',
    'UnsupportedFileFormatError',
    'EmptyFileError',
    'CorruptedFileError',
]
