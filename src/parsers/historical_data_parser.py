"""
HistoricalDataParser - Parser for historical P&L data files for budget calculations.

Reuses PLParser via composition to handle QuickBooks P&L structure with 12 monthly columns.
Adds historical-specific validation: account mapping and data completeness checks.

Returns PLModel with period-aware values for downstream budget calculations.
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Union

from ..loaders.file_loader import FileLoader
from ..models.pl_model import PLModel
from .pl_parser import PLParser

logger = logging.getLogger(__name__)


class HistoricalDataParser:
    """
    Parser for historical financial data files with validation.

    Uses PLParser composition to handle QuickBooks P&L structure with multiple
    monthly period columns. Validates data completeness and provides account
    mapping capabilities for matching historical to current accounts.
    """

    def __init__(self, file_loader: FileLoader):
        """
        Initialize parser with FileLoader dependency.

        Args:
            file_loader: FileLoader instance for file I/O
        """
        self.file_loader = file_loader
        self._pl_parser = PLParser(file_loader)

    def parse(self, file_path: Union[str, Path]) -> PLModel:
        """
        Parse historical data file and return PLModel with validation.

        Process:
        1. Delegate parsing to PLParser (handles 12 monthly columns)
        2. Validate data completeness (period count, sparse data, key sections)
        3. Log warnings for any completeness issues
        4. Return PLModel even if validation warnings exist

        Args:
            file_path: Path to historical P&L CSV file

        Returns:
            PLModel with period-aware values for all 12 months

        Raises:
            ValueError: If file structure is invalid (delegated from PLParser)
        """
        # Delegate parsing to PLParser
        logger.info(f"Parsing historical data file: {file_path}")
        model = self._pl_parser.parse(file_path)

        # Validate completeness
        warnings = self.validate_completeness(model)

        # Log all warnings
        for warning in warnings:
            logger.warning(warning)

        if not warnings:
            logger.info("Historical data validation complete - no issues found")
        else:
            logger.info(f"Historical data validation complete - {len(warnings)} warning(s) logged")

        return model

    def validate_account_mapping(
        self,
        current_accounts: List[str],
        historical_model: PLModel
    ) -> Dict[str, List[str]]:
        """
        Validate account mapping between current and historical accounts.

        Performs case-insensitive exact match validation between current account
        list and accounts found in historical model hierarchy. Returns mapping
        results with matched, missing, and extra accounts.

        Args:
            current_accounts: List of current period account names
            historical_model: Parsed PLModel from historical data file

        Returns:
            Dict with keys:
                - 'matched_accounts': List of accounts found in both (using current names)
                - 'missing_in_historical': Accounts in current but not historical
                - 'extra_in_historical': Accounts in historical but not current
        """
        # Extract all account names from historical hierarchy
        historical_accounts = self._extract_account_names(historical_model.hierarchy)

        # Create case-insensitive lookup sets (store as lowercase for comparison)
        current_lookup = {name.lower(): name for name in current_accounts}
        historical_lookup = {name.lower(): name for name in historical_accounts}

        # Find matched accounts (case-insensitive)
        matched = []
        for lower_name, original_name in current_lookup.items():
            if lower_name in historical_lookup:
                matched.append(original_name)  # Use current period name

        # Find missing accounts (in current but not historical)
        missing = []
        for lower_name, original_name in current_lookup.items():
            if lower_name not in historical_lookup:
                missing.append(original_name)
                logger.warning(
                    f"Account mapping: '{original_name}' exists in current period "
                    f"but missing in historical data"
                )

        # Find extra accounts (in historical but not current)
        extra = []
        for lower_name, original_name in historical_lookup.items():
            if lower_name not in current_lookup:
                extra.append(original_name)
                logger.warning(
                    f"Account mapping: '{original_name}' exists in historical data "
                    f"but not in current period"
                )

        return {
            'matched_accounts': matched,
            'missing_in_historical': missing,
            'extra_in_historical': extra
        }

    def validate_completeness(self, model: PLModel) -> List[str]:
        """
        Validate data completeness for historical model.

        Checks:
        1. Period count (warns if < 12 months)
        2. Sparse account data (accounts missing values for some periods)
        3. Key sections exist (Income, Cost of Goods Sold, Expenses)

        Args:
            model: PLModel from historical data file

        Returns:
            List of warning messages (empty if no issues)
        """
        warnings = []

        # Check period count
        periods = model.get_periods()
        if len(periods) < 12:
            warning = (
                f"Insufficient historical periods: found {len(periods)} months, "
                f"expected 12 for full year budget calculations"
            )
            warnings.append(warning)

        # Check for sparse account data
        sparse_accounts = self._check_sparse_accounts(model.hierarchy, len(periods))
        if sparse_accounts:
            warning = (
                f"Sparse account data detected: {len(sparse_accounts)} account(s) "
                f"missing values for some periods: {', '.join(sparse_accounts[:5])}"
                + (f" and {len(sparse_accounts) - 5} more" if len(sparse_accounts) > 5 else "")
            )
            warnings.append(warning)

        # Check key sections exist
        missing_sections = []
        if not model.get_income():
            missing_sections.append('Income')
        # Note: COGS is optional (service businesses may not have it)
        # Only check if Expenses exists
        if not model.get_expenses():
            missing_sections.append('Expenses')

        if missing_sections:
            warning = (
                f"Missing key sections in historical data: {', '.join(missing_sections)}"
            )
            warnings.append(warning)

        return warnings

    def _extract_account_names(self, hierarchy: Dict[str, Any]) -> List[str]:
        """
        Extract all account names from hierarchy tree.

        Recursively walks hierarchy to collect all account 'name' fields,
        excluding calculated rows (which don't have 'name' field in hierarchy).

        Args:
            hierarchy: Hierarchy dict from PLModel

        Returns:
            List of all account names found in hierarchy
        """
        account_names = []

        def walk_tree(node: Any):
            """Recursively walk tree and collect account names."""
            if isinstance(node, dict):
                # If this node has a name, collect it
                if 'name' in node:
                    account_names.append(node['name'])

                # Recurse into children if present
                if 'children' in node:
                    for child in node['children']:
                        walk_tree(child)

                # Recurse into other dict values
                for key, value in node.items():
                    if key not in ('name', 'children', 'values', 'parent', 'total'):
                        walk_tree(value)

            elif isinstance(node, list):
                # Recurse into list items
                for item in node:
                    walk_tree(item)

        walk_tree(hierarchy)
        return account_names

    def _check_sparse_accounts(
        self,
        hierarchy: Dict[str, Any],
        expected_period_count: int
    ) -> List[str]:
        """
        Check for accounts with missing values for some periods.

        Walks hierarchy to find accounts where len(values) < expected_period_count.

        Args:
            hierarchy: Hierarchy dict from PLModel
            expected_period_count: Expected number of periods

        Returns:
            List of account names with sparse data
        """
        sparse_accounts = []

        def walk_tree(node: Any):
            """Recursively check accounts for sparse data."""
            if isinstance(node, dict):
                # Check if this node has values and a name
                if 'values' in node and 'name' in node:
                    values_dict = node['values']
                    if isinstance(values_dict, dict):
                        if len(values_dict) < expected_period_count:
                            sparse_accounts.append(node['name'])

                # Recurse into children if present
                if 'children' in node:
                    for child in node['children']:
                        walk_tree(child)

                # Recurse into other dict values
                for key, value in node.items():
                    if key not in ('name', 'children', 'values', 'parent', 'total'):
                        walk_tree(value)

            elif isinstance(node, list):
                # Recurse into list items
                for item in node:
                    walk_tree(item)

        walk_tree(hierarchy)
        return sparse_accounts
