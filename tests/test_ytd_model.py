"""
Unit tests for YTDModel - model for year-to-date aggregation results.

Tests:
- Property accessors
- Section accessors
- Serialization (to_dict/from_dict)
- Roundtrip preservation
- Edge cases (empty hierarchy, missing sections)
"""
import pandas as pd
import pytest

from src.models import YTDModel


class TestYTDModel:
    """Test suite for YTDModel class."""

    @pytest.fixture
    def sample_ytd_hierarchy(self):
        """Create sample YTD hierarchy with cumulative data."""
        return {
            'Income': {
                'name': 'Income',
                'children': [
                    {
                        'name': 'Product Revenue',
                        'values': {
                            '2024-01': {
                                'cumulative_budget': 100000,
                                'cumulative_actual': 110000,
                                'cumulative_dollar_variance': 10000,
                                'cumulative_pct_variance': 10.0,
                                'ytd_pct_of_budget': 110.0,
                                'is_favorable': True,
                                'is_flagged': False
                            },
                            '2024-02': {
                                'cumulative_budget': 200000,
                                'cumulative_actual': 215000,
                                'cumulative_dollar_variance': 15000,
                                'cumulative_pct_variance': 7.5,
                                'ytd_pct_of_budget': 107.5,
                                'is_favorable': True,
                                'is_flagged': False
                            }
                        }
                    },
                    {
                        'name': 'Service Revenue',
                        'values': {
                            '2024-01': {
                                'cumulative_budget': 50000,
                                'cumulative_actual': 48000,
                                'cumulative_dollar_variance': -2000,
                                'cumulative_pct_variance': -4.0,
                                'ytd_pct_of_budget': 96.0,
                                'is_favorable': False,
                                'is_flagged': False
                            },
                            '2024-02': {
                                'cumulative_budget': 100000,
                                'cumulative_actual': 98000,
                                'cumulative_dollar_variance': -2000,
                                'cumulative_pct_variance': -2.0,
                                'ytd_pct_of_budget': 98.0,
                                'is_favorable': False,
                                'is_flagged': False
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
                                'cumulative_budget': 30000,
                                'cumulative_actual': 28000,
                                'cumulative_dollar_variance': -2000,
                                'cumulative_pct_variance': -6.67,
                                'ytd_pct_of_budget': 93.33,
                                'is_favorable': True,
                                'is_flagged': False
                            },
                            '2024-02': {
                                'cumulative_budget': 60000,
                                'cumulative_actual': 58000,
                                'cumulative_dollar_variance': -2000,
                                'cumulative_pct_variance': -3.33,
                                'ytd_pct_of_budget': 96.67,
                                'is_favorable': True,
                                'is_flagged': False
                            }
                        }
                    }
                ]
            }
        }

    @pytest.fixture
    def sample_calculated_rows(self):
        """Create sample calculated rows with section summaries."""
        return {
            'income': {
                '2024-01': {
                    'cumulative_budget': 150000,
                    'cumulative_actual': 158000,
                    'cumulative_dollar_variance': 8000,
                    'cumulative_pct_variance': 5.33,
                    'ytd_pct_of_budget': 105.33,
                    'is_favorable': True,
                    'is_flagged': False
                },
                '2024-02': {
                    'cumulative_budget': 300000,
                    'cumulative_actual': 313000,
                    'cumulative_dollar_variance': 13000,
                    'cumulative_pct_variance': 4.33,
                    'ytd_pct_of_budget': 104.33,
                    'is_favorable': True,
                    'is_flagged': False
                }
            },
            'expenses': {
                '2024-01': {
                    'cumulative_budget': 30000,
                    'cumulative_actual': 28000,
                    'cumulative_dollar_variance': -2000,
                    'cumulative_pct_variance': -6.67,
                    'ytd_pct_of_budget': 93.33,
                    'is_favorable': True,
                    'is_flagged': False
                },
                '2024-02': {
                    'cumulative_budget': 60000,
                    'cumulative_actual': 58000,
                    'cumulative_dollar_variance': -2000,
                    'cumulative_pct_variance': -3.33,
                    'ytd_pct_of_budget': 96.67,
                    'is_favorable': True,
                    'is_flagged': False
                }
            }
        }

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample metadata DataFrame."""
        return pd.DataFrame([
            {'account_name': 'Income', 'section': 'Income', 'is_parent': False},
            {'account_name': 'Product Revenue', 'section': 'Income', 'is_parent': False},
            {'account_name': 'Service Revenue', 'section': 'Income', 'is_parent': False},
            {'account_name': 'Expenses', 'section': 'Expenses', 'is_parent': False},
            {'account_name': 'Marketing', 'section': 'Expenses', 'is_parent': False}
        ])

    @pytest.fixture
    def ytd_model(self, sample_dataframe, sample_ytd_hierarchy, sample_calculated_rows):
        """Create YTDModel instance for testing."""
        return YTDModel(
            df=sample_dataframe,
            hierarchy=sample_ytd_hierarchy,
            calculated_rows=sample_calculated_rows,
            fiscal_year_start_month=1,
            aggregation_start_period='2024-01'
        )

    def test_ytd_model_properties(self, ytd_model, sample_ytd_hierarchy, sample_calculated_rows):
        """Test YTDModel property accessors return correct values."""
        # Test hierarchy property
        assert ytd_model.hierarchy == sample_ytd_hierarchy
        assert 'Income' in ytd_model.hierarchy
        assert 'Expenses' in ytd_model.hierarchy

        # Test calculated_rows property
        assert ytd_model.calculated_rows == sample_calculated_rows
        assert 'income' in ytd_model.calculated_rows
        assert 'expenses' in ytd_model.calculated_rows

        # Test fiscal_year_start_month property
        assert ytd_model.fiscal_year_start_month == 1

        # Test aggregation_start_period property
        assert ytd_model.aggregation_start_period == '2024-01'

    def test_ytd_model_section_accessors(self, ytd_model):
        """Test get_income_ytd and get_expenses_ytd return section data."""
        # Test get_income_ytd
        income_ytd = ytd_model.get_income_ytd()
        assert income_ytd is not None
        assert income_ytd['name'] == 'Income'
        assert 'children' in income_ytd
        assert len(income_ytd['children']) == 2

        # Test get_expenses_ytd
        expenses_ytd = ytd_model.get_expenses_ytd()
        assert expenses_ytd is not None
        assert expenses_ytd['name'] == 'Expenses'
        assert 'children' in expenses_ytd
        assert len(expenses_ytd['children']) == 1

    def test_ytd_model_serialization_roundtrip(self, ytd_model):
        """Test to_dict -> from_dict preserves model data."""
        # Serialize to dict
        data = ytd_model.to_dict()

        # Verify dict contains all required keys
        assert 'dataframe' in data
        assert 'hierarchy' in data
        assert 'calculated_rows' in data
        assert 'fiscal_year_start_month' in data
        assert 'aggregation_start_period' in data

        # Deserialize back to YTDModel
        restored_model = YTDModel.from_dict(data)

        # Verify data is preserved
        assert restored_model.fiscal_year_start_month == ytd_model.fiscal_year_start_month
        assert restored_model.aggregation_start_period == ytd_model.aggregation_start_period
        assert restored_model.hierarchy == ytd_model.hierarchy
        assert restored_model.calculated_rows == ytd_model.calculated_rows
        assert len(restored_model._df) == len(ytd_model._df)

    def test_ytd_model_hierarchy_structure(self, ytd_model):
        """Test hierarchy contains required cumulative variance attributes."""
        # Access hierarchy
        hierarchy = ytd_model.hierarchy

        # Check Income section structure
        income_section = hierarchy['Income']
        product_revenue = income_section['children'][0]
        assert product_revenue['name'] == 'Product Revenue'
        assert 'values' in product_revenue

        # Check period data structure
        period_data = product_revenue['values']['2024-01']
        required_keys = [
            'cumulative_budget',
            'cumulative_actual',
            'cumulative_dollar_variance',
            'cumulative_pct_variance',
            'ytd_pct_of_budget',
            'is_favorable',
            'is_flagged'
        ]
        for key in required_keys:
            assert key in period_data, f"Missing required key: {key}"

    def test_ytd_model_to_dict_format(self, ytd_model):
        """Test to_dict returns correctly formatted dictionary."""
        data = ytd_model.to_dict()

        # Check dataframe is serialized
        assert isinstance(data['dataframe'], list)  # records format

        # Check hierarchy is preserved
        assert isinstance(data['hierarchy'], dict)
        assert 'Income' in data['hierarchy']

        # Check calculated_rows is preserved
        assert isinstance(data['calculated_rows'], dict)

        # Check metadata is preserved
        assert isinstance(data['fiscal_year_start_month'], int)
        assert isinstance(data['aggregation_start_period'], str)

    def test_ytd_model_from_dict_validation(self):
        """Test from_dict validates required keys."""
        # Test missing dataframe
        with pytest.raises(ValueError, match="Missing 'dataframe' key"):
            YTDModel.from_dict({
                'hierarchy': {},
                'calculated_rows': {},
                'fiscal_year_start_month': 1,
                'aggregation_start_period': '2024-01'
            })

        # Test missing hierarchy
        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            YTDModel.from_dict({
                'dataframe': [],
                'calculated_rows': {},
                'fiscal_year_start_month': 1,
                'aggregation_start_period': '2024-01'
            })

        # Test missing calculated_rows
        with pytest.raises(ValueError, match="Missing 'calculated_rows' key"):
            YTDModel.from_dict({
                'dataframe': [],
                'hierarchy': {},
                'fiscal_year_start_month': 1,
                'aggregation_start_period': '2024-01'
            })

        # Test missing fiscal_year_start_month
        with pytest.raises(ValueError, match="Missing 'fiscal_year_start_month' key"):
            YTDModel.from_dict({
                'dataframe': [],
                'hierarchy': {},
                'calculated_rows': {},
                'aggregation_start_period': '2024-01'
            })

        # Test missing aggregation_start_period
        with pytest.raises(ValueError, match="Missing 'aggregation_start_period' key"):
            YTDModel.from_dict({
                'dataframe': [],
                'hierarchy': {},
                'calculated_rows': {},
                'fiscal_year_start_month': 1
            })

    def test_ytd_model_empty_hierarchy(self):
        """Test YTDModel with empty hierarchy."""
        empty_df = pd.DataFrame()
        empty_hierarchy = {}
        empty_calculated_rows = {}

        model = YTDModel(
            df=empty_df,
            hierarchy=empty_hierarchy,
            calculated_rows=empty_calculated_rows,
            fiscal_year_start_month=1,
            aggregation_start_period=None
        )

        assert model.hierarchy == {}
        assert model.calculated_rows == {}
        assert model.get_income_ytd() == {}
        assert model.get_expenses_ytd() == {}

    def test_ytd_model_missing_sections(self):
        """Test YTDModel with missing sections returns empty dicts."""
        df = pd.DataFrame()
        hierarchy = {'Income': {'name': 'Income', 'children': []}}  # No Expenses section
        calculated_rows = {}

        model = YTDModel(
            df=df,
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            fiscal_year_start_month=1,
            aggregation_start_period='2024-01'
        )

        assert model.get_income_ytd() is not None
        assert model.get_expenses_ytd() == {}  # Missing section returns empty dict

    def test_ytd_model_non_calendar_fiscal_year(self):
        """Test YTDModel with non-calendar fiscal year metadata."""
        df = pd.DataFrame()
        hierarchy = {}
        calculated_rows = {}

        model = YTDModel(
            df=df,
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            fiscal_year_start_month=7,  # Fiscal year starts in July
            aggregation_start_period='2024-07'
        )

        assert model.fiscal_year_start_month == 7
        assert model.aggregation_start_period == '2024-07'

    def test_ytd_model_dataframe_access(self, ytd_model):
        """Test YTDModel provides access to underlying DataFrame."""
        df = ytd_model._df
        assert df is not None
        assert len(df) > 0
        assert 'account_name' in df.columns
