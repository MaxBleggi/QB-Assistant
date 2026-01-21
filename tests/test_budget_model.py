"""
Unit tests for BudgetModel data structure.

Tests section accessors, serialization roundtrip, and period utilities.
"""
import pandas as pd
import pytest

from src.models import BudgetModel


class TestBudgetModel:
    """Test suite for BudgetModel class."""

    @pytest.fixture
    def sample_hierarchy(self):
        """Create sample budget hierarchy with period data."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Product Sales',
                        'values': {'Jan 2025': 10000.0, 'Feb 2025': 12000.0, 'Mar 2025': 11000.0}
                    },
                    {
                        'name': 'Service Revenue',
                        'values': {'Jan 2025': 5000.0, 'Feb 2025': 5500.0, 'Mar 2025': 6000.0}
                    }
                ]
            },
            'Expenses': {
                'children': [
                    {
                        'name': 'Marketing',
                        'values': {'Jan 2025': 2000.0, 'Feb 2025': 2200.0, 'Mar 2025': 2100.0}
                    },
                    {
                        'name': 'Rent',
                        'values': {'Jan 2025': 3000.0, 'Feb 2025': 3000.0, 'Mar 2025': 3000.0}
                    }
                ]
            }
        }

    @pytest.fixture
    def sample_calculated_rows(self):
        """Create sample calculated rows."""
        return [
            {
                'account_name': 'Total Income',
                'values': {'Jan 2025': 15000.0, 'Feb 2025': 17500.0, 'Mar 2025': 17000.0}
            },
            {
                'account_name': 'Total Expenses',
                'values': {'Jan 2025': 5000.0, 'Feb 2025': 5200.0, 'Mar 2025': 5100.0}
            },
            {
                'account_name': 'Net Income',
                'values': {'Jan 2025': 10000.0, 'Feb 2025': 12300.0, 'Mar 2025': 11900.0}
            }
        ]

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample budget DataFrame."""
        return pd.DataFrame([
            {'account_name': 'Product Sales', 'section': 'Income', 'is_parent': False},
            {'account_name': 'Service Revenue', 'section': 'Income', 'is_parent': False},
            {'account_name': 'Marketing', 'section': 'Expenses', 'is_parent': False},
            {'account_name': 'Rent', 'section': 'Expenses', 'is_parent': False}
        ])

    @pytest.fixture
    def budget_model(self, sample_dataframe, sample_hierarchy, sample_calculated_rows):
        """Create BudgetModel instance with sample data."""
        return BudgetModel(
            df=sample_dataframe,
            hierarchy=sample_hierarchy,
            calculated_rows=sample_calculated_rows
        )

    def test_get_income_returns_income_section(self, budget_model, sample_hierarchy):
        """
        Given: BudgetModel initialized with sample hierarchy
        When: get_income() called
        Then: returns Income section from hierarchy
        """
        income = budget_model.get_income()

        assert income is not None
        assert 'children' in income
        assert len(income['children']) == 2
        assert income['children'][0]['name'] == 'Product Sales'

    def test_get_expenses_returns_expenses_section(self, budget_model, sample_hierarchy):
        """
        Given: BudgetModel initialized with sample hierarchy
        When: get_expenses() called
        Then: returns Expenses section from hierarchy
        """
        expenses = budget_model.get_expenses()

        assert expenses is not None
        assert 'children' in expenses
        assert len(expenses['children']) == 2
        assert expenses['children'][0]['name'] == 'Marketing'

    def test_to_dict_includes_all_fields(self, budget_model):
        """
        Given: BudgetModel initialized with all fixtures
        When: to_dict() called
        Then: result has keys 'dataframe', 'hierarchy', 'calculated_rows'
        """
        result = budget_model.to_dict()

        assert 'dataframe' in result
        assert 'hierarchy' in result
        assert 'calculated_rows' in result
        assert result['dataframe'] is not None
        assert result['hierarchy'] is not None
        assert result['calculated_rows'] is not None

    def test_from_dict_reconstructs_model(self, budget_model):
        """
        Given: dict from to_dict()
        When: BudgetModel.from_dict(dict_data) called
        Then: reconstructed model equals original (hierarchy, calculated_rows, DataFrame shape match)
        """
        # Serialize to dict
        data = budget_model.to_dict()

        # Reconstruct from dict
        reconstructed = BudgetModel.from_dict(data)

        # Verify hierarchy matches
        assert reconstructed.hierarchy == budget_model.hierarchy

        # Verify calculated_rows matches
        assert reconstructed.calculated_rows == budget_model.calculated_rows

        # Verify DataFrame shape matches
        assert reconstructed.dataframe.shape == budget_model.dataframe.shape

        # Verify DataFrame columns match
        assert list(reconstructed.dataframe.columns) == list(budget_model.dataframe.columns)

    def test_get_period_column_returns_correct_name(self, budget_model):
        """
        Given: period_index = 0
        When: get_period_column(0) called
        Then: returns column name for first period (e.g., 'Jan 2025')
        """
        period_name = budget_model.get_period_column(0)

        assert period_name == 'Jan 2025'

    def test_get_period_column_second_period(self, budget_model):
        """
        Given: period_index = 1
        When: get_period_column(1) called
        Then: returns column name for second period
        """
        period_name = budget_model.get_period_column(1)

        assert period_name == 'Feb 2025'

    def test_hierarchy_property(self, budget_model, sample_hierarchy):
        """Verify hierarchy property returns hierarchy dict."""
        assert budget_model.hierarchy == sample_hierarchy

    def test_calculated_rows_property(self, budget_model, sample_calculated_rows):
        """Verify calculated_rows property returns calculated rows list."""
        assert budget_model.calculated_rows == sample_calculated_rows

    def test_from_dict_missing_dataframe_key(self):
        """Verify from_dict raises ValueError if dataframe key missing."""
        data = {
            'hierarchy': {},
            'calculated_rows': []
        }

        with pytest.raises(ValueError, match="Missing 'dataframe' key"):
            BudgetModel.from_dict(data)

    def test_from_dict_missing_hierarchy_key(self):
        """Verify from_dict raises ValueError if hierarchy key missing."""
        data = {
            'dataframe': [],
            'calculated_rows': []
        }

        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            BudgetModel.from_dict(data)

    def test_from_dict_missing_calculated_rows_key(self):
        """Verify from_dict raises ValueError if calculated_rows key missing."""
        data = {
            'dataframe': [],
            'hierarchy': {}
        }

        with pytest.raises(ValueError, match="Missing 'calculated_rows' key"):
            BudgetModel.from_dict(data)

    def test_get_income_empty_when_missing(self):
        """Verify get_income returns empty dict when Income section missing."""
        df = pd.DataFrame()
        hierarchy = {'Expenses': {}}
        model = BudgetModel(df, hierarchy, [])

        income = model.get_income()

        assert income == {}

    def test_get_expenses_empty_when_missing(self):
        """Verify get_expenses returns empty dict when Expenses section missing."""
        df = pd.DataFrame()
        hierarchy = {'Income': {}}
        model = BudgetModel(df, hierarchy, [])

        expenses = model.get_expenses()

        assert expenses == {}
