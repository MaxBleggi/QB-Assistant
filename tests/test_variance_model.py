"""
Tests for VarianceModel - data model for variance analysis results.

Covers:
- Constructor with hierarchy and unmatched lists
- Section accessors (get_income_variances, get_expense_variances)
- Serialization (to_dict, from_dict)
- Edge cases (missing sections, empty unmatched lists)
"""
import pytest
import pandas as pd

from src.models import VarianceModel


@pytest.fixture
def sample_variance_hierarchy():
    """Sample variance hierarchy with Income and Expenses sections."""
    return {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Product Revenue',
                    'values': {
                        '2024-01': {
                            'budget_value': 100000,
                            'actual_value': 120000,
                            'dollar_variance': 20000,
                            'pct_variance': 20.0,
                            'is_favorable': True,
                            'is_flagged': True
                        }
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Marketing',
                    'values': {
                        '2024-01': {
                            'budget_value': 50000,
                            'actual_value': 45000,
                            'dollar_variance': -5000,
                            'pct_variance': -10.0,
                            'is_favorable': True,
                            'is_flagged': True
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_calculated_rows():
    """Sample calculated rows for variance totals."""
    return [
        {
            'account_name': 'Total Income Variance',
            'values': {
                '2024-01': {
                    'budget_value': 100000,
                    'actual_value': 120000,
                    'dollar_variance': 20000,
                    'pct_variance': 20.0
                }
            }
        },
        {
            'account_name': 'Total Expenses Variance',
            'values': {
                '2024-01': {
                    'budget_value': 50000,
                    'actual_value': 45000,
                    'dollar_variance': -5000,
                    'pct_variance': -10.0
                }
            }
        }
    ]


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for VarianceModel."""
    return pd.DataFrame([
        {'account_name': 'Product Revenue', 'section': 'Income', 'is_parent': False},
        {'account_name': 'Marketing', 'section': 'Expenses', 'is_parent': False}
    ])


class TestVarianceModel:
    """Test suite for VarianceModel."""

    def test_variance_model_constructor(
        self,
        sample_dataframe,
        sample_variance_hierarchy,
        sample_calculated_rows
    ):
        """Test VarianceModel accepts df, hierarchy, calculated_rows, unmatched lists."""
        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows,
            unmatched_budget_accounts=['Old Account'],
            unmatched_actual_accounts=['New Account']
        )

        assert model.hierarchy == sample_variance_hierarchy
        assert model.calculated_rows == sample_calculated_rows
        assert model.unmatched_budget_accounts == ['Old Account']
        assert model.unmatched_actual_accounts == ['New Account']
        assert len(model.dataframe) == 2

    def test_get_income_variances(self, sample_dataframe, sample_variance_hierarchy, sample_calculated_rows):
        """Test get_income_variances() returns Income section dict."""
        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows
        )

        income_variances = model.get_income_variances()

        assert income_variances == sample_variance_hierarchy['Income']
        assert income_variances['name'] == 'Income'
        assert len(income_variances['children']) == 1
        assert income_variances['children'][0]['name'] == 'Product Revenue'

    def test_get_expense_variances(self, sample_dataframe, sample_variance_hierarchy, sample_calculated_rows):
        """Test get_expense_variances() returns Expenses section dict."""
        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows
        )

        expense_variances = model.get_expense_variances()

        assert expense_variances == sample_variance_hierarchy['Expenses']
        assert expense_variances['name'] == 'Expenses'
        assert len(expense_variances['children']) == 1
        assert expense_variances['children'][0]['name'] == 'Marketing'

    def test_unmatched_accounts_properties(self, sample_dataframe, sample_variance_hierarchy, sample_calculated_rows):
        """Test unmatched_budget_accounts and unmatched_actual_accounts return lists."""
        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows,
            unmatched_budget_accounts=['Budget Account 1', 'Budget Account 2'],
            unmatched_actual_accounts=['Actual Account 1']
        )

        assert model.unmatched_budget_accounts == ['Budget Account 1', 'Budget Account 2']
        assert model.unmatched_actual_accounts == ['Actual Account 1']

    def test_serialization_round_trip(self, sample_dataframe, sample_variance_hierarchy, sample_calculated_rows):
        """Test to_dict() then from_dict() preserves all data."""
        original_model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows,
            unmatched_budget_accounts=['Old Account'],
            unmatched_actual_accounts=['New Account']
        )

        # Serialize to dict
        data_dict = original_model.to_dict()

        # Deserialize from dict
        reconstructed_model = VarianceModel.from_dict(data_dict)

        # Compare hierarchy
        assert reconstructed_model.hierarchy == original_model.hierarchy

        # Compare calculated rows
        assert reconstructed_model.calculated_rows == original_model.calculated_rows

        # Compare unmatched lists
        assert reconstructed_model.unmatched_budget_accounts == original_model.unmatched_budget_accounts
        assert reconstructed_model.unmatched_actual_accounts == original_model.unmatched_actual_accounts

        # Compare DataFrames
        assert reconstructed_model.dataframe.equals(original_model.dataframe)

    def test_missing_section_returns_empty_dict(self, sample_dataframe, sample_calculated_rows):
        """Test section accessors return {} when section missing."""
        # Create hierarchy without Income section
        hierarchy = {
            'Expenses': {
                'name': 'Expenses',
                'children': []
            }
        }

        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=hierarchy,
            calculated_rows=sample_calculated_rows
        )

        # get_income_variances should return empty dict
        income = model.get_income_variances()
        assert income == {}

    def test_default_empty_unmatched_lists(self, sample_dataframe, sample_variance_hierarchy, sample_calculated_rows):
        """Test defaults to empty lists when unmatched accounts not provided."""
        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows
            # Not providing unmatched_budget_accounts or unmatched_actual_accounts
        )

        assert model.unmatched_budget_accounts == []
        assert model.unmatched_actual_accounts == []

    def test_to_dict_includes_all_fields(self, sample_dataframe, sample_variance_hierarchy, sample_calculated_rows):
        """Test to_dict() serialization includes all fields."""
        model = VarianceModel(
            df=sample_dataframe,
            hierarchy=sample_variance_hierarchy,
            calculated_rows=sample_calculated_rows,
            unmatched_budget_accounts=['Old'],
            unmatched_actual_accounts=['New']
        )

        data_dict = model.to_dict()

        # Check all required keys present
        assert 'dataframe' in data_dict
        assert 'hierarchy' in data_dict
        assert 'calculated_rows' in data_dict
        assert 'unmatched_budget_accounts' in data_dict
        assert 'unmatched_actual_accounts' in data_dict

        # Check values
        assert data_dict['hierarchy'] == sample_variance_hierarchy
        assert data_dict['calculated_rows'] == sample_calculated_rows
        assert data_dict['unmatched_budget_accounts'] == ['Old']
        assert data_dict['unmatched_actual_accounts'] == ['New']

    def test_from_dict_missing_dataframe_raises(self):
        """Test from_dict() raises ValueError when dataframe missing."""
        data = {
            'hierarchy': {},
            'calculated_rows': []
        }

        with pytest.raises(ValueError, match="Missing 'dataframe' key"):
            VarianceModel.from_dict(data)

    def test_from_dict_missing_hierarchy_raises(self):
        """Test from_dict() raises ValueError when hierarchy missing."""
        data = {
            'dataframe': [],
            'calculated_rows': []
        }

        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            VarianceModel.from_dict(data)

    def test_from_dict_missing_calculated_rows_raises(self):
        """Test from_dict() raises ValueError when calculated_rows missing."""
        data = {
            'dataframe': [],
            'hierarchy': {}
        }

        with pytest.raises(ValueError, match="Missing 'calculated_rows' key"):
            VarianceModel.from_dict(data)

    def test_from_dict_with_missing_unmatched_lists(self):
        """Test from_dict() defaults to empty lists when unmatched lists missing."""
        data = {
            'dataframe': [],
            'hierarchy': {},
            'calculated_rows': []
            # unmatched lists not provided
        }

        model = VarianceModel.from_dict(data)

        assert model.unmatched_budget_accounts == []
        assert model.unmatched_actual_accounts == []
