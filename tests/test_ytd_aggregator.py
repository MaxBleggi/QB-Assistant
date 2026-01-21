"""
Tests for YTDAggregator - service for year-to-date budget and actual aggregation.

Covers:
- Calendar fiscal year (fiscal_year_start_month=1)
- Non-calendar fiscal year (fiscal_year_start_month=7)
- Cumulative budget and actual accumulation
- Cumulative variance calculations
- YTD percentage of budget
- Partial-year scenarios
- Section summaries
- Edge cases (zero budget, negative values, single period)
"""
import pytest
import pandas as pd

from src.models import BudgetModel, PLModel, YTDModel
from src.services import YTDAggregator


@pytest.fixture
def calendar_budget_model():
    """BudgetModel with calendar fiscal year periods (Jan-Mar)."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Product Revenue',
                    'values': {
                        '2024-01': 100000,
                        '2024-02': 100000,
                        '2024-03': 100000
                    }
                },
                {
                    'name': 'Service Revenue',
                    'values': {
                        '2024-01': 50000,
                        '2024-02': 50000,
                        '2024-03': 50000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Marketing',
                    'values': {
                        '2024-01': 30000,
                        '2024-02': 30000,
                        '2024-03': 30000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Product Revenue', 'section': 'Income'},
        {'account_name': 'Service Revenue', 'section': 'Income'},
        {'account_name': 'Marketing', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def calendar_pl_model():
    """PLModel with actual data for calendar fiscal year periods."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Product Revenue',
                    'values': {
                        '2024-01': 90000,  # -10k variance
                        '2024-02': 110000,  # +10k variance
                        '2024-03': 95000   # -5k variance
                    }
                },
                {
                    'name': 'Service Revenue',
                    'values': {
                        '2024-01': 50000,
                        '2024-02': 50000,
                        '2024-03': 50000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Marketing',
                    'values': {
                        '2024-01': 28000,  # -2k variance (favorable)
                        '2024-02': 32000,  # +2k variance (unfavorable)
                        '2024-03': 30000   # 0 variance
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Product Revenue', 'section': 'Income'},
        {'account_name': 'Service Revenue', 'section': 'Income'},
        {'account_name': 'Marketing', 'section': 'Expenses'}
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def non_calendar_budget_model():
    """BudgetModel with non-calendar fiscal year periods (Jul-Sep)."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Revenue',
                    'values': {
                        '2024-07': 100000,
                        '2024-08': 100000,
                        '2024-09': 100000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Costs',
                    'values': {
                        '2024-07': 80000,
                        '2024-08': 80000,
                        '2024-09': 80000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def non_calendar_pl_model():
    """PLModel with actual data for non-calendar fiscal year periods."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Revenue',
                    'values': {
                        '2024-07': 105000,
                        '2024-08': 110000,
                        '2024-09': 108000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Costs',
                    'values': {
                        '2024-07': 75000,
                        '2024-08': 80000,
                        '2024-09': 85000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def partial_year_budget_model():
    """BudgetModel with partial-year data (Mar-May)."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Revenue',
                    'values': {
                        '2024-03': 100000,
                        '2024-04': 100000,
                        '2024-05': 100000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Costs',
                    'values': {
                        '2024-03': 50000,
                        '2024-04': 50000,
                        '2024-05': 50000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def partial_year_pl_model():
    """PLModel with partial-year actual data."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'Revenue',
                    'values': {
                        '2024-03': 95000,
                        '2024-04': 105000,
                        '2024-05': 100000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Costs',
                    'values': {
                        '2024-03': 48000,
                        '2024-04': 52000,
                        '2024-05': 50000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def zero_budget_model():
    """BudgetModel with zero budget for testing edge case."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'New Product',
                    'values': {
                        '2024-01': 0,
                        '2024-02': 0
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Costs',
                    'values': {
                        '2024-01': 10000,
                        '2024-02': 10000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'New Product', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def zero_budget_pl_model():
    """PLModel with actual values for zero budget scenario."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'children': [
                {
                    'name': 'New Product',
                    'values': {
                        '2024-01': 5000,
                        '2024-02': 10000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'children': [
                {
                    'name': 'Costs',
                    'values': {
                        '2024-01': 8000,
                        '2024-02': 12000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'New Product', 'section': 'Income'},
        {'account_name': 'Costs', 'section': 'Expenses'}
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


class TestYTDAggregatorCalendarFiscalYear:
    """Tests for calendar fiscal year (fiscal_year_start_month=1)."""

    def test_calendar_fiscal_year_period_order(self, calendar_budget_model, calendar_pl_model):
        """Test calendar fiscal year processes periods in chronological order."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate(fiscal_year_start_month=1)

        assert isinstance(ytd_model, YTDModel)
        assert ytd_model.fiscal_year_start_month == 1

        # Check periods are in chronological order
        income_section = ytd_model.get_income_ytd()
        product_revenue = income_section['children'][0]
        periods = list(product_revenue['values'].keys())
        assert periods == ['2024-01', '2024-02', '2024-03']

    def test_calendar_cumulative_accumulation(self, calendar_budget_model, calendar_pl_model):
        """Test budget and actual values accumulate correctly across periods."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate(fiscal_year_start_month=1)

        # Get Product Revenue account
        income_section = ytd_model.get_income_ytd()
        product_revenue = income_section['children'][0]
        values = product_revenue['values']

        # Check cumulative budget accumulation
        assert values['2024-01']['cumulative_budget'] == 100000
        assert values['2024-02']['cumulative_budget'] == 200000
        assert values['2024-03']['cumulative_budget'] == 300000

        # Check cumulative actual accumulation
        assert values['2024-01']['cumulative_actual'] == 90000
        assert values['2024-02']['cumulative_actual'] == 200000  # 90k + 110k
        assert values['2024-03']['cumulative_actual'] == 295000  # 90k + 110k + 95k


class TestYTDAggregatorNonCalendarFiscalYear:
    """Tests for non-calendar fiscal year (fiscal_year_start_month=7)."""

    def test_non_calendar_fiscal_year_period_order(self, non_calendar_budget_model, non_calendar_pl_model):
        """Test non-calendar fiscal year reorders periods correctly."""
        aggregator = YTDAggregator(non_calendar_budget_model, non_calendar_pl_model)
        ytd_model = aggregator.calculate(fiscal_year_start_month=7)

        assert ytd_model.fiscal_year_start_month == 7
        assert ytd_model.aggregation_start_period == '2024-07'

        # Check periods are in fiscal year order (Jul, Aug, Sep)
        income_section = ytd_model.get_income_ytd()
        revenue = income_section['children'][0]
        periods = list(revenue['values'].keys())
        assert periods == ['2024-07', '2024-08', '2024-09']

    def test_non_calendar_cumulative_accumulation(self, non_calendar_budget_model, non_calendar_pl_model):
        """Test cumulative accumulation works correctly for non-calendar fiscal year."""
        aggregator = YTDAggregator(non_calendar_budget_model, non_calendar_pl_model)
        ytd_model = aggregator.calculate(fiscal_year_start_month=7)

        # Get Revenue account
        income_section = ytd_model.get_income_ytd()
        revenue = income_section['children'][0]
        values = revenue['values']

        # Check cumulative budget
        assert values['2024-07']['cumulative_budget'] == 100000
        assert values['2024-08']['cumulative_budget'] == 200000
        assert values['2024-09']['cumulative_budget'] == 300000

        # Check cumulative actual
        assert values['2024-07']['cumulative_actual'] == 105000
        assert values['2024-08']['cumulative_actual'] == 215000
        assert values['2024-09']['cumulative_actual'] == 323000


class TestYTDAggregatorVarianceCalculations:
    """Tests for variance calculation logic."""

    def test_cumulative_variance_computation(self, calendar_budget_model, calendar_pl_model):
        """Test cumulative_dollar_variance = cumulative_actual - cumulative_budget."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        # Get Product Revenue account
        income_section = ytd_model.get_income_ytd()
        product_revenue = income_section['children'][0]
        values = product_revenue['values']

        # Period 1: actual=90k, budget=100k, variance=-10k
        assert values['2024-01']['cumulative_dollar_variance'] == -10000

        # Period 2: actual=200k, budget=200k, variance=0
        assert values['2024-02']['cumulative_dollar_variance'] == 0

        # Period 3: actual=295k, budget=300k, variance=-5k
        assert values['2024-03']['cumulative_dollar_variance'] == -5000

    def test_cumulative_percentage_variance(self, calendar_budget_model, calendar_pl_model):
        """Test cumulative_pct_variance = (cumulative_dollar_variance / cumulative_budget * 100)."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        # Get Product Revenue account
        income_section = ytd_model.get_income_ytd()
        product_revenue = income_section['children'][0]
        values = product_revenue['values']

        # Period 1: -10k / 100k * 100 = -10%
        assert values['2024-01']['cumulative_pct_variance'] == -10.0

        # Period 2: 0 / 200k * 100 = 0%
        assert values['2024-02']['cumulative_pct_variance'] == 0.0

        # Period 3: -5k / 300k * 100 = -1.67%
        assert round(values['2024-03']['cumulative_pct_variance'], 2) == -1.67

    def test_ytd_pct_of_budget(self, calendar_budget_model, calendar_pl_model):
        """Test ytd_pct_of_budget = (cumulative_actual / cumulative_budget * 100)."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        # Get Product Revenue account
        income_section = ytd_model.get_income_ytd()
        product_revenue = income_section['children'][0]
        values = product_revenue['values']

        # Period 1: 90k / 100k * 100 = 90%
        assert values['2024-01']['ytd_pct_of_budget'] == 90.0

        # Period 2: 200k / 200k * 100 = 100%
        assert values['2024-02']['ytd_pct_of_budget'] == 100.0

        # Period 3: 295k / 300k * 100 = 98.33%
        assert round(values['2024-03']['ytd_pct_of_budget'], 2) == 98.33

    def test_favorable_unfavorable_income(self, calendar_budget_model, calendar_pl_model):
        """Test favorable/unfavorable logic for Income section."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        income_section = ytd_model.get_income_ytd()
        product_revenue = income_section['children'][0]
        values = product_revenue['values']

        # Period 1: actual < budget, unfavorable for Income
        assert values['2024-01']['is_favorable'] is False

        # Period 2: actual = budget, not favorable (variance is 0, not > 0)
        assert values['2024-02']['is_favorable'] is False

        # Period 3: actual < budget, unfavorable for Income
        assert values['2024-03']['is_favorable'] is False

    def test_favorable_unfavorable_expenses(self, calendar_budget_model, calendar_pl_model):
        """Test favorable/unfavorable logic for Expenses section."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        expenses_section = ytd_model.get_expenses_ytd()
        marketing = expenses_section['children'][0]
        values = marketing['values']

        # Period 1: actual < budget, favorable for Expenses
        assert values['2024-01']['is_favorable'] is True

        # Period 2: actual = budget (cumulative: 60k vs 60k), not favorable
        assert values['2024-02']['is_favorable'] is False

        # Period 3: actual = budget (cumulative: 90k vs 90k), not favorable
        assert values['2024-03']['is_favorable'] is False


class TestYTDAggregatorSectionSummaries:
    """Tests for section-level summary calculations."""

    def test_section_summaries_in_calculated_rows(self, calendar_budget_model, calendar_pl_model):
        """Test section-level summaries computed correctly in calculated_rows."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        calculated_rows = ytd_model.calculated_rows

        # Check income section summary exists
        assert 'income' in calculated_rows
        income_summary = calculated_rows['income']

        # Period 1 totals: Product (100k) + Service (50k) = 150k budget
        assert income_summary['2024-01']['cumulative_budget'] == 150000
        # Period 1 totals: Product (90k) + Service (50k) = 140k actual
        assert income_summary['2024-01']['cumulative_actual'] == 140000
        # Period 1 variance: -10k
        assert income_summary['2024-01']['cumulative_dollar_variance'] == -10000

        # Check expenses section summary exists
        assert 'expenses' in calculated_rows
        expenses_summary = calculated_rows['expenses']

        # Period 1 totals: Marketing (30k budget, 28k actual)
        assert expenses_summary['2024-01']['cumulative_budget'] == 30000
        assert expenses_summary['2024-01']['cumulative_actual'] == 28000


class TestYTDAggregatorPartialYear:
    """Tests for partial-year scenarios."""

    def test_partial_year_aggregation_start(self, partial_year_budget_model, partial_year_pl_model):
        """Test partial-year scenario aggregates from earliest available period."""
        aggregator = YTDAggregator(partial_year_budget_model, partial_year_pl_model)
        ytd_model = aggregator.calculate(fiscal_year_start_month=1)

        # Should start from March (earliest available), not January
        assert ytd_model.aggregation_start_period == '2024-03'

        # Check periods
        income_section = ytd_model.get_income_ytd()
        revenue = income_section['children'][0]
        periods = list(revenue['values'].keys())
        assert periods == ['2024-03', '2024-04', '2024-05']

        # Check accumulation starts from March
        values = revenue['values']
        assert values['2024-03']['cumulative_budget'] == 100000
        assert values['2024-04']['cumulative_budget'] == 200000
        assert values['2024-05']['cumulative_budget'] == 300000


class TestYTDAggregatorEdgeCases:
    """Tests for edge cases."""

    def test_zero_budget_handling(self, zero_budget_model, zero_budget_pl_model):
        """Test zero budget handled correctly (avoid division by zero)."""
        aggregator = YTDAggregator(zero_budget_model, zero_budget_pl_model)
        ytd_model = aggregator.calculate()

        income_section = ytd_model.get_income_ytd()
        new_product = income_section['children'][0]
        values = new_product['values']

        # Period 1: budget=0, actual=5000
        assert values['2024-01']['cumulative_budget'] == 0
        assert values['2024-01']['cumulative_actual'] == 5000
        assert values['2024-01']['cumulative_pct_variance'] == 0.0  # Avoid div by zero
        assert values['2024-01']['ytd_pct_of_budget'] == 0.0  # Avoid div by zero

    def test_single_period(self):
        """Test aggregator with single period."""
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
                    {'name': 'Costs', 'values': {'2024-01': 50000}}
                ]
            }
        }

        df = pd.DataFrame([
            {'account_name': 'Revenue', 'section': 'Income'},
            {'account_name': 'Costs', 'section': 'Expenses'}
        ])

        budget_model = BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])
        pl_model = PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])

        aggregator = YTDAggregator(budget_model, pl_model)
        ytd_model = aggregator.calculate()

        # Should work with single period
        income_section = ytd_model.get_income_ytd()
        revenue = income_section['children'][0]
        assert '2024-01' in revenue['values']
        assert revenue['values']['2024-01']['cumulative_budget'] == 100000

    def test_negative_values(self):
        """Test aggregator with negative values."""
        hierarchy = {
            'Income': {
                'name': 'Income',
                'children': [
                    {
                        'name': 'Revenue',
                        'values': {
                            '2024-01': 100000,
                            '2024-02': -20000  # Negative value (refund/correction)
                        }
                    }
                ]
            },
            'Expenses': {
                'name': 'Expenses',
                'children': [
                    {'name': 'Costs', 'values': {'2024-01': 50000, '2024-02': 50000}}
                ]
            }
        }

        df = pd.DataFrame([
            {'account_name': 'Revenue', 'section': 'Income'},
            {'account_name': 'Costs', 'section': 'Expenses'}
        ])

        budget_model = BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])
        pl_model = PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])

        aggregator = YTDAggregator(budget_model, pl_model)
        ytd_model = aggregator.calculate()

        # Check cumulative handles negative values
        income_section = ytd_model.get_income_ytd()
        revenue = income_section['children'][0]
        values = revenue['values']

        assert values['2024-01']['cumulative_actual'] == 100000
        assert values['2024-02']['cumulative_actual'] == 80000  # 100k + (-20k)


class TestYTDAggregatorReturnsYTDModel:
    """Tests for YTDModel return value."""

    def test_returns_ytd_model_instance(self, calendar_budget_model, calendar_pl_model):
        """Test calculate() returns YTDModel instance with correct structure."""
        aggregator = YTDAggregator(calendar_budget_model, calendar_pl_model)
        ytd_model = aggregator.calculate()

        # Check return type
        assert isinstance(ytd_model, YTDModel)

        # Check hierarchy exists
        assert ytd_model.hierarchy is not None
        assert 'Income' in ytd_model.hierarchy
        assert 'Expenses' in ytd_model.hierarchy

        # Check calculated_rows exists
        assert ytd_model.calculated_rows is not None

        # Check metadata
        assert ytd_model.fiscal_year_start_month == 1
        assert ytd_model.aggregation_start_period == '2024-01'

        # Check DataFrame exists
        assert ytd_model._df is not None
