"""
Unit tests for PLModel accessors and period methods.

Tests section accessors, period utilities, calculated row access, and search functionality.
"""
import pandas as pd
import pytest

from src.models import PLModel


class TestPLModel:
    """Test suite for PLModel class."""

    @pytest.fixture
    def sample_hierarchy(self):
        """Create sample P&L hierarchy with period data."""
        return {
            'Income': {
                'children': [
                    {
                        'name': 'Design income',
                        'values': {'Nov 2025': 637.50, 'Nov 2024': 500.00}
                    },
                    {
                        'name': 'Landscaping Services',
                        'parent': True,
                        'children': [
                            {
                                'name': 'Job Materials',
                                'parent': True,
                                'children': [
                                    {
                                        'name': 'Plants and Soil',
                                        'values': {'Nov 2025': 1766.98, 'Nov 2024': 1500.00}
                                    }
                                ],
                                'total': {'Nov 2025': 1766.98, 'Nov 2024': 1500.00}
                            }
                        ],
                        'total': {'Nov 2025': 1766.98, 'Nov 2024': 1500.00}
                    }
                ]
            },
            'Cost of Goods Sold': {
                'children': [
                    {
                        'name': 'Cost of Goods Sold',
                        'values': {'Nov 2025': 228.75, 'Nov 2024': 200.00}
                    }
                ]
            },
            'Expenses': {
                'children': [
                    {
                        'name': 'Advertising',
                        'values': {'Nov 2025': 74.86, 'Nov 2024': 50.00}
                    },
                    {
                        'name': 'Rent',
                        'values': {'Nov 2025': 900.00, 'Nov 2024': 900.00}
                    }
                ]
            },
            'Other Expenses': {
                'children': [
                    {
                        'name': 'Miscellaneous',
                        'values': {'Nov 2025': 2666.00, 'Nov 2024': 2000.00}
                    }
                ]
            }
        }

    @pytest.fixture
    def sample_calculated_rows(self):
        """Create sample calculated rows."""
        return [
            {
                'account_name': 'Gross Profit',
                'values': {'Nov 2025': 2582.53, 'Nov 2024': 2100.00}
            },
            {
                'account_name': 'Net Operating Income',
                'values': {'Nov 2025': 2227.82, 'Nov 2024': 1800.00}
            },
            {
                'account_name': 'Net Income',
                'values': {'Nov 2025': -438.18, 'Nov 2024': -200.00}
            }
        ]

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample metadata DataFrame."""
        return pd.DataFrame([
            {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Design income', 'values': {'Nov 2025': 637.50, 'Nov 2024': 500.00}, 'row_type': 'child'},
            {'account_name': 'Expenses', 'values': {}, 'row_type': 'section'},
            {'account_name': 'Rent', 'values': {'Nov 2025': 900.00, 'Nov 2024': 900.00}, 'row_type': 'child'},
        ])

    @pytest.fixture
    def pl_model(self, sample_dataframe, sample_hierarchy, sample_calculated_rows):
        """Create PLModel instance with sample data."""
        return PLModel(
            df=sample_dataframe,
            hierarchy=sample_hierarchy,
            calculated_rows=sample_calculated_rows
        )

    def test_get_income_accessor(self, pl_model):
        """
        Given: PLModel with Income section containing 'Design income' account
        When: get_income() called
        Then: returns Income subtree with account and period-aware values dict
        """
        income = pl_model.get_income()

        assert income is not None
        assert 'children' in income
        assert len(income['children']) > 0

        # Find Design income
        design_income = None
        for child in income['children']:
            if child.get('name') == 'Design income':
                design_income = child
                break

        assert design_income is not None
        assert 'values' in design_income
        assert design_income['values']['Nov 2025'] == 637.50
        assert design_income['values']['Nov 2024'] == 500.00

    def test_get_cogs_accessor_present(self, pl_model):
        """
        Given: PLModel with COGS section
        When: get_cogs() called
        Then: returns COGS section dict
        """
        cogs = pl_model.get_cogs()

        assert cogs is not None
        assert 'children' in cogs
        assert len(cogs['children']) > 0

    def test_get_cogs_accessor_absent(self, sample_dataframe):
        """
        Given: PLModel without COGS section
        When: get_cogs() called
        Then: returns None
        """
        # Create hierarchy without COGS
        hierarchy_no_cogs = {
            'Income': {'children': []},
            'Expenses': {'children': []}
        }

        model = PLModel(df=sample_dataframe, hierarchy=hierarchy_no_cogs, calculated_rows=[])
        cogs = model.get_cogs()

        assert cogs is None

    def test_get_expenses_accessor(self, pl_model):
        """
        Given: PLModel with Expenses section
        When: get_expenses() called
        Then: returns Expenses section dict with nested structure
        """
        expenses = pl_model.get_expenses()

        assert expenses is not None
        assert 'children' in expenses
        assert len(expenses['children']) > 0

        # Find Rent
        rent = None
        for child in expenses['children']:
            if child.get('name') == 'Rent':
                rent = child
                break

        assert rent is not None
        assert 'values' in rent
        assert rent['values']['Nov 2025'] == 900.00

    def test_get_other_expenses_accessor_present(self, pl_model):
        """
        Given: PLModel with Other Expenses section
        When: get_other_expenses() called
        Then: returns Other Expenses section dict
        """
        other = pl_model.get_other_expenses()

        assert other is not None
        assert 'children' in other

    def test_get_other_expenses_accessor_absent(self, sample_dataframe):
        """
        Given: PLModel without Other Expenses section
        When: get_other_expenses() called
        Then: returns None
        """
        hierarchy_no_other = {
            'Income': {'children': []},
            'Expenses': {'children': []}
        }

        model = PLModel(df=sample_dataframe, hierarchy=hierarchy_no_other, calculated_rows=[])
        other = model.get_other_expenses()

        assert other is None

    def test_get_periods_method(self, pl_model):
        """
        Given: PLModel with 2 periods
        When: get_periods() called
        Then: returns list with 2 period label strings
        """
        periods = pl_model.get_periods()

        assert isinstance(periods, list)
        assert len(periods) == 2
        assert 'Nov 2025' in periods
        assert 'Nov 2024' in periods

    def test_get_periods_from_calculated_rows(self, sample_dataframe):
        """
        Given: PLModel with no child nodes but calculated rows have periods
        When: get_periods() called
        Then: returns periods from calculated rows
        """
        # Empty hierarchy but calculated rows with periods
        hierarchy = {'Income': {}, 'Expenses': {}}
        calculated_rows = [
            {'account_name': 'Net Income', 'values': {'Period A': 100.0, 'Period B': 200.0}}
        ]

        model = PLModel(df=sample_dataframe, hierarchy=hierarchy, calculated_rows=calculated_rows)
        periods = model.get_periods()

        assert len(periods) == 2
        assert 'Period A' in periods
        assert 'Period B' in periods

    def test_get_periods_empty_model(self, sample_dataframe):
        """
        Given: PLModel with no periods
        When: get_periods() called
        Then: returns empty list
        """
        hierarchy = {'Income': {}, 'Expenses': {}}
        model = PLModel(df=sample_dataframe, hierarchy=hierarchy, calculated_rows=[])

        periods = model.get_periods()

        assert isinstance(periods, list)
        assert len(periods) == 0

    def test_get_calculated_row(self, pl_model):
        """
        Given: PLModel with calculated row 'Net Income'
        When: get_calculated_row('Net Income') called
        Then: returns dict with account_name and values dict
        """
        net_income = pl_model.get_calculated_row('Net Income')

        assert net_income is not None
        assert net_income['account_name'] == 'Net Income'
        assert 'values' in net_income
        assert net_income['values']['Nov 2025'] == -438.18
        assert net_income['values']['Nov 2024'] == -200.00

    def test_get_calculated_row_gross_profit(self, pl_model):
        """
        Given: PLModel with calculated row 'Gross Profit'
        When: get_calculated_row('Gross Profit') called
        Then: returns correct calculated row
        """
        gross_profit = pl_model.get_calculated_row('Gross Profit')

        assert gross_profit is not None
        assert gross_profit['account_name'] == 'Gross Profit'
        assert gross_profit['values']['Nov 2025'] == 2582.53

    def test_get_calculated_row_not_found(self, pl_model):
        """
        Given: PLModel without 'Nonexistent' calculated row
        When: get_calculated_row('Nonexistent') called
        Then: returns None
        """
        result = pl_model.get_calculated_row('Nonexistent')

        assert result is None

    def test_account_search_with_periods(self, pl_model):
        """
        Given: PLModel with account 'Rent' in Expenses
        When: get_account_by_name('Rent') called
        Then: returns account node with period-aware values dict
        """
        rent = pl_model.get_account_by_name('Rent')

        assert rent is not None
        assert rent['name'] == 'Rent'
        assert 'values' in rent
        assert rent['values']['Nov 2025'] == 900.00
        assert rent['values']['Nov 2024'] == 900.00

    def test_account_search_nested(self, pl_model):
        """
        Given: PLModel with nested account 'Plants and Soil'
        When: get_account_by_name('Plants and Soil') called
        Then: returns account node with period values
        """
        plants = pl_model.get_account_by_name('Plants and Soil')

        assert plants is not None
        assert plants['name'] == 'Plants and Soil'
        assert 'values' in plants
        assert plants['values']['Nov 2025'] == 1766.98

    def test_account_search_not_found(self, pl_model):
        """
        Given: PLModel without 'Nonexistent' account
        When: get_account_by_name('Nonexistent') called
        Then: returns None
        """
        result = pl_model.get_account_by_name('Nonexistent')

        assert result is None

    def test_hierarchy_property(self, pl_model):
        """
        Given: PLModel with hierarchy
        When: hierarchy property accessed
        Then: returns hierarchy dict
        """
        hierarchy = pl_model.hierarchy

        assert isinstance(hierarchy, dict)
        assert 'Income' in hierarchy
        assert 'Expenses' in hierarchy

    def test_calculated_rows_property(self, pl_model, sample_calculated_rows):
        """
        Given: PLModel with calculated rows
        When: calculated_rows property accessed
        Then: returns list of calculated row dicts
        """
        calculated = pl_model.calculated_rows

        assert isinstance(calculated, list)
        assert len(calculated) == len(sample_calculated_rows)
        assert calculated[0]['account_name'] == 'Gross Profit'

    def test_to_dict_serialization(self, pl_model):
        """
        Given: PLModel instance
        When: to_dict() called
        Then: returns dict with dataframe, hierarchy, and calculated_rows keys
        """
        result = pl_model.to_dict()

        assert 'dataframe' in result
        assert 'hierarchy' in result
        assert 'calculated_rows' in result
        assert isinstance(result['hierarchy'], dict)
        assert isinstance(result['calculated_rows'], list)

    def test_from_dict_deserialization(self, pl_model):
        """
        Given: Dict representation of PLModel
        When: from_dict() called
        Then: returns new PLModel instance with same data
        """
        # Serialize
        data_dict = pl_model.to_dict()

        # Deserialize
        restored = PLModel.from_dict(data_dict)

        assert isinstance(restored, PLModel)
        assert restored.hierarchy == pl_model.hierarchy
        assert len(restored.calculated_rows) == len(pl_model.calculated_rows)
        assert restored.dataframe.shape == pl_model.dataframe.shape

    def test_from_dict_missing_hierarchy_key(self, sample_dataframe):
        """
        Given: Dict missing 'hierarchy' key
        When: from_dict() called
        Then: raises ValueError
        """
        data = {
            'dataframe': sample_dataframe.to_dict(),
            'calculated_rows': []
            # Missing 'hierarchy'
        }

        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            PLModel.from_dict(data)

    def test_from_dict_missing_calculated_rows_key(self, sample_dataframe):
        """
        Given: Dict missing 'calculated_rows' key
        When: from_dict() called
        Then: raises ValueError
        """
        data = {
            'dataframe': sample_dataframe.to_dict(),
            'hierarchy': {}
            # Missing 'calculated_rows'
        }

        with pytest.raises(ValueError, match="Missing 'calculated_rows' key"):
            PLModel.from_dict(data)

    def test_dataframe_property(self, pl_model, sample_dataframe):
        """
        Given: PLModel with DataFrame
        When: dataframe property accessed
        Then: returns underlying DataFrame
        """
        df = pl_model.dataframe

        assert isinstance(df, pd.DataFrame)
        assert df.shape == sample_dataframe.shape
