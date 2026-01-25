"""
Tests for ForecastBudgetVarianceCalculator - service for budget vs forecast variance analysis.

Covers:
- Period overlap detection (full, partial, no overlap)
- PLForecastModel value extraction (uses 'projected' not lower_bound/upper_bound)
- Multi-scenario selection (Expected default, fallback, calculate_all_scenarios)
- Variance calculations (dollar and percentage)
- Favorable/unfavorable determination (Income vs Expenses)
- Threshold flagging (percentage and absolute)
- Warning message generation (actionable recommendations)
- Edge cases (zero budget, empty overlapping periods)
"""
import pytest
import pandas as pd

from src.models import BudgetModel, PLForecastModel, VarianceModel, MultiScenarioForecastResult
from src.services import ForecastBudgetVarianceCalculator


@pytest.fixture
def budget_model_jan_dec():
    """BudgetModel with Jan-Dec periods for overlap testing."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'parent': True,
            'children': [
                {
                    'name': 'Revenue',
                    'values': {
                        'Jan': 50000, 'Feb': 50000, 'Mar': 50000,
                        'Apr': 51000, 'May': 51000, 'Jun': 51000,
                        'Jul': 52000, 'Aug': 52000, 'Sep': 52000,
                        'Oct': 53000, 'Nov': 53000, 'Dec': 53000
                    }
                }
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'parent': True,
            'children': [
                {
                    'name': 'Payroll',
                    'values': {
                        'Jan': 30000, 'Feb': 30000, 'Mar': 30000,
                        'Apr': 30000, 'May': 30000, 'Jun': 30000,
                        'Jul': 30000, 'Aug': 30000, 'Sep': 30000,
                        'Oct': 30000, 'Nov': 30000, 'Dec': 30000
                    }
                },
                {
                    'name': 'Rent',
                    'values': {
                        'Jan': 6000, 'Feb': 6000, 'Mar': 6000,
                        'Apr': 6000, 'May': 6000, 'Jun': 6000,
                        'Jul': 6000, 'Aug': 6000, 'Sep': 6000,
                        'Oct': 6000, 'Nov': 6000, 'Dec': 6000
                    }
                }
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Payroll', 'section': 'Expenses'},
        {'account_name': 'Rent', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def pl_forecast_apr_sep():
    """PLForecastModel with Apr-Sep periods (partial overlap with Jan-Dec budget)."""
    hierarchy = {
        'Income': [
            {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Revenue',
                        'projected': {
                            'Apr': 45000, 'May': 46000, 'Jun': 45000,
                            'Jul': 47000, 'Aug': 48000, 'Sep': 49000
                        },
                        'lower_bound': {
                            'Apr': 40000, 'May': 41000, 'Jun': 40000,
                            'Jul': 42000, 'Aug': 43000, 'Sep': 44000
                        },
                        'upper_bound': {
                            'Apr': 50000, 'May': 51000, 'Jun': 50000,
                            'Jul': 52000, 'Aug': 53000, 'Sep': 54000
                        }
                    }
                ]
            }
        ],
        'Expenses': [
            {
                'name': 'Expenses',
                'parent': True,
                'children': [
                    {
                        'name': 'Payroll',
                        'projected': {
                            'Apr': 35000, 'May': 35000, 'Jun': 35000,
                            'Jul': 35000, 'Aug': 35000, 'Sep': 35000
                        },
                        'lower_bound': {
                            'Apr': 33000, 'May': 33000, 'Jun': 33000,
                            'Jul': 33000, 'Aug': 33000, 'Sep': 33000
                        },
                        'upper_bound': {
                            'Apr': 37000, 'May': 37000, 'Jun': 37000,
                            'Jul': 37000, 'Aug': 37000, 'Sep': 37000
                        }
                    },
                    {
                        'name': 'Rent',
                        'projected': {
                            'Apr': 5000, 'May': 5000, 'Jun': 5000,
                            'Jul': 5000, 'Aug': 5000, 'Sep': 5000
                        },
                        'lower_bound': {
                            'Apr': 5000, 'May': 5000, 'Jun': 5000,
                            'Jul': 5000, 'Aug': 5000, 'Sep': 5000
                        },
                        'upper_bound': {
                            'Apr': 5000, 'May': 5000, 'Jun': 5000,
                            'Jul': 5000, 'Aug': 5000, 'Sep': 5000
                        }
                    }
                ]
            }
        ]
    }

    calculated_rows = {}
    metadata = {'confidence_level': 0.8, 'forecast_horizon': 6, 'excluded_periods': [], 'warnings': []}

    return PLForecastModel(hierarchy=hierarchy, calculated_rows=calculated_rows, metadata=metadata)


@pytest.fixture
def pl_forecast_jul_dec():
    """PLForecastModel with Jul-Dec periods (no overlap with Jan-Jun budget)."""
    hierarchy = {
        'Income': [
            {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Revenue',
                        'projected': {'Jul': 52000, 'Aug': 53000, 'Sep': 54000, 'Oct': 55000, 'Nov': 56000, 'Dec': 57000},
                        'lower_bound': {'Jul': 47000, 'Aug': 48000, 'Sep': 49000, 'Oct': 50000, 'Nov': 51000, 'Dec': 52000},
                        'upper_bound': {'Jul': 57000, 'Aug': 58000, 'Sep': 59000, 'Oct': 60000, 'Nov': 61000, 'Dec': 62000}
                    }
                ]
            }
        ],
        'Expenses': [
            {
                'name': 'Expenses',
                'parent': True,
                'children': [
                    {
                        'name': 'Payroll',
                        'projected': {'Jul': 30000, 'Aug': 30000, 'Sep': 30000, 'Oct': 30000, 'Nov': 30000, 'Dec': 30000},
                        'lower_bound': {'Jul': 28000, 'Aug': 28000, 'Sep': 28000, 'Oct': 28000, 'Nov': 28000, 'Dec': 28000},
                        'upper_bound': {'Jul': 32000, 'Aug': 32000, 'Sep': 32000, 'Oct': 32000, 'Nov': 32000, 'Dec': 32000}
                    }
                ]
            }
        ]
    }

    calculated_rows = {}
    metadata = {'confidence_level': 0.8, 'forecast_horizon': 6, 'excluded_periods': [], 'warnings': []}

    return PLForecastModel(hierarchy=hierarchy, calculated_rows=calculated_rows, metadata=metadata)


@pytest.fixture
def budget_model_jan_jun():
    """BudgetModel with Jan-Jun periods (for no overlap testing)."""
    hierarchy = {
        'Income': {
            'name': 'Income',
            'parent': True,
            'children': [
                {'name': 'Revenue', 'values': {'Jan': 50000, 'Feb': 50000, 'Mar': 50000, 'Apr': 50000, 'May': 50000, 'Jun': 50000}}
            ]
        },
        'Expenses': {
            'name': 'Expenses',
            'parent': True,
            'children': [
                {'name': 'Payroll', 'values': {'Jan': 30000, 'Feb': 30000, 'Mar': 30000, 'Apr': 30000, 'May': 30000, 'Jun': 30000}}
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Revenue', 'section': 'Income'},
        {'account_name': 'Payroll', 'section': 'Expenses'}
    ])

    return BudgetModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def multi_scenario_forecast_result(pl_forecast_apr_sep):
    """MultiScenarioForecastResult with Optimistic, Expected, Pessimistic scenarios."""
    # Create Expected scenario (uses pl_forecast_apr_sep)
    expected_forecast = pl_forecast_apr_sep

    # Create Optimistic scenario (higher revenue, lower expenses)
    optimistic_hierarchy = {
        'Income': [
            {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Revenue',
                        'projected': {'Apr': 50000, 'May': 51000, 'Jun': 50000, 'Jul': 52000, 'Aug': 53000, 'Sep': 54000},
                        'lower_bound': {'Apr': 45000, 'May': 46000, 'Jun': 45000, 'Jul': 47000, 'Aug': 48000, 'Sep': 49000},
                        'upper_bound': {'Apr': 55000, 'May': 56000, 'Jun': 55000, 'Jul': 57000, 'Aug': 58000, 'Sep': 59000}
                    }
                ]
            }
        ],
        'Expenses': [
            {
                'name': 'Expenses',
                'parent': True,
                'children': [
                    {
                        'name': 'Payroll',
                        'projected': {'Apr': 28000, 'May': 28000, 'Jun': 28000, 'Jul': 28000, 'Aug': 28000, 'Sep': 28000},
                        'lower_bound': {'Apr': 26000, 'May': 26000, 'Jun': 26000, 'Jul': 26000, 'Aug': 26000, 'Sep': 26000},
                        'upper_bound': {'Apr': 30000, 'May': 30000, 'Jun': 30000, 'Jul': 30000, 'Aug': 30000, 'Sep': 30000}
                    },
                    {
                        'name': 'Rent',
                        'projected': {'Apr': 5000, 'May': 5000, 'Jun': 5000, 'Jul': 5000, 'Aug': 5000, 'Sep': 5000},
                        'lower_bound': {'Apr': 5000, 'May': 5000, 'Jun': 5000, 'Jul': 5000, 'Aug': 5000, 'Sep': 5000},
                        'upper_bound': {'Apr': 5000, 'May': 5000, 'Jun': 5000, 'Jul': 5000, 'Aug': 5000, 'Sep': 5000}
                    }
                ]
            }
        ]
    }
    optimistic_forecast = PLForecastModel(
        hierarchy=optimistic_hierarchy,
        calculated_rows={},
        metadata={'confidence_level': 0.8, 'forecast_horizon': 6, 'excluded_periods': [], 'warnings': []}
    )

    # Create Pessimistic scenario (lower revenue, higher expenses)
    pessimistic_hierarchy = {
        'Income': [
            {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Revenue',
                        'projected': {'Apr': 40000, 'May': 41000, 'Jun': 40000, 'Jul': 42000, 'Aug': 43000, 'Sep': 44000},
                        'lower_bound': {'Apr': 35000, 'May': 36000, 'Jun': 35000, 'Jul': 37000, 'Aug': 38000, 'Sep': 39000},
                        'upper_bound': {'Apr': 45000, 'May': 46000, 'Jun': 45000, 'Jul': 47000, 'Aug': 48000, 'Sep': 49000}
                    }
                ]
            }
        ],
        'Expenses': [
            {
                'name': 'Expenses',
                'parent': True,
                'children': [
                    {
                        'name': 'Payroll',
                        'projected': {'Apr': 38000, 'May': 38000, 'Jun': 38000, 'Jul': 38000, 'Aug': 38000, 'Sep': 38000},
                        'lower_bound': {'Apr': 36000, 'May': 36000, 'Jun': 36000, 'Jul': 36000, 'Aug': 36000, 'Sep': 36000},
                        'upper_bound': {'Apr': 40000, 'May': 40000, 'Jun': 40000, 'Jul': 40000, 'Aug': 40000, 'Sep': 40000}
                    },
                    {
                        'name': 'Rent',
                        'projected': {'Apr': 5000, 'May': 5000, 'Jun': 5000, 'Jul': 5000, 'Aug': 5000, 'Sep': 5000},
                        'lower_bound': {'Apr': 5000, 'May': 5000, 'Jun': 5000, 'Jul': 5000, 'Aug': 5000, 'Sep': 5000},
                        'upper_bound': {'Apr': 5000, 'May': 5000, 'Jun': 5000, 'Jul': 5000, 'Aug': 5000, 'Sep': 5000}
                    }
                ]
            }
        ]
    }
    pessimistic_forecast = PLForecastModel(
        hierarchy=pessimistic_hierarchy,
        calculated_rows={},
        metadata={'confidence_level': 0.8, 'forecast_horizon': 6, 'excluded_periods': [], 'warnings': []}
    )

    # Create empty CashFlowForecastModel placeholder (not used in budget variance)
    from src.models.cash_flow_forecast_model import CashFlowForecastModel
    empty_cf = CashFlowForecastModel(df=pd.DataFrame(), hierarchy={}, calculated_rows={}, metadata={})

    scenario_forecasts = {
        'Optimistic': {'cash_flow_forecast': empty_cf, 'pl_forecast': optimistic_forecast},
        'Expected': {'cash_flow_forecast': empty_cf, 'pl_forecast': expected_forecast},
        'Pessimistic': {'cash_flow_forecast': empty_cf, 'pl_forecast': pessimistic_forecast}
    }

    return MultiScenarioForecastResult(scenario_forecasts=scenario_forecasts, forecast_horizon=6)


@pytest.fixture
def multi_scenario_no_expected(multi_scenario_forecast_result):
    """MultiScenarioForecastResult without Expected scenario (for fallback testing)."""
    # Remove Expected scenario
    scenario_forecasts = {
        'Optimistic': multi_scenario_forecast_result.get_scenario_forecast('Optimistic'),
        'Pessimistic': multi_scenario_forecast_result.get_scenario_forecast('Pessimistic')
    }
    return MultiScenarioForecastResult(scenario_forecasts=scenario_forecasts, forecast_horizon=6)


# Period overlap tests

def test_period_overlap_full_overlap(budget_model_jan_dec):
    """Budget and forecast cover identical periods - all periods should be in overlap."""
    # Create forecast with Jan-Dec (same as budget)
    hierarchy = {
        'Income': [
            {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Revenue',
                        'projected': {month: 50000 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
                        'lower_bound': {month: 45000 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
                        'upper_bound': {month: 55000 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
                    }
                ]
            }
        ],
        'Expenses': [
            {
                'name': 'Expenses',
                'parent': True,
                'children': [
                    {
                        'name': 'Payroll',
                        'projected': {month: 30000 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
                        'lower_bound': {month: 28000 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']},
                        'upper_bound': {month: 32000 for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}
                    }
                ]
            }
        ]
    }
    forecast = PLForecastModel(hierarchy=hierarchy, calculated_rows={}, metadata={'confidence_level': 0.8, 'forecast_horizon': 12, 'excluded_periods': [], 'warnings': []})

    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, forecast)
    result = calculator.calculate(threshold_pct=10.0)

    # All 12 months should have variance data
    revenue_variance = result.hierarchy['Income']['children'][0]
    assert len(revenue_variance['values']) == 12
    assert set(revenue_variance['values'].keys()) == {'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'}


def test_period_overlap_partial_overlap(budget_model_jan_dec, pl_forecast_apr_sep):
    """Forecast extends beyond budget period - only common months in overlap."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)

    # Only Apr-Sep should have variance data (6 months)
    revenue_variance = result.hierarchy['Income']['children'][0]
    assert len(revenue_variance['values']) == 6
    assert set(revenue_variance['values'].keys()) == {'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'}


def test_period_overlap_no_overlap(budget_model_jan_jun, pl_forecast_jul_dec):
    """Budget and forecast have completely different periods - empty overlap."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_jun, pl_forecast_jul_dec)
    result = calculator.calculate(threshold_pct=10.0)

    # No overlapping periods - empty variance
    assert result.hierarchy == {}
    assert result.calculated_rows == []


# PLForecastModel value extraction tests

def test_forecast_value_extraction_uses_projected(budget_model_jan_dec, pl_forecast_apr_sep):
    """PLForecastModel has three values (projected/lower_bound/upper_bound) - variance uses projected only."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)

    # Check Jun variance uses projected=45000 (not lower_bound=40000 or upper_bound=50000)
    revenue_variance = result.hierarchy['Income']['children'][0]
    jun_variance = revenue_variance['values']['Jun']

    # Budget for Jun is 51000, projected forecast is 45000
    assert jun_variance['budget_value'] == 51000
    assert jun_variance['actual_value'] == 45000  # Should use projected
    assert jun_variance['dollar_variance'] == -6000  # 45000 - 51000


# Variance calculation tests

def test_variance_calculation_income_below_budget(budget_model_jan_dec, pl_forecast_apr_sep):
    """Revenue forecast below budget - negative dollar variance, negative pct variance, unfavorable, flagged."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)

    # Jun: budget=51000, forecast=45000 -> variance=-6000, pct=-11.76%
    revenue_variance = result.hierarchy['Income']['children'][0]
    jun_variance = revenue_variance['values']['Jun']

    assert jun_variance['dollar_variance'] == -6000
    assert abs(jun_variance['pct_variance'] - (-11.76)) < 0.1  # ~-11.76%
    assert jun_variance['is_favorable'] is False  # Income below budget is unfavorable
    assert jun_variance['is_flagged'] is True  # Exceeds 10% threshold


def test_variance_calculation_expense_below_budget(budget_model_jan_dec, pl_forecast_apr_sep):
    """Expense forecast below budget - negative dollar variance, negative pct variance, favorable, flagged."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)

    # Rent Jun: budget=6000, forecast=5000 -> variance=-1000, pct=-16.67%
    expenses_section = result.hierarchy['Expenses']
    rent_variance = None
    for child in expenses_section['children']:
        if child['name'] == 'Rent':
            rent_variance = child
            break

    assert rent_variance is not None
    jun_variance = rent_variance['values']['Jun']

    assert jun_variance['dollar_variance'] == -1000
    assert abs(jun_variance['pct_variance'] - (-16.67)) < 0.1  # ~-16.67%
    assert jun_variance['is_favorable'] is True  # Expense below budget is favorable
    assert jun_variance['is_flagged'] is True  # Exceeds 10% threshold


# Multi-scenario selection tests

def test_multi_scenario_expected_default(budget_model_jan_dec, multi_scenario_forecast_result):
    """MultiScenarioForecastResult with Expected scenario - returns single VarianceModel for Expected."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, multi_scenario_forecast_result)
    result = calculator.calculate(threshold_pct=10.0, calculate_all_scenarios=False)

    # Should return single VarianceModel (not dict)
    assert isinstance(result, VarianceModel)
    assert not isinstance(result, dict)

    # Verify it used Expected scenario (revenue forecast for Jun should be 45000 from Expected)
    revenue_variance = result.hierarchy['Income']['children'][0]
    jun_variance = revenue_variance['values']['Jun']
    assert jun_variance['actual_value'] == 45000  # Expected scenario value


def test_multi_scenario_fallback_to_first(budget_model_jan_dec, multi_scenario_no_expected):
    """MultiScenarioForecastResult without Expected - falls back to first available scenario."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, multi_scenario_no_expected)
    result = calculator.calculate(threshold_pct=10.0, calculate_all_scenarios=False)

    # Should return single VarianceModel (not dict)
    assert isinstance(result, VarianceModel)

    # Should use first scenario (Optimistic, revenue Jun=50000)
    revenue_variance = result.hierarchy['Income']['children'][0]
    jun_variance = revenue_variance['values']['Jun']
    assert jun_variance['actual_value'] == 50000  # Optimistic scenario value


def test_multi_scenario_calculate_all(budget_model_jan_dec, multi_scenario_forecast_result):
    """calculate_all_scenarios=True - returns dict mapping scenario names to VarianceModels."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, multi_scenario_forecast_result)
    result = calculator.calculate(threshold_pct=10.0, calculate_all_scenarios=True)

    # Should return dict
    assert isinstance(result, dict)
    assert len(result) == 3
    assert set(result.keys()) == {'Optimistic', 'Expected', 'Pessimistic'}

    # Each should be VarianceModel
    assert isinstance(result['Optimistic'], VarianceModel)
    assert isinstance(result['Expected'], VarianceModel)
    assert isinstance(result['Pessimistic'], VarianceModel)

    # Verify different forecast values
    opt_revenue = result['Optimistic'].hierarchy['Income']['children'][0]['values']['Jun']['actual_value']
    exp_revenue = result['Expected'].hierarchy['Income']['children'][0]['values']['Jun']['actual_value']
    pess_revenue = result['Pessimistic'].hierarchy['Income']['children'][0]['values']['Jun']['actual_value']

    assert opt_revenue == 50000  # Optimistic
    assert exp_revenue == 45000  # Expected
    assert pess_revenue == 40000  # Pessimistic


# Warning message generation tests

def test_warning_message_income_below_budget(budget_model_jan_dec, pl_forecast_apr_sep):
    """Revenue forecast below budget - warning message with reforecasting recommendation."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)
    warnings = calculator.generate_warning_messages(result)

    # Should have warning for Revenue Jun (11.8% below budget)
    revenue_warnings = [w for w in warnings if 'Revenue' in w and 'Jun' in w]
    assert len(revenue_warnings) >= 1

    warning = revenue_warnings[0]
    assert 'Revenue forecast $45,000' in warning
    assert '11.8%' in warning
    assert 'below budget $51,000' in warning
    assert 'Jun' in warning
    assert 'reforecasting may be needed' in warning


def test_warning_message_expense_above_budget(budget_model_jan_dec, pl_forecast_apr_sep):
    """Expense forecast above budget - warning message with cost control recommendation."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)
    warnings = calculator.generate_warning_messages(result)

    # Payroll forecast is 35000 vs budget 30000 (16.7% above)
    payroll_warnings = [w for w in warnings if 'Payroll' in w]
    assert len(payroll_warnings) >= 1

    warning = payroll_warnings[0]
    assert 'Payroll' in warning
    assert '16.7%' in warning
    assert 'above' in warning
    assert 'cost control review recommended' in warning


def test_warning_message_expense_below_budget(budget_model_jan_dec, pl_forecast_apr_sep):
    """Expense forecast below budget - warning message with favorable tracking note."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)
    warnings = calculator.generate_warning_messages(result)

    # Rent forecast is 5000 vs budget 6000 (16.7% below)
    rent_warnings = [w for w in warnings if 'Rent' in w]
    assert len(rent_warnings) >= 1

    warning = rent_warnings[0]
    assert 'Rent' in warning
    assert '16.7%' in warning
    assert 'below' in warning
    assert 'spending tracking favorably to budget' in warning


def test_warning_message_formatting(budget_model_jan_dec, pl_forecast_apr_sep):
    """Warning messages use proper currency and percentage formatting."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)
    warnings = calculator.generate_warning_messages(result)

    # Check formatting
    for warning in warnings:
        # Should have currency formatting with comma separator
        assert '$' in warning
        # Should have percentage with decimal
        assert '%' in warning
        # Should have period name
        assert any(month in warning for month in ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'])


def test_warning_messages_multi_scenario(budget_model_jan_dec, multi_scenario_forecast_result):
    """calculate_all_scenarios=True - returns dict of scenario names to warning lists."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, multi_scenario_forecast_result)
    result = calculator.calculate(threshold_pct=10.0, calculate_all_scenarios=True)
    warnings = calculator.generate_warning_messages(result)

    # Should return dict
    assert isinstance(warnings, dict)
    assert set(warnings.keys()) == {'Optimistic', 'Expected', 'Pessimistic'}

    # Each should be list of warnings
    assert isinstance(warnings['Optimistic'], list)
    assert isinstance(warnings['Expected'], list)
    assert isinstance(warnings['Pessimistic'], list)


# Threshold flagging tests

def test_threshold_flagging_exceeds_percentage(budget_model_jan_dec, pl_forecast_apr_sep):
    """Variance exceeds threshold_pct - is_flagged=True."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)

    # Revenue Jun: -11.76% (exceeds 10%)
    revenue_variance = result.hierarchy['Income']['children'][0]
    jun_variance = revenue_variance['values']['Jun']
    assert jun_variance['is_flagged'] is True


def test_threshold_flagging_below_threshold(budget_model_jan_dec):
    """Variance below threshold_pct - is_flagged=False."""
    # Create forecast with small variance (5% below budget)
    hierarchy = {
        'Income': [
            {
                'name': 'Income',
                'parent': True,
                'children': [
                    {
                        'name': 'Revenue',
                        'projected': {'Apr': 48450},  # Budget is 51000, variance is -2550 = -5%
                        'lower_bound': {'Apr': 45000},
                        'upper_bound': {'Apr': 52000}
                    }
                ]
            }
        ],
        'Expenses': [
            {
                'name': 'Expenses',
                'parent': True,
                'children': [
                    {
                        'name': 'Payroll',
                        'projected': {'Apr': 30000},
                        'lower_bound': {'Apr': 28000},
                        'upper_bound': {'Apr': 32000}
                    }
                ]
            }
        ]
    }
    forecast = PLForecastModel(hierarchy=hierarchy, calculated_rows={}, metadata={'confidence_level': 0.8, 'forecast_horizon': 1, 'excluded_periods': [], 'warnings': []})

    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, forecast)
    result = calculator.calculate(threshold_pct=10.0, threshold_abs=999999)

    # Revenue Apr: -5% (below 10% threshold)
    revenue_variance = result.hierarchy['Income']['children'][0]
    apr_variance = revenue_variance['values']['Apr']
    assert apr_variance['is_flagged'] is False


# Edge case tests

def test_single_pl_forecast_model(budget_model_jan_dec, pl_forecast_apr_sep):
    """Single PLForecastModel (not MultiScenarioForecastResult) - returns single VarianceModel."""
    calculator = ForecastBudgetVarianceCalculator(budget_model_jan_dec, pl_forecast_apr_sep)
    result = calculator.calculate(threshold_pct=10.0)

    # Should return single VarianceModel
    assert isinstance(result, VarianceModel)
    assert not isinstance(result, dict)
