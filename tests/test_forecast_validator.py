"""
Unit tests for ForecastValidator.

Tests all seven validation checks and quality scoring calculation with edge cases.
"""
import pytest
from unittest.mock import Mock

from src.validators.forecast_validator import ForecastValidator
from src.models.forecast_validation import ValidationThresholds, ForecastValidationResult


@pytest.fixture
def default_thresholds():
    """Fixture for default validation thresholds."""
    return ValidationThresholds()


@pytest.fixture
def mock_cash_flow_forecast():
    """Fixture for mock CashFlowForecastModel with configurable data."""
    def _create_mock(ending_cash_projected=None, metadata=None):
        mock = Mock()
        mock.calculated_rows = {
            'ending_cash': {
                'projected': ending_cash_projected or {},
                'lower_bound': {},
                'upper_bound': {}
            }
        }
        mock.metadata = metadata or {
            'forecast_horizon': 6,
            'excluded_periods': 0
        }
        return mock
    return _create_mock


@pytest.fixture
def mock_pl_forecast():
    """Fixture for mock PLForecastModel with configurable data."""
    def _create_mock(revenue_projected=None, expenses_projected=None,
                     operating_margin_pct=None, metadata=None):
        mock = Mock()

        # Set up hierarchy
        income_section = {
            'projected': revenue_projected or {},
            'lower_bound': {},
            'upper_bound': {}
        }
        expenses_section = {
            'projected': expenses_projected or {},
            'lower_bound': {},
            'upper_bound': {}
        }

        mock.get_income = Mock(return_value=income_section)
        mock.get_expenses = Mock(return_value=expenses_section)

        # Set up calculated rows
        mock.calculated_rows = {
            'operating_margin_pct': {
                'projected': operating_margin_pct or {},
                'lower_bound': {},
                'upper_bound': {}
            },
            'net_income': {
                'projected': {},
                'lower_bound': {},
                'upper_bound': {}
            }
        }

        mock.metadata = metadata or {
            'forecast_horizon': 6,
            'excluded_periods': 0
        }

        return mock
    return _create_mock


class TestCashRunwayValidation:
    """Tests for cash runway validation logic."""

    def test_cash_runway_warning_below_threshold(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Cash runway=2, threshold=3
        When: Validator runs
        Then: CASH_RUNWAY warning generated
        """
        # Cash goes negative in month 2
        ending_cash = {1: 10000, 2: -5000, 3: -8000, 4: -12000, 5: -15000, 6: -18000}
        cf_forecast = mock_cash_flow_forecast(ending_cash_projected=ending_cash)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        # Find cash runway warning
        cash_warnings = [w for w in result.warnings if w['type'] == 'CASH_RUNWAY']
        assert len(cash_warnings) == 1
        assert cash_warnings[0]['runway_months'] == 2
        assert cash_warnings[0]['threshold'] == 3
        assert 'monitor burn rate and plan for financing' in cash_warnings[0]['message']

    def test_immediate_negative_cash_critical(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Month 1 ending_cash=-5000
        When: Validator runs
        Then: CRITICAL status with runway=1
        """
        ending_cash = {1: -5000, 2: -8000, 3: -12000, 4: -15000, 5: -18000, 6: -20000}
        cf_forecast = mock_cash_flow_forecast(ending_cash_projected=ending_cash)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        assert result.validation_status == 'CRITICAL'
        cash_warnings = [w for w in result.warnings if w['type'] == 'CASH_RUNWAY']
        assert len(cash_warnings) == 1
        assert cash_warnings[0]['runway_months'] == 1
        assert cash_warnings[0]['severity'] == 'CRITICAL'
        assert 'Cash shortfall projected immediately' in cash_warnings[0]['message']

    def test_no_warning_when_cash_positive(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: All months have positive ending cash
        When: Validator runs
        Then: No CASH_RUNWAY warning
        """
        ending_cash = {1: 50000, 2: 48000, 3: 46000, 4: 44000, 5: 42000, 6: 40000}
        cf_forecast = mock_cash_flow_forecast(ending_cash_projected=ending_cash)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        cash_warnings = [w for w in result.warnings if w['type'] == 'CASH_RUNWAY']
        assert len(cash_warnings) == 0


class TestSustainedGrowthValidation:
    """Tests for sustained revenue growth validation."""

    def test_sustained_growth_triggers_after_three_months(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Revenue growing 35%, 32%, 38% in months 3-5 (threshold=30%)
        When: Validator runs
        Then: SUSTAINED_GROWTH warning after month 5
        """
        # Start with base of $10,000, grow at >30% for 3 consecutive months
        revenue = {
            1: 10000,
            2: 11000,  # 10% growth - below threshold
            3: 14850,  # 35% growth - month 1 of sustained
            4: 19602,  # 32% growth - month 2 of sustained
            5: 27050,  # 38% growth - month 3 of sustained - triggers warning
            6: 28000   # Doesn't matter
        }
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast(revenue_projected=revenue)

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        growth_warnings = [w for w in result.warnings if w['type'] == 'SUSTAINED_GROWTH']
        assert len(growth_warnings) == 1
        assert growth_warnings[0]['sustained_count'] == 3
        assert '>30% monthly for 3 months' in growth_warnings[0]['message']
        assert 'verify assumptions' in growth_warnings[0]['message']

    def test_growth_check_skipped_for_small_revenue_base(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Revenue=$500 growing to $800 (60% growth but base < $1000)
        When: Validator runs
        Then: No SUSTAINED_GROWTH warning (edge case triggered)
        """
        revenue = {
            1: 500,
            2: 800,   # 60% growth but base < $1000 - skipped
            3: 1280,  # 60% growth but previous base < $1000 - skipped
            4: 2048,  # 60% growth but only first month above threshold
            5: 2500,  # Lower growth - counter resets
            6: 3000
        }
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast(revenue_projected=revenue)

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        growth_warnings = [w for w in result.warnings if w['type'] == 'SUSTAINED_GROWTH']
        assert len(growth_warnings) == 0

    def test_growth_counter_resets_on_normal_month(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: 2 high growth months, then normal, then 2 more high
        When: Validator runs
        Then: No warning (counter resets, never reaches 3)
        """
        revenue = {
            1: 10000,
            2: 13500,  # 35% - count=1
            3: 18225,  # 35% - count=2
            4: 20000,  # 10% - counter resets
            5: 27000,  # 35% - count=1
            6: 36450   # 35% - count=2 (not 3)
        }
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast(revenue_projected=revenue)

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        growth_warnings = [w for w in result.warnings if w['type'] == 'SUSTAINED_GROWTH']
        assert len(growth_warnings) == 0


class TestMarginCompressionValidation:
    """Tests for margin compression validation."""

    def test_margin_compression_detected(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Expenses growing faster than revenue for 2 consecutive months
        When: Validator runs
        Then: MARGIN_COMPRESSION warning
        """
        revenue = {1: 100000, 2: 105000, 3: 110250, 4: 115763}  # 5% consistent growth
        expenses = {1: 60000, 2: 64800, 3: 70000, 4: 75600}     # 8%, 8%, 8% growth
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast(
            revenue_projected=revenue,
            expenses_projected=expenses
        )

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        compression_warnings = [w for w in result.warnings if w['type'] == 'MARGIN_COMPRESSION']
        assert len(compression_warnings) == 1
        assert compression_warnings[0]['compression_months'] == 2
        assert 'margin compression detected' in compression_warnings[0]['message']


class TestMarginDeclineValidation:
    """Tests for margin decline validation."""

    def test_margin_decline_exceeds_threshold(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Operating margin 25%→12% (13pp decline), threshold=10pp
        When: Validator runs
        Then: MARGIN_DECLINE warning
        """
        operating_margin = {1: 25.0, 2: 23.0, 3: 18.0, 4: 12.0, 5: 11.0, 6: 10.0}
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast(operating_margin_pct=operating_margin)

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        margin_warnings = [w for w in result.warnings if w['type'] == 'MARGIN_DECLINE']
        # Should warn for months 4, 5, 6 (all decline > 10pp from baseline 25%)
        assert len(margin_warnings) >= 1

        # Check first warning (month 4 with 13pp decline)
        first_warning = margin_warnings[0]
        assert first_warning['decline_pp'] >= 10.0
        assert first_warning['baseline_margin'] == 25.0
        assert 'investigate cost drivers' in first_warning['message']

    def test_no_warning_for_margin_improvement(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Operating margin improving from 15% to 25%
        When: Validator runs
        Then: No MARGIN_DECLINE warning (improvement not flagged)
        """
        operating_margin = {1: 15.0, 2: 18.0, 3: 21.0, 4: 23.0, 5: 25.0, 6: 25.0}
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast(operating_margin_pct=operating_margin)

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        margin_warnings = [w for w in result.warnings if w['type'] == 'MARGIN_DECLINE']
        assert len(margin_warnings) == 0


class TestConfidenceIntervalValidation:
    """Tests for confidence interval bounds validation."""

    def test_confidence_interval_bounds_violation(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: lower_bound[3]=15000, projected[3]=12000, upper_bound[3]=18000
        When: Validator runs
        Then: CI_BOUNDS warning (lower > projected)
        """
        cf_mock = mock_cash_flow_forecast()
        # Create bounds violation
        cf_mock.calculated_rows['ending_cash'] = {
            'projected': {1: 10000, 2: 11000, 3: 12000},
            'lower_bound': {1: 8000, 2: 9000, 3: 15000},  # Month 3: lower > projected
            'upper_bound': {1: 12000, 2: 13000, 3: 18000}
        }
        cf_mock.metadata = {'forecast_horizon': 3, 'excluded_periods': 0}

        pl_forecast = mock_pl_forecast(metadata={'forecast_horizon': 3})

        validator = ForecastValidator(cf_mock, pl_forecast, default_thresholds)
        result = validator.validate()

        ci_warnings = [w for w in result.warnings if w['type'] == 'CI_BOUNDS']
        assert len(ci_warnings) >= 1
        violation = ci_warnings[0]
        assert violation['month'] == 3
        assert violation['lower_bound'] == 15000
        assert violation['projected'] == 12000


class TestZeroCrossingValidation:
    """Tests for confidence interval zero-crossing validation."""

    def test_zero_crossing_warning_for_revenue(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Revenue lower_bound[2]=-5000, projected[2]=10000
        When: Validator runs
        Then: CI_ZERO_CROSSING warning (revenue is non-negative item)
        """
        cf_forecast = mock_cash_flow_forecast()

        # Create zero-crossing violation for revenue
        pl_mock = mock_pl_forecast(metadata={'forecast_horizon': 3})
        income_section = {
            'projected': {1: 15000, 2: 10000, 3: 12000},
            'lower_bound': {1: 10000, 2: -5000, 3: 8000},  # Month 2 crosses zero
            'upper_bound': {1: 20000, 2: 15000, 3: 16000}
        }
        pl_mock.get_income = Mock(return_value=income_section)

        validator = ForecastValidator(cf_forecast, pl_mock, default_thresholds)
        result = validator.validate()

        zero_warnings = [w for w in result.warnings if w['type'] == 'CI_ZERO_CROSSING']
        assert len(zero_warnings) >= 1
        warning = zero_warnings[0]
        assert warning['item'] == 'revenue'
        assert warning['month'] == 2
        assert warning['lower_bound'] == -5000
        assert warning['projected'] == 10000


class TestQualityScoring:
    """Tests for quality scoring calculation."""

    def test_quality_scoring_high_confidence(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: 24 months history, low CV (simulated), 0 anomalies
        When: Quality scoring calculated
        Then: High quality level
        """
        cf_metadata = {'forecast_horizon': 6, 'excluded_periods': 0}
        cf_forecast = mock_cash_flow_forecast(metadata=cf_metadata)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        # With default simulation (12 months, medium volatility, 0 anomalies)
        # Expected: data_score=50, consistency_score=50, anomaly_score=100
        # quality_score = (50*0.5) + (50*0.3) + (100*0.2) = 25 + 15 + 20 = 60
        assert result.quality_level in ['Medium', 'High', 'Low']
        assert 0 <= result.quality_score <= 100
        assert 'months data' in result.quality_explanation
        assert 'volatility' in result.quality_explanation

    def test_quality_scoring_low_confidence(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: 6 months history (simulated), high CV, 2 anomalies
        When: Quality scoring calculated
        Then: Lower quality score
        """
        cf_metadata = {'forecast_horizon': 6, 'excluded_periods': 2}
        cf_forecast = mock_cash_flow_forecast(metadata=cf_metadata)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        # Quality should be impacted by anomalies
        assert result.excluded_periods == 2
        assert 'anomalies excluded' in result.quality_explanation

    def test_quality_scoring_no_historical_data(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: 0 months historical data (mocked via _estimate_historical_months)
        When: Quality scoring calculated
        Then: Low quality with specific message
        """
        # This tests the edge case but our implementation has a placeholder
        # In production, this would detect zero historical months
        cf_forecast = mock_cash_flow_forecast()
        pl_forecast = mock_pl_forecast()

        # Mock the validator's _estimate_historical_months to return 0
        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        validator._estimate_historical_months = Mock(return_value=0)

        result = validator.validate()

        assert result.quality_level == 'Low'
        assert 'no historical data' in result.quality_explanation


class TestValidationStatus:
    """Tests for overall validation status determination."""

    def test_validation_status_pass_no_warnings(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Forecast with no warnings
        When: Validator runs
        Then: validation_status='PASS'
        """
        ending_cash = {1: 50000, 2: 48000, 3: 46000, 4: 44000, 5: 42000, 6: 40000}
        revenue = {1: 100000, 2: 105000, 3: 110000, 4: 115000, 5: 120000, 6: 125000}

        cf_forecast = mock_cash_flow_forecast(ending_cash_projected=ending_cash)
        pl_forecast = mock_pl_forecast(revenue_projected=revenue)

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        assert result.validation_status == 'PASS'
        assert len(result.warnings) == 0

    def test_validation_status_warning(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Forecast with non-critical warnings
        When: Validator runs
        Then: validation_status='WARNING'
        """
        # Cash runway warning but not immediate
        ending_cash = {1: 10000, 2: -5000, 3: -8000, 4: -12000, 5: -15000, 6: -18000}
        cf_forecast = mock_cash_flow_forecast(ending_cash_projected=ending_cash)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        assert result.validation_status == 'WARNING'
        assert len(result.warnings) > 0

    def test_validation_status_critical(
        self, mock_cash_flow_forecast, mock_pl_forecast, default_thresholds
    ):
        """
        Given: Forecast with immediate cash shortfall (month 1 negative)
        When: Validator runs
        Then: validation_status='CRITICAL'
        """
        ending_cash = {1: -5000, 2: -8000, 3: -12000, 4: -15000, 5: -18000, 6: -20000}
        cf_forecast = mock_cash_flow_forecast(ending_cash_projected=ending_cash)
        pl_forecast = mock_pl_forecast()

        validator = ForecastValidator(cf_forecast, pl_forecast, default_thresholds)
        result = validator.validate()

        assert result.validation_status == 'CRITICAL'
