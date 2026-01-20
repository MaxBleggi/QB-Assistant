"""
Unit tests for CashFlowModel.

Tests section accessors, cash position properties, serialization,
and handling of missing data.
"""
import pandas as pd
import pytest

from src.models import CashFlowModel


class TestCashFlowModel:
    """Test suite for CashFlowModel class."""

    @pytest.fixture
    def sample_hierarchy(self):
        """Create sample hierarchy structure."""
        return {
            'OPERATING ACTIVITIES': [
                {'name': 'Net Income', 'value': 1481.28},
                {'name': 'Adjustments to reconcile...', 'parent': True, 'children': [
                    {'name': 'Accounts Payable (A/P)', 'value': -369.72},
                    {'name': 'Accounts Receivable (A/R)', 'value': -2853.02},
                ], 'total': 406.19}
            ],
            'INVESTING ACTIVITIES': [],
            'FINANCING ACTIVITIES': [
                {'name': 'Notes Payable', 'value': 25000.00},
                {'name': 'Opening Balance Equity', 'value': -27832.50}
            ]
        }

    @pytest.fixture
    def sample_calculated_rows(self):
        """Create sample calculated rows."""
        return [
            {'account_name': 'Net cash provided by operating activities', 'value': 1887.47},
            {'account_name': 'Net cash provided by financing activities', 'value': -2832.50},
            {'account_name': 'NET CASH INCREASE FOR PERIOD', 'value': -945.03},
            {'account_name': 'Cash at beginning of period', 'value': 5008.55},
            {'account_name': 'CASH AT END OF PERIOD', 'value': 4063.52}
        ]

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        data = {
            'account_name': ['OPERATING ACTIVITIES', 'Net Income'],
            'raw_value': ['', '1,481.28'],
            'numeric_value': [None, 1481.28],
            'row_type': ['section', 'child']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata."""
        return {'total_rows': 20, 'sections': ['OPERATING ACTIVITIES']}

    @pytest.fixture
    def cash_flow_model(self, sample_df, sample_hierarchy, sample_calculated_rows, sample_metadata):
        """Create CashFlowModel instance with sample data."""
        return CashFlowModel(
            df=sample_df,
            hierarchy=sample_hierarchy,
            calculated_rows=sample_calculated_rows,
            metadata=sample_metadata
        )

    def test_get_operating(self, cash_flow_model):
        """
        Given: Model with OPERATING ACTIVITIES section containing 2 items
        When: get_operating() called
        Then: Returns list with 2 items
        """
        operating = cash_flow_model.get_operating()

        assert isinstance(operating, list)
        assert len(operating) == 2
        assert operating[0]['name'] == 'Net Income'
        assert operating[1].get('parent') is True

    def test_get_investing(self, cash_flow_model):
        """
        Given: Model with empty INVESTING ACTIVITIES section
        When: get_investing() called
        Then: Returns empty list
        """
        investing = cash_flow_model.get_investing()

        assert isinstance(investing, list)
        assert len(investing) == 0

    def test_get_financing(self, cash_flow_model):
        """
        Given: Model with FINANCING ACTIVITIES section containing 2 items
        When: get_financing() called
        Then: Returns list with 2 items
        """
        financing = cash_flow_model.get_financing()

        assert isinstance(financing, list)
        assert len(financing) == 2
        assert financing[0]['name'] == 'Notes Payable'
        assert financing[1]['name'] == 'Opening Balance Equity'

    def test_get_missing_section(self, sample_df, sample_metadata):
        """
        Given: Model missing a section
        When: get_operating() called for missing section
        Then: Returns empty list
        """
        # Create model with only FINANCING section
        hierarchy = {'FINANCING ACTIVITIES': []}
        calculated_rows = []

        model = CashFlowModel(df=sample_df, hierarchy=hierarchy,
                            calculated_rows=calculated_rows, metadata=sample_metadata)

        operating = model.get_operating()
        assert operating == []

    def test_beginning_cash_property(self, cash_flow_model):
        """
        Given: Calculated rows include 'Cash at beginning of period' = 5008.55
        When: beginning_cash property accessed
        Then: Returns 5008.55
        """
        beginning_cash = cash_flow_model.beginning_cash

        assert beginning_cash == 5008.55

    def test_ending_cash_property(self, cash_flow_model):
        """
        Given: Calculated rows include 'CASH AT END OF PERIOD' = 4063.52
        When: ending_cash property accessed
        Then: Returns 4063.52
        """
        ending_cash = cash_flow_model.ending_cash

        assert ending_cash == 4063.52

    def test_cash_properties_missing_data(self, sample_df, sample_hierarchy, sample_metadata):
        """
        Given: Calculated rows missing 'CASH AT END OF PERIOD'
        When: ending_cash property accessed
        Then: Returns None
        """
        # Create model with only beginning cash
        calculated_rows = [
            {'account_name': 'Cash at beginning of period', 'value': 5008.55}
        ]

        model = CashFlowModel(df=sample_df, hierarchy=sample_hierarchy,
                            calculated_rows=calculated_rows, metadata=sample_metadata)

        assert model.beginning_cash == 5008.55
        assert model.ending_cash is None

    def test_beginning_cash_missing(self, sample_df, sample_hierarchy, sample_metadata):
        """
        Given: Calculated rows missing 'Cash at beginning of period'
        When: beginning_cash property accessed
        Then: Returns None
        """
        # Create model with only ending cash
        calculated_rows = [
            {'account_name': 'CASH AT END OF PERIOD', 'value': 4063.52}
        ]

        model = CashFlowModel(df=sample_df, hierarchy=sample_hierarchy,
                            calculated_rows=calculated_rows, metadata=sample_metadata)

        assert model.beginning_cash is None
        assert model.ending_cash == 4063.52

    def test_hierarchy_property(self, cash_flow_model):
        """
        Given: Model with hierarchy
        When: hierarchy property accessed
        Then: Returns hierarchy dict
        """
        hierarchy = cash_flow_model.hierarchy

        assert isinstance(hierarchy, dict)
        assert 'OPERATING ACTIVITIES' in hierarchy
        assert 'INVESTING ACTIVITIES' in hierarchy
        assert 'FINANCING ACTIVITIES' in hierarchy

    def test_calculated_rows_property(self, cash_flow_model):
        """
        Given: Model with calculated rows
        When: calculated_rows property accessed
        Then: Returns calculated rows list
        """
        calculated = cash_flow_model.calculated_rows

        assert isinstance(calculated, list)
        assert len(calculated) >= 4
        assert any(row['account_name'] == 'Cash at beginning of period' for row in calculated)

    def test_metadata_property(self, cash_flow_model):
        """
        Given: Model with metadata
        When: metadata property accessed
        Then: Returns metadata dict
        """
        metadata = cash_flow_model.metadata

        assert isinstance(metadata, dict)
        assert 'total_rows' in metadata
        assert metadata['total_rows'] == 20

    def test_serialization_round_trip(self, cash_flow_model):
        """
        Given: Model with hierarchy and calculated_rows
        When: to_dict() then from_dict() called
        Then: Reconstructed model equals original (hierarchy and calculated_rows preserved)
        """
        # Serialize to dict
        data = cash_flow_model.to_dict()

        # Check dict has all required keys
        assert 'dataframe' in data
        assert 'hierarchy' in data
        assert 'calculated_rows' in data
        assert 'metadata' in data

        # Deserialize back to model
        reconstructed = CashFlowModel.from_dict(data)

        # Verify hierarchy preserved
        assert reconstructed.hierarchy == cash_flow_model.hierarchy

        # Verify calculated rows preserved
        assert len(reconstructed.calculated_rows) == len(cash_flow_model.calculated_rows)
        assert reconstructed.calculated_rows == cash_flow_model.calculated_rows

        # Verify metadata preserved
        assert reconstructed.metadata == cash_flow_model.metadata

        # Verify DataFrame preserved
        assert len(reconstructed.dataframe) == len(cash_flow_model.dataframe)

        # Verify cash properties still work
        assert reconstructed.beginning_cash == cash_flow_model.beginning_cash
        assert reconstructed.ending_cash == cash_flow_model.ending_cash

    def test_to_dict_structure(self, cash_flow_model):
        """
        Given: Model with all components
        When: to_dict() called
        Then: Returns dict with correct structure
        """
        data = cash_flow_model.to_dict()

        assert isinstance(data, dict)
        assert 'dataframe' in data
        assert 'hierarchy' in data
        assert 'calculated_rows' in data
        assert 'metadata' in data

        # Check hierarchy structure
        assert isinstance(data['hierarchy'], dict)
        assert 'OPERATING ACTIVITIES' in data['hierarchy']

        # Check calculated rows structure
        assert isinstance(data['calculated_rows'], list)
        assert len(data['calculated_rows']) >= 4

    def test_from_dict_missing_keys(self, sample_df):
        """
        Given: Dict missing required keys
        When: from_dict() called
        Then: Raises ValueError
        """
        # Missing hierarchy
        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            CashFlowModel.from_dict({'dataframe': sample_df.to_dict()})

        # Missing calculated_rows
        with pytest.raises(ValueError, match="Missing 'calculated_rows' key"):
            CashFlowModel.from_dict({
                'dataframe': sample_df.to_dict(),
                'hierarchy': {}
            })

        # Missing dataframe
        with pytest.raises(ValueError, match="Missing 'dataframe' key"):
            CashFlowModel.from_dict({
                'hierarchy': {},
                'calculated_rows': []
            })

    def test_dataframe_property(self, cash_flow_model):
        """
        Given: Model with DataFrame
        When: dataframe property accessed
        Then: Returns DataFrame
        """
        df = cash_flow_model.dataframe

        assert isinstance(df, pd.DataFrame)
        assert 'account_name' in df.columns
        assert len(df) > 0

    def test_empty_calculated_rows(self, sample_df, sample_hierarchy, sample_metadata):
        """
        Given: Model with empty calculated_rows
        When: Cash properties accessed
        Then: Returns None gracefully
        """
        model = CashFlowModel(df=sample_df, hierarchy=sample_hierarchy,
                            calculated_rows=[], metadata=sample_metadata)

        assert model.beginning_cash is None
        assert model.ending_cash is None
        assert model.calculated_rows == []

    def test_model_initialization_without_metadata(self, sample_df, sample_hierarchy, sample_calculated_rows):
        """
        Given: Model initialized without metadata parameter
        When: Model created
        Then: Metadata defaults to empty dict
        """
        model = CashFlowModel(df=sample_df, hierarchy=sample_hierarchy,
                            calculated_rows=sample_calculated_rows)

        assert model.metadata == {}
        assert isinstance(model.metadata, dict)
