"""
Client manager service for client folder discovery, creation, deletion, and validation.

Handles client folder structure (clients/[name]/) with security-first design to
prevent path traversal attacks and ensure safe filesystem operations.
"""
import re
import shutil
from pathlib import Path
from typing import List


class ClientManager:
    """
    Service layer for client folder management with security validation.

    Provides static methods for client discovery, creation, deletion, and name
    validation with strict security controls to prevent directory traversal.
    """

    @staticmethod
    def validate_client_name(name: str) -> str:
        """
        Validate client name against security constraints.

        Enforces strict whitelist validation to prevent path traversal attacks:
        - Only alphanumeric characters, hyphens, and underscores allowed
        - Length limit of 100 characters
        - No empty strings or whitespace-only names
        - Explicit checks for path traversal sequences

        Args:
            name: Client name to validate

        Returns:
            Validated and stripped client name

        Raises:
            ValueError: If name contains invalid characters, is too long, or is empty
        """
        if not name or not name.strip():
            raise ValueError("Client name cannot be empty")

        name = name.strip()

        if len(name) > 100:
            raise ValueError("Client name too long (max 100 characters)")

        # Strict whitelist: alphanumeric, hyphens, underscores only
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError(
                f"Client name contains invalid characters. "
                f"Only letters, numbers, hyphens, and underscores allowed."
            )

        # Explicit path traversal checks (defense in depth)
        if '..' in name or '/' in name or '\\' in name:
            raise ValueError("Client name contains path traversal sequences")

        return name

    @staticmethod
    def discover_clients(project_root: Path) -> List[str]:
        """
        Discover existing client folders by scanning clients/ directory.

        Args:
            project_root: Project root path

        Returns:
            List of client folder names (empty list if clients/ doesn't exist)
        """
        clients_dir = project_root / "clients"

        # Return empty list if clients directory doesn't exist
        if not clients_dir.exists():
            return []

        # Scan for directories only (ignore files)
        client_names = []
        for item in clients_dir.iterdir():
            if item.is_dir():
                client_names.append(item.name)

        return sorted(client_names)

    @staticmethod
    def create_client(name: str, project_root: Path) -> None:
        """
        Create new client folder with validation and default configuration.

        Creates directory structure:
        - clients/[name]/
        - clients/[name]/input/
        - clients/[name]/config.yaml (with default settings)

        Args:
            name: Client name (will be validated)
            project_root: Project root path

        Raises:
            ValueError: If client name invalid or client already exists
        """
        # Step 1: Validate name
        validated_name = ClientManager.validate_client_name(name)

        # Step 2: Construct paths
        clients_dir = project_root / "clients"
        client_path = clients_dir / validated_name
        input_path = client_path / "input"
        config_path = client_path / "config.yaml"

        # Step 3: Create clients/ directory if needed (one-time setup)
        clients_dir.mkdir(exist_ok=True)

        # Step 4: Resolve and validate before creation (prevent TOCTOU)
        try:
            resolved_client = client_path.resolve()
            resolved_client.relative_to(clients_dir.resolve())
        except (ValueError, RuntimeError):
            raise ValueError("Client path resolves outside clients directory")

        # Step 5: Create client directory (fail if exists - prevent race condition)
        try:
            client_path.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            raise ValueError(f"Client '{name}' already exists")

        # Step 6: Create subdirectories and config
        input_path.mkdir(parents=False, exist_ok=False)

        # Initialize default config
        from ..models.client_config import ClientConfigModel
        from ..persistence.config_manager import ConfigManager

        default_config = ClientConfigModel()

        config_mgr = ConfigManager(project_root)
        # allow_external_path=True enables saving to clients/ (outside config/)
        config_mgr.save_config(default_config, str(config_path), allow_external_path=True)

    @staticmethod
    def delete_client(name: str, project_root: Path) -> None:
        """
        Delete client folder after validation.

        Uses path canonicalization and validation to ensure only intended
        directory is deleted (prevents symlink attacks and path traversal).

        Args:
            name: Client name to delete
            project_root: Project root path

        Raises:
            ValueError: If client name invalid, path unsafe, or client doesn't exist
        """
        # Step 1: Validate name
        validated_name = ClientManager.validate_client_name(name)

        # Step 2: Construct and resolve path
        clients_dir = project_root / "clients"
        client_path = clients_dir / validated_name

        try:
            # Resolve to canonical path (follows symlinks)
            resolved_path = client_path.resolve()

            # Step 3: Verify path is under clients/ directory
            resolved_path.relative_to(clients_dir.resolve())
        except (ValueError, RuntimeError):
            raise ValueError(
                f"Client path resolves outside clients directory: {client_path}"
            )

        # Step 4: Verify exists and is directory
        if not resolved_path.exists():
            raise ValueError(f"Client '{name}' does not exist")

        if not resolved_path.is_dir():
            raise ValueError(f"Client path is not a directory: {resolved_path}")

        # Step 5: Safe to delete
        shutil.rmtree(resolved_path)
