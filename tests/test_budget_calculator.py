"""
Unit tests for BudgetCalculator service.

Tests budget methodologies (growth, average, zero-based), parameter application
(percentage growth, absolute adjustments, overrides), and edge cases.
"""
import pandas as pd
import pytest

from src.models import PLModel, ParameterModel
from src.services import BudgetCalculator


class TestBudgetCalculator:
    """Test suite for BudgetCalculator class."""

    @pytest.fixture
    def sample_pl_model(self):
        """Create sample PLModel with 12 monthly periods."""
        hierarchy = {
            'Income': {
                'children': [
                    {
                        'name': 'Product Sales',
                        'values': {
                            'Jan 2024': 10000.0,
                            'Feb 2024': 10500.0,
                            'Mar 2024': 11000.0,
                            'Apr 2024': 10800.0,
                            'May 2024': 11200.0,
                            'Jun 2024': 11500.0,
                            'Jul 2024': 12000.0,
                            'Aug 2024': 12200.0,
                            'Sep 2024': 11800.0,
                            'Oct 2024': 12500.0,
                            'Nov 2024': 13000.0,
                            'Dec 2024': 13500.0
                        }
                    },
                    {
                        'name': 'Service Revenue',
                        'values': {
                            'Jan 2024': 5000.0,
                            'Feb 2024': 5100.0,
                            'Mar 2024': 5200.0,
                            'Apr 2024': 5300.0,
                            'May 2024': 5400.0,
                            'Jun 2024': 5500.0,
                            'Jul 2024': 5600.0,
                            'Aug 2024': 5700.0,
                            'Sep 2024': 5800.0,
                            'Oct 2024': 5900.0,
                            'Nov 2024': 6000.0,
                            'Dec 2024': 6100.0
                        }
                    }
                ]
            },
            'Expenses': {
                'children': [
                    {
                        'name': 'Marketing',
                        'values': {
                            'Jan 2024': 2000.0,
                            'Feb 2024': 2000.0,
                            'Mar 2024': 2000.0,
                            'Apr 2024': 2000.0,
                            'May 2024': 2000.0,
                            'Jun 2024': 2000.0,
                            'Jul 2024': 2000.0,
                            'Aug 2024': 2000.0,
                            'Sep 2024': 2000.0,
                            'Oct 2024': 2000.0,
                            'Nov 2024': 2000.0,
                            'Dec 2024': 2000.0
                        }
                    },
                    {
                        'name': 'Rent',
                        'values': {
                            'Jan 2024': 3000.0,
                            'Feb 2024': 3000.0,
                            'Mar 2024': 3000.0,
                            'Apr 2024': 3000.0,
                            'May 2024': 3000.0,
                            'Jun 2024': 3000.0,
                            'Jul 2024': 3000.0,
                            'Aug 2024': 3000.0,
                            'Sep 2024': 3000.0,
                            'Oct 2024': 3000.0,
                            'Nov 2024': 3000.0,
                            'Dec 2024': 3000.0
                        }
                    }
                ]
            }
        }

        calculated_rows = [
            {
                'account_name': 'Net Income',
                'values': {f'{month} 2024': 0.0 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
            }
        ]

        df = pd.DataFrame([
            {'account_name': 'Product Sales', 'section': 'Income'},
            {'account_name': 'Service Revenue', 'section': 'Income'},
            {'account_name': 'Marketing', 'section': 'Expenses'},
            {'account_name': 'Rent', 'section': 'Expenses'}
        ])

        return PLModel(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows)

    @pytest.fixture
    def growth_params(self):
        """Create ParameterModel with growth_from_prior_year methodology and 15% growth."""
        return ParameterModel(parameters={
            'budget_methodology': 'growth_from_prior_year',
            'revenue_growth_rate': 0.15,
            'category_growth_rates': {},
            'expense_adjustment_factor': {},
            'account_overrides': {}
        })

    @pytest.fixture
    def average_params(self):
        """Create ParameterModel with historical_average methodology."""
        return ParameterModel(parameters={
            'budget_methodology': 'historical_average',
            'revenue_growth_rate': 0.0,
            'category_growth_rates': {},
            'expense_adjustment_factor': {},
            'account_overrides': {}
        })

    @pytest.fixture
    def zero_based_params(self):
        """Create ParameterModel with zero_based methodology."""
        return ParameterModel(parameters={
            'budget_methodology': 'zero_based',
            'revenue_growth_rate': 0.0,
            'category_growth_rates': {},
            'expense_adjustment_factor': {},
            'account_overrides': {}
        })

    def test_growth_from_prior_year_methodology(self, sample_pl_model, growth_params):
        """
        Given: sample_pl_model with revenue $13,500/month in Dec 2024, growth_params with 15% growth
        When: BudgetCalculator(sample_pl_model, growth_params).calculate() called
        Then: resulting BudgetModel has revenue ~$15,525/month (13500 * 1.15)
        """
        # Given
        calculator = BudgetCalculator(sample_pl_model, growth_params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()
        product_sales = income_section['children'][0]

        # Last period value is 13500, with 15% growth = 15525
        expected_value = 13500.0 * 1.15

        # Check first period has expected value
        first_period_value = product_sales['values']['Jan 2024']
        assert abs(first_period_value - expected_value) < 0.01

    def test_historical_average_methodology(self, sample_pl_model, average_params):
        """
        Given: sample_pl_model with Product Sales averaging ~11,666/month, average_params
        When: calculate() called
        Then: resulting BudgetModel has all periods = average value
        """
        # Given
        calculator = BudgetCalculator(sample_pl_model, average_params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()
        product_sales = income_section['children'][0]

        # Calculate expected average: sum of all months / 12
        # (10000 + 10500 + 11000 + 10800 + 11200 + 11500 + 12000 + 12200 + 11800 + 12500 + 13000 + 13500) / 12
        expected_avg = 140000.0 / 12  # 11666.67

        # All periods should have the average value
        for period, value in product_sales['values'].items():
            assert abs(value - expected_avg) < 0.01

    def test_zero_based_methodology(self, sample_pl_model, zero_based_params):
        """
        Given: sample_pl_model with any data, zero_based_params
        When: calculate() called
        Then: resulting BudgetModel has all account values = $0
        """
        # Given
        calculator = BudgetCalculator(sample_pl_model, zero_based_params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()
        expenses_section = budget_model.get_expenses()

        # All income accounts should be zero
        for child in income_section['children']:
            for period, value in child['values'].items():
                assert value == 0.0

        # All expense accounts should be zero
        for child in expenses_section['children']:
            for period, value in child['values'].items():
                assert value == 0.0

    def test_percentage_growth_parameter(self, sample_pl_model):
        """
        Given: growth_params with revenue_growth_rate=0.20 (20%)
        When: calculate() called
        Then: Income section values increased by 20%
        """
        # Given
        params = ParameterModel(parameters={
            'budget_methodology': 'growth_from_prior_year',
            'revenue_growth_rate': 0.20,
            'category_growth_rates': {},
            'expense_adjustment_factor': {},
            'account_overrides': {}
        })
        calculator = BudgetCalculator(sample_pl_model, params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()
        product_sales = income_section['children'][0]

        # Last period value (13500) with 20% growth = 16200
        expected_value = 13500.0 * 1.20

        first_period_value = product_sales['values']['Jan 2024']
        assert abs(first_period_value - expected_value) < 0.01

    def test_absolute_adjustment_parameter(self, sample_pl_model, growth_params):
        """
        Given: growth_params with expense_adjustment_factor={'Marketing': 500}, sample_pl_model with Marketing $2000/month
        When: calculate() called
        Then: resulting BudgetModel Marketing = base_value + $500 per period
        """
        # Given
        growth_params.set_parameter('expense_adjustment_factor', {'Marketing': 500})
        calculator = BudgetCalculator(sample_pl_model, growth_params)

        # When
        budget_model = calculator.calculate()

        # Then
        expenses_section = budget_model.get_expenses()
        marketing = expenses_section['children'][0]

        # Base methodology uses last period (2000), then adds 500
        expected_value = 2000.0 + 500.0

        first_period_value = marketing['values']['Jan 2024']
        assert abs(first_period_value - expected_value) < 0.01

    def test_account_override_parameter(self, sample_pl_model, growth_params):
        """
        Given: growth_params with account_overrides={'Product Sales': {'Jan 2024': 20000}}, PLModel with Product Sales
        When: calculate() called
        Then: resulting BudgetModel Product Sales Jan 2024 = 20000 (override replaces calculated value)
        """
        # Given
        override_values = {
            'Jan 2024': 20000.0,
            'Feb 2024': 21000.0,
            'Mar 2024': 22000.0,
            'Apr 2024': 21500.0,
            'May 2024': 22500.0,
            'Jun 2024': 23000.0,
            'Jul 2024': 23500.0,
            'Aug 2024': 24000.0,
            'Sep 2024': 24500.0,
            'Oct 2024': 25000.0,
            'Nov 2024': 25500.0,
            'Dec 2024': 26000.0
        }
        growth_params.set_parameter('account_overrides', {'Product Sales': override_values})
        calculator = BudgetCalculator(sample_pl_model, growth_params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()
        product_sales = income_section['children'][0]

        # Override value should replace calculated value
        assert product_sales['values']['Jan 2024'] == 20000.0
        assert product_sales['values']['Feb 2024'] == 21000.0

    def test_new_account_override(self, sample_pl_model, growth_params):
        """
        Given: growth_params with account_overrides={'New Product Line': {period_values}}, PLModel without 'New Product Line'
        When: calculate() called
        Then: resulting BudgetModel includes 'New Product Line' with override values (new account handled)
        """
        # Given
        new_account_values = {
            'Jan 2024': 5000.0,
            'Feb 2024': 5500.0,
            'Mar 2024': 6000.0,
            'Apr 2024': 6200.0,
            'May 2024': 6500.0,
            'Jun 2024': 7000.0,
            'Jul 2024': 7200.0,
            'Aug 2024': 7500.0,
            'Sep 2024': 7800.0,
            'Oct 2024': 8000.0,
            'Nov 2024': 8500.0,
            'Dec 2024': 9000.0
        }
        growth_params.set_parameter('account_overrides', {'New Product Line': new_account_values})
        calculator = BudgetCalculator(sample_pl_model, growth_params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()

        # Find new account in children
        new_account = None
        for child in income_section['children']:
            if child['name'] == 'New Product Line':
                new_account = child
                break

        assert new_account is not None
        assert new_account['values']['Jan 2024'] == 5000.0
        assert new_account['values']['Dec 2024'] == 9000.0

    def test_parent_node_skipping(self, sample_pl_model, growth_params):
        """
        Given: sample_pl_model with parent node (parent: True) in hierarchy
        When: calculate() processes hierarchy
        Then: parent node skipped, only leaf accounts have values calculated
        """
        # Given - add parent node to hierarchy
        sample_pl_model.hierarchy['Income']['children'].append({
            'name': 'Total Services',
            'parent': True,
            'children': [
                {
                    'name': 'Consulting',
                    'values': {f'{month} 2024': 1000.0 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
                }
            ],
            'total': {f'{month} 2024': 1000.0 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
        })

        calculator = BudgetCalculator(sample_pl_model, growth_params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()

        # Find parent node
        parent_node = None
        for child in income_section['children']:
            if child.get('name') == 'Total Services':
                parent_node = child
                break

        # Parent node should not have 'values' key (or values unchanged from original)
        # Only child (Consulting) should have calculated values
        assert parent_node is not None
        consulting = parent_node['children'][0]

        # Consulting should have calculated values (last period 1000 * 1.15 = 1150)
        expected_value = 1000.0 * 1.15
        assert abs(consulting['values']['Jan 2024'] - expected_value) < 0.01

    def test_zero_historical_values_handling(self, sample_pl_model, average_params):
        """
        Given: sample_pl_model with zero revenue for some periods, average_params
        When: calculate() called
        Then: completes without division errors, average includes zero values
        """
        # Given - set some periods to zero
        sample_pl_model.hierarchy['Income']['children'][0]['values']['Jan 2024'] = 0.0
        sample_pl_model.hierarchy['Income']['children'][0]['values']['Feb 2024'] = 0.0

        calculator = BudgetCalculator(sample_pl_model, average_params)

        # When
        budget_model = calculator.calculate()

        # Then - should complete without errors
        income_section = budget_model.get_income()
        product_sales = income_section['children'][0]

        # Average calculation should include zeros
        # New sum: (0 + 0 + 11000 + 10800 + 11200 + 11500 + 12000 + 12200 + 11800 + 12500 + 13000 + 13500) / 12
        expected_avg = 119500.0 / 12

        first_period_value = product_sales['values']['Jan 2024']
        assert abs(first_period_value - expected_avg) < 0.01

    def test_category_growth_rates(self, sample_pl_model):
        """
        Given: growth_params with category_growth_rates={'Service Revenue': 0.25}
        When: calculate() called
        Then: Service Revenue grows by 25%, Product Sales uses default revenue_growth_rate
        """
        # Given
        params = ParameterModel(parameters={
            'budget_methodology': 'growth_from_prior_year',
            'revenue_growth_rate': 0.10,  # 10% default
            'category_growth_rates': {'Service Revenue': 0.25},  # 25% for Service Revenue
            'expense_adjustment_factor': {},
            'account_overrides': {}
        })
        calculator = BudgetCalculator(sample_pl_model, params)

        # When
        budget_model = calculator.calculate()

        # Then
        income_section = budget_model.get_income()
        product_sales = income_section['children'][0]
        service_revenue = income_section['children'][1]

        # Product Sales: 13500 * 1.10 = 14850
        expected_product = 13500.0 * 1.10
        # Service Revenue: 6100 * 1.25 = 7625
        expected_service = 6100.0 * 1.25

        assert abs(product_sales['values']['Jan 2024'] - expected_product) < 0.01
        assert abs(service_revenue['values']['Jan 2024'] - expected_service) < 0.01

    def test_calculated_rows_generated(self, sample_pl_model, growth_params):
        """
        Given: sample_pl_model and growth_params
        When: calculate() called
        Then: BudgetModel has calculated_rows with Total Income, Total Expenses, Net Income
        """
        # Given
        calculator = BudgetCalculator(sample_pl_model, growth_params)

        # When
        budget_model = calculator.calculate()

        # Then
        assert len(budget_model.calculated_rows) > 0

        # Find calculated row names
        calc_row_names = [row['account_name'] for row in budget_model.calculated_rows]

        assert 'Total Income' in calc_row_names
        assert 'Total Expenses' in calc_row_names
        assert 'Net Income' in calc_row_names
