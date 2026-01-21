"""
Tests for BudgetVarianceCalculator - service for budget vs actual variance analysis.

Covers:
- Basic variance calculations (dollar and percentage)
- Favorable/unfavorable determination (Income vs Expenses)
- Threshold flagging (percentage and absolute)
- Edge cases (zero budget, negative values)
- Unmatched account tracking
- Section-level summaries
"""
import pytest
import pandas as pd

from src.models import BudgetModel, PLModel, VarianceModel
from src.services import BudgetVarianceCalculator


@pytest.fixture
def sample_budget_model():
    """BudgetModel with realistic hierarchy and values."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Product Revenue', 'values': {'2024-01': 100000}},
                {'name': 'Service Revenue', 'values': {'2024-01': 50000}},
                {'name': 'Legacy Product', 'values': {'2024-01': 10000}}  # Will be unmatched
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Marketing', 'values': {'2024-01': 30000}},
                {'name': 'Sales Costs', 'values': {'2024-01': 20000}},
                {'name': 'Zero Budget Item', 'values': {'2024-01': 0}}  # Zero budget test
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Product Revenue', 'section': 'Income'},
        {'account_name': 'Service Revenue', 'section': 'Income'},
        {'account_name': 'Legacy Product', 'section': 'Income'},
        {'account_name': 'Marketing', 'section': 'Expenses'},
        {'account_name': 'Sales Costs', 'section': 'Expenses'},
        {'account_name': 'Zero Budget Item', 'section': 'Expenses'}
    ])

    calculated_rows = []

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows)


@pytest.fixture
def sample_actual_model():
    """PLModel with actual P&L data (variances from budget)."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Product Revenue', 'values': {'2024-01': 120000}},  # +20% favorable
                {'name': 'Service Revenue', 'values': {'2024-01': 45000}},   # -10% unfavorable
                {'name': 'New Service', 'values': {'2024-01': 5000}}    # Unmatched
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Marketing', 'values': {'2024-01': 25000}},         # -16.7% favorable
                {'name': 'Sales Costs', 'values': {'2024-01': 24000}},       # +20% unfavorable
                {'name': 'Zero Budget Item', 'values': {'2024-01': 5000}}    # From zero budget
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Product Revenue', 'section': 'Income'},
        {'account_name': 'Service Revenue', 'section': 'Income'},
        {'account_name': 'New Service', 'section': 'Income'},
        {'account_name': 'Marketing', 'section': 'Expenses'},
        {'account_name': 'Sales Costs', 'section': 'Expenses'},
        {'account_name': 'Zero Budget Item', 'section': 'Expenses'}
    ])

    calculated_rows = []

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows)


@pytest.fixture
def simple_budget_model():
    """Simple BudgetModel for focused tests."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Revenue', 'values': {'2024-01': 100000}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Costs', 'values': {'2024-01': 80000}}
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def simple_actual_model_income_favorable():
    """Simple actual model with favorable income variance."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Revenue', 'values': {'2024-01': 120000}}  # +20% favorable
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Costs', 'values': {'2024-01': 80000}}
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def simple_actual_model_expense_favorable():
    """Simple actual model with favorable expense variance."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {'name': 'Revenue', 'values': {'2024-01': 100000}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {'name': 'Costs', 'values': {'2024-01': 70000}}  # -12.5% favorable
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


class TestBudgetVarianceCalculator:
    """Test suite for BudgetVarianceCalculator."""

    def test_dollar_variance_calculation(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test dollar_variance = actual - budget."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # Find Revenue account in variance hierarchy
        revenue_account = result.get_income_variances()['children'][0]
        variance_data = revenue_account['values']['2024-01']

        assert variance_data['budget_value'] == 100000
        assert variance_data['actual_value'] == 120000
        assert variance_data['dollar_variance'] == 20000

    def test_percentage_variance_calculation(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test pct_variance = (actual - budget) / budget * 100."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        revenue_account = result.get_income_variances()['children'][0]
        variance_data = revenue_account['values']['2024-01']

        assert variance_data['pct_variance'] == 20.0

    def test_income_favorable_variance(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test Income: actual > budget sets is_favorable=True."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        revenue_account = result.get_income_variances()['children'][0]
        variance_data = revenue_account['values']['2024-01']

        assert variance_data['is_favorable'] is True
        assert variance_data['dollar_variance'] > 0

    def test_income_unfavorable_variance(self, sample_budget_model, sample_actual_model):
        """Test Income: actual < budget sets is_favorable=False."""
        calculator = BudgetVarianceCalculator(sample_budget_model, sample_actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # Service Revenue has unfavorable variance (45k actual vs 50k budget)
        income_accounts = result.get_income_variances()['children']
        service_revenue = next(a for a in income_accounts if a['name'] == 'Service Revenue')
        variance_data = service_revenue['values']['2024-01']

        assert variance_data['is_favorable'] is False
        assert variance_data['dollar_variance'] < 0
        assert variance_data['dollar_variance'] == -5000

    def test_expenses_favorable_variance(self, simple_budget_model, simple_actual_model_expense_favorable):
        """Test Expenses: actual < budget sets is_favorable=True."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_expense_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        costs_account = result.get_expense_variances()['children'][0]
        variance_data = costs_account['values']['2024-01']

        assert variance_data['is_favorable'] is True
        assert variance_data['dollar_variance'] < 0  # Spent less than budget
        assert variance_data['dollar_variance'] == -10000

    def test_expenses_unfavorable_variance(self, sample_budget_model, sample_actual_model):
        """Test Expenses: actual > budget sets is_favorable=False."""
        calculator = BudgetVarianceCalculator(sample_budget_model, sample_actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # Sales Costs has unfavorable variance (24k actual vs 20k budget)
        expense_accounts = result.get_expense_variances()['children']
        sales_costs = next(a for a in expense_accounts if a['name'] == 'Sales Costs')
        variance_data = sales_costs['values']['2024-01']

        assert variance_data['is_favorable'] is False
        assert variance_data['dollar_variance'] > 0  # Spent more than budget
        assert variance_data['dollar_variance'] == 4000

    def test_threshold_flagging_percentage(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test abs(pct_variance) > threshold_pct sets is_flagged=True."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)

        # Revenue has 20% variance, should be flagged with 10% threshold
        result = calculator.calculate(threshold_pct=10, threshold_abs=50000)

        revenue_account = result.get_income_variances()['children'][0]
        variance_data = revenue_account['values']['2024-01']

        assert variance_data['pct_variance'] == 20.0
        assert variance_data['is_flagged'] is True

    def test_threshold_flagging_absolute(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test abs(dollar_variance) > threshold_abs sets is_flagged=True."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)

        # Revenue has $20k variance, should be flagged with $10k threshold
        result = calculator.calculate(threshold_pct=50, threshold_abs=10000)

        revenue_account = result.get_income_variances()['children'][0]
        variance_data = revenue_account['values']['2024-01']

        assert variance_data['dollar_variance'] == 20000
        assert variance_data['is_flagged'] is True

    def test_below_thresholds_not_flagged(self, simple_budget_model):
        """Test variance below both thresholds sets is_flagged=False."""
        # Create actual with small variance (5% and $5k)
        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {'2024-01': 105000}}  # +5%
                ]
            },
            'Expenses': {
                'name': 'Expenses',
                'children': [
                    {'name': 'Costs', 'values': {'2024-01': 80000}}
                ]
            }
        }

        df = pd.DataFrame([
            {'account_name': 'Revenue', 'section': 'Income'},
            {'account_name': 'Costs', 'section': 'Expenses'}
        ])

        actual_model = PLModel(df=df, hierarchy=actual_hierarchy, calculated_rows=[])

        calculator = BudgetVarianceCalculator(simple_budget_model, actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        revenue_account = result.get_income_variances()['children'][0]
        variance_data = revenue_account['values']['2024-01']

        assert variance_data['pct_variance'] == 5.0
        assert variance_data['dollar_variance'] == 5000
        assert variance_data['is_flagged'] is False

    def test_zero_budget_handling(self, sample_budget_model, sample_actual_model):
        """Test zero budget sets pct_variance=None, dollar_variance still calculated."""
        calculator = BudgetVarianceCalculator(sample_budget_model, sample_actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # Zero Budget Item has budget=0, actual=5000
        expense_accounts = result.get_expense_variances()['children']
        zero_budget = next(a for a in expense_accounts if a['name'] == 'Zero Budget Item')
        variance_data = zero_budget['values']['2024-01']

        assert variance_data['budget_value'] == 0
        assert variance_data['actual_value'] == 5000
        assert variance_data['dollar_variance'] == 5000
        assert variance_data['pct_variance'] is None  # Cannot calculate percentage

    def test_unmatched_budget_accounts(self, sample_budget_model, sample_actual_model):
        """Test budget accounts without actuals in unmatched_budget_accounts list."""
        calculator = BudgetVarianceCalculator(sample_budget_model, sample_actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # 'Legacy Product' is in budget but not in actual
        assert 'Legacy Product' in result.unmatched_budget_accounts

    def test_unmatched_actual_accounts(self, sample_budget_model, sample_actual_model):
        """Test actual accounts without budget in unmatched_actual_accounts list."""
        calculator = BudgetVarianceCalculator(sample_budget_model, sample_actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # 'New Service' is in actual but not in budget
        assert 'New Service' in result.unmatched_actual_accounts

    def test_negative_actual_values(self):
        """Test negative actual values calculate variance correctly."""
        budget_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {'2024-01': 100000}}
                ]
            },
            'Expenses': {
                'name': 'Expenses',
                'children': [
                    {'name': 'Refunds', 'values': {'2024-01': 5000}}
                ]
            }
        }

        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {'name': 'Revenue', 'values': {'2024-01': 100000}}
                ]
            },
            'Expenses': {
                'name': 'Expenses',
                'children': [
                    {'name': 'Refunds', 'values': {'2024-01': -2000}}  # Negative (credit)
                ]
            }
        }

        df = pd.DataFrame([
            {'account_name': 'Revenue', 'section': 'Income'},
            {'account_name': 'Refunds', 'section': 'Expenses'}
        ])

        budget_model = BudgetModel(df=df, hierarchy=budget_hierarchy, calculated_rows=[])
        actual_model = PLModel(df=df, hierarchy=actual_hierarchy, calculated_rows=[])

        calculator = BudgetVarianceCalculator(budget_model, actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        expense_accounts = result.get_expense_variances()['children']
        refunds = next(a for a in expense_accounts if a['name'] == 'Refunds')
        variance_data = refunds['values']['2024-01']

        assert variance_data['budget_value'] == 5000
        assert variance_data['actual_value'] == -2000
        assert variance_data['dollar_variance'] == -7000  # -2000 - 5000
        assert variance_data['pct_variance'] == -140.0   # (-7000 / 5000) * 100

    def test_section_level_summary(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test calculated_rows contain section-level variance summaries."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # Should have section-level summaries in calculated_rows
        assert len(result.calculated_rows) > 0

        # Find Income variance total
        income_total = next(
            (row for row in result.calculated_rows if 'Income' in row['account_name']),
            None
        )

        assert income_total is not None
        assert '2024-01' in income_total['values']

        # Income total should aggregate the revenue variance
        income_variance = income_total['values']['2024-01']
        assert income_variance['budget_value'] == 100000
        assert income_variance['actual_value'] == 120000
        assert income_variance['dollar_variance'] == 20000

    def test_returns_variance_model(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test calculate() returns VarianceModel instance."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        assert isinstance(result, VarianceModel)
        assert hasattr(result, 'hierarchy')
        assert hasattr(result, 'calculated_rows')
        assert hasattr(result, 'unmatched_budget_accounts')
        assert hasattr(result, 'unmatched_actual_accounts')

    def test_variance_hierarchy_structure(self, simple_budget_model, simple_actual_model_income_favorable):
        """Test variance hierarchy has correct structure."""
        calculator = BudgetVarianceCalculator(simple_budget_model, simple_actual_model_income_favorable)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        # Check hierarchy has Income and Expenses sections
        assert 'Income' in result.hierarchy
        assert 'Expenses' in result.hierarchy

        # Check Income section has children
        income_section = result.hierarchy['Income']
        assert 'name' in income_section
        assert 'children' in income_section
        assert len(income_section['children']) > 0

        # Check account has variance attributes
        account = income_section['children'][0]
        assert 'name' in account
        assert 'values' in account

        # Check period variance data
        period_data = account['values']['2024-01']
        assert 'budget_value' in period_data
        assert 'actual_value' in period_data
        assert 'dollar_variance' in period_data
        assert 'pct_variance' in period_data
        assert 'is_favorable' in period_data
        assert 'is_flagged' in period_data

    def test_multiple_periods(self):
        """Test variance calculation across multiple periods."""
        budget_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            '2024-01': 100000,
                            '2024-02': 110000,
                            '2024-03': 120000
                        }
                    }
                ]
            }
        }

        actual_hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            '2024-01': 120000,  # +20%
                            '2024-02': 105000,  # -4.5%
                            '2024-03': 130000   # +8.3%
                        }
                    }
                ]
            }
        }

        df = pd.DataFrame([
            {'account_name': 'Revenue', 'section': 'Income'}
        ])

        budget_model = BudgetModel(df=df, hierarchy=budget_hierarchy, calculated_rows=[])
        actual_model = PLModel(df=df, hierarchy=actual_hierarchy, calculated_rows=[])

        calculator = BudgetVarianceCalculator(budget_model, actual_model)
        result = calculator.calculate(threshold_pct=10, threshold_abs=10000)

        revenue_account = result.get_income_variances()['children'][0]

        # Check all periods calculated
        assert '2024-01' in revenue_account['values']
        assert '2024-02' in revenue_account['values']
        assert '2024-03' in revenue_account['values']

        # Check variances for each period
        jan = revenue_account['values']['2024-01']
        assert jan['dollar_variance'] == 20000
        assert jan['pct_variance'] == 20.0
        assert jan['is_flagged'] is True  # Exceeds 10% threshold

        feb = revenue_account['values']['2024-02']
        assert feb['dollar_variance'] == -5000
        assert feb['pct_variance'] == pytest.approx(-4.545, rel=0.01)
        assert feb['is_flagged'] is False  # Below threshold

        mar = revenue_account['values']['2024-03']
        assert mar['dollar_variance'] == 10000
        assert mar['pct_variance'] == pytest.approx(8.333, rel=0.01)
        assert mar['is_flagged'] is False  # Below 10% threshold
