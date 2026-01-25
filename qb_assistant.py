#!/usr/bin/env python3
"""
QB-Assistant Main Application Entry Point

Simple launcher for non-technical bookkeeper users. Double-click this script
(or run via 'python qb_assistant.py') to start the application.

This script:
1. Auto-detects project root directory
2. Creates necessary directories (clients/, config/) if they don't exist
3. Sets up basic logging to qb_assistant.log for debugging
4. Launches the GUI with client selection screen
"""

import os
import sys
import logging
from pathlib import Path


def setup_logging(project_root: Path) -> None:
    """
    Configure basic logging to file for debugging.

    Args:
        project_root: Path to project root directory
    """
    log_file = project_root / "qb_assistant.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("QB-Assistant starting...")
    logging.debug(f"Project root: {project_root}")


def create_directories(project_root: Path) -> None:
    """
    Create necessary application directories if they don't exist.

    Args:
        project_root: Path to project root directory
    """
    clients_dir = project_root / "clients"
    config_dir = project_root / "config"

    # Create clients directory
    if not clients_dir.exists():
        clients_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created clients directory: {clients_dir}")
    else:
        logging.debug(f"Clients directory exists: {clients_dir}")

    # Create config directory
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created config directory: {config_dir}")
    else:
        logging.debug(f"Config directory exists: {config_dir}")


def main():
    """
    Main application entry point.

    Initializes application environment and launches GUI.
    """
    try:
        # Auto-detect project root (directory containing this script)
        project_root = Path(__file__).parent.resolve()

        # Set up logging
        setup_logging(project_root)

        # Create necessary directories
        create_directories(project_root)

        # Import application components (after logging setup for better error reporting)
        from src.gui.app import App
        from src.gui.forms.client_selection_form import ClientSelectionForm

        logging.info("Initializing application...")

        # Initialize application with project root
        app = App(str(project_root))

        # Show client selection form as initial screen
        # User must select a client before proceeding
        logging.info("Launching client selection screen...")
        app.show_form(ClientSelectionForm)

        # Start GUI event loop
        logging.info("Application ready - starting event loop")
        app.mainloop()

        logging.info("Application closed normally")

    except Exception as e:
        # Log any startup errors
        logging.error(f"Application startup failed: {e}", exc_info=True)

        # Try to show error dialog if tkinter is available
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "QB-Assistant Startup Error",
                f"Failed to start application:\n\n{str(e)}\n\nCheck qb_assistant.log for details."
            )
        except:
            # If GUI error dialog fails, just print to console
            print(f"ERROR: Failed to start application: {e}", file=sys.stderr)
            print("Check qb_assistant.log for details.", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
