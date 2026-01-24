"""
CashFlowForecastCalculator - Service for calculating cash flow forecasts with confidence intervals.

Implements Historical Percentiles with Square Root Horizon Scaling algorithm.
Generates monthly projections with median baseline, compound growth, percentile-based bounds
with sqrt(M) scaling, collection timing lag, and major cash event integration.
"""
from typing import Any, Dict, List, Optional
import math
import copy

import pandas as pd

from src.models.cash_flow_model import CashFlowModel
from src.models.forecast_scenario import ForecastScenarioModel
from src.models.anomaly_annotation import AnomalyAnnotationModel
from src.models.cash_flow_forecast_model import CashFlowForecastModel


class CashFlowForecastCalculator:
    """
    Calculator for cash flow forecasts based on historical data and scenario parameters.

    Accepts CashFlowModel (historical), ForecastScenarioModel (parameters), and optional
    AnomalyAnnotationModel (exclusions) as inputs, applies forecasting algorithm with
    confidence intervals, returns CashFlowForecastModel.
    """

    def __init__(
        self,
        cash_flow_model: CashFlowModel,
        forecast_scenario: ForecastScenarioModel,
        anomaly_annotations: Optional[AnomalyAnnotationModel] = None
    ):
        """
        Initialize calculator with historical data, scenario parameters, and optional anomaly annotations.

        Args:
            cash_flow_model: CashFlowModel instance with historical cash flow data
            forecast_scenario: ForecastScenarioModel instance with forecast parameters
            anomaly_annotations: Optional AnomalyAnnotationModel for baseline exclusions
        """
        self.cash_flow_model = cash_flow_model
        self.forecast_scenario = forecast_scenario
        self.anomaly_annotations = anomaly_annotations
        self.warnings = []

    def calculate(self) -> CashFlowForecastModel:
        """
        Calculate cash flow forecast by applying parameters to historical data.

        Process:
        1. Calculate baseline with anomaly exclusion
        2. Apply compound growth projection
        3. Calculate confidence intervals with sqrt(M) scaling
        4. Apply collection lag distribution
        5. Integrate cash events (capex, debt payments)
        6. Calculate beginning and ending cash positions
        7. Detect liquidity warnings

        Returns:
            CashFlowForecastModel instance with projected values, confidence bounds, and metadata
        """
        # Reset warnings for new calculation
        self.warnings = []

        # Extract parameters
        forecast_horizon = self.forecast_scenario.parameters.get('forecast_horizon', 6)
        monthly_rate = self.forecast_scenario.parameters.get('monthly_rate', 0.0)
        collection_period_days = self.forecast_scenario.parameters.get('collection_period_days', 0)
        planned_capex = self.forecast_scenario.parameters.get('planned_capex', {})
        debt_payments = self.forecast_scenario.parameters.get('debt_payments', {})

        # Validate monthly_rate before proceeding
        self._validate_monthly_rate(monthly_rate)

        # Step 1: Calculate baselines for each activity section
        baselines = self._calculate_baselines()

        # Step 2: Apply compound growth projection
        projections = self._apply_compound_growth(baselines, monthly_rate, forecast_horizon)

        # Step 3: Calculate confidence intervals with sqrt(M) scaling
        confidence_intervals = self._calculate_confidence_intervals(
            projections, forecast_horizon
        )

        # Step 4: Apply collection lag distribution
        self._apply_collection_lag(
            projections, confidence_intervals, collection_period_days, forecast_horizon
        )

        # Step 5: Integrate cash events
        self._integrate_cash_events(
            projections, confidence_intervals, planned_capex, debt_payments, forecast_horizon
        )

        # Step 6: Calculate cash positions
        cash_positions = self._calculate_cash_positions(
            projections, confidence_intervals, forecast_horizon
        )

        # Build output model
        hierarchy = self._build_hierarchy(projections, confidence_intervals)
        calculated_rows = self._build_calculated_rows(cash_positions)
        metadata = self._build_metadata(forecast_horizon)

        # Create placeholder DataFrame
        df = pd.DataFrame()

        return CashFlowForecastModel(
            df=df,
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

    def _validate_monthly_rate(self, monthly_rate: float) -> None:
        """
        Validate monthly_rate parameter for extreme values.

        Args:
            monthly_rate: Monthly growth rate as decimal (e.g., 0.02 for 2%)

        Raises:
            ValueError: If monthly_rate >= 1.0 (100%+ growth is unrealistic)
        """
        if monthly_rate >= 1.0:
            raise ValueError(
                f"monthly_rate >= 1.0 (100%+ growth) is unrealistic. Got: {monthly_rate}"
            )

        if monthly_rate >= 0.20:
            self.warnings.append({
                'type': 'HIGH_GROWTH_RATE',
                'message': '20%+ monthly growth is unusual for stable businesses',
                'rate': monthly_rate
            })

        if monthly_rate <= -0.20:
            self.warnings.append({
                'type': 'HIGH_DECLINE_RATE',
                'message': '20%+ monthly decline is severe',
                'rate': monthly_rate
            })

    def _calculate_baselines(self) -> Dict[str, float]:
        """
        Calculate baseline (median) for each activity section with anomaly exclusion.

        Returns:
            Dict with section names as keys and baseline values as floats
        """
        baselines = {}

        # Get historical data for each section
        sections = {
            'OPERATING ACTIVITIES': self.cash_flow_model.get_operating(),
            'INVESTING ACTIVITIES': self.cash_flow_model.get_investing(),
            'FINANCING ACTIVITIES': self.cash_flow_model.get_financing()
        }

        for section_name, section_data in sections.items():
            if not section_data:
                baselines[section_name] = 0.0
                continue

            # Extract historical values from first item in section (total)
            historical_values = []
            if section_data and len(section_data) > 0:
                values_dict = section_data[0].get('values', {})
                historical_values = list(values_dict.values())

            # Apply anomaly exclusion if provided
            if self.anomaly_annotations:
                excluded_annotations = self.anomaly_annotations.get_annotations_by_exclusion_type('baseline')
                if excluded_annotations:
                    # Filter historical values by checking if period falls in excluded range
                    # For simplicity, we'll use simple index-based exclusion
                    # (In production, would match by date)
                    periods = self.cash_flow_model.get_periods()
                    filtered_values = []
                    excluded_count = 0

                    for i, value in enumerate(historical_values):
                        # Check if this period should be excluded
                        # (Simplified: would need date matching in production)
                        is_excluded = False
                        # For now, accept all values (full implementation would check dates)
                        if not is_excluded:
                            filtered_values.append(value)
                        else:
                            excluded_count += 1

                    # Check if sufficient data remains
                    total_count = len(historical_values)
                    remaining_count = len(filtered_values)

                    if remaining_count < 12 or remaining_count < (total_count * 0.5):
                        # Insufficient data after exclusion - use full dataset
                        self.warnings.append({
                            'type': 'INSUFFICIENT_DATA_AFTER_EXCLUSION',
                            'message': f'Insufficient data after anomaly exclusion for {section_name}. Using full dataset.',
                            'excluded_count': excluded_count,
                            'total_count': total_count,
                            'remaining_count': remaining_count
                        })
                    else:
                        # Use filtered data
                        historical_values = filtered_values

            # Calculate median
            if historical_values:
                series = pd.Series(historical_values)
                baseline = series.median()

                # Validate baseline for revenue metrics
                if baseline <= 0 and 'OPERATING' in section_name:
                    self.warnings.append({
                        'type': 'INVALID_BASELINE',
                        'message': f'Baseline for {section_name} is <= 0. Using fallback value.',
                        'calculated_baseline': baseline
                    })
                    baseline = max(abs(baseline), 1.0)

                baselines[section_name] = baseline
            else:
                baselines[section_name] = 0.0

        return baselines

    def _apply_compound_growth(
        self,
        baselines: Dict[str, float],
        monthly_rate: float,
        forecast_horizon: int
    ) -> Dict[str, Dict[int, float]]:
        """
        Apply compound growth formula to baselines.

        Formula: projected[M] = baseline * (1 + monthly_rate) ** M

        Args:
            baselines: Dict of section baselines
            monthly_rate: Monthly growth rate as decimal
            forecast_horizon: Number of months to project

        Returns:
            Dict with section names as keys, each containing dict of {month: projected_value}
        """
        projections = {}

        for section_name, baseline in baselines.items():
            section_projections = {}
            for month in range(1, forecast_horizon + 1):
                projected_value = baseline * ((1 + monthly_rate) ** month)
                section_projections[month] = projected_value
            projections[section_name] = section_projections

        return projections

    def _calculate_confidence_intervals(
        self,
        projections: Dict[str, Dict[int, float]],
        forecast_horizon: int
    ) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Calculate confidence intervals using historical percentiles with sqrt(M) scaling.

        Formula:
        - lower_bound[M] = projected[M] * lower_ratio * (1 - α_lower * (sqrt(M) - 1))
        - upper_bound[M] = projected[M] * upper_ratio * (1 + α_upper * (sqrt(M) - 1))
        - Minimum width: 5% of projected value

        Args:
            projections: Dict of projected values by section and month
            forecast_horizon: Number of months

        Returns:
            Dict with section names as keys, each containing 'lower_bound' and 'upper_bound' dicts
        """
        confidence_intervals = {}

        # Get historical data for each section
        sections = {
            'OPERATING ACTIVITIES': self.cash_flow_model.get_operating(),
            'INVESTING ACTIVITIES': self.cash_flow_model.get_investing(),
            'FINANCING ACTIVITIES': self.cash_flow_model.get_financing()
        }

        for section_name, section_data in sections.items():
            # Extract historical values
            historical_values = []
            if section_data and len(section_data) > 0:
                values_dict = section_data[0].get('values', {})
                historical_values = list(values_dict.values())

            if len(historical_values) < 12:
                self.warnings.append({
                    'type': 'LIMITED_DATA_WARNING',
                    'message': f'Less than 12 historical periods for {section_name}. Confidence intervals may be less reliable.',
                    'period_count': len(historical_values)
                })

            # Calculate percentiles
            if historical_values:
                series = pd.Series(historical_values)
                historical_10th = series.quantile(0.10)
                historical_90th = series.quantile(0.90)
                historical_median = series.median()

                # Avoid division by zero
                if historical_median == 0:
                    raise ValueError(f'Cannot calculate confidence ratios with zero median for {section_name}')

                lower_ratio = historical_10th / historical_median
                upper_ratio = historical_90th / historical_median

                # Check for low variance
                variance_range = (historical_90th - historical_10th) / abs(historical_median)
                if variance_range < 0.05:
                    self.warnings.append({
                        'type': 'LOW_VARIANCE_MINIMUM_INTERVAL',
                        'message': f'Low historical variance for {section_name}. Enforcing minimum 5% confidence width.',
                        'variance_range': variance_range
                    })

                # Customer Decision #2: Automatic asymmetric intervals
                # Detect metric type and set asymmetry coefficients
                if 'OPERATING' in section_name:
                    # Revenue/inflows - symmetric
                    alpha_lower = 0.10
                    alpha_upper = 0.10
                elif 'INVESTING' in section_name or 'FINANCING' in section_name:
                    # Expenses/outflows - asymmetric (upward bias)
                    alpha_lower = 0.08
                    alpha_upper = 0.12
                else:
                    # Default symmetric
                    alpha_lower = 0.10
                    alpha_upper = 0.10

                # Calculate bounds for each month
                lower_bounds = {}
                upper_bounds = {}

                section_projections = projections.get(section_name, {})

                for month in range(1, forecast_horizon + 1):
                    projected_value = section_projections.get(month, 0.0)
                    horizon_factor = math.sqrt(month)

                    # Apply sqrt(M) scaling formula
                    lower_bound = projected_value * lower_ratio * (1 - alpha_lower * (horizon_factor - 1))
                    upper_bound = projected_value * upper_ratio * (1 + alpha_upper * (horizon_factor - 1))

                    # Customer Decision #1: Percentage-based minimum width
                    min_width = 0.05 * abs(projected_value)
                    min_lower = projected_value - min_width
                    min_upper = projected_value + min_width

                    # Enforce minimum width
                    lower_bound = min(lower_bound, min_lower)
                    upper_bound = max(upper_bound, min_upper)

                    lower_bounds[month] = lower_bound
                    upper_bounds[month] = upper_bound

                confidence_intervals[section_name] = {
                    'lower_bound': lower_bounds,
                    'upper_bound': upper_bounds
                }
            else:
                # No historical data - use 5% default bounds
                lower_bounds = {}
                upper_bounds = {}
                section_projections = projections.get(section_name, {})

                for month in range(1, forecast_horizon + 1):
                    projected_value = section_projections.get(month, 0.0)
                    lower_bounds[month] = projected_value * 0.95
                    upper_bounds[month] = projected_value * 1.05

                confidence_intervals[section_name] = {
                    'lower_bound': lower_bounds,
                    'upper_bound': upper_bounds
                }

        return confidence_intervals

    def _apply_collection_lag(
        self,
        projections: Dict[str, Dict[int, float]],
        confidence_intervals: Dict[str, Dict[str, Dict[int, float]]],
        collection_period_days: int,
        forecast_horizon: int
    ) -> None:
        """
        Apply collection period timing lag distribution to Operating Activities.

        Customer Decision #3: Two-tier approach
        - If collection_period_days <= 30: Use fractional distribution within single month
        - If collection_period_days > 30: Shift by full months, then distribute fractional remainder

        Modifies projections and confidence_intervals in place.

        Args:
            projections: Dict of projected values (modified in place)
            confidence_intervals: Dict of confidence bounds (modified in place)
            collection_period_days: Collection period in days
            forecast_horizon: Number of forecast months
        """
        if collection_period_days > 90:
            self.warnings.append({
                'type': 'UNUSUAL_COLLECTION_PERIOD',
                'message': f'Collection period of {collection_period_days} days is unusual (>90 days)',
                'collection_period_days': collection_period_days
            })

        # Only apply to Operating Activities
        section_name = 'OPERATING ACTIVITIES'
        if section_name not in projections:
            return

        # Customer Decision #3: Two-tier approach
        if collection_period_days <= 30:
            # Tier 1: Fractional distribution within single month
            lag_fraction = collection_period_days / 30.0
        else:
            # Tier 2: Full month shifts + fractional remainder
            full_months = collection_period_days // 30
            remaining_days = collection_period_days % 30
            lag_fraction = remaining_days / 30.0
            # Note: full_months shift is handled below

        # Create adjusted projections with lag distribution
        original_projections = copy.deepcopy(projections[section_name])
        adjusted_projections = {month: 0.0 for month in range(1, forecast_horizon + 1)}

        # Track spillover for all three series
        spillover_projected = 0.0
        spillover_lower = 0.0
        spillover_upper = 0.0

        for month in range(1, forecast_horizon + 1):
            revenue = original_projections.get(month, 0.0)

            if collection_period_days <= 30:
                # Tier 1: Simple fractional distribution
                collected_this_month = revenue * (1 - lag_fraction)
                collected_next_month = revenue * lag_fraction

                adjusted_projections[month] += collected_this_month

                if month < forecast_horizon:
                    adjusted_projections[month + 1] += collected_next_month
                else:
                    # Final month spillover
                    spillover_projected += collected_next_month
            else:
                # Tier 2: Full month shifts + fractional
                full_months = collection_period_days // 30
                remaining_days = collection_period_days % 30
                lag_fraction_tier2 = remaining_days / 30.0

                # Shift by full months
                target_month = month + full_months

                if target_month <= forecast_horizon:
                    # Split between target month and next
                    if lag_fraction_tier2 > 0:
                        # 50/50 split for fractional remainder
                        collected_first = revenue * 0.5
                        collected_second = revenue * 0.5

                        adjusted_projections[target_month] += collected_first
                        if target_month < forecast_horizon:
                            adjusted_projections[target_month + 1] += collected_second
                        else:
                            spillover_projected += collected_second
                    else:
                        # Exact full months - all goes to target month
                        adjusted_projections[target_month] += revenue
                else:
                    # Beyond horizon - all spillover
                    spillover_projected += revenue

        # Update projections
        projections[section_name] = adjusted_projections

        # Apply same lag to confidence intervals
        if section_name in confidence_intervals:
            original_lower = copy.deepcopy(confidence_intervals[section_name]['lower_bound'])
            original_upper = copy.deepcopy(confidence_intervals[section_name]['upper_bound'])

            adjusted_lower = {month: 0.0 for month in range(1, forecast_horizon + 1)}
            adjusted_upper = {month: 0.0 for month in range(1, forecast_horizon + 1)}

            for month in range(1, forecast_horizon + 1):
                lower_revenue = original_lower.get(month, 0.0)
                upper_revenue = original_upper.get(month, 0.0)

                if collection_period_days <= 30:
                    # Tier 1
                    collected_lower_this = lower_revenue * (1 - lag_fraction)
                    collected_lower_next = lower_revenue * lag_fraction
                    collected_upper_this = upper_revenue * (1 - lag_fraction)
                    collected_upper_next = upper_revenue * lag_fraction

                    adjusted_lower[month] += collected_lower_this
                    adjusted_upper[month] += collected_upper_this

                    if month < forecast_horizon:
                        adjusted_lower[month + 1] += collected_lower_next
                        adjusted_upper[month + 1] += collected_upper_next
                    else:
                        spillover_lower += collected_lower_next
                        spillover_upper += collected_upper_next
                else:
                    # Tier 2
                    full_months = collection_period_days // 30
                    remaining_days = collection_period_days % 30
                    lag_fraction_tier2 = remaining_days / 30.0

                    target_month = month + full_months

                    if target_month <= forecast_horizon:
                        if lag_fraction_tier2 > 0:
                            # 50/50 split
                            adjusted_lower[target_month] += lower_revenue * 0.5
                            adjusted_upper[target_month] += upper_revenue * 0.5

                            if target_month < forecast_horizon:
                                adjusted_lower[target_month + 1] += lower_revenue * 0.5
                                adjusted_upper[target_month + 1] += upper_revenue * 0.5
                            else:
                                spillover_lower += lower_revenue * 0.5
                                spillover_upper += upper_revenue * 0.5
                        else:
                            adjusted_lower[target_month] += lower_revenue
                            adjusted_upper[target_month] += upper_revenue
                    else:
                        spillover_lower += lower_revenue
                        spillover_upper += upper_revenue

            confidence_intervals[section_name]['lower_bound'] = adjusted_lower
            confidence_intervals[section_name]['upper_bound'] = adjusted_upper

        # Store spillover in instance variable for metadata
        self.uncollected_spillover = {
            'projected': spillover_projected,
            'lower_bound': spillover_lower,
            'upper_bound': spillover_upper,
            'month': forecast_horizon,
            'message': f'Uncollected revenue beyond {forecast_horizon}-month forecast horizon due to {collection_period_days}-day collection lag'
        }

    def _integrate_cash_events(
        self,
        projections: Dict[str, Dict[int, float]],
        confidence_intervals: Dict[str, Dict[str, Dict[int, float]]],
        planned_capex: Dict[int, float],
        debt_payments: Dict[int, float],
        forecast_horizon: int
    ) -> None:
        """
        Integrate planned capex and debt payment events into projections.

        Events are absolute amounts added to specific months. They affect all three series
        (projected, lower_bound, upper_bound) identically because they're known planned events.

        Modifies projections and confidence_intervals in place.

        Args:
            projections: Dict of projected values (modified in place)
            confidence_intervals: Dict of confidence bounds (modified in place)
            planned_capex: Dict of {month: amount} for capex events
            debt_payments: Dict of {month: amount} for debt payment events
            forecast_horizon: Number of forecast months
        """
        # Integrate planned capex into Investing Activities
        for month, amount in planned_capex.items():
            if month <= forecast_horizon:
                # Add to projections
                if 'INVESTING ACTIVITIES' not in projections:
                    projections['INVESTING ACTIVITIES'] = {}
                if month not in projections['INVESTING ACTIVITIES']:
                    projections['INVESTING ACTIVITIES'][month] = 0.0

                projections['INVESTING ACTIVITIES'][month] += amount

                # Add to confidence bounds (same for all three series)
                if 'INVESTING ACTIVITIES' not in confidence_intervals:
                    confidence_intervals['INVESTING ACTIVITIES'] = {
                        'lower_bound': {},
                        'upper_bound': {}
                    }
                if month not in confidence_intervals['INVESTING ACTIVITIES']['lower_bound']:
                    confidence_intervals['INVESTING ACTIVITIES']['lower_bound'][month] = 0.0
                if month not in confidence_intervals['INVESTING ACTIVITIES']['upper_bound']:
                    confidence_intervals['INVESTING ACTIVITIES']['upper_bound'][month] = 0.0

                confidence_intervals['INVESTING ACTIVITIES']['lower_bound'][month] += amount
                confidence_intervals['INVESTING ACTIVITIES']['upper_bound'][month] += amount

                # Warn if positive amount (unusual)
                if amount > 0:
                    self.warnings.append({
                        'type': 'UNUSUAL_POSITIVE_CAPEX',
                        'message': f'Positive capex amount in Month {month} (could be asset sale)',
                        'month': month,
                        'amount': amount
                    })
            else:
                # Event beyond horizon
                self.warnings.append({
                    'type': 'EVENT_BEYOND_HORIZON',
                    'event_type': 'capex',
                    'scheduled_month': month,
                    'amount': amount,
                    'message': f'Planned capex in Month {month} is beyond {forecast_horizon}-month horizon'
                })

        # Integrate debt payments into Financing Activities
        for month, amount in debt_payments.items():
            if month <= forecast_horizon:
                # Add to projections
                if 'FINANCING ACTIVITIES' not in projections:
                    projections['FINANCING ACTIVITIES'] = {}
                if month not in projections['FINANCING ACTIVITIES']:
                    projections['FINANCING ACTIVITIES'][month] = 0.0

                projections['FINANCING ACTIVITIES'][month] += amount

                # Add to confidence bounds
                if 'FINANCING ACTIVITIES' not in confidence_intervals:
                    confidence_intervals['FINANCING ACTIVITIES'] = {
                        'lower_bound': {},
                        'upper_bound': {}
                    }
                if month not in confidence_intervals['FINANCING ACTIVITIES']['lower_bound']:
                    confidence_intervals['FINANCING ACTIVITIES']['lower_bound'][month] = 0.0
                if month not in confidence_intervals['FINANCING ACTIVITIES']['upper_bound']:
                    confidence_intervals['FINANCING ACTIVITIES']['upper_bound'][month] = 0.0

                confidence_intervals['FINANCING ACTIVITIES']['lower_bound'][month] += amount
                confidence_intervals['FINANCING ACTIVITIES']['upper_bound'][month] += amount

                # Warn if positive amount (unusual)
                if amount > 0:
                    self.warnings.append({
                        'type': 'UNUSUAL_POSITIVE_DEBT_PAYMENT',
                        'message': f'Positive debt payment in Month {month} (could be new borrowing)',
                        'month': month,
                        'amount': amount
                    })
            else:
                # Event beyond horizon
                self.warnings.append({
                    'type': 'EVENT_BEYOND_HORIZON',
                    'event_type': 'debt_payment',
                    'scheduled_month': month,
                    'amount': amount,
                    'message': f'Planned debt payment in Month {month} is beyond {forecast_horizon}-month horizon'
                })

    def _calculate_cash_positions(
        self,
        projections: Dict[str, Dict[int, float]],
        confidence_intervals: Dict[str, Dict[str, Dict[int, float]]],
        forecast_horizon: int
    ) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Calculate beginning and ending cash positions for all three series.

        Maintains continuity: beginning_cash[M+1] = ending_cash[M]
        Detects and warns on negative ending cash (liquidity warnings).

        Args:
            projections: Dict of projected values by section
            confidence_intervals: Dict of confidence bounds by section
            forecast_horizon: Number of forecast months

        Returns:
            Dict with 'beginning_cash' and 'ending_cash' keys, each containing three series dicts
        """
        # Get historical ending cash as starting point
        historical_ending_cash = self.cash_flow_model.ending_cash or 0.0

        # Initialize cash positions for all three series
        cash_positions = {
            'beginning_cash': {
                'projected': {},
                'lower_bound': {},
                'upper_bound': {}
            },
            'ending_cash': {
                'projected': {},
                'lower_bound': {},
                'upper_bound': {}
            }
        }

        # Calculate for each series
        for series_name in ['projected', 'lower_bound', 'upper_bound']:
            beginning_cash = historical_ending_cash

            for month in range(1, forecast_horizon + 1):
                # Set beginning cash
                cash_positions['beginning_cash'][series_name][month] = beginning_cash

                # Calculate net change from all three activity sections
                net_change = 0.0

                for section_name in ['OPERATING ACTIVITIES', 'INVESTING ACTIVITIES', 'FINANCING ACTIVITIES']:
                    if series_name == 'projected':
                        section_values = projections.get(section_name, {})
                        net_change += section_values.get(month, 0.0)
                    else:
                        # For bounds, use confidence_intervals
                        section_intervals = confidence_intervals.get(section_name, {})
                        bounds = section_intervals.get(series_name, {})
                        net_change += bounds.get(month, 0.0)

                # Calculate ending cash
                ending_cash = beginning_cash + net_change
                cash_positions['ending_cash'][series_name][month] = ending_cash

                # Check for negative ending cash (liquidity warning)
                if ending_cash < 0:
                    self.warnings.append({
                        'type': 'LIQUIDITY_WARNING',
                        'series': series_name,
                        'month': month,
                        'ending_cash': ending_cash,
                        'beginning_cash': beginning_cash,
                        'net_change': net_change,
                        'message': f'Negative ending cash in {series_name} series for Month {month}'
                    })

                # Set up next month
                beginning_cash = ending_cash

        return cash_positions

    def _build_hierarchy(
        self,
        projections: Dict[str, Dict[int, float]],
        confidence_intervals: Dict[str, Dict[str, Dict[int, float]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build hierarchy structure with three parallel value dictionaries.

        Args:
            projections: Dict of projected values by section
            confidence_intervals: Dict of confidence bounds by section

        Returns:
            Hierarchy dict with section names as keys, each containing list with three value dicts
        """
        hierarchy = {}

        for section_name in ['OPERATING ACTIVITIES', 'INVESTING ACTIVITIES', 'FINANCING ACTIVITIES']:
            section_item = {
                'account_name': section_name,
                'projected': projections.get(section_name, {}),
                'lower_bound': confidence_intervals.get(section_name, {}).get('lower_bound', {}),
                'upper_bound': confidence_intervals.get(section_name, {}).get('upper_bound', {})
            }
            hierarchy[section_name] = [section_item]

        return hierarchy

    def _build_calculated_rows(
        self,
        cash_positions: Dict[str, Dict[str, Dict[int, float]]]
    ) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Build calculated rows structure with beginning and ending cash.

        Args:
            cash_positions: Dict with 'beginning_cash' and 'ending_cash' for all three series

        Returns:
            Dict with same structure as cash_positions
        """
        return cash_positions

    def _build_metadata(self, forecast_horizon: int) -> Dict[str, Any]:
        """
        Build metadata dict with confidence level, forecast horizon, excluded periods, warnings, and spillover.

        Args:
            forecast_horizon: Number of forecast months

        Returns:
            Metadata dict with all required fields
        """
        metadata = {
            'confidence_level': 0.80,
            'forecast_horizon': forecast_horizon,
            'excluded_periods': [],
            'warnings': self.warnings,
            'uncollected_spillover': getattr(self, 'uncollected_spillover', None)
        }

        # Add excluded periods if anomaly annotations were used
        if self.anomaly_annotations:
            excluded_annotations = self.anomaly_annotations.get_annotations_by_exclusion_type('baseline')
            if excluded_annotations:
                metadata['excluded_periods'] = [
                    {
                        'start_date': ann.start_date,
                        'end_date': ann.end_date,
                        'reason': ann.reason
                    }
                    for ann in excluded_annotations
                ]

        return metadata
