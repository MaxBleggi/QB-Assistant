"""
ForecastBudgetVarianceCalculator service for budget vs forecast variance analysis.

Compares budget projections to forecast projections for overlapping periods, calculating:
- Dollar variance (forecast_projected - budget)
- Percentage variance ((forecast_projected - budget) / budget * 100)
- Favorable vs unfavorable determination (section-aware)
- Significant variance flagging based on configurable thresholds
- Actionable warning messages for business decision-making
"""
from typing import Any, Dict, List, Union, Optional

import pandas as pd

from src.models import BudgetModel, PLForecastModel, VarianceModel, MultiScenarioForecastResult
from .line_item_matcher import LineItemMatcher


class ForecastBudgetVarianceCalculator:
    """
    Calculator for budget vs forecast variance analysis.

    Accepts BudgetModel and PLForecastModel (or MultiScenarioForecastResult) as inputs,
    matches accounts using LineItemMatcher, calculates variances for overlapping periods only,
    handles multi-scenario selection logic, generates actionable warning messages.
    """

    def __init__(
        self,
        budget_model: BudgetModel,
        forecast_input: Union[PLForecastModel, MultiScenarioForecastResult]
    ):
        """
        Initialize calculator with budget and forecast data.

        Args:
            budget_model: BudgetModel instance with budget projections
            forecast_input: PLForecastModel instance or MultiScenarioForecastResult with forecast data
        """
        self._budget_model = budget_model
        self._forecast_input = forecast_input
        self._is_multi_scenario = isinstance(forecast_input, MultiScenarioForecastResult)

    def calculate(
        self,
        threshold_pct: float = 10.0,
        threshold_abs: float = 0.0,
        calculate_all_scenarios: bool = False
    ) -> Union[VarianceModel, Dict[str, VarianceModel]]:
        """
        Calculate budget vs forecast variances for overlapping periods only.

        Process:
        1. Select scenario(s) based on calculate_all_scenarios flag
        2. Extract overlapping periods between budget and forecast
        3. Match budget accounts to forecast accounts using LineItemMatcher
        4. Calculate dollar variance (forecast_projected - budget)
        5. Calculate percentage variance ((forecast_projected - budget) / budget * 100)
        6. Determine favorable vs unfavorable (section-aware)
        7. Flag significant variances exceeding thresholds
        8. Build variance hierarchy with all attributes
        9. Calculate section-level summaries
        10. Return VarianceModel (or dict of VarianceModels for multi-scenario)

        Args:
            threshold_pct: Percentage threshold for flagging (default: 10 for 10%)
            threshold_abs: Absolute dollar threshold for flagging (default: 0)
            calculate_all_scenarios: If True and multi-scenario input, calculate variance for all scenarios.
                                    If False, use Expected scenario (fallback to first if missing).

        Returns:
            VarianceModel instance (single scenario) or dict mapping scenario_name to VarianceModel (all scenarios)
        """
        if self._is_multi_scenario:
            if calculate_all_scenarios:
                # Calculate variance for all scenarios
                result = {}
                for scenario_name in self._forecast_input.list_scenarios():
                    scenario_forecast = self._forecast_input.get_scenario_forecast(scenario_name)
                    pl_forecast = scenario_forecast['pl_forecast']
                    result[scenario_name] = self._calculate_single_variance(
                        pl_forecast,
                        threshold_pct,
                        threshold_abs
                    )
                return result
            else:
                # Extract Expected scenario (fallback to first)
                pl_forecast = self._extract_default_scenario()
                return self._calculate_single_variance(pl_forecast, threshold_pct, threshold_abs)
        else:
            # Direct PLForecastModel
            return self._calculate_single_variance(
                self._forecast_input,
                threshold_pct,
                threshold_abs
            )

    def _normalize_forecast_hierarchy(self, forecast_hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize PLForecastModel hierarchy structure to match BudgetModel structure.

        PLForecastModel wraps section nodes in lists: {'Income': [{name: 'Income', ...}]}
        BudgetModel uses direct dicts: {'Income': {name: 'Income', ...}}

        This method unwraps list wrappers to create compatible structure for LineItemMatcher.

        Args:
            forecast_hierarchy: Original forecast hierarchy with list wrappers

        Returns:
            Normalized hierarchy with dict structure matching BudgetModel
        """
        normalized = {}
        for section_name, section_data in forecast_hierarchy.items():
            if isinstance(section_data, list) and len(section_data) > 0:
                # Unwrap list wrapper
                normalized[section_name] = section_data[0]
            else:
                # Already dict structure or empty
                normalized[section_name] = section_data
        return normalized

    def _extract_default_scenario(self) -> PLForecastModel:
        """
        Extract Expected scenario from MultiScenarioForecastResult, fallback to first scenario.

        Returns:
            PLForecastModel for Expected scenario (or first available scenario)
        """
        scenarios = self._forecast_input.list_scenarios()
        if not scenarios:
            raise ValueError("MultiScenarioForecastResult has no scenarios")

        # Try Expected scenario first
        expected_forecast = self._forecast_input.get_scenario_forecast('Expected')
        if expected_forecast:
            return expected_forecast['pl_forecast']

        # Fallback to first scenario
        first_scenario = scenarios[0]
        first_forecast = self._forecast_input.get_scenario_forecast(first_scenario)
        return first_forecast['pl_forecast']

    def _calculate_single_variance(
        self,
        pl_forecast: PLForecastModel,
        threshold_pct: float,
        threshold_abs: float
    ) -> VarianceModel:
        """
        Calculate variance for a single PLForecastModel against budget.

        Args:
            pl_forecast: PLForecastModel instance
            threshold_pct: Percentage threshold
            threshold_abs: Absolute threshold

        Returns:
            VarianceModel with variance data
        """
        # Get hierarchies from models
        budget_hierarchy = self._budget_model.hierarchy
        forecast_hierarchy = pl_forecast.hierarchy

        # Normalize forecast hierarchy structure (PLForecastModel wraps sections in lists)
        normalized_forecast_hierarchy = self._normalize_forecast_hierarchy(forecast_hierarchy)

        # Extract periods from both models
        budget_periods = self._extract_periods_from_hierarchy(budget_hierarchy)
        forecast_periods = self._extract_periods_from_forecast_hierarchy(forecast_hierarchy)

        # Calculate overlapping periods (only compare common months)
        overlapping_periods = list(set(budget_periods) & set(forecast_periods))

        # If no overlap, return empty variance
        if not overlapping_periods:
            return VarianceModel(
                df=pd.DataFrame(),
                hierarchy={},
                calculated_rows=[],
                unmatched_budget_accounts=[],
                unmatched_actual_accounts=[]
            )

        # Match accounts using LineItemMatcher (use normalized forecast hierarchy)
        section_mappings, unmatched_budget, unmatched_forecast = LineItemMatcher.match_accounts(
            budget_hierarchy,
            normalized_forecast_hierarchy
        )

        # Build variance hierarchy
        variance_hierarchy = {}

        # Process each section (Income, Expenses)
        for section_name in ['Income', 'Expenses']:
            budget_section = budget_hierarchy.get(section_name, {})
            forecast_section = normalized_forecast_hierarchy.get(section_name, {})
            mapping = section_mappings.get(section_name, {})

            if budget_section or forecast_section:
                variance_section = self._process_section(
                    section_name,
                    budget_section,
                    forecast_section,
                    mapping,
                    overlapping_periods,
                    threshold_pct,
                    threshold_abs
                )
                variance_hierarchy[section_name] = variance_section

        # Create DataFrame for VarianceModel
        df = self._create_variance_dataframe(variance_hierarchy, overlapping_periods)

        # Calculate section-level summaries
        calculated_rows = self._calculate_totals(variance_hierarchy, overlapping_periods)

        return VarianceModel(
            df=df,
            hierarchy=variance_hierarchy,
            calculated_rows=calculated_rows,
            unmatched_budget_accounts=unmatched_budget,
            unmatched_actual_accounts=unmatched_forecast
        )

    def _process_section(
        self,
        section_name: str,
        budget_section: Dict[str, Any],
        forecast_section: Dict[str, Any],
        mapping: Dict[str, str],
        overlapping_periods: List[str],
        threshold_pct: float,
        threshold_abs: float
    ) -> Dict[str, Any]:
        """
        Process a single section (Income or Expenses) to calculate variances.

        Args:
            section_name: Section name ('Income' or 'Expenses')
            budget_section: Budget section from hierarchy
            forecast_section: Forecast section from hierarchy
            mapping: Dict mapping budget account names to forecast account names
            overlapping_periods: List of periods that overlap between budget and forecast
            threshold_pct: Percentage threshold
            threshold_abs: Absolute threshold

        Returns:
            Variance section dict with children containing variance attributes
        """
        # Create section container
        variance_section = {
            'name': section_name,
            'children': []
        }

        # Process matched accounts
        for budget_name, forecast_name in mapping.items():
            # Find account nodes in hierarchies
            budget_node = self._find_account_by_name(budget_section, budget_name)
            forecast_node = self._find_account_by_name(forecast_section, forecast_name)

            # Debug logging for account matching failures
            if budget_node is None:
                import logging
                logging.debug(f"Budget account '{budget_name}' not found in section '{section_name}'")
            if forecast_node is None:
                import logging
                logging.debug(f"Forecast account '{forecast_name}' not found in section '{section_name}'")

            if budget_node and forecast_node:
                # Calculate variances for this account
                variance_account = self._calculate_account_variance(
                    budget_name,
                    budget_node,
                    forecast_node,
                    section_name,
                    overlapping_periods,
                    threshold_pct,
                    threshold_abs
                )
                variance_section['children'].append(variance_account)

        return variance_section

    def _calculate_account_variance(
        self,
        account_name: str,
        budget_node: Dict[str, Any],
        forecast_node: Dict[str, Any],
        section_name: str,
        overlapping_periods: List[str],
        threshold_pct: float,
        threshold_abs: float
    ) -> Dict[str, Any]:
        """
        Calculate variance for a single matched account across overlapping periods only.

        Args:
            account_name: Account name
            budget_node: Budget account node with values dict
            forecast_node: Forecast account node with projected/lower_bound/upper_bound dicts
            section_name: Section name for favorable/unfavorable logic
            overlapping_periods: List of periods to compare
            threshold_pct: Percentage threshold
            threshold_abs: Absolute threshold

        Returns:
            Variance account dict with budget_value, actual_value (forecast), dollar_variance,
            pct_variance, is_favorable, is_flagged per period
        """
        budget_values = budget_node.get('values', {})
        # Extract 'projected' values from forecast (PLForecastModel has projected/lower_bound/upper_bound)
        forecast_projected = forecast_node.get('projected', {})

        # Debug: Log if budget values are missing
        if not budget_values:
            import logging
            logging.warning(f"Budget node for '{account_name}' has no 'values' dict. Node keys: {budget_node.keys()}")

        variance_data = {}

        # Only calculate variance for overlapping periods
        for period in overlapping_periods:
            budget_value = budget_values.get(period, 0.0)
            forecast_value = forecast_projected.get(period, 0.0)

            # Calculate dollar variance (forecast - budget)
            dollar_variance = forecast_value - budget_value

            # Calculate percentage variance (handle zero budget)
            if budget_value != 0:
                pct_variance = (dollar_variance / budget_value) * 100
            else:
                pct_variance = None  # Cannot calculate percentage with zero budget

            # Determine if favorable
            is_favorable = self._is_favorable(section_name, dollar_variance)

            # Flag if exceeds thresholds
            is_flagged = False
            if pct_variance is not None:
                if abs(pct_variance) > threshold_pct or abs(dollar_variance) > threshold_abs:
                    is_flagged = True
            else:
                # If pct_variance is None (zero budget), flag based on absolute only
                if abs(dollar_variance) > threshold_abs:
                    is_flagged = True

            variance_data[period] = {
                'budget_value': budget_value,
                'actual_value': forecast_value,  # Using 'actual_value' key for VarianceModel compatibility
                'dollar_variance': dollar_variance,
                'pct_variance': pct_variance,
                'is_favorable': is_favorable,
                'is_flagged': is_flagged
            }

        return {
            'name': account_name,
            'values': variance_data
        }

    def _is_favorable(self, section_name: str, dollar_variance: float) -> bool:
        """
        Determine if variance is favorable based on section type.

        For Income: forecast > budget (positive variance) is favorable
        For Expenses: forecast < budget (negative variance) is favorable

        Args:
            section_name: Section name ('Income' or 'Expenses')
            dollar_variance: Dollar variance (forecast - budget)

        Returns:
            True if variance is favorable, False otherwise
        """
        if section_name == 'Income':
            return dollar_variance > 0  # More revenue is good
        else:  # Expenses
            return dollar_variance < 0  # Less expenses is good

    def _find_account_by_name(self, section: Dict[str, Any], account_name: str) -> Optional[Dict[str, Any]]:
        """
        Search section hierarchy for account by name.

        Args:
            section: Section dict from hierarchy
            account_name: Account name to find

        Returns:
            Account node dict if found, None otherwise
        """
        def search_node(node: Any) -> Optional[Dict[str, Any]]:
            """Recursively search for account."""
            if isinstance(node, dict):
                # Check if this node matches
                if node.get('name') == account_name and not node.get('parent', False):
                    return node

                # Search children
                if 'children' in node:
                    for child in node['children']:
                        result = search_node(child)
                        if result:
                            return result

            elif isinstance(node, list):
                for item in node:
                    result = search_node(item)
                    if result:
                        return result

            return None

        return search_node(section)

    def _extract_periods_from_hierarchy(self, hierarchy: Dict[str, Any]) -> List[str]:
        """
        Extract period labels from budget hierarchy (values dict).

        Args:
            hierarchy: Budget hierarchy tree

        Returns:
            List of period labels
        """
        def find_first_values(node: Any) -> Optional[Dict[str, Any]]:
            """Recursively search for first values dict."""
            if isinstance(node, dict):
                if 'values' in node and isinstance(node['values'], dict):
                    return node['values']

                if 'children' in node:
                    for child in node['children']:
                        result = find_first_values(child)
                        if result:
                            return result

                for key, value in node.items():
                    if key != 'values':
                        result = find_first_values(value)
                        if result:
                            return result

            elif isinstance(node, list):
                for item in node:
                    result = find_first_values(item)
                    if result:
                        return result

            return None

        first_values = find_first_values(hierarchy)
        if first_values:
            return list(first_values.keys())
        return []

    def _extract_periods_from_forecast_hierarchy(self, hierarchy: Dict[str, Any]) -> List[str]:
        """
        Extract period labels from forecast hierarchy (projected dict).

        PLForecastModel stores values in 'projected' / 'lower_bound' / 'upper_bound' dicts.

        Args:
            hierarchy: Forecast hierarchy tree

        Returns:
            List of period labels
        """
        def find_first_projected(node: Any) -> Optional[Dict[str, Any]]:
            """Recursively search for first projected dict."""
            if isinstance(node, dict):
                if 'projected' in node and isinstance(node['projected'], dict):
                    return node['projected']

                if 'children' in node:
                    for child in node['children']:
                        result = find_first_projected(child)
                        if result:
                            return result

                for key, value in node.items():
                    if key not in ['projected', 'lower_bound', 'upper_bound']:
                        result = find_first_projected(value)
                        if result:
                            return result

            elif isinstance(node, list):
                for item in node:
                    result = find_first_projected(item)
                    if result:
                        return result

            return None

        first_projected = find_first_projected(hierarchy)
        if first_projected:
            return list(first_projected.keys())
        return []

    def _create_variance_dataframe(self, hierarchy: Dict[str, Any], periods: List[str]) -> pd.DataFrame:
        """
        Create DataFrame with variance account metadata.

        Args:
            hierarchy: Variance hierarchy tree
            periods: List of period labels

        Returns:
            DataFrame with account names and metadata
        """
        rows = []

        def extract_accounts(node: Any, section: str = None) -> None:
            """Recursively extract account information."""
            if isinstance(node, dict):
                if 'name' in node:
                    rows.append({
                        'account_name': node['name'],
                        'section': section,
                        'is_parent': node.get('parent', False)
                    })

                if 'children' in node:
                    for child in node['children']:
                        extract_accounts(child, section)

            elif isinstance(node, list):
                for item in node:
                    extract_accounts(item, section)

        # Extract accounts from each section
        for section_name, section_data in hierarchy.items():
            extract_accounts(section_data, section_name)

        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def _calculate_totals(self, hierarchy: Dict[str, Any], periods: List[str]) -> List[Dict[str, Any]]:
        """
        Calculate section-level variance summaries for calculated_rows.

        Args:
            hierarchy: Variance hierarchy tree
            periods: List of period labels

        Returns:
            List of calculated row dicts with variance summaries
        """
        calculated_rows = []

        # Calculate Income variance total
        income_total = self._sum_section_variances(hierarchy.get('Income', {}), periods)
        if income_total:
            calculated_rows.append({
                'account_name': 'Total Income Variance',
                'values': income_total
            })

        # Calculate Expenses variance total
        expenses_total = self._sum_section_variances(hierarchy.get('Expenses', {}), periods)
        if expenses_total:
            calculated_rows.append({
                'account_name': 'Total Expenses Variance',
                'values': expenses_total
            })

        return calculated_rows

    def _sum_section_variances(self, section: Dict[str, Any], periods: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Sum all variance values in a section.

        Args:
            section: Section dict from variance hierarchy
            periods: List of period labels

        Returns:
            Dict mapping periods to aggregated variance data
        """
        # Initialize period totals
        period_totals = {}
        for period in periods:
            period_totals[period] = {
                'budget_value': 0.0,
                'actual_value': 0.0,
                'dollar_variance': 0.0,
                'pct_variance': None,  # Will calculate after summing
                'is_favorable': None,  # Will determine after summing
                'is_flagged': False
            }

        def sum_node(node: Any) -> None:
            """Recursively sum variance values."""
            if isinstance(node, dict):
                # Skip parent nodes
                if node.get('parent', False):
                    if 'children' in node:
                        for child in node['children']:
                            sum_node(child)
                    return

                # Sum leaf node values
                if 'values' in node and isinstance(node['values'], dict):
                    for period, variance_data in node['values'].items():
                        if period in period_totals and isinstance(variance_data, dict):
                            period_totals[period]['budget_value'] += variance_data.get('budget_value', 0.0)
                            period_totals[period]['actual_value'] += variance_data.get('actual_value', 0.0)
                            period_totals[period]['dollar_variance'] += variance_data.get('dollar_variance', 0.0)

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        sum_node(child)

            elif isinstance(node, list):
                for item in node:
                    sum_node(item)

        sum_node(section)

        # Calculate percentage variance for totals
        for period in period_totals:
            budget_total = period_totals[period]['budget_value']
            if budget_total != 0:
                period_totals[period]['pct_variance'] = (
                    period_totals[period]['dollar_variance'] / budget_total
                ) * 100

        return period_totals if any(period_totals.values()) else {}

    def generate_warning_messages(
        self,
        variance_result: Union[VarianceModel, Dict[str, VarianceModel]]
    ) -> Union[List[str], Dict[str, List[str]]]:
        """
        Generate actionable warning messages for flagged variances.

        Iterates through flagged variances and generates business-context-aware warning strings.
        Income and Expense variances receive different actionable recommendations.

        Args:
            variance_result: VarianceModel or dict of VarianceModels (from calculate_all_scenarios=True)

        Returns:
            List of warning message strings (single scenario) or dict mapping scenario names
            to warning lists (multi-scenario)
        """
        if isinstance(variance_result, dict):
            # Multi-scenario: return dict of warning lists
            warnings_dict = {}
            for scenario_name, variance_model in variance_result.items():
                warnings_dict[scenario_name] = self._generate_warnings_for_model(variance_model)
            return warnings_dict
        else:
            # Single scenario: return list of warnings
            return self._generate_warnings_for_model(variance_result)

    def _generate_warnings_for_model(self, variance_model: VarianceModel) -> List[str]:
        """
        Generate warning messages for a single VarianceModel.

        Args:
            variance_model: VarianceModel instance

        Returns:
            List of warning message strings
        """
        warnings = []
        hierarchy = variance_model.hierarchy

        # Process each section
        for section_name, section_data in hierarchy.items():
            self._extract_warnings_from_section(
                section_data,
                section_name,
                warnings
            )

        return warnings

    def _extract_warnings_from_section(
        self,
        section: Dict[str, Any],
        section_name: str,
        warnings: List[str]
    ) -> None:
        """
        Recursively extract warnings from section hierarchy.

        Args:
            section: Section dict from variance hierarchy
            section_name: Section name ('Income' or 'Expenses')
            warnings: List to append warning messages to (modified in-place)
        """
        def process_node(node: Any) -> None:
            """Recursively process nodes for flagged variances."""
            if isinstance(node, dict):
                # Check if this node has flagged variances
                if 'values' in node and 'name' in node:
                    account_name = node['name']
                    for period, variance_data in node['values'].items():
                        if isinstance(variance_data, dict) and variance_data.get('is_flagged', False):
                            # Generate warning message for this flagged variance
                            warning = self._format_warning_message(
                                account_name,
                                period,
                                variance_data,
                                section_name
                            )
                            warnings.append(warning)

                # Traverse children
                if 'children' in node:
                    for child in node['children']:
                        process_node(child)

            elif isinstance(node, list):
                for item in node:
                    process_node(item)

        process_node(section)

    def _format_warning_message(
        self,
        account_name: str,
        period: str,
        variance_data: Dict[str, Any],
        section_name: str
    ) -> str:
        """
        Format warning message for a single flagged variance.

        Template: "{account} forecast ${forecast:,} is {pct:.1f}% {above/below} budget ${budget:,} for {period} - {recommendation}"

        Args:
            account_name: Account name
            period: Period label
            variance_data: Variance data dict with budget_value, actual_value, pct_variance, etc.
            section_name: Section name ('Income' or 'Expenses')

        Returns:
            Formatted warning message string
        """
        forecast_value = variance_data['actual_value']  # forecast value stored as 'actual_value'
        budget_value = variance_data['budget_value']
        dollar_variance = variance_data['dollar_variance']
        pct_variance = variance_data.get('pct_variance')

        # Determine above/below
        if dollar_variance > 0:
            direction = "above"
        else:
            direction = "below"

        # Determine recommendation based on section and variance direction
        if section_name == 'Income':
            if dollar_variance > 0:
                recommendation = "strong performance, validate growth assumptions"
            else:
                recommendation = "reforecasting may be needed to align with targets"
        else:  # Expenses
            if dollar_variance > 0:
                recommendation = "cost control review recommended"
            else:
                recommendation = "spending tracking favorably to budget"

        # Format percentage
        if pct_variance is not None:
            pct_str = f"{abs(pct_variance):.1f}%"
        else:
            pct_str = "N/A%"

        # Build warning message
        warning = (
            f"{account_name} forecast ${forecast_value:,.0f} is {pct_str} {direction} "
            f"budget ${budget_value:,.0f} for {period} - {recommendation}"
        )

        return warning
