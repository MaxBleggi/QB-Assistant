"""
Unit tests for ForecastTemplateService.

Tests template structure, copy behavior, and error handling for unknown template names.
"""
import pytest

from src.services.forecast_templates import ForecastTemplateService


class TestForecastTemplateService:
    """Test suite for ForecastTemplateService class."""

    def test_get_template_conservative_returns_all_categories(self):
        """
        Given: Template name 'Conservative'
        When: ForecastTemplateService.get_template('Conservative') called
        Then: Returns dict with all four parameter category keys populated
        """
        template = ForecastTemplateService.get_template('Conservative')

        assert 'revenue_growth_rates' in template
        assert 'expense_trend_adjustments' in template
        assert 'cash_flow_timing_params' in template
        assert 'major_cash_events' in template

        # Verify each category has content
        assert isinstance(template['revenue_growth_rates'], dict)
        assert isinstance(template['expense_trend_adjustments'], dict)
        assert isinstance(template['cash_flow_timing_params'], dict)
        assert isinstance(template['major_cash_events'], dict)

    def test_get_template_expected_returns_all_categories(self):
        """
        Given: Template name 'Expected'
        When: get_template('Expected') called
        Then: Returns dict with all four parameter category keys populated
        """
        template = ForecastTemplateService.get_template('Expected')

        assert 'revenue_growth_rates' in template
        assert 'expense_trend_adjustments' in template
        assert 'cash_flow_timing_params' in template
        assert 'major_cash_events' in template

    def test_get_template_optimistic_returns_all_categories(self):
        """
        Given: Template name 'Optimistic'
        When: get_template('Optimistic') called
        Then: Returns dict with all four parameter category keys populated
        """
        template = ForecastTemplateService.get_template('Optimistic')

        assert 'revenue_growth_rates' in template
        assert 'expense_trend_adjustments' in template
        assert 'cash_flow_timing_params' in template
        assert 'major_cash_events' in template

    def test_get_template_raises_valueerror_for_unknown_template(self):
        """
        Given: Unknown template name 'CustomTemplate'
        When: get_template('CustomTemplate') called
        Then: Raises ValueError with message indicating unknown template
        """
        with pytest.raises(ValueError) as exc_info:
            ForecastTemplateService.get_template('CustomTemplate')

        assert 'CustomTemplate' in str(exc_info.value)
        assert 'Unknown template' in str(exc_info.value)

    def test_list_templates_returns_three_template_names(self):
        """
        Given: No arguments
        When: ForecastTemplateService.list_templates() called
        Then: Returns list of exactly three template names
        """
        templates = ForecastTemplateService.list_templates()

        assert len(templates) == 3
        assert 'Conservative' in templates
        assert 'Expected' in templates
        assert 'Optimistic' in templates

    def test_template_mutation_doesnt_affect_subsequent_calls(self):
        """
        Given: Template = get_template('Expected'), modify template['revenue_growth_rates']
        When: get_template('Expected') called again
        Then: Returns original unmodified template (copy behavior)
        """
        # Get template and modify it
        template1 = ForecastTemplateService.get_template('Expected')
        original_monthly_rate = template1['revenue_growth_rates']['monthly_rate']
        template1['revenue_growth_rates']['monthly_rate'] = 999.99

        # Get template again
        template2 = ForecastTemplateService.get_template('Expected')

        # Verify second call returns original values
        assert template2['revenue_growth_rates']['monthly_rate'] == original_monthly_rate
        assert template2['revenue_growth_rates']['monthly_rate'] != 999.99

    def test_templates_have_different_values(self):
        """
        Given: Three templates
        When: Templates compared
        Then: Each template has different values (not identical)
        """
        conservative = ForecastTemplateService.get_template('Conservative')
        expected = ForecastTemplateService.get_template('Expected')
        optimistic = ForecastTemplateService.get_template('Optimistic')

        # Compare monthly rates (should be different)
        conservative_rate = conservative['revenue_growth_rates']['monthly_rate']
        expected_rate = expected['revenue_growth_rates']['monthly_rate']
        optimistic_rate = optimistic['revenue_growth_rates']['monthly_rate']

        assert conservative_rate != expected_rate
        assert expected_rate != optimistic_rate
        assert conservative_rate != optimistic_rate

        # Verify conservative < expected < optimistic (growth rates)
        assert conservative_rate < expected_rate < optimistic_rate

    def test_template_structure_has_required_revenue_fields(self):
        """
        Given: Template from get_template
        When: revenue_growth_rates inspected
        Then: Contains required fields (monthly_rate, use_averaged)
        """
        template = ForecastTemplateService.get_template('Conservative')
        revenue_params = template['revenue_growth_rates']

        assert 'monthly_rate' in revenue_params
        assert 'use_averaged' in revenue_params
        assert isinstance(revenue_params['monthly_rate'], (int, float))
        assert isinstance(revenue_params['use_averaged'], bool)

    def test_template_structure_has_required_expense_fields(self):
        """
        Given: Template from get_template
        When: expense_trend_adjustments inspected
        Then: Contains required fields (cogs_trend, opex_trend)
        """
        template = ForecastTemplateService.get_template('Expected')
        expense_params = template['expense_trend_adjustments']

        assert 'cogs_trend' in expense_params
        assert 'opex_trend' in expense_params
        assert isinstance(expense_params['cogs_trend'], (int, float))
        assert isinstance(expense_params['opex_trend'], (int, float))

    def test_template_structure_has_required_cash_flow_fields(self):
        """
        Given: Template from get_template
        When: cash_flow_timing_params inspected
        Then: Contains required fields (collection_period_days, payment_terms_days)
        """
        template = ForecastTemplateService.get_template('Optimistic')
        cash_flow_params = template['cash_flow_timing_params']

        assert 'collection_period_days' in cash_flow_params
        assert 'payment_terms_days' in cash_flow_params
        assert isinstance(cash_flow_params['collection_period_days'], int)
        assert isinstance(cash_flow_params['payment_terms_days'], int)

    def test_template_structure_has_required_major_events_fields(self):
        """
        Given: Template from get_template
        When: major_cash_events inspected
        Then: Contains required fields (planned_capex, debt_payments)
        """
        template = ForecastTemplateService.get_template('Conservative')
        major_events_params = template['major_cash_events']

        assert 'planned_capex' in major_events_params
        assert 'debt_payments' in major_events_params
        assert isinstance(major_events_params['planned_capex'], list)
        assert isinstance(major_events_params['debt_payments'], list)
