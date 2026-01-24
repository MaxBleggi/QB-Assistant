"""
Forecast template service.

Provides pre-defined scenario templates (Conservative, Expected, Optimistic) with
parameter sets for revenue growth, expense trends, cash flow timing, and major cash events.
"""
from typing import Any, Dict, List
import copy


class ForecastTemplateService:
    """
    Service for providing forecast scenario templates.

    Offers three pre-defined templates with different assumption levels:
    - Conservative: Lower growth rates, cautious assumptions
    - Expected: Moderate growth rates, balanced assumptions
    - Optimistic: Higher growth rates, aggressive assumptions
    """

    # Template definitions with all four parameter categories
    TEMPLATES = {
        'Conservative': {
            'revenue_growth_rates': {
                'monthly_rate': 0.02,  # 2% monthly growth
                'use_averaged': True
            },
            'expense_trend_adjustments': {
                'cogs_trend': 0.03,  # 3% COGS increase
                'opex_trend': 0.02   # 2% OpEx increase
            },
            'cash_flow_timing_params': {
                'collection_period_days': 60,  # Conservative: longer collection
                'payment_terms_days': 30       # Standard payment terms
            },
            'major_cash_events': {
                'planned_capex': [],      # No major capital expenditures
                'debt_payments': []       # No debt payments planned
            },
            'external_events': {
                'events': []              # No external economic events by default
            }
        },
        'Expected': {
            'revenue_growth_rates': {
                'monthly_rate': 0.05,  # 5% monthly growth
                'use_averaged': True
            },
            'expense_trend_adjustments': {
                'cogs_trend': 0.04,  # 4% COGS increase
                'opex_trend': 0.03   # 3% OpEx increase
            },
            'cash_flow_timing_params': {
                'collection_period_days': 45,  # Expected: standard collection
                'payment_terms_days': 30       # Standard payment terms
            },
            'major_cash_events': {
                'planned_capex': [],      # No major capital expenditures
                'debt_payments': []       # No debt payments planned
            },
            'external_events': {
                'events': []              # No external economic events by default
            }
        },
        'Optimistic': {
            'revenue_growth_rates': {
                'monthly_rate': 0.10,  # 10% monthly growth
                'use_averaged': True
            },
            'expense_trend_adjustments': {
                'cogs_trend': 0.05,  # 5% COGS increase
                'opex_trend': 0.04   # 4% OpEx increase
            },
            'cash_flow_timing_params': {
                'collection_period_days': 30,  # Optimistic: faster collection
                'payment_terms_days': 45       # Extended payment terms
            },
            'major_cash_events': {
                'planned_capex': [],      # No major capital expenditures
                'debt_payments': []       # No debt payments planned
            },
            'external_events': {
                'events': []              # No external economic events by default
            }
        }
    }

    @staticmethod
    def get_template(name: str) -> Dict[str, Any]:
        """
        Get forecast template by name.

        Args:
            name: Template name ('Conservative', 'Expected', or 'Optimistic')

        Returns:
            Deep copy of template dict with all four parameter categories

        Raises:
            ValueError: If template name is not recognized
        """
        if name not in ForecastTemplateService.TEMPLATES:
            valid_names = list(ForecastTemplateService.TEMPLATES.keys())
            raise ValueError(
                f"Unknown template '{name}'. Valid templates: {valid_names}"
            )

        # Return deep copy to prevent template mutation
        return copy.deepcopy(ForecastTemplateService.TEMPLATES[name])

    @staticmethod
    def list_templates() -> List[str]:
        """
        Get list of available template names.

        Returns:
            List of template names
        """
        return list(ForecastTemplateService.TEMPLATES.keys())

    @staticmethod
    def create_scenario_from_template(
        template_name: str,
        scenario_name: str,
        overrides: Dict[str, Any] = None
    ):
        """
        Create ForecastScenarioModel from template with optional parameter overrides.

        Flattens nested template structure and merges with user overrides to produce
        ForecastScenarioModel with flat parameter keys.

        Args:
            template_name: Name of template ('Conservative', 'Expected', or 'Optimistic')
            scenario_name: Name for the created scenario
            overrides: Optional dict of parameter overrides (keys take precedence over template)

        Returns:
            ForecastScenarioModel instance with scenario_name, merged parameters,
            and metadata indicating template source

        Raises:
            ValueError: If template_name not found

        Example:
            >>> scenario = ForecastTemplateService.create_scenario_from_template(
            ...     'Conservative',
            ...     'My Conservative Case',
            ...     overrides={'monthly_rate': 0.03}
            ... )
            >>> scenario.parameters['monthly_rate']
            0.03
        """
        # Import here to avoid circular dependency
        from src.models.forecast_scenario import ForecastScenarioModel

        # Get base template (this will raise ValueError if template not found)
        template = ForecastTemplateService.get_template(template_name)

        # Flatten nested template structure to flat parameter keys
        flattened_params = ForecastTemplateService._flatten_template(template)

        # Merge user overrides (overrides take precedence)
        if overrides:
            flattened_params.update(overrides)

        # Create scenario model with flattened parameters
        return ForecastScenarioModel(
            parameters=flattened_params,
            scenario_name=scenario_name,
            description=f"Created from {template_name} template"
        )

    @staticmethod
    def _flatten_template(template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested template structure to flat parameter keys.

        Converts nested structure like:
            {'revenue_growth_rates': {'monthly_rate': 0.02}}
        To flat structure:
            {'monthly_rate': 0.02}

        Args:
            template: Nested template dict from TEMPLATES

        Returns:
            Flat dict with leaf parameter keys and values
        """
        flattened = {}

        for category_key, category_value in template.items():
            if isinstance(category_value, dict):
                # Extract leaf values from nested dict
                for param_key, param_value in category_value.items():
                    # For nested structures like major_cash_events with arrays,
                    # keep the full key to avoid collisions
                    if isinstance(param_value, (list, dict)) and param_value:
                        # Keep structured values with prefixed key
                        flattened[param_key] = param_value
                    else:
                        # Simple leaf values - use direct key
                        flattened[param_key] = param_value
            else:
                # Non-dict values - preserve as-is
                flattened[category_key] = category_value

        return flattened
