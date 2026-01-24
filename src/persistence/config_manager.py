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
                     Can be either:
                     - 'filename.json' -> resolves to config/filename.json
                     - 'config/filename.json' -> also resolves to config/filename.json

        Returns:
            Validated absolute Path object

        Raises:
            ValueError: If filepath is outside config directory or contains traversal sequences
        """
        requested_path = Path(filepath)

        # Convert to absolute path
        if not requested_path.is_absolute():
            # If path starts with 'config/', resolve relative to project_root
            # Otherwise resolve relative to config_dir for backward compatibility
            if str(filepath).startswith('config/') or str(filepath).startswith('config\\'):
                full_path = (self.project_root / requested_path).resolve()
            else:
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

    def load_config(self, filepath: str, model_class=None) -> ParameterModel:
        """
        Load ParameterModel (or subclass) from JSON configuration file.

        Args:
            filepath: Path to JSON file (relative to config directory or absolute within config)
            model_class: Model class to instantiate (default: ParameterModel). Must have from_dict classmethod.

        Returns:
            ParameterModel instance (or subclass) with loaded parameters

        Raises:
            ValueError: If filepath is invalid or outside config directory
            JSONDecodeError: If file contains invalid JSON syntax
            PermissionError: If insufficient permissions to read file
            Exception: If model_class.from_dict fails
        """
        # Default to ParameterModel for backward compatibility
        if model_class is None:
            model_class = ParameterModel

        validated_path = self._validate_filepath(filepath)

        # Handle missing file - create default, save it, and return
        if not validated_path.exists():
            default_instance = model_class()
            self.save_config(default_instance, filepath)
            return default_instance

        # Read and parse JSON with context manager
        try:
            with open(validated_path, 'r') as f:
                data = json.load(f)

            # Reconstruct model from dict using provided model_class
            return model_class.from_dict(data)

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
        except Exception as e:
            # Wrap model_class.from_dict errors with context
            raise Exception(
                f"Failed to load config from {filepath} using {model_class.__name__}: {str(e)}"
            ) from e
