"""
PLForecastCalculator - Service for calculating P&L forecasts with confidence intervals.

Implements Historical Percentiles with Square Root Horizon Scaling algorithm.
Generates monthly projections with median baseline, category-specific compound growth rates,
percentile-based bounds with sqrt(M) scaling, and calculated margin metrics.
"""
from typing import Any, Dict, Optional
import math

import pandas as pd

from src.models.pl_model import PLModel
from src.models.forecast_scenario import ForecastScenarioModel
from src.models.anomaly_annotation import AnomalyAnnotationModel
from src.models.pl_forecast_model import PLForecastModel
from src.services.volatility_calculator import VolatilityCalculator
from src.services.anomaly_data_filter import AnomalyDataFilter


class PLForecastCalculator:
    """
    Calculator for P&L forecasts based on historical data and scenario parameters.

    Accepts PLModel (historical), ForecastScenarioModel (parameters), and optional
    AnomalyAnnotationModel (exclusions) as inputs, applies forecasting algorithm with
    confidence intervals, returns PLForecastModel.
    """

    def __init__(
        self,
        pl_model: PLModel,
        forecast_scenario: ForecastScenarioModel,
        anomaly_annotations: Optional[AnomalyAnnotationModel] = None
    ):
        """
        Initialize calculator with historical data, scenario parameters, and optional anomaly annotations.

        Args:
            pl_model: PLModel instance with historical P&L data
            forecast_scenario: ForecastScenarioModel instance with forecast parameters
            anomaly_annotations: Optional AnomalyAnnotationModel for baseline exclusions
        """
        self.pl_model = pl_model
        self.forecast_scenario = forecast_scenario
        self.anomaly_annotations = anomaly_annotations
        self.warnings = []
        self.volatility_metadata = None
        self.exclusion_metadata = None

    def calculate(self) -> PLForecastModel:
        """
        Calculate P&L forecast by applying parameters to historical data.

        Process:
        1. Calculate baseline with anomaly exclusion
        2. Apply category-specific compound growth projection
        3. Calculate confidence intervals with sqrt(M) scaling
        4. Calculate margins from projected values
        5. Assemble PLForecastModel

        Returns:
            PLForecastModel instance with projected values, confidence bounds, and metadata
        """
        # Reset warnings for new calculation
        self.warnings = []

        # Extract parameters
        forecast_horizon = self.forecast_scenario.parameters.get('forecast_horizon', 6)
        revenue_growth_rate = self.forecast_scenario.parameters.get('revenue_growth_rate', 0.0)
        cogs_trend = self.forecast_scenario.parameters.get('cogs_trend', 0.0)
        opex_trend = self.forecast_scenario.parameters.get('opex_trend', 0.0)

        # Step 1: Calculate baselines for each P&L section
        baselines = self._calculate_baselines()

        # Step 2: Apply category-specific compound growth
        projections = self._apply_compound_growth(
            baselines, revenue_growth_rate, cogs_trend, opex_trend, forecast_horizon
        )

        # Step 3: Calculate confidence intervals with sqrt(M) scaling
        confidence_intervals = self._calculate_confidence_intervals(
            projections, baselines, forecast_horizon
        )

        # Step 4: Calculate margins from projected values
        margins = self._calculate_margins(projections, forecast_horizon)

        # Build output model
        hierarchy = self._build_hierarchy(projections, confidence_intervals)
        calculated_rows = margins
        metadata = self._build_metadata(forecast_horizon)

        return PLForecastModel(
            hierarchy=hierarchy,
            calculated_rows=calculated_rows,
            metadata=metadata
        )

    def _calculate_baselines(self) -> Dict[str, float]:
        """
        Calculate baseline (median) for each P&L section with anomaly exclusion.

        Returns:
            Dict with section names as keys ('Income', 'Cost of Goods Sold', 'Expenses')
            and baseline values as floats

        Raises:
            ValueError: If insufficient data remains after exclusion or if revenue baseline <= 0
        """
        baselines = {}

        # Get historical data for each section
        sections = {
            'Income': self.pl_model.get_income(),
            'Cost of Goods Sold': self.pl_model.get_cogs(),
            'Expenses': self.pl_model.get_expenses()
        }

        for section_name, section_data in sections.items():
            # Handle missing COGS (service businesses)
            if section_data is None:
                if section_name == 'Cost of Goods Sold':
                    baselines[section_name] = 0.0
                    self.warnings.append({
                        'type': 'NO_COGS_SECTION',
                        'message': 'Service business detected - no COGS section present. COGS baseline set to 0.',
                        'section': section_name
                    })
                    continue
                else:
                    baselines[section_name] = 0.0
                    continue

            # Extract historical values from section
            # PLModel sections have period-aware 'values' dict at hierarchy nodes
            historical_values = []
            if isinstance(section_data, dict):
                # Check for children (traverse to get all leaf values)
                if 'children' in section_data:
                    for child in section_data['children']:
                        if 'values' in child and isinstance(child['values'], dict):
                            historical_values.extend(child['values'].values())
                # Or direct values dict
                elif 'values' in section_data:
                    historical_values = list(section_data['values'].values())
            elif isinstance(section_data, list):
                # Section is a list of items
                for item in section_data:
                    if isinstance(item, dict) and 'values' in item:
                        historical_values.extend(item['values'].values())

            # If still no values, try to extract from first-level aggregation
            if not historical_values and isinstance(section_data, dict):
                # Look for any values dict in the structure
                def extract_values(node):
                    vals = []
                    if isinstance(node, dict):
                        if 'values' in node and isinstance(node['values'], dict):
                            vals.extend(node['values'].values())
                        for key, value in node.items():
                            if key != 'values':
                                vals.extend(extract_values(value))
                    elif isinstance(node, list):
                        for item in node:
                            vals.extend(extract_values(item))
                    return vals

                historical_values = extract_values(section_data)

            # Apply anomaly exclusion if provided
            if self.anomaly_annotations and historical_values:
                # Get period labels for datetime index
                periods = self.pl_model.get_periods()

                # Create pandas Series with datetime index
                series = pd.Series(historical_values, index=pd.to_datetime(periods))

                # Get annotations for baseline exclusion
                annotations = self.anomaly_annotations.get_annotations()

                # Apply filter
                filter_service = AnomalyDataFilter(series, annotations, exclusion_type='baseline')
                try:
                    filter_result = filter_service.filter()
                    filtered_series = filter_result['filtered_series']
                    metadata = filter_result['metadata']

                    # Check data sufficiency: <12 periods AND >=50% excluded
                    if len(filtered_series) < 12 and metadata['exclusion_percentage'] >= 0.5:
                        raise ValueError(
                            f'Insufficient data after anomaly exclusion for {section_name}. '
                            f'Need >= 12 periods or < 50% exclusion. Got {len(filtered_series)}/{metadata["total_count"]} periods '
                            f'({metadata["exclusion_percentage"]:.1%} excluded).'
                        )

                    # Warn if <12 periods but <50% excluded (still proceed)
                    if len(filtered_series) < 12:
                        self.warnings.append({
                            'type': 'INSUFFICIENT_DATA_AFTER_EXCLUSION',
                            'message': f'Less than 12 periods remain for {section_name} after exclusion ({len(filtered_series)}/{metadata["total_count"]}). Proceeding with reduced dataset.',
                            'excluded_count': metadata['excluded_count'],
                            'total_count': metadata['total_count'],
                            'remaining_count': len(filtered_series)
                        })

                    # Use filtered series
                    series = filtered_series

                    # Store metadata for later use (only store once, all sections use same annotations)
                    if self.exclusion_metadata is None:
                        self.exclusion_metadata = metadata

                except ValueError as e:
                    # Re-raise insufficient data errors
                    raise e
            else:
                # No anomaly filtering - use historical values as-is
                series = pd.Series(historical_values)

            # Calculate median
            if len(series) > 0:
                baseline = series.median()

                # Validate revenue baseline
                if section_name == 'Income' and baseline <= 0:
                    raise ValueError(
                        f'Invalid revenue baseline: {baseline}. Revenue baseline must be > 0.'
                    )

                baselines[section_name] = baseline
            else:
                baselines[section_name] = 0.0

        return baselines

    def _apply_compound_growth(
        self,
        baselines: Dict[str, float],
        revenue_growth_rate: float,
        cogs_trend: float,
        opex_trend: float,
        forecast_horizon: int
    ) -> Dict[str, Dict[int, float]]:
        """
        Apply category-specific compound growth rates to baselines.

        Formula: projected[M] = baseline * (1 + rate) ** M

        Args:
            baselines: Dict of section baselines
            revenue_growth_rate: Monthly growth rate for Income (decimal, e.g., 0.05 for 5%)
            cogs_trend: Monthly growth rate for COGS
            opex_trend: Monthly growth rate for Expenses
            forecast_horizon: Number of months to project

        Returns:
            Dict with section names as keys, each containing dict of {month: projected_value}

        Raises:
            ValueError: If any growth rate >= 1.0 (100%+ growth)
        """
        # Map growth rates to sections
        growth_rates = {
            'Income': revenue_growth_rate,
            'Cost of Goods Sold': cogs_trend,
            'Expenses': opex_trend
        }

        # Validate growth rates
        for section_name, rate in growth_rates.items():
            if rate >= 1.0:
                raise ValueError(
                    f'Growth rate must be < 100% (< 1.0). Got {rate} for {section_name}.'
                )

            if rate >= 0.20 or rate <= -0.20:
                self.warnings.append({
                    'type': 'HIGH_GROWTH_RATE',
                    'message': f'Growth rate of {rate*100:.1f}% for {section_name} is unusually high.',
                    'section': section_name,
                    'rate': rate
                })

        # Apply compound growth
        projections = {}

        for section_name, baseline in baselines.items():
            rate = growth_rates.get(section_name, 0.0)
            section_projections = {}

            for month in range(1, forecast_horizon + 1):
                projected_value = baseline * ((1 + rate) ** month)
                section_projections[month] = projected_value

            projections[section_name] = section_projections

        return projections

    def _calculate_confidence_intervals(
        self,
        projections: Dict[str, Dict[int, float]],
        baselines: Dict[str, float],
        forecast_horizon: int
    ) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Calculate confidence intervals using historical percentiles with sqrt(M) scaling.

        Formula:
        - lower_bound[M] = projected[M] * lower_ratio * (1 - α_lower * (sqrt(M) - 1))
        - upper_bound[M] = projected[M] * upper_ratio * (1 + α_upper * (sqrt(M) - 1))
        - Minimum width: 5% of projected value
        - Symmetric alpha coefficients: 0.10 for both lower and upper

        Args:
            projections: Dict of projected values by section and month
            baselines: Dict of baseline values (for percentile calculation)
            forecast_horizon: Number of months

        Returns:
            Dict with section names as keys, each containing 'lower_bound' and 'upper_bound' dicts
        """
        confidence_intervals = {}

        # Get historical data for each section
        sections = {
            'Income': self.pl_model.get_income(),
            'Cost of Goods Sold': self.pl_model.get_cogs(),
            'Expenses': self.pl_model.get_expenses()
        }

        for section_name, section_data in sections.items():
            # Handle missing COGS (service businesses)
            if section_data is None and section_name == 'Cost of Goods Sold':
                # Return empty bounds for COGS
                confidence_intervals[section_name] = {
                    'lower_bound': {},
                    'upper_bound': {}
                }
                continue

            # Extract historical values (same logic as baseline calculation)
            historical_values = []
            if isinstance(section_data, dict):
                def extract_values(node):
                    vals = []
                    if isinstance(node, dict):
                        if 'values' in node and isinstance(node['values'], dict):
                            vals.extend(node['values'].values())
                        for key, value in node.items():
                            if key != 'values':
                                vals.extend(extract_values(value))
                    elif isinstance(node, list):
                        for item in node:
                            vals.extend(extract_values(item))
                    return vals

                historical_values = extract_values(section_data)
            elif isinstance(section_data, list):
                for item in section_data:
                    if isinstance(item, dict) and 'values' in item:
                        historical_values.extend(item['values'].values())

            if len(historical_values) < 12:
                self.warnings.append({
                    'type': 'LIMITED_DATA_WARNING',
                    'message': f'Less than 12 historical periods for {section_name}. Confidence intervals may be less reliable.',
                    'period_count': len(historical_values),
                    'section': section_name
                })

            # Calculate volatility using VolatilityCalculator
            if historical_values and len(historical_values) >= 3:
                series = pd.Series(historical_values)

                # Extract confidence_level from forecast scenario parameters
                confidence_level = self.forecast_scenario.parameters.get('confidence_level', 0.80)

                # Instantiate VolatilityCalculator
                volatility_calc = VolatilityCalculator(
                    historical_values=series,
                    confidence_level=confidence_level,
                    anomaly_annotations=self.anomaly_annotations
                )

                # Calculate volatility
                result = volatility_calc.calculate()

                # Extract ratios
                lower_ratio = result['percentile_ratios']['lower_ratio']
                upper_ratio = result['percentile_ratios']['upper_ratio']

                # Store metadata for later inclusion in forecast metadata
                self.volatility_metadata = result['metadata']

                # Merge warnings from volatility calculator
                if volatility_calc.warnings:
                    for warning_msg in volatility_calc.warnings:
                        # Detect warning type from message content
                        if 'Low historical variance' in warning_msg:
                            warning_type = 'LOW_VARIANCE_MINIMUM_INTERVAL'
                        elif 'Insufficient historical data' in warning_msg:
                            warning_type = 'INSUFFICIENT_VOLATILITY_DATA'
                        elif 'zero median' in warning_msg:
                            warning_type = 'ZERO_MEDIAN_VOLATILITY'
                        else:
                            warning_type = 'VOLATILITY_CALCULATION'

                        self.warnings.append({
                            'type': warning_type,
                            'message': warning_msg,
                            'section': section_name
                        })

                # Symmetric alpha coefficients for P&L
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

                    # Enforce minimum 5% width
                    min_width = 0.05 * abs(projected_value)
                    min_lower = projected_value - min_width
                    min_upper = projected_value + min_width

                    # Ensure bounds meet minimum width
                    lower_bound = min(lower_bound, min_lower)
                    upper_bound = max(upper_bound, min_upper)

                    lower_bounds[month] = lower_bound
                    upper_bounds[month] = upper_bound

                confidence_intervals[section_name] = {
                    'lower_bound': lower_bounds,
                    'upper_bound': upper_bounds
                }
            else:
                # Insufficient data - use 5% default bounds
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

    def _calculate_margins(
        self,
        projections: Dict[str, Dict[int, float]],
        forecast_horizon: int
    ) -> Dict[str, Dict[str, Dict[int, float]]]:
        """
        Calculate forecasted margins from projected values.

        Formulas:
        - gross_profit = income - cogs
        - gross_margin_pct = (gross_profit / income) * 100
        - operating_income = gross_profit - expenses
        - operating_margin_pct = (operating_income / income) * 100
        - net_income = operating_income (no tax/interest in MVP)

        Division by zero protection: if income = 0, margin percentages = 0.0

        Args:
            projections: Dict of projected values by section and month
            forecast_horizon: Number of months

        Returns:
            Dict with margin metric names as keys, each containing 'projected',
            'lower_bound', and 'upper_bound' dicts (bounds are empty for margins)
        """
        margins = {
            'gross_profit': {'projected': {}, 'lower_bound': {}, 'upper_bound': {}},
            'gross_margin_pct': {'projected': {}, 'lower_bound': {}, 'upper_bound': {}},
            'operating_income': {'projected': {}, 'lower_bound': {}, 'upper_bound': {}},
            'operating_margin_pct': {'projected': {}, 'lower_bound': {}, 'upper_bound': {}},
            'net_income': {'projected': {}, 'lower_bound': {}, 'upper_bound': {}}
        }

        income_projections = projections.get('Income', {})
        cogs_projections = projections.get('Cost of Goods Sold', {})
        expenses_projections = projections.get('Expenses', {})

        for month in range(1, forecast_horizon + 1):
            income = income_projections.get(month, 0.0)
            cogs = cogs_projections.get(month, 0.0)
            expenses = expenses_projections.get(month, 0.0)

            # Calculate gross profit
            gross_profit = income - cogs
            margins['gross_profit']['projected'][month] = gross_profit

            # Calculate gross margin percentage
            if income > 0:
                gross_margin_pct = (gross_profit / income) * 100
            else:
                gross_margin_pct = 0.0
            margins['gross_margin_pct']['projected'][month] = gross_margin_pct

            # Calculate operating income
            operating_income = gross_profit - expenses
            margins['operating_income']['projected'][month] = operating_income

            # Calculate operating margin percentage
            if income > 0:
                operating_margin_pct = (operating_income / income) * 100
            else:
                operating_margin_pct = 0.0
            margins['operating_margin_pct']['projected'][month] = operating_margin_pct

            # Net income (no tax/interest in MVP)
            net_income = operating_income
            margins['net_income']['projected'][month] = net_income

        return margins

    def _build_hierarchy(
        self,
        projections: Dict[str, Dict[int, float]],
        confidence_intervals: Dict[str, Dict[str, Dict[int, float]]]
    ) -> Dict[str, Any]:
        """
        Build hierarchy structure with three parallel value dictionaries.

        Args:
            projections: Dict of projected values by section
            confidence_intervals: Dict of confidence bounds by section

        Returns:
            Hierarchy dict with section names as keys, each containing list with three value dicts
        """
        hierarchy = {}

        for section_name in ['Income', 'Cost of Goods Sold', 'Expenses']:
            section_item = {
                'account_name': section_name,
                'projected': projections.get(section_name, {}),
                'lower_bound': confidence_intervals.get(section_name, {}).get('lower_bound', {}),
                'upper_bound': confidence_intervals.get(section_name, {}).get('upper_bound', {})
            }
            hierarchy[section_name] = [section_item]

        return hierarchy

    def _build_metadata(self, forecast_horizon: int) -> Dict[str, Any]:
        """
        Build metadata dict with confidence level, forecast horizon, excluded periods, warnings, and volatility statistics.

        Args:
            forecast_horizon: Number of forecast months

        Returns:
            Metadata dict with all required fields
        """
        # Get confidence level from scenario or default
        confidence_level = self.forecast_scenario.parameters.get('confidence_level', 0.80)

        metadata = {
            'confidence_level': confidence_level,
            'forecast_horizon': forecast_horizon,
            'excluded_periods': [],
            'warnings': self.warnings,
            'volatility_statistics': self.volatility_metadata if self.volatility_metadata else None
        }

        # Add excluded periods if anomaly annotations were used
        if self.anomaly_annotations:
            excluded_annotations = self.anomaly_annotations.get_annotations_by_exclusion_type('baseline')
            if not excluded_annotations:
                excluded_annotations = self.anomaly_annotations.get_annotations_by_exclusion_type('both')

            if excluded_annotations:
                # Use exclusion metadata from filter
                if self.exclusion_metadata and self.exclusion_metadata['excluded_periods']:
                    metadata['excluded_periods'] = self.exclusion_metadata['excluded_periods']

        return metadata
