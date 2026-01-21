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
