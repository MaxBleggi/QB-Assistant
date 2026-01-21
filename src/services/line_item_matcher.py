"""
LineItemMatcher helper for matching budget account names to actual account names.

Implements two-pass matching strategy:
1. Exact match (case-insensitive)
2. Fuzzy match using difflib for remaining accounts

Matches accounts within same section only (Income to Income, Expenses to Expenses).
"""
from typing import Any, Dict, List, Tuple
import difflib


class LineItemMatcher:
    """
    Helper for matching budget account names to actual P&L account names.

    Handles account name variations (typos, spacing differences, abbreviations)
    through exact matching followed by fuzzy matching with configurable threshold.
    """

    @staticmethod
    def match_accounts(
        budget_hierarchy: Dict[str, Any],
        actual_hierarchy: Dict[str, Any]
    ) -> Tuple[Dict[str, Dict[str, str]], List[str], List[str]]:
        """
        Match budget accounts to actual accounts within each section.

        Strategy:
        1. Extract account names from each section separately
        2. First pass: exact match (case-insensitive)
        3. Second pass: fuzzy match for remaining unmatched accounts
        4. Return mappings per section plus unmatched lists

        Args:
            budget_hierarchy: Budget hierarchy tree with sections (Income, Expenses)
            actual_hierarchy: Actual P&L hierarchy tree with sections (Income, Expenses)

        Returns:
            Tuple of (section_mappings, unmatched_budget_accounts, unmatched_actual_accounts)
            - section_mappings: Dict mapping section name to dict of {budget_name: actual_name}
            - unmatched_budget_accounts: List of budget account names without matches
            - unmatched_actual_accounts: List of actual account names without matches
        """
        section_mappings = {}
        all_unmatched_budget = []
        all_unmatched_actual = []

        # Process each section separately (Income, Expenses)
        for section_name in ['Income', 'Expenses']:
            # Extract account names from both hierarchies
            budget_accounts = LineItemMatcher._extract_account_names(
                budget_hierarchy.get(section_name, {})
            )
            actual_accounts = LineItemMatcher._extract_account_names(
                actual_hierarchy.get(section_name, {})
            )

            # Match accounts within this section
            section_mapping, unmatched_budget, unmatched_actual = LineItemMatcher._match_account_lists(
                budget_accounts,
                actual_accounts
            )

            # Store results
            section_mappings[section_name] = section_mapping
            all_unmatched_budget.extend(unmatched_budget)
            all_unmatched_actual.extend(unmatched_actual)

        return section_mappings, all_unmatched_budget, all_unmatched_actual

    @staticmethod
    def _extract_account_names(section_hierarchy: Dict[str, Any]) -> List[str]:
        """
        Extract all account names from a section hierarchy.

        Recursively traverses hierarchy tree, collecting names from leaf nodes
        (skipping parent nodes which are just containers).

        Args:
            section_hierarchy: Section dict from hierarchy tree

        Returns:
            List of account names (leaf nodes only)
        """
        names = []

        def traverse(node: Any) -> None:
            """Recursively collect account names."""
            if isinstance(node, dict):
                # Skip parent nodes - they're just containers
                if node.get('parent', False):
                    # Still traverse children
                    if 'children' in node:
                        for child in node['children']:
                            traverse(child)
                    return

                # Collect leaf node name
                if 'name' in node and not node.get('parent', False):
                    names.append(node['name'])

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        traverse(child)

            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(section_hierarchy)
        return names

    @staticmethod
    def _match_account_lists(
        budget_accounts: List[str],
        actual_accounts: List[str]
    ) -> Tuple[Dict[str, str], List[str], List[str]]:
        """
        Match two lists of account names using exact + fuzzy matching.

        Args:
            budget_accounts: List of budget account names
            actual_accounts: List of actual account names

        Returns:
            Tuple of (mapping, unmatched_budget, unmatched_actual)
            - mapping: Dict mapping budget account name to actual account name
            - unmatched_budget: List of budget accounts without matches
            - unmatched_actual: List of actual accounts without matches
        """
        mapping = {}
        remaining_budget = set(budget_accounts)
        remaining_actual = set(actual_accounts)

        # First pass: exact match (case-insensitive)
        for budget_name in list(remaining_budget):
            for actual_name in list(remaining_actual):
                if budget_name.lower() == actual_name.lower():
                    mapping[budget_name] = actual_name
                    remaining_budget.remove(budget_name)
                    remaining_actual.remove(actual_name)
                    break

        # Second pass: fuzzy match for remaining accounts
        for budget_name in list(remaining_budget):
            # Find closest match using difflib
            matches = difflib.get_close_matches(
                budget_name,
                remaining_actual,
                n=1,
                cutoff=0.75  # 75% similarity threshold
            )

            if matches:
                actual_name = matches[0]
                mapping[budget_name] = actual_name
                remaining_budget.remove(budget_name)
                remaining_actual.remove(actual_name)

        # Return mapping and unmatched lists
        return mapping, list(remaining_budget), list(remaining_actual)
