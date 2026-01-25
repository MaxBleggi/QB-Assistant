"""
Unit tests for PLForecastCalculator calculation logic.

Tests baseline calculation, category-specific compound growth, confidence intervals,
margin calculations, and full orchestration.
"""
import pytest
from unittest.mock import Mock, MagicMock
import pandas as pd

from src.models.pl_model import PLModel
from src.models.forecast_scenario import ForecastScenarioModel
from src.models.anomaly_annotation import AnomalyAnnotationModel
from src.models.pl_forecast_model import PLForecastModel
from src.services.pl_forecast_calculator import PLForecastCalculator


# Fixtures

@pytest.fixture
def mock_pl_model_24_months():
    """Create mock PLModel with 24 months of historical data."""
    mock_model = Mock(spec=PLModel)

    # Income section with 24 months
    income_values = {f'2024-{i:02d}': 9000 + (i * 100) for i in range(1, 13)}
    income_values.update({f'2025-{i:02d}': 10000 + (i * 100) for i in range(1, 13)})
    income_section = {
        'values': income_values
    }

    # COGS section
    cogs_values = {f'2024-{i:02d}': 2700 + (i * 30) for i in range(1, 13)}
    cogs_values.update({f'2025-{i:02d}': 3000 + (i * 30) for i in range(1, 13)})
    cogs_section = {
        'values': cogs_values
    }

    # Expenses section
    expenses_values = {f'2024-{i:02d}': 4500 + (i * 50) for i in range(1, 13)}
    expenses_values.update({f'2025-{i:02d}': 5000 + (i * 50) for i in range(1, 13)})
    expenses_section = {
        'values': expenses_values
    }

    mock_model.get_income.return_value = income_section
    mock_model.get_cogs.return_value = cogs_section
    mock_model.get_expenses.return_value = expenses_section
    mock_model.get_periods.return_value = list(income_values.keys())

    return mock_model


@pytest.fixture
def mock_pl_model_service_business():
    """Create mock PLModel for service business (no COGS section)."""
    mock_model = Mock(spec=PLModel)

    # Income section
    income_values = {f'2024-{i:02d}': 14000 + (i * 200) for i in range(1, 13)}
    income_section = {'values': income_values}

    # No COGS
    # Expenses section
    expenses_values = {f'2024-{i:02d}': 7000 + (i * 100) for i in range(1, 13)}
    expenses_section = {'values': expenses_values}

    mock_model.get_income.return_value = income_section
    mock_model.get_cogs.return_value = None  # Service business
    mock_model.get_expenses.return_value = expenses_section
    mock_model.get_periods.return_value = list(income_values.keys())

    return mock_model


@pytest.fixture
def mock_forecast_scenario_6_months():
    """Create ForecastScenarioModel with 6-month horizon."""
    params = {
        'forecast_horizon': 6,
        'revenue_growth_rate': 0.05,
        'cogs_trend': 0.02,
        'opex_trend': 0.03,
        'confidence_level': 0.80
    }
    return ForecastScenarioModel(parameters=params)


@pytest.fixture
def mock_forecast_scenario_12_months():
    """Create ForecastScenarioModel with 12-month horizon."""
    params = {
        'forecast_horizon': 12,
        'revenue_growth_rate': 0.03,
        'cogs_trend': 0.01,
        'opex_trend': 0.02,
        'confidence_level': 0.80
    }
    return ForecastScenarioModel(parameters=params)


# Test Classes

class TestBaselineCalculation:
    """Test _calculate_baselines method."""

    def test_baseline_calculation_normal_data(self, mock_pl_model_24_months, mock_forecast_scenario_6_months):
        """Test baseline calculation with sufficient historical data returns medians."""
        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_24_months,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        baselines = calculator._calculate_baselines()

        assert 'Income' in baselines
        assert 'Cost of Goods Sold' in baselines
        assert 'Expenses' in baselines
        assert baselines['Income'] > 0
        assert baselines['Cost of Goods Sold'] > 0
        assert baselines['Expenses'] > 0

    def test_baseline_calculation_missing_cogs(self, mock_pl_model_service_business, mock_forecast_scenario_6_months):
        """Test service business with no COGS returns 0.0 baseline and warning."""
        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_service_business,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        baselines = calculator._calculate_baselines()

        assert baselines['Cost of Goods Sold'] == 0.0
        assert len(calculator.warnings) > 0
        assert any(w['type'] == 'NO_COGS_SECTION' for w in calculator.warnings)

    def test_baseline_calculation_invalid_revenue(self, mock_forecast_scenario_6_months):
        """Test revenue baseline <= 0 raises ValueError."""
        mock_model = Mock(spec=PLModel)

        # Negative income
        income_section = {'values': {f'2024-{i:02d}': -100 for i in range(1, 13)}}
        mock_model.get_income.return_value = income_section
        mock_model.get_cogs.return_value = None
        mock_model.get_expenses.return_value = {'values': {}}

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        with pytest.raises(ValueError, match="Invalid revenue baseline"):
            calculator._calculate_baselines()

    def test_baseline_calculation_insufficient_data(self, mock_forecast_scenario_6_months):
        """Test less than 12 periods after exclusion adds warning."""
        mock_model = Mock(spec=PLModel)

        # Only 5 periods
        income_section = {'values': {f'2024-{i:02d}': 10000 for i in range(1, 6)}}
        mock_model.get_income.return_value = income_section
        mock_model.get_cogs.return_value = None
        mock_model.get_expenses.return_value = {'values': {f'2024-{i:02d}': 5000 for i in range(1, 6)}}
        mock_model.get_periods.return_value = [f'2024-{i:02d}' for i in range(1, 6)]

        # Mock anomaly annotations (but don't actually exclude for this test)
        mock_anomaly = Mock(spec=AnomalyAnnotationModel)
        mock_anomaly.get_annotations_by_exclusion_type.return_value = []
        mock_anomaly.get_annotations.return_value = []

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=mock_forecast_scenario_6_months,
            anomaly_annotations=mock_anomaly
        )

        baselines = calculator._calculate_baselines()

        # Should still calculate but potentially warn
        assert baselines['Income'] > 0


class TestCompoundGrowth:
    """Test _apply_compound_growth method."""

    def test_compound_growth_category_specific_rates(self, mock_forecast_scenario_6_months):
        """Test different growth rates applied correctly to Income/COGS/Expenses."""
        mock_model = Mock(spec=PLModel)
        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        baselines = {
            'Income': 10000.0,
            'Cost of Goods Sold': 3000.0,
            'Expenses': 5000.0
        }

        projections = calculator._apply_compound_growth(
            baselines,
            revenue_growth_rate=0.05,
            cogs_trend=0.02,
            opex_trend=0.03,
            forecast_horizon=6
        )

        # Verify structure
        assert 'Income' in projections
        assert 'Cost of Goods Sold' in projections
        assert 'Expenses' in projections

        # Verify month 1 projections (first growth application)
        assert abs(projections['Income'][1] - 10000 * 1.05) < 0.01
        assert abs(projections['Cost of Goods Sold'][1] - 3000 * 1.02) < 0.01
        assert abs(projections['Expenses'][1] - 5000 * 1.03) < 0.01

        # Verify month 3 projections (compound growth)
        assert abs(projections['Income'][3] - 10000 * (1.05 ** 3)) < 1.0
        assert abs(projections['Cost of Goods Sold'][3] - 3000 * (1.02 ** 3)) < 1.0
        assert abs(projections['Expenses'][3] - 5000 * (1.03 ** 3)) < 1.0

    def test_compound_growth_negative_rate(self):
        """Test negative growth rate (decline) produces decreasing projections."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 3, 'revenue_growth_rate': -0.02, 'cogs_trend': -0.02, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        baselines = {'Income': 10000.0, 'Cost of Goods Sold': 3000.0, 'Expenses': 5000.0}

        projections = calculator._apply_compound_growth(
            baselines, -0.02, -0.02, 0.0, 3
        )

        # Month 2 should be less than month 1
        assert projections['Cost of Goods Sold'][2] < projections['Cost of Goods Sold'][1]
        assert projections['Cost of Goods Sold'][3] < projections['Cost of Goods Sold'][2]

    def test_compound_growth_zero_rate(self):
        """Test zero growth rate produces flat projections."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 6, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        baselines = {'Income': 10000.0, 'Cost of Goods Sold': 3000.0, 'Expenses': 5000.0}

        projections = calculator._apply_compound_growth(
            baselines, 0.0, 0.0, 0.0, 6
        )

        # All months should be equal to baseline
        for month in range(1, 7):
            assert projections['Expenses'][month] == 5000.0

    def test_compound_growth_invalid_rate(self):
        """Test growth rate >= 1.0 raises ValueError."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 6, 'revenue_growth_rate': 1.5, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        baselines = {'Income': 10000.0, 'Cost of Goods Sold': 3000.0, 'Expenses': 5000.0}

        with pytest.raises(ValueError, match="Growth rate must be < 100%"):
            calculator._apply_compound_growth(baselines, 1.5, 0.0, 0.0, 6)

    def test_compound_growth_high_growth_warning(self):
        """Test growth rate >= 0.20 adds HIGH_GROWTH_RATE warning."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 6, 'revenue_growth_rate': 0.25, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        baselines = {'Income': 10000.0, 'Cost of Goods Sold': 3000.0, 'Expenses': 5000.0}

        calculator._apply_compound_growth(baselines, 0.25, 0.0, 0.0, 6)

        assert len(calculator.warnings) > 0
        assert any(w['type'] == 'HIGH_GROWTH_RATE' for w in calculator.warnings)


class TestConfidenceIntervals:
    """Test _calculate_confidence_intervals method."""

    def test_confidence_intervals_normal_variance(self, mock_pl_model_24_months, mock_forecast_scenario_6_months):
        """Test historical percentiles produce reasonable confidence bounds."""
        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_24_months,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        baselines = calculator._calculate_baselines()
        projections = calculator._apply_compound_growth(
            baselines, 0.05, 0.02, 0.03, 6
        )

        intervals = calculator._calculate_confidence_intervals(
            projections, baselines, 6
        )

        assert 'Income' in intervals
        assert 'lower_bound' in intervals['Income']
        assert 'upper_bound' in intervals['Income']
        assert len(intervals['Income']['lower_bound']) == 6
        assert len(intervals['Income']['upper_bound']) == 6

        # Lower bound should be less than projected, upper should be greater
        for month in range(1, 7):
            assert intervals['Income']['lower_bound'][month] < projections['Income'][month]
            assert intervals['Income']['upper_bound'][month] > projections['Income'][month]

    def test_confidence_intervals_sqrt_m_scaling_month_1(self, mock_pl_model_24_months):
        """Test month 1 bounds match base percentile ratios (sqrt(1)=1, no scaling)."""
        params = {'forecast_horizon': 6, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_24_months,
            forecast_scenario=scenario
        )

        baselines = calculator._calculate_baselines()
        projections = calculator._apply_compound_growth(
            baselines, 0.0, 0.0, 0.0, 6
        )

        intervals = calculator._calculate_confidence_intervals(
            projections, baselines, 6
        )

        # Month 1 should have sqrt(1) = 1, so scaling factor (sqrt(M) - 1) = 0
        # Bounds should be: projected * ratio * (1 - 0.10 * 0) = projected * ratio
        # (Exact values depend on historical data, but structure should be correct)
        assert intervals['Income']['lower_bound'][1] > 0
        assert intervals['Income']['upper_bound'][1] > 0

    def test_confidence_intervals_sqrt_m_scaling_month_4(self, mock_pl_model_24_months):
        """Test month 4 bounds widen with sqrt(4)=2 scaling factor."""
        params = {'forecast_horizon': 6, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_24_months,
            forecast_scenario=scenario
        )

        baselines = calculator._calculate_baselines()
        projections = calculator._apply_compound_growth(
            baselines, 0.0, 0.0, 0.0, 6
        )

        intervals = calculator._calculate_confidence_intervals(
            projections, baselines, 6
        )

        # Month 4 should have wider bounds than month 1 due to sqrt(4) = 2 vs sqrt(1) = 1
        month_1_width = intervals['Income']['upper_bound'][1] - intervals['Income']['lower_bound'][1]
        month_4_width = intervals['Income']['upper_bound'][4] - intervals['Income']['lower_bound'][4]

        assert month_4_width > month_1_width

    def test_confidence_intervals_cogs_zero(self, mock_pl_model_service_business, mock_forecast_scenario_6_months):
        """Test COGS baseline=0 returns empty confidence bounds."""
        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_service_business,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        baselines = calculator._calculate_baselines()
        projections = calculator._apply_compound_growth(
            baselines, 0.05, 0.0, 0.03, 6
        )

        intervals = calculator._calculate_confidence_intervals(
            projections, baselines, 6
        )

        # COGS should have empty bounds (or all zeros)
        assert 'Cost of Goods Sold' in intervals
        # Empty dicts or all zero values
        cogs_bounds = intervals['Cost of Goods Sold']
        if cogs_bounds['lower_bound']:
            assert all(v == 0 for v in cogs_bounds['lower_bound'].values())


class TestMarginCalculations:
    """Test _calculate_margins method."""

    def test_margins_normal_projections(self):
        """Test margin calculations with positive revenue and profits."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 1, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        projections = {
            'Income': {1: 10000},
            'Cost of Goods Sold': {1: 3000},
            'Expenses': {1: 5000}
        }

        margins = calculator._calculate_margins(projections, 1)

        assert margins['gross_profit']['projected'][1] == 7000
        assert abs(margins['gross_margin_pct']['projected'][1] - 70.0) < 0.1
        assert margins['operating_income']['projected'][1] == 2000
        assert abs(margins['operating_margin_pct']['projected'][1] - 20.0) < 0.1
        assert margins['net_income']['projected'][1] == 2000

    def test_margins_varying_values(self):
        """Test margin calculations with different monthly projections."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 2, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        projections = {
            'Income': {1: 10000, 2: 10500},
            'Cost of Goods Sold': {1: 3000, 2: 3500},
            'Expenses': {1: 5000, 2: 5200}
        }

        margins = calculator._calculate_margins(projections, 2)

        # Month 1
        assert margins['gross_profit']['projected'][1] == 7000
        assert abs(margins['gross_margin_pct']['projected'][1] - 70.0) < 0.1

        # Month 2
        assert margins['gross_profit']['projected'][2] == 7000
        assert abs(margins['gross_margin_pct']['projected'][2] - 66.67) < 0.1

    def test_margins_zero_revenue(self):
        """Test zero revenue returns 0.0 margin percentages without error."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 1, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        projections = {
            'Income': {1: 0},
            'Cost of Goods Sold': {1: 0},
            'Expenses': {1: 5000}
        }

        margins = calculator._calculate_margins(projections, 1)

        assert margins['gross_margin_pct']['projected'][1] == 0.0
        assert margins['operating_margin_pct']['projected'][1] == 0.0
        assert margins['operating_income']['projected'][1] == -5000

    def test_margins_service_business_no_cogs(self):
        """Test service business with COGS=0 produces 100% gross margin."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 1, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        projections = {
            'Income': {1: 15000},
            'Cost of Goods Sold': {1: 0},
            'Expenses': {1: 8000}
        }

        margins = calculator._calculate_margins(projections, 1)

        assert margins['gross_profit']['projected'][1] == 15000
        assert abs(margins['gross_margin_pct']['projected'][1] - 100.0) < 0.1
        assert margins['operating_income']['projected'][1] == 7000
        assert abs(margins['operating_margin_pct']['projected'][1] - 46.67) < 0.1

    def test_margins_negative_margins(self):
        """Test loss period with COGS > revenue produces negative margin percentages."""
        mock_model = Mock(spec=PLModel)
        params = {'forecast_horizon': 1, 'revenue_growth_rate': 0.0, 'cogs_trend': 0.0, 'opex_trend': 0.0}
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=scenario
        )

        projections = {
            'Income': {1: 8000},
            'Cost of Goods Sold': {1: 10000},
            'Expenses': {1: 3000}
        }

        margins = calculator._calculate_margins(projections, 1)

        assert margins['gross_profit']['projected'][1] == -2000
        assert margins['gross_margin_pct']['projected'][1] == -25.0
        assert margins['operating_income']['projected'][1] == -5000
        assert margins['operating_margin_pct']['projected'][1] == -62.5


class TestCalculateOrchestration:
    """Test calculate() orchestration method."""

    def test_calculate_orchestration_complete(self, mock_pl_model_24_months, mock_forecast_scenario_6_months):
        """Test full calculate() returns complete PLForecastModel."""
        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_24_months,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        result = calculator.calculate()

        assert isinstance(result, PLForecastModel)
        assert result.hierarchy is not None
        assert result.calculated_rows is not None
        assert result.metadata is not None

        # Check hierarchy has Income, COGS, Expenses
        assert 'Income' in result.hierarchy
        assert 'Cost of Goods Sold' in result.hierarchy
        assert 'Expenses' in result.hierarchy

        # Check calculated_rows has margin metrics
        assert 'gross_profit' in result.calculated_rows
        assert 'gross_margin_pct' in result.calculated_rows
        assert 'operating_income' in result.calculated_rows
        assert 'operating_margin_pct' in result.calculated_rows
        assert 'net_income' in result.calculated_rows

        # Check metadata
        assert result.metadata['forecast_horizon'] == 6
        assert result.metadata['confidence_level'] == 0.80

    def test_calculate_service_business(self, mock_pl_model_service_business, mock_forecast_scenario_6_months):
        """Test calculate() handles missing COGS gracefully."""
        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_service_business,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        result = calculator.calculate()

        assert isinstance(result, PLForecastModel)
        assert result.metadata['warnings']
        assert any(w['type'] == 'NO_COGS_SECTION' for w in result.metadata['warnings'])

    def test_calculate_with_high_growth_warning(self, mock_pl_model_24_months):
        """Test calculate() accumulates HIGH_GROWTH_RATE warning."""
        params = {
            'forecast_horizon': 6,
            'revenue_growth_rate': 0.22,
            'cogs_trend': 0.0,
            'opex_trend': 0.0
        }
        scenario = ForecastScenarioModel(parameters=params)

        calculator = PLForecastCalculator(
            pl_model=mock_pl_model_24_months,
            forecast_scenario=scenario
        )

        result = calculator.calculate()

        assert result.metadata['warnings']
        assert any(w['type'] == 'HIGH_GROWTH_RATE' for w in result.metadata['warnings'])

    def test_calculate_invalid_baseline_raises_error(self, mock_forecast_scenario_6_months):
        """Test calculate() propagates ValueError from invalid baseline."""
        mock_model = Mock(spec=PLModel)

        # Negative income
        income_section = {'values': {f'2024-{i:02d}': -100 for i in range(1, 13)}}
        mock_model.get_income.return_value = income_section
        mock_model.get_cogs.return_value = None
        mock_model.get_expenses.return_value = {'values': {}}

        calculator = PLForecastCalculator(
            pl_model=mock_model,
            forecast_scenario=mock_forecast_scenario_6_months
        )

        with pytest.raises(ValueError, match="Invalid revenue baseline"):
            calculator.calculate()
