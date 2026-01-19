"""
Unit tests for BalanceSheetModel.

Tests hierarchy accessors, account lookup, serialization/deserialization,
and edge cases for missing sections.
"""
import pandas as pd
import pytest

from src.models import BalanceSheetModel


# Module-level fixture accessible to all test classes
@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'account_name': ['Assets', 'Checking', 'Liabilities', 'Credit Card', 'Equity'],
        'row_type': ['section', 'child', 'section', 'child', 'section'],
        'numeric_value': [None, 1201.0, None, 157.72, None]
    })


class TestBalanceSheetModel:
    """Test suite for BalanceSheetModel class."""

    @pytest.fixture
    def sample_hierarchy(self):
        """Create sample hierarchy tree for testing."""
        return {
            'Assets': {
                'children': [
                    {
                        'name': 'Bank Accounts',
                        'parent': True,
                        'children': [
                            {'name': 'Checking', 'value': 1201.0},
                            {'name': 'Savings', 'value': 800.0}
                        ],
                        'total': 2001.0
                    }
                ]
            },
            'Liabilities': {
                'children': [
                    {
                        'name': 'Credit Cards',
                        'parent': True,
                        'children': [
                            {'name': 'Mastercard', 'value': 157.72}
                        ],
                        'total': 157.72
                    }
                ]
            },
            'Equity': {
                'children': [
                    {'name': 'Opening Balance Equity', 'value': -9905.0}
                ]
            }
        }

    @pytest.fixture
    def balance_sheet_model(self, sample_dataframe, sample_hierarchy):
        """Create BalanceSheetModel instance."""
        return BalanceSheetModel(df=sample_dataframe, hierarchy=sample_hierarchy)

    def test_model_initialization(self, sample_dataframe, sample_hierarchy):
        """
        Given: Valid DataFrame and hierarchy
        When: BalanceSheetModel instantiated
        Then: Model stores both correctly
        """
        model = BalanceSheetModel(df=sample_dataframe, hierarchy=sample_hierarchy)

        assert model.dataframe is not None
        assert model.hierarchy == sample_hierarchy
        assert len(model.dataframe) == 5

    def test_get_assets(self, balance_sheet_model):
        """
        Given: BalanceSheetModel with Assets section
        When: get_assets() called
        Then: Returns Assets section subtree
        """
        assets = balance_sheet_model.get_assets()

        assert assets is not None
        assert 'children' in assets
        assert len(assets['children']) > 0
        assert assets['children'][0]['name'] == 'Bank Accounts'

    def test_get_liabilities(self, balance_sheet_model):
        """
        Given: BalanceSheetModel with Liabilities section
        When: get_liabilities() called
        Then: Returns Liabilities section subtree
        """
        liabilities = balance_sheet_model.get_liabilities()

        assert liabilities is not None
        assert 'children' in liabilities

    def test_get_equity(self, balance_sheet_model):
        """
        Given: BalanceSheetModel with Equity section
        When: get_equity() called
        Then: Returns Equity section subtree
        """
        equity = balance_sheet_model.get_equity()

        assert equity is not None
        assert 'children' in equity

    def test_get_account_by_name_found(self, balance_sheet_model):
        """
        Given: BalanceSheetModel with 'Checking' account
        When: get_account_by_name('Checking') called
        Then: Returns account dict
        """
        account = balance_sheet_model.get_account_by_name('Checking')

        assert account is not None
        assert account['name'] == 'Checking'
        assert account['value'] == 1201.0

    def test_get_account_by_name_not_found(self, balance_sheet_model):
        """
        Given: BalanceSheetModel without 'NonExistent' account
        When: get_account_by_name('NonExistent') called
        Then: Returns None
        """
        account = balance_sheet_model.get_account_by_name('NonExistent')

        assert account is None

    def test_get_account_by_name_parent(self, balance_sheet_model):
        """
        Given: BalanceSheetModel with 'Bank Accounts' parent
        When: get_account_by_name('Bank Accounts') called
        Then: Returns parent account dict with children
        """
        account = balance_sheet_model.get_account_by_name('Bank Accounts')

        assert account is not None
        assert account['name'] == 'Bank Accounts'
        assert account['parent'] is True
        assert 'children' in account
        assert len(account['children']) == 2

    def test_missing_section_graceful(self, sample_dataframe):
        """
        Given: BalanceSheetModel with missing Equity section
        When: get_equity() called
        Then: Returns empty dict (no exception)
        """
        # Create hierarchy without Equity
        hierarchy = {
            'Assets': {'children': []},
            'Liabilities': {'children': []}
        }

        model = BalanceSheetModel(df=sample_dataframe, hierarchy=hierarchy)
        equity = model.get_equity()

        assert equity == {}

    def test_to_dict_includes_hierarchy(self, balance_sheet_model):
        """
        Given: BalanceSheetModel instance
        When: to_dict() called
        Then: Result includes both dataframe and hierarchy
        """
        result = balance_sheet_model.to_dict()

        assert 'dataframe' in result
        assert 'hierarchy' in result
        assert isinstance(result['dataframe'], list)  # records format
        assert isinstance(result['hierarchy'], dict)

    def test_serialization_roundtrip(self, balance_sheet_model):
        """
        Given: BalanceSheetModel instance
        When: to_dict() then from_dict() called
        Then: Reconstructed model has same data
        """
        # Serialize
        serialized = balance_sheet_model.to_dict()

        # Deserialize
        reconstructed = BalanceSheetModel.from_dict(serialized)

        # Verify DataFrame
        assert len(reconstructed.dataframe) == len(balance_sheet_model.dataframe)
        assert list(reconstructed.dataframe.columns) == list(balance_sheet_model.dataframe.columns)

        # Verify hierarchy
        assert reconstructed.hierarchy == balance_sheet_model.hierarchy

    def test_from_dict_missing_dataframe(self):
        """
        Given: Dict without 'dataframe' key
        When: from_dict() called
        Then: Raises ValueError
        """
        data = {'hierarchy': {}}

        with pytest.raises(ValueError, match="Missing 'dataframe' key"):
            BalanceSheetModel.from_dict(data)

    def test_from_dict_missing_hierarchy(self):
        """
        Given: Dict without 'hierarchy' key
        When: from_dict() called
        Then: Raises ValueError
        """
        data = {'dataframe': []}

        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            BalanceSheetModel.from_dict(data)

    def test_hierarchy_property(self, balance_sheet_model, sample_hierarchy):
        """
        Given: BalanceSheetModel instance
        When: hierarchy property accessed
        Then: Returns hierarchy dict
        """
        assert balance_sheet_model.hierarchy == sample_hierarchy

    def test_base_model_properties(self, balance_sheet_model):
        """
        Given: BalanceSheetModel instance
        When: Base DataModel properties accessed
        Then: Work correctly (inherited functionality)
        """
        # Test inherited properties
        assert balance_sheet_model.shape == (5, 3)
        assert 'account_name' in balance_sheet_model.columns
        assert len(balance_sheet_model.head(3)) == 3


class TestBalanceSheetModelCombinedSections:
    """Test handling of combined 'Liabilities and Equity' section."""

    @pytest.fixture
    def combined_hierarchy(self):
        """Create hierarchy with combined 'Liabilities and Equity' section."""
        return {
            'Assets': {
                'children': [
                    {'name': 'Checking', 'value': 1201.0}
                ]
            },
            'Liabilities and Equity': {
                'children': [
                    {
                        'name': 'Liabilities',
                        'parent': True,
                        'children': [
                            {'name': 'Credit Card', 'value': 157.72}
                        ]
                    },
                    {
                        'name': 'Equity',
                        'parent': True,
                        'children': [
                            {'name': 'Opening Balance Equity', 'value': -9905.0}
                        ]
                    }
                ]
            }
        }

    def test_get_liabilities_from_combined(self, sample_dataframe, combined_hierarchy):
        """
        Given: BalanceSheetModel with 'Liabilities and Equity' section
        When: get_liabilities() called
        Then: Returns appropriate subtree
        """
        model = BalanceSheetModel(df=sample_dataframe, hierarchy=combined_hierarchy)
        liabilities = model.get_liabilities()

        # Should return the combined section or extract Liabilities from it
        assert liabilities is not None

    def test_get_equity_from_combined(self, sample_dataframe, combined_hierarchy):
        """
        Given: BalanceSheetModel with 'Liabilities and Equity' section
        When: get_equity() called
        Then: Returns appropriate subtree
        """
        model = BalanceSheetModel(df=sample_dataframe, hierarchy=combined_hierarchy)
        equity = model.get_equity()

        # Should return the combined section or extract Equity from it
        assert equity is not None
