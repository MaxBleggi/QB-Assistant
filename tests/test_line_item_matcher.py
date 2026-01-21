"""
Tests for LineItemMatcher - helper for matching budget accounts to actual accounts.

Covers:
- Exact matching (case-sensitive and case-insensitive)
- Fuzzy matching with various similarity levels
- Unmatched account tracking
- Section-aware matching (Income vs Expenses isolation)
- Threshold behavior (cutoff at 75% similarity)
"""
import pytest

from src.services.line_item_matcher import LineItemMatcher


@pytest.fixture
def budget_hierarchy_exact_match():
    """Budget hierarchy with accounts for exact matching tests."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Product Revenue', 'values': {'2024-01': 100000}},
                {'name': 'Service Revenue', 'values': {'2024-01': 50000}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Marketing', 'values': {'2024-01': 20000}},
                {'name': 'Sales', 'values': {'2024-01': 30000}}
            ]
        }
    }


@pytest.fixture
def actual_hierarchy_exact_match():
    """Actual hierarchy with identical account names."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Product Revenue', 'values': {'2024-01': 120000}},
                {'name': 'Service Revenue', 'values': {'2024-01': 55000}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Marketing', 'values': {'2024-01': 18000}},
                {'name': 'Sales', 'values': {'2024-01': 32000}}
            ]
        }
    }


@pytest.fixture
def budget_hierarchy_fuzzy():
    """Budget hierarchy for fuzzy matching tests."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Product Revenue', 'values': {}},
                {'name': 'Sales', 'values': {}},
                {'name': 'Consulting Fees', 'values': {}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Marketing Costs', 'values': {}},
                {'name': 'Engineering', 'values': {}}
            ]
        }
    }


@pytest.fixture
def actual_hierarchy_fuzzy():
    """Actual hierarchy with typos and variations."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Product  Revenue', 'values': {}},  # Extra space
                {'name': 'Sale', 'values': {}},  # Missing 's'
                {'name': 'Service Revenue', 'values': {}}  # Not in budget
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Marketing Cost', 'values': {}},  # Singular instead of plural
                {'name': 'Research', 'values': {}}  # Not in budget (too dissimilar to Engineering)
            ]
        }
    }


@pytest.fixture
def budget_hierarchy_cross_section():
    """Budget hierarchy with same account name in different sections."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Revenue', 'values': {}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Revenue', 'values': {}}  # Same name, different section
            ]
        }
    }


@pytest.fixture
def actual_hierarchy_cross_section():
    """Actual hierarchy with same account name in different sections."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Revenue', 'values': {}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Revenue', 'values': {}}
            ]
        }
    }


class TestLineItemMatcher:
    """Test suite for LineItemMatcher."""

    def test_exact_match(self, budget_hierarchy_exact_match, actual_hierarchy_exact_match):
        """Test identical account names match correctly."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_exact_match,
            actual_hierarchy_exact_match
        )

        # All accounts should match exactly
        assert mappings['Income']['Product Revenue'] == 'Product Revenue'
        assert mappings['Income']['Service Revenue'] == 'Service Revenue'
        assert mappings['Expenses']['Marketing'] == 'Marketing'
        assert mappings['Expenses']['Sales'] == 'Sales'

        # No unmatched accounts
        assert unmatched_budget == []
        assert unmatched_actual == []

    def test_case_insensitive_exact_match(self):
        """Test 'Revenue' matches 'revenue' (case-insensitive)."""
        budget_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {}}
                ]
            }
        }

        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'revenue', 'values': {}}
                ]
            }
        }

        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy,
            actual_hierarchy
        )

        assert mappings['Income']['Revenue'] == 'revenue'
        assert unmatched_budget == []
        assert unmatched_actual == []

    def test_fuzzy_match_with_typo(self, budget_hierarchy_fuzzy, actual_hierarchy_fuzzy):
        """Test 'Sales' matches 'Sale' (fuzzy match)."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_fuzzy,
            actual_hierarchy_fuzzy
        )

        # 'Sales' should fuzzy match to 'Sale'
        assert mappings['Income']['Sales'] == 'Sale'

    def test_fuzzy_match_with_extra_space(self, budget_hierarchy_fuzzy, actual_hierarchy_fuzzy):
        """Test 'Product Revenue' matches 'Product  Revenue' (extra space)."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_fuzzy,
            actual_hierarchy_fuzzy
        )

        # 'Product Revenue' should fuzzy match to 'Product  Revenue'
        assert mappings['Income']['Product Revenue'] == 'Product  Revenue'

    def test_fuzzy_match_singular_plural(self, budget_hierarchy_fuzzy, actual_hierarchy_fuzzy):
        """Test 'Marketing Costs' matches 'Marketing Cost' (plural/singular)."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_fuzzy,
            actual_hierarchy_fuzzy
        )

        # 'Marketing Costs' should fuzzy match to 'Marketing Cost'
        assert mappings['Expenses']['Marketing Costs'] == 'Marketing Cost'

    def test_no_match_below_threshold(self, budget_hierarchy_fuzzy, actual_hierarchy_fuzzy):
        """Test accounts below 75% similarity not matched."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_fuzzy,
            actual_hierarchy_fuzzy
        )

        # 'Engineering' and 'Research' are too dissimilar (below 75% threshold)
        assert 'Engineering' in unmatched_budget
        assert 'Research' in unmatched_actual

    def test_unmatched_budget_account(self, budget_hierarchy_fuzzy, actual_hierarchy_fuzzy):
        """Test budget account without match appears in unmatched_budget_accounts."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_fuzzy,
            actual_hierarchy_fuzzy
        )

        # 'Consulting Fees' has no match in actual
        assert 'Consulting Fees' in unmatched_budget

    def test_unmatched_actual_account(self, budget_hierarchy_fuzzy, actual_hierarchy_fuzzy):
        """Test actual account without match appears in unmatched_actual_accounts."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_fuzzy,
            actual_hierarchy_fuzzy
        )

        # 'Service Revenue' has no match in budget
        assert 'Service Revenue' in unmatched_actual

    def test_section_aware_matching(self, budget_hierarchy_cross_section, actual_hierarchy_cross_section):
        """Test accounts match within same section only, not cross-section."""
        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy_cross_section,
            actual_hierarchy_cross_section
        )

        # Income 'Revenue' should match Income 'Revenue'
        assert mappings['Income']['Revenue'] == 'Revenue'

        # Expenses 'Revenue' should match Expenses 'Revenue'
        assert mappings['Expenses']['Revenue'] == 'Revenue'

        # Both mappings exist but are in separate sections
        assert 'Income' in mappings
        assert 'Expenses' in mappings

        # No cross-section matching
        assert unmatched_budget == []
        assert unmatched_actual == []

    def test_empty_section_handling(self):
        """Test handling of empty sections."""
        budget_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': []
            },
            'Expenses': {
                'name': 'Expenses',
                'children': [
                    {'name': 'Marketing', 'values': {}}
                ]
            }
        }

        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {}}
                ]
            },
            'Expenses': {
                'name': 'Expenses',
                'children': []
            }
        }

        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy,
            actual_hierarchy
        )

        # Empty sections should not cause errors
        assert 'Marketing' in unmatched_budget
        assert 'Revenue' in unmatched_actual

    def test_parent_nodes_skipped(self):
        """Test parent nodes are skipped during account extraction."""
        budget_hierarchy = {
            'Income': {
                'name': 'Income',
                'parent': True,  # Parent node
                'children': [
                    {
                        'name': 'Product Sales',
                        'parent': True,  # Parent subcategory
                        'children': [
                            {'name': 'Product A', 'values': {}},
                            {'name': 'Product B', 'values': {}}
                        ]
                    }
                ]
            }
        }

        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Product Sales',
                        'parent': True,
                        'children': [
                            {'name': 'Product A', 'values': {}},
                            {'name': 'Product B', 'values': {}}
                        ]
                    }
                ]
            }
        }

        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy,
            actual_hierarchy
        )

        # Only leaf nodes should be matched
        assert mappings['Income']['Product A'] == 'Product A'
        assert mappings['Income']['Product B'] == 'Product B'

        # Parent nodes should not appear in mappings
        assert 'Income' not in mappings['Income']
        assert 'Product Sales' not in mappings['Income']

    def test_missing_section_handling(self):
        """Test handling when a section is missing from one hierarchy."""
        budget_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {}}
                ]
            }
            # No Expenses section
        }

        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {}}
                ]
            },
            'Expenses': {
                'name': 'Expenses',
                'children': [
                    {'name': 'Marketing', 'values': {}}
                ]
            }
        }

        mappings, unmatched_budget, unmatched_actual = LineItemMatcher.match_accounts(
            budget_hierarchy,
            actual_hierarchy
        )

        # Income should match
        assert mappings['Income']['Revenue'] == 'Revenue'

        # Expenses from actual should be unmatched (no Expenses in budget)
        assert 'Marketing' in unmatched_actual
