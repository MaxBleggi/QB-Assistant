"""
Unit tests for PLForecastModel structure and serialization.

Tests initialization, accessors, validation, and round-trip serialization.
"""
import pytest
import pandas as pd

from src.models.pl_forecast_model import PLForecastModel


class TestPLForecastModelInitialization:
    """Test PLForecastModel initialization and validation."""

    def test_initialization_with_valid_data(self):
        """Test initialization with valid hierarchy, calculated_rows, metadata."""
        hierarchy = {
            'Income': [{
                'account_name': 'Income',
                'projected': {1: 10000, 2: 10500, 3: 11025},
                'lower_bound': {1: 9000, 2: 9450, 3: 9922},
                'upper_bound': {1: 11000, 2: 11550, 3: 12127}
            }],
            'Cost of Goods Sold': [{
                'account_name': 'Cost of Goods Sold',
                'projected': {1: 3000, 2: 3150, 3: 3307},
                'lower_bound': {1: 2850, 2: 2992, 3: 3142},
                'upper_bound': {1: 3150, 2: 3307, 3: 3472}
            }],
            'Expenses': [{
                'account_name': 'Expenses',
                'projected': {1: 5000, 2: 5250, 3: 5512},
                'lower_bound': {1: 4750, 2: 4987, 3: 5236},
                'upper_bound': {1: 5250, 2: 5512, 3: 5787}
            }]
        }

        calculated_rows = {
            'gross_profit': {
                'projected': {1: 7000, 2: 7350, 3: 7717},
                'lower_bound': {},
                'upper_bound': {}
            },
            'gross_margin_pct': {
                'projected': {1: 70.0, 2: 70.0, 3: 70.0},
                'lower_bound': {},
                'upper_bound': {}
            },
            'operating_income': {
                'projected': {1: 2000, 2: 2100, 3: 2205},
                'lower_bound': {},
                'upper_bound': {}
            },
            'operating_margin_pct': {
                'projected': {1: 20.0, 2: 20.0, 3: 20.0},
                'lower_bound': {},
                'upper_bound': {}
            },
            'net_income': {
                'projected': {1: 2000, 2: 2100, 3: 2205},
                'lower_bound': {},
                'upper_bound': {}
            }
        }

        metadata = {
            'confidence_level': 0.80,
            'forecast_horizon': 3,
            'excluded_periods': [],
            'warnings': []
        }

        model = PLForecastModel(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

        assert model is not None
        assert model.hierarchy == hierarchy
        assert model.calculated_rows == calculated_rows
        assert model.metadata == metadata

    def test_initialization_without_metadata_raises_error(self):
        """Test that initialization without metadata raises ValueError."""
        hierarchy = {'Income': []}
        calculated_rows = {}

        with pytest.raises(ValueError, match="metadata is required"):
            PLForecastModel(
                hierarchy=hierarchy,
                calculated_rows=calculated_rows,
                metadata=None
            )

    def test_initialization_without_hierarchy_raises_error(self):
        """Test that initialization without hierarchy raises ValueError."""
        calculated_rows = {}
        metadata = {'confidence_level': 0.80}

        with pytest.raises(ValueError, match="hierarchy is required"):
            PLForecastModel(
                hierarchy=None,
                calculated_rows=calculated_rows,
                metadata=metadata
            )

    def test_initialization_with_empty_hierarchy_raises_error(self):
        """Test that initialization with empty hierarchy raises ValueError."""
        calculated_rows = {}
        metadata = {'confidence_level': 0.80}

        with pytest.raises(ValueError, match="hierarchy is required"):
            PLForecastModel(
                hierarchy={},
                calculated_rows=calculated_rows,
                metadata=metadata
            )


class TestPLForecastModelAccessors:
    """Test PLForecastModel accessor methods."""

    @pytest.fixture
    def sample_model(self):
        """Create sample PLForecastModel for testing."""
        hierarchy = {
            'Income': [{
                'account_name': 'Income',
                'projected': {1: 10000, 2: 10500, 3: 11025, 4: 11576, 5: 12155, 6: 12762},
                'lower_bound': {1: 9000, 2: 9450, 3: 9922, 4: 10418, 5: 10939, 6: 11486},
                'upper_bound': {1: 11000, 2: 11550, 3: 12127, 4: 12733, 5: 13370, 6: 14038}
            }],
            'Expenses': [{
                'account_name': 'Expenses',
                'projected': {1: 5000, 2: 5250, 3: 5512, 4: 5788, 5: 6077, 6: 6381},
                'lower_bound': {1: 4750, 2: 4987, 3: 5236, 4: 5498, 5: 5773, 6: 6062},
                'upper_bound': {1: 5250, 2: 5512, 3: 5787, 4: 6076, 5: 6380, 6: 6699}
            }]
        }

        calculated_rows = {
            'gross_profit': {'projected': {1: 10000, 2: 10500}, 'lower_bound': {}, 'upper_bound': {}},
            'gross_margin_pct': {'projected': {1: 100.0, 2: 100.0}, 'lower_bound': {}, 'upper_bound': {}},
            'operating_income': {'projected': {1: 5000, 2: 5250}, 'lower_bound': {}, 'upper_bound': {}},
            'operating_margin_pct': {'projected': {1: 50.0, 2: 50.0}, 'lower_bound': {}, 'upper_bound': {}},
            'net_income': {'projected': {1: 5000, 2: 5250}, 'lower_bound': {}, 'upper_bound': {}}
        }

        metadata = {
            'confidence_level': 0.80,
            'forecast_horizon': 6,
            'excluded_periods': [],
            'warnings': []
        }

        return PLForecastModel(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

    def test_get_income_returns_income_section(self, sample_model):
        """Test get_income() returns Income section dict with value dicts."""
        income = sample_model.get_income()

        assert income is not None
        assert income['account_name'] == 'Income'
        assert 'projected' in income
        assert 'lower_bound' in income
        assert 'upper_bound' in income
        assert len(income['projected']) == 6
        assert income['projected'][1] == 10000

    def test_get_expenses_returns_expenses_section(self, sample_model):
        """Test get_expenses() returns Expenses section dict."""
        expenses = sample_model.get_expenses()

        assert expenses is not None
        assert expenses['account_name'] == 'Expenses'
        assert 'projected' in expenses
        assert len(expenses['projected']) == 6

    def test_get_margins_returns_calculated_rows(self, sample_model):
        """Test get_margins() returns dict with 5 margin metrics."""
        margins = sample_model.get_margins()

        assert margins is not None
        assert 'gross_profit' in margins
        assert 'gross_margin_pct' in margins
        assert 'operating_income' in margins
        assert 'operating_margin_pct' in margins
        assert 'net_income' in margins

        # Check structure
        assert 'projected' in margins['gross_profit']
        assert 'lower_bound' in margins['gross_profit']
        assert 'upper_bound' in margins['gross_profit']


class TestPLForecastModelSerialization:
    """Test PLForecastModel serialization (to_dict/from_dict)."""

    def test_to_dict_produces_serializable_dict(self):
        """Test to_dict() produces dict with all required keys."""
        hierarchy = {
            'Income': [{
                'account_name': 'Income',
                'projected': {1: 10000},
                'lower_bound': {1: 9000},
                'upper_bound': {1: 11000}
            }]
        }

        calculated_rows = {
            'gross_profit': {'projected': {1: 10000}, 'lower_bound': {}, 'upper_bound': {}}
        }

        metadata = {
            'confidence_level': 0.80,
            'forecast_horizon': 1,
            'excluded_periods': [],
            'warnings': []
        }

        model = PLForecastModel(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

        data = model.to_dict()

        assert 'dataframe' in data
        assert 'hierarchy' in data
        assert 'calculated_rows' in data
        assert 'metadata' in data
        assert data['hierarchy'] == hierarchy
        assert data['calculated_rows'] == calculated_rows
        assert data['metadata'] == metadata

    def test_from_dict_reconstructs_equivalent_model(self):
        """Test from_dict() creates equivalent model (round-trip serialization)."""
        hierarchy = {
            'Income': [{
                'account_name': 'Income',
                'projected': {1: 10000, 2: 10500, 3: 11025},
                'lower_bound': {1: 9000, 2: 9450, 3: 9922},
                'upper_bound': {1: 11000, 2: 11550, 3: 12127}
            }],
            'Expenses': [{
                'account_name': 'Expenses',
                'projected': {1: 5000, 2: 5250, 3: 5512},
                'lower_bound': {1: 4750, 2: 4987, 3: 5236},
                'upper_bound': {1: 5250, 2: 5512, 3: 5787}
            }]
        }

        calculated_rows = {
            'gross_profit': {'projected': {1: 10000, 2: 10500, 3: 11025}, 'lower_bound': {}, 'upper_bound': {}},
            'net_income': {'projected': {1: 5000, 2: 5250, 3: 5512}, 'lower_bound': {}, 'upper_bound': {}}
        }

        metadata = {
            'confidence_level': 0.80,
            'forecast_horizon': 3,
            'excluded_periods': ['2024-01-01'],
            'warnings': [{'type': 'HIGH_GROWTH_RATE', 'message': 'Test warning'}]
        }

        original_model = PLForecastModel(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

        # Round-trip
        data = original_model.to_dict()
        reconstructed_model = PLForecastModel.from_dict(data)

        # Verify equivalence
        assert reconstructed_model.hierarchy == original_model.hierarchy
        assert reconstructed_model.calculated_rows == original_model.calculated_rows
        assert reconstructed_model.metadata == original_model.metadata

    def test_from_dict_raises_error_when_metadata_missing(self):
        """Test from_dict() raises ValueError when metadata missing."""
        data = {
            'hierarchy': {'Income': []},
            'calculated_rows': {}
        }

        with pytest.raises(ValueError, match="Missing 'metadata' key"):
            PLForecastModel.from_dict(data)

    def test_from_dict_raises_error_when_hierarchy_missing(self):
        """Test from_dict() raises ValueError when hierarchy missing."""
        data = {
            'calculated_rows': {},
            'metadata': {'confidence_level': 0.80}
        }

        with pytest.raises(ValueError, match="Missing 'hierarchy' key"):
            PLForecastModel.from_dict(data)

    def test_from_dict_raises_error_when_calculated_rows_missing(self):
        """Test from_dict() raises ValueError when calculated_rows missing."""
        data = {
            'hierarchy': {'Income': []},
            'metadata': {'confidence_level': 0.80}
        }

        with pytest.raises(ValueError, match="Missing 'calculated_rows' key"):
            PLForecastModel.from_dict(data)
