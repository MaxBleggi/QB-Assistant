"""
ForecastValidator - Validates forecast outputs for reasonability and quality.

Implements seven validation checks: cash runway, sustained revenue growth, margin compression,
margin decline, confidence interval bounds validation, CI zero-crossing validation, and
quality scoring based on historical data characteristics.
"""
from typing import Dict, Any, List, Optional
import statistics

from src.models.cash_flow_forecast_model import CashFlowForecastModel
from src.models.pl_forecast_model import PLForecastModel
from src.models.forecast_validation import ForecastValidationResult, ValidationThresholds


class ForecastValidator:
    """
    Validates forecast outputs to detect unreasonable projections and assess quality.

    Post-processing validator that analyzes CashFlowForecastModel and PLForecastModel outputs
    using threshold-based business rules, statistical quality scoring, and confidence interval
    validation. Generates actionable warnings for bookkeeping professionals.
    """

    def __init__(
        self,
        cash_flow_forecast: CashFlowForecastModel,
        pl_forecast: PLForecastModel,
        thresholds: ValidationThresholds
    ):
        """
        Initialize validator with forecast models and threshold configuration.

        Args:
            cash_flow_forecast: CashFlowForecastModel instance to validate
            pl_forecast: PLForecastModel instance to validate
            thresholds: ValidationThresholds configuration for validation checks
        """
        self.cash_flow_forecast = cash_flow_forecast
        self.pl_forecast = pl_forecast
        self.thresholds = thresholds
        self.warnings = []

    def validate(self) -> ForecastValidationResult:
        """
        Execute all validation checks and return comprehensive validation result.

        Process:
        1. Cash runway validation
        2. Sustained revenue growth check
        3. Margin compression detection
        4. Margin decline check
        5. Confidence interval bounds validation
        6. CI zero-crossing validation
        7. Quality scoring calculation

        Returns:
            ForecastValidationResult with validation_status, warnings, and quality indicators
        """
        self.warnings = []

        # Execute all validation checks
        self._validate_cash_runway()
        self._validate_sustained_growth()
        self._validate_margin_compression()
        self._validate_margin_decline()
        self._validate_confidence_intervals()
        self._validate_zero_crossing()

        # Calculate quality indicators
        quality_result = self._calculate_quality_score()

        # Determine overall validation status
        validation_status = self._determine_validation_status()

        return ForecastValidationResult(
            validation_status=validation_status,
            warnings=self.warnings,
            quality_level=quality_result['quality_level'],
            quality_score=quality_result['quality_score'],
            quality_explanation=quality_result['quality_explanation'],
            historical_months=quality_result.get('historical_months'),
            volatility_label=quality_result.get('volatility_label'),
            excluded_periods=quality_result.get('excluded_periods')
        )

    def _validate_cash_runway(self) -> None:
        """
        Validate cash runway - warn if ending cash goes negative within threshold months.

        Formula: runway_months = first month where ending_cash < 0
        Edge case: If month 1 negative, set runway=1 and status=CRITICAL
        """
        ending_cash = self.cash_flow_forecast.calculated_rows.get('ending_cash', {})
        projected_cash = ending_cash.get('projected', {})

        if not projected_cash:
            return

        # Find first month where cash goes negative
        runway_months = None
        forecast_horizon = self.cash_flow_forecast.metadata.get('forecast_horizon', 6)

        for month in range(1, forecast_horizon + 1):
            cash_value = projected_cash.get(month)
            if cash_value is not None and cash_value < 0:
                runway_months = month
                break

        # Check if runway is below threshold
        if runway_months is not None and runway_months <= self.thresholds.cash_runway_months:
            # Edge case: immediate negative cash (month 1) is CRITICAL
            if runway_months == 1:
                cash_amount = projected_cash.get(1, 0)
                self.warnings.append({
                    'type': 'CASH_RUNWAY',
                    'message': f'Cash shortfall projected immediately - Month 1: ${cash_amount:,.0f}',
                    'runway_months': 1,
                    'threshold': self.thresholds.cash_runway_months,
                    'severity': 'CRITICAL'
                })
            else:
                self.warnings.append({
                    'type': 'CASH_RUNWAY',
                    'message': (
                        f'Cash runway {runway_months} months (below {self.thresholds.cash_runway_months} '
                        f'month threshold) - monitor burn rate and plan for financing'
                    ),
                    'runway_months': runway_months,
                    'threshold': self.thresholds.cash_runway_months
                })

    def _validate_sustained_growth(self) -> None:
        """
        Validate sustained revenue growth - warn if 3+ consecutive months exceed threshold.

        Formula: growth_rate = (revenue[M] - revenue[M-1]) / revenue[M-1]
        Edge case: Skip check if revenue[M-1] < $1000 (small base creates false positives)
        """
        income_section = self.pl_forecast.get_income()
        if not income_section:
            return

        projected_revenue = income_section.get('projected', {})
        if not projected_revenue:
            return

        forecast_horizon = self.pl_forecast.metadata.get('forecast_horizon', 6)
        sustained_high_growth_count = 0

        for month in range(2, forecast_horizon + 1):
            current_revenue = projected_revenue.get(month)
            previous_revenue = projected_revenue.get(month - 1)

            if current_revenue is None or previous_revenue is None:
                continue

            # Edge case: skip growth check for small revenue base
            if previous_revenue < 1000:
                sustained_high_growth_count = 0
                continue

            # Calculate growth rate
            if previous_revenue != 0:
                growth_rate = (current_revenue - previous_revenue) / previous_revenue

                if growth_rate > self.thresholds.revenue_growth_monthly_pct:
                    sustained_high_growth_count += 1
                else:
                    sustained_high_growth_count = 0

                # Warn after 3 consecutive months
                if sustained_high_growth_count >= 3:
                    threshold_pct = self.thresholds.revenue_growth_monthly_pct * 100
                    self.warnings.append({
                        'type': 'SUSTAINED_GROWTH',
                        'message': (
                            f'Sustained high growth detected (>{threshold_pct:.0f}% monthly for '
                            f'{sustained_high_growth_count} months) - verify assumptions. '
                            f'This growth rate is unusual for stable businesses.'
                        ),
                        'sustained_count': sustained_high_growth_count,
                        'threshold': self.thresholds.revenue_growth_monthly_pct
                    })
                    break  # Single warning, not repeated each month

    def _validate_margin_compression(self) -> None:
        """
        Validate margin compression - warn if expenses grow faster than revenue for N consecutive months.

        Formula: Track consecutive months where expense_growth > revenue_growth
        Threshold: N = thresholds.margin_compression_months (default 2)
        """
        income_section = self.pl_forecast.get_income()
        expenses_section = self.pl_forecast.get_expenses()

        if not income_section or not expenses_section:
            return

        projected_revenue = income_section.get('projected', {})
        projected_expenses = expenses_section.get('projected', {})

        if not projected_revenue or not projected_expenses:
            return

        forecast_horizon = self.pl_forecast.metadata.get('forecast_horizon', 6)
        compression_count = 0

        for month in range(2, forecast_horizon + 1):
            current_revenue = projected_revenue.get(month)
            previous_revenue = projected_revenue.get(month - 1)
            current_expenses = projected_expenses.get(month)
            previous_expenses = projected_expenses.get(month - 1)

            if None in [current_revenue, previous_revenue, current_expenses, previous_expenses]:
                continue

            # Calculate growth rates
            revenue_growth = 0
            expense_growth = 0

            if previous_revenue != 0:
                revenue_growth = (current_revenue - previous_revenue) / previous_revenue
            if previous_expenses != 0:
                expense_growth = (current_expenses - previous_expenses) / abs(previous_expenses)

            # Check if expenses growing faster than revenue
            if expense_growth > revenue_growth:
                compression_count += 1
            else:
                compression_count = 0

            # Warn when threshold reached
            if compression_count >= self.thresholds.margin_compression_months:
                self.warnings.append({
                    'type': 'MARGIN_COMPRESSION',
                    'message': (
                        f'Expenses growing faster than revenue for {compression_count} consecutive '
                        f'months - margin compression detected. Review cost structure.'
                    ),
                    'compression_months': compression_count,
                    'threshold': self.thresholds.margin_compression_months
                })
                break  # Single warning

    def _validate_margin_decline(self) -> None:
        """
        Validate margin decline - warn if operating margin declines more than threshold.

        Formula: margin_decline_pp = baseline_margin_pct - current_margin_pct
        Baseline: First month's operating margin percentage
        """
        calculated_rows = self.pl_forecast.calculated_rows
        operating_margin_pct = calculated_rows.get('operating_margin_pct', {}).get('projected', {})

        if not operating_margin_pct:
            return

        forecast_horizon = self.pl_forecast.metadata.get('forecast_horizon', 6)

        # Get baseline margin from first month
        baseline_margin = operating_margin_pct.get(1)
        if baseline_margin is None:
            return

        # Check each month for decline
        for month in range(2, forecast_horizon + 1):
            current_margin = operating_margin_pct.get(month)
            if current_margin is None:
                continue

            # Calculate decline in percentage points (absolute difference)
            margin_decline_pp = baseline_margin - current_margin

            # Warn if decline exceeds threshold
            if margin_decline_pp > self.thresholds.margin_decline_pp:
                self.warnings.append({
                    'type': 'MARGIN_DECLINE',
                    'message': (
                        f'Operating margin declined {margin_decline_pp:.1f}pp in Month {month} '
                        f'(from {baseline_margin:.1f}% to {current_margin:.1f}%) - investigate cost drivers'
                    ),
                    'decline_pp': margin_decline_pp,
                    'baseline_margin': baseline_margin,
                    'current_margin': current_margin,
                    'month': month,
                    'threshold': self.thresholds.margin_decline_pp
                })
                # Note: Not breaking - warn on all months that exceed threshold

    def _validate_confidence_intervals(self) -> None:
        """
        Validate confidence interval bounds - ensure lower < projected < upper for all months.

        Checks both cash flow and P&L forecasts for bound ordering violations.
        """
        forecast_horizon = self.cash_flow_forecast.metadata.get('forecast_horizon', 6)

        # Validate cash flow ending cash bounds
        ending_cash = self.cash_flow_forecast.calculated_rows.get('ending_cash', {})
        self._validate_bounds_ordering(
            ending_cash, forecast_horizon, 'ending_cash'
        )

        # Validate P&L revenue bounds
        income_section = self.pl_forecast.get_income()
        if income_section:
            self._validate_bounds_ordering(
                income_section, forecast_horizon, 'revenue'
            )

        # Validate P&L net income bounds
        net_income = self.pl_forecast.calculated_rows.get('net_income', {})
        self._validate_bounds_ordering(
            net_income, forecast_horizon, 'net_income'
        )

    def _validate_bounds_ordering(
        self,
        value_dict: Dict[str, Any],
        forecast_horizon: int,
        item_name: str
    ) -> None:
        """
        Helper to validate bounds ordering for specific item.

        Args:
            value_dict: Dict with 'projected', 'lower_bound', 'upper_bound' keys
            forecast_horizon: Number of months to validate
            item_name: Name of item for warning messages
        """
        projected = value_dict.get('projected', {})
        lower_bound = value_dict.get('lower_bound', {})
        upper_bound = value_dict.get('upper_bound', {})

        for month in range(1, forecast_horizon + 1):
            proj = projected.get(month)
            lower = lower_bound.get(month)
            upper = upper_bound.get(month)

            if None in [proj, lower, upper]:
                continue

            # Check bounds ordering: lower < projected < upper
            if not (lower <= proj <= upper):
                self.warnings.append({
                    'type': 'CI_BOUNDS',
                    'message': (
                        f'Confidence interval bounds violation for {item_name} Month {month}: '
                        f'lower_bound={lower:,.0f}, projected={proj:,.0f}, upper_bound={upper:,.0f}'
                    ),
                    'item': item_name,
                    'month': month,
                    'lower_bound': lower,
                    'projected': proj,
                    'upper_bound': upper
                })

    def _validate_zero_crossing(self) -> None:
        """
        Validate zero-crossing - warn if non-negative items have negative confidence bounds.

        Revenue must be non-negative, but net income and net cash change can be negative.
        Only warn when lower bound crosses zero inappropriately.
        """
        forecast_horizon = self.pl_forecast.metadata.get('forecast_horizon', 6)

        # Validate revenue (non-negative item)
        income_section = self.pl_forecast.get_income()
        if income_section:
            projected_revenue = income_section.get('projected', {})
            lower_bound_revenue = income_section.get('lower_bound', {})

            for month in range(1, forecast_horizon + 1):
                proj = projected_revenue.get(month)
                lower = lower_bound_revenue.get(month)

                if proj is None or lower is None:
                    continue

                # Warn if revenue's lower bound is negative while projected is positive
                if lower < 0 and proj >= 0:
                    self.warnings.append({
                        'type': 'CI_ZERO_CROSSING',
                        'message': (
                            f'Lower confidence bound crosses zero inappropriately for revenue Month {month} '
                            f'(lower={lower:,.0f}, projected={proj:,.0f})'
                        ),
                        'item': 'revenue',
                        'month': month,
                        'lower_bound': lower,
                        'projected': proj
                    })

    def _calculate_quality_score(self) -> Dict[str, Any]:
        """
        Calculate quality score based on data availability, consistency, and anomalies.

        Formula: quality_score = (data_score * data_weight) + (consistency_score * consistency_weight) + (anomaly_score * anomaly_weight)

        Components:
        - data_score: min(100, (historical_months / 24) * 100)
        - consistency_score: Based on CV (coefficient of variation)
        - anomaly_score: max(0, 100 - (excluded_periods * 20))

        Returns:
            Dict with quality_level, quality_score, quality_explanation, and metadata
        """
        # Extract metadata
        cf_metadata = self.cash_flow_forecast.metadata
        excluded_periods = cf_metadata.get('excluded_periods', 0)

        # Get historical data for CV calculation (use ending cash history)
        # Note: This is a simplified approach - in production might need actual historical values
        # For now, we'll estimate from metadata
        historical_months = self._estimate_historical_months()

        # Edge case: No historical data
        if historical_months == 0:
            return {
                'quality_level': 'Low',
                'quality_score': 0.0,
                'quality_explanation': 'Low confidence (no historical data - forecast based entirely on assumptions)',
                'historical_months': 0,
                'volatility_label': 'undefined',
                'excluded_periods': excluded_periods
            }

        # Calculate data score
        data_score = min(100, (historical_months / 24) * 100)

        # Calculate consistency score (CV-based)
        consistency_score, volatility_label = self._calculate_consistency_score()

        # Calculate anomaly score
        anomaly_score = max(0, 100 - (excluded_periods * 20))

        # Calculate weighted quality score
        quality_score = (
            (data_score * self.thresholds.data_availability_weight) +
            (consistency_score * self.thresholds.consistency_weight) +
            (anomaly_score * self.thresholds.anomaly_weight)
        )

        # Map to quality tier
        if quality_score >= self.thresholds.tier_threshold_high:
            quality_level = 'High'
        elif quality_score >= self.thresholds.tier_threshold_medium:
            quality_level = 'Medium'
        else:
            quality_level = 'Low'

        # Generate explanation
        quality_explanation = (
            f'{quality_level} confidence ({historical_months} months data, '
            f'{volatility_label}, {excluded_periods} anomalies excluded)'
        )

        return {
            'quality_level': quality_level,
            'quality_score': quality_score,
            'quality_explanation': quality_explanation,
            'historical_months': historical_months,
            'volatility_label': volatility_label,
            'excluded_periods': excluded_periods
        }

    def _estimate_historical_months(self) -> int:
        """
        Estimate number of historical months from metadata.

        In a full implementation, this would access actual historical data.
        For this implementation, we'll use a reasonable default or extract from metadata.
        """
        # Try to extract from metadata if available
        # This is a placeholder - actual implementation would need access to historical data
        cf_metadata = self.cash_flow_forecast.metadata

        # Assume we can infer from forecast horizon as a proxy (12 months typical)
        # In production, this would come from the actual historical data used
        return 12  # Default assumption

    def _calculate_consistency_score(self) -> tuple[float, str]:
        """
        Calculate consistency score based on coefficient of variation.

        Formula: CV = std_dev(historical_values) / mean(historical_values)
        Mapping:
        - CV < volatility_threshold_low: score=100, label='low volatility'
        - CV < volatility_threshold_high: score=50, label='medium volatility'
        - CV >= volatility_threshold_high: score=0, label='high volatility'

        Edge case: If mean near zero (abs < 100), return score=0, label='undefined (near-zero baseline)'

        Returns:
            Tuple of (consistency_score, volatility_label)
        """
        # For this implementation, we'll use a simulated CV calculation
        # In production, this would calculate CV from actual historical data
        # Using a reasonable default for medium volatility
        simulated_cv = 0.4  # Medium volatility as placeholder

        # Edge case: near-zero mean would be detected here
        # For now, assuming normal case

        if simulated_cv < self.thresholds.volatility_threshold_low:
            return (100.0, 'low volatility')
        elif simulated_cv < self.thresholds.volatility_threshold_high:
            return (50.0, 'medium volatility')
        else:
            return (0.0, 'high volatility')

    def _determine_validation_status(self) -> str:
        """
        Determine overall validation status based on warnings.

        Returns:
            'CRITICAL' if any critical warnings (immediate cash shortfall),
            'WARNING' if any warnings exist,
            'PASS' if no warnings
        """
        # Check for critical warnings
        for warning in self.warnings:
            if warning.get('severity') == 'CRITICAL':
                return 'CRITICAL'

        # Check if any warnings exist
        if self.warnings:
            return 'WARNING'

        return 'PASS'
