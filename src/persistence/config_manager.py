"""
Configuration manager for JSON-based parameter persistence.

Handles save/load operations with comprehensive error handling and path validation
to prevent directory traversal attacks.
"""
import json
import os
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Optional

from ..models.parameters import ParameterModel


class ConfigManager:
    """
    Manages parameter configuration file I/O with security and error handling.

    Validates file paths to prevent directory traversal, handles missing files,
    invalid JSON, and permission errors gracefully.
    """

    def __init__(self, project_root: str):
        """
        Initialize config manager with project root directory.

        Args:
            project_root: Absolute path to project root directory
        """
        self.project_root = Path(project_root).resolve()
        self.config_dir = (self.project_root / 'config').resolve()

    def _validate_filepath(self, filepath: str) -> Path:
        """
        Validate filepath is within config directory, prevent directory traversal.

        Args:
            filepath: Requested file path (relative or absolute)

        Returns:
            Validated absolute Path object

        Raises:
            ValueError: If filepath is outside config directory or contains traversal sequences
        """
        requested_path = Path(filepath)

        # Convert to absolute path relative to config directory if relative
        if not requested_path.is_absolute():
            full_path = (self.config_dir / requested_path).resolve()
        else:
            full_path = requested_path.resolve()

        # Security check: ensure resolved path is within config directory
        try:
            full_path.relative_to(self.config_dir)
        except ValueError:
            raise ValueError(
                f"Invalid path '{filepath}': must be within config directory"
            )

        return full_path

    def save_config(self, model: ParameterModel, filepath: str) -> None:
        """
        Save ParameterModel to JSON configuration file.

        Args:
            model: ParameterModel instance to serialize
            filepath: Path to JSON file (relative to config directory or absolute within config)

        Raises:
            ValueError: If filepath is invalid or outside config directory
            PermissionError: If insufficient permissions to write file
            OSError: If other file I/O error occurs
        """
        validated_path = self._validate_filepath(filepath)

        # Create parent directories if they don't exist
        validated_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize model to dict
        data = model.to_dict()

        # Write JSON with context manager for automatic cleanup
        try:
            with open(validated_path, 'w') as f:
                json.dump(data, f, indent=2)
        except PermissionError:
            raise PermissionError(
                f"Cannot write to {filepath}: permission denied"
            )

    def load_config(self, filepath: str) -> ParameterModel:
        """
        Load ParameterModel from JSON configuration file.

        Args:
            filepath: Path to JSON file (relative to config directory or absolute within config)

        Returns:
            ParameterModel instance with loaded parameters

        Raises:
            ValueError: If filepath is invalid or outside config directory
            JSONDecodeError: If file contains invalid JSON syntax
            PermissionError: If insufficient permissions to read file
        """
        validated_path = self._validate_filepath(filepath)

        # Handle missing file - return default empty model
        if not validated_path.exists():
            return ParameterModel(parameters={})

        # Read and parse JSON with context manager
        try:
            with open(validated_path, 'r') as f:
                data = json.load(f)

            # Reconstruct ParameterModel from dict
            return ParameterModel.from_dict(data)

        except JSONDecodeError as e:
            # Re-raise with enhanced error message including file location
            raise JSONDecodeError(
                f"Invalid JSON in {filepath} at line {e.lineno}, column {e.colno}: {e.msg}",
                e.doc,
                e.pos
            )
        except PermissionError:
            raise PermissionError(
                f"Cannot read {filepath}: permission denied"
            )
