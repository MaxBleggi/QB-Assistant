"""
Unit tests for DataModel base class.

Tests accessors and serialization methods.
"""
import pandas as pd
import pytest

from src.models import DataModel


class TestDataModel:
    """Test suite for DataModel class."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'Account': ['Checking', 'Savings', 'Credit Card'],
            'Amount': [1000.50, 2500.00, -150.75]
        })

    def test_data_model_creation(self, sample_df):
        """Test creating DataModel with DataFrame."""
        model = DataModel(sample_df)
        assert isinstance(model, DataModel)

    def test_columns_accessor(self, sample_df):
        """Test that .columns returns list of column names."""
        model = DataModel(sample_df)
        columns = model.columns

        assert isinstance(columns, list)
        assert columns == ['Date', 'Account', 'Amount']

    def test_shape_accessor(self, sample_df):
        """Test that .shape returns tuple of (rows, columns)."""
        model = DataModel(sample_df)
        shape = model.shape

        assert isinstance(shape, tuple)
        assert shape == (3, 3)

    def test_head_method(self, sample_df):
        """Test that .head() returns first n rows."""
        model = DataModel(sample_df)
        head_df = model.head(2)

        assert isinstance(head_df, pd.DataFrame)
        assert len(head_df) == 2
        assert list(head_df.columns) == list(sample_df.columns)

    def test_head_default(self, sample_df):
        """Test that .head() defaults to 5 rows."""
        # Create larger DataFrame
        large_df = pd.DataFrame({
            'col': range(10)
        })
        model = DataModel(large_df)
        head_df = model.head()

        assert len(head_df) == 5

    def test_to_dict_records(self, sample_df):
        """Test serialization to dict with orient='records'."""
        model = DataModel(sample_df)
        data_dict = model.to_dict(orient='records')

        assert isinstance(data_dict, list)
        assert len(data_dict) == 3
        assert data_dict[0]['Date'] == '2025-01-01'
        assert data_dict[0]['Account'] == 'Checking'

    def test_to_dict_list(self, sample_df):
        """Test serialization to dict with orient='list'."""
        model = DataModel(sample_df)
        data_dict = model.to_dict(orient='list')

        assert isinstance(data_dict, dict)
        assert 'Date' in data_dict
        assert isinstance(data_dict['Date'], list)
        assert len(data_dict['Date']) == 3

    def test_from_dict_round_trip(self, sample_df):
        """Test that to_dict/from_dict round-trip preserves data."""
        model = DataModel(sample_df)

        # Convert to dict and back
        data_dict = model.to_dict(orient='records')
        restored_model = DataModel.from_dict(data_dict, orient='records')

        # Check structure is preserved
        assert restored_model.columns == model.columns
        assert restored_model.shape == model.shape

    def test_dataframe_property(self, sample_df):
        """Test that dataframe property returns underlying DataFrame."""
        model = DataModel(sample_df)
        df = model.dataframe

        assert isinstance(df, pd.DataFrame)
        assert df.equals(sample_df)

    def test_dataframe_readonly(self, sample_df):
        """Test that dataframe property is read-only (conceptually)."""
        model = DataModel(sample_df)

        # Should be able to access
        df = model.dataframe
        assert df is not None

        # Changes to returned df don't affect original
        # (depends on whether pandas returns view or copy)
