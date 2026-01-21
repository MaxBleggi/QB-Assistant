"""
Unit and integration tests for HistoricalDataParser.

Tests parser initialization, PLParser composition, account mapping validation,
data completeness validation, warning generation, and real file integration.
"""
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest

from src.loaders import FileLoader
from src.parsers import HistoricalDataParser
from src.parsers.pl_parser import PLParser
from src.models import PLModel


@pytest.fixture
def file_loader():
    """Create FileLoader instance for tests."""
    return FileLoader()


@pytest.fixture
def historical_parser(file_loader):
    """Create HistoricalDataParser instance for tests."""
    return HistoricalDataParser(file_loader)


@pytest.fixture
def mock_pl_model_12_periods():
    """
    Create mock PLModel with 12 periods and complete data.

    Simulates successful parse of historical file with all 12 months.
    """
    hierarchy = {
        'Income': {
            'children': [
                {'name': 'Design income', 'values': {
                    'Nov 2024': 100.0, 'Dec 2024': 110.0, 'Jan 2025': 120.0,
                    'Feb 2025': 130.0, 'Mar 2025': 140.0, 'Apr 2025': 150.0,
                    'May 2025': 160.0, 'Jun 2025': 170.0, 'Jul 2025': 180.0,
                    'Aug 2025': 190.0, 'Sep 2025': 200.0, 'Oct 2025': 210.0
                }},
                {'name': 'Landscaping Services', 'parent': True, 'children': [
                    {'name': 'Job Materials', 'parent': True, 'children': [
                        {'name': 'Plants and Soil', 'values': {
                            'Nov 2024': 200.0, 'Dec 2024': 220.0, 'Jan 2025': 240.0,
                            'Feb 2025': 260.0, 'Mar 2025': 280.0, 'Apr 2025': 300.0,
                            'May 2025': 320.0, 'Jun 2025': 340.0, 'Jul 2025': 360.0,
                            'Aug 2025': 380.0, 'Sep 2025': 400.0, 'Oct 2025': 420.0
                        }}
                    ], 'total': {
                        'Nov 2024': 200.0, 'Dec 2024': 220.0, 'Jan 2025': 240.0,
                        'Feb 2025': 260.0, 'Mar 2025': 280.0, 'Apr 2025': 300.0,
                        'May 2025': 320.0, 'Jun 2025': 340.0, 'Jul 2025': 360.0,
                        'Aug 2025': 380.0, 'Sep 2025': 400.0, 'Oct 2025': 420.0
                    }}
                ], 'total': None}
            ]
        },
        'Cost of Goods Sold': {
            'children': [
                {'name': 'Cost of Goods Sold', 'values': {
                    'Nov 2024': 50.0, 'Dec 2024': 55.0, 'Jan 2025': 60.0,
                    'Feb 2025': 65.0, 'Mar 2025': 70.0, 'Apr 2025': 75.0,
                    'May 2025': 80.0, 'Jun 2025': 85.0, 'Jul 2025': 90.0,
                    'Aug 2025': 95.0, 'Sep 2025': 100.0, 'Oct 2025': 105.0
                }}
            ]
        },
        'Expenses': {
            'children': [
                {'name': 'Advertising', 'values': {
                    'Nov 2024': 25.0, 'Dec 2024': 27.5, 'Jan 2025': 30.0,
                    'Feb 2025': 32.5, 'Mar 2025': 35.0, 'Apr 2025': 37.5,
                    'May 2025': 40.0, 'Jun 2025': 42.5, 'Jul 2025': 45.0,
                    'Aug 2025': 47.5, 'Sep 2025': 50.0, 'Oct 2025': 52.5
                }}
            ]
        }
    }

    calculated_rows = [
        {'account_name': 'Gross Profit', 'values': {
            'Nov 2024': 250.0, 'Dec 2024': 275.0, 'Jan 2025': 300.0,
            'Feb 2025': 325.0, 'Mar 2025': 350.0, 'Apr 2025': 375.0,
            'May 2025': 400.0, 'Jun 2025': 425.0, 'Jul 2025': 450.0,
            'Aug 2025': 475.0, 'Sep 2025': 500.0, 'Oct 2025': 525.0
        }},
        {'account_name': 'Net Income', 'values': {
            'Nov 2024': 225.0, 'Dec 2024': 247.5, 'Jan 2025': 270.0,
            'Feb 2025': 292.5, 'Mar 2025': 315.0, 'Apr 2025': 337.5,
            'May 2025': 360.0, 'Jun 2025': 382.5, 'Jul 2025': 405.0,
            'Aug 2025': 427.5, 'Sep 2025': 450.0, 'Oct 2025': 472.5
        }}
    ]

    df = pd.DataFrame([
        {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
        {'account_name': 'Design income', 'values': hierarchy['Income']['children'][0]['values'], 'row_type': 'child'},
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=calculated_rows)


@pytest.fixture
def mock_pl_model_10_periods():
    """Create mock PLModel with only 10 periods (incomplete)."""
    hierarchy = {
        'Income': {
            'children': [
                {'name': 'Design income', 'values': {
                    'Nov 2024': 100.0, 'Dec 2024': 110.0, 'Jan 2025': 120.0,
                    'Feb 2025': 130.0, 'Mar 2025': 140.0, 'Apr 2025': 150.0,
                    'May 2025': 160.0, 'Jun 2025': 170.0, 'Jul 2025': 180.0,
                    'Aug 2025': 190.0  # Only 10 periods
                }}
            ]
        },
        'Expenses': {
            'children': []
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def mock_pl_model_sparse():
    """Create mock PLModel with sparse account data."""
    hierarchy = {
        'Income': {
            'children': [
                {'name': 'Design income', 'values': {
                    'Nov 2024': 100.0, 'Dec 2024': 110.0, 'Jan 2025': 120.0,
                    'Feb 2025': 130.0, 'Mar 2025': 140.0, 'Apr 2025': 150.0,
                    'May 2025': 160.0, 'Jun 2025': 170.0, 'Jul 2025': 180.0,
                    'Aug 2025': 190.0, 'Sep 2025': 200.0, 'Oct 2025': 210.0
                }},
                {'name': 'Consulting', 'values': {
                    'Nov 2024': 300.0, 'Dec 2024': 310.0  # Only 2 periods - sparse
                }}
            ]
        },
        'Expenses': {
            'children': []
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Income', 'values': {}, 'row_type': 'section'},
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


@pytest.fixture
def mock_pl_model_missing_section():
    """Create mock PLModel missing Income section."""
    hierarchy = {
        'Expenses': {
            'children': [
                {'name': 'Advertising', 'values': {
                    'Nov 2024': 25.0, 'Dec 2024': 27.5, 'Jan 2025': 30.0,
                    'Feb 2025': 32.5, 'Mar 2025': 35.0, 'Apr 2025': 37.5,
                    'May 2025': 40.0, 'Jun 2025': 42.5, 'Jul 2025': 45.0,
                    'Aug 2025': 47.5, 'Sep 2025': 50.0, 'Oct 2025': 52.5
                }}
            ]
        }
    }

    df = pd.DataFrame([
        {'account_name': 'Expenses', 'values': {}, 'row_type': 'section'},
    ])

    return PLModel(df=df, hierarchy=hierarchy, calculated_rows=[])


# Unit Tests

def test_historical_parser_init(file_loader):
    """Test HistoricalDataParser instantiates with FileLoader."""
    parser = HistoricalDataParser(file_loader)
    assert parser.file_loader is file_loader
    assert isinstance(parser._pl_parser, PLParser)
    assert parser._pl_parser.file_loader is file_loader


@patch('src.parsers.historical_data_parser.PLParser')
def test_parse_returns_pl_model(mock_pl_parser_class, historical_parser, mock_pl_model_12_periods):
    """Test parse() returns PLModel with correct period count."""
    # Setup mock
    mock_pl_parser_instance = Mock()
    mock_pl_parser_instance.parse.return_value = mock_pl_model_12_periods
    historical_parser._pl_parser = mock_pl_parser_instance

    # Parse file
    result = historical_parser.parse('/path/to/historic.csv')

    # Verify
    assert isinstance(result, PLModel)
    assert len(result.get_periods()) == 12
    mock_pl_parser_instance.parse.assert_called_once_with('/path/to/historic.csv')


def test_validate_account_mapping_all_matched(historical_parser, mock_pl_model_12_periods):
    """Test account mapping with all accounts matched."""
    current_accounts = ['Design income', 'Plants and Soil', 'Cost of Goods Sold', 'Advertising']

    result = historical_parser.validate_account_mapping(current_accounts, mock_pl_model_12_periods)

    assert set(result['matched_accounts']) == set(current_accounts)
    assert result['missing_in_historical'] == []
    assert result['extra_in_historical'] == []


def test_validate_account_mapping_case_insensitive(historical_parser, mock_pl_model_12_periods):
    """Test account mapping handles case differences."""
    current_accounts = ['DESIGN INCOME', 'plants and soil']

    result = historical_parser.validate_account_mapping(current_accounts, mock_pl_model_12_periods)

    # Should match despite case differences
    assert len(result['matched_accounts']) == 2
    assert 'DESIGN INCOME' in result['matched_accounts']
    assert 'plants and soil' in result['matched_accounts']


def test_validate_account_mapping_missing_accounts(historical_parser, mock_pl_model_12_periods, caplog):
    """Test account mapping detects missing accounts and logs warning."""
    current_accounts = ['Design income', 'Marketing']  # Marketing not in historical

    result = historical_parser.validate_account_mapping(current_accounts, mock_pl_model_12_periods)

    assert result['matched_accounts'] == ['Design income']
    assert result['missing_in_historical'] == ['Marketing']
    assert 'Marketing' in caplog.text
    assert 'missing in historical data' in caplog.text


def test_validate_account_mapping_extra_accounts(historical_parser, mock_pl_model_12_periods, caplog):
    """Test account mapping detects extra accounts in historical data."""
    current_accounts = ['Design income']  # Historical has more accounts

    result = historical_parser.validate_account_mapping(current_accounts, mock_pl_model_12_periods)

    assert result['matched_accounts'] == ['Design income']
    assert len(result['extra_in_historical']) > 0
    assert 'Plants and Soil' in result['extra_in_historical']


def test_validate_completeness_full_data(historical_parser, mock_pl_model_12_periods):
    """Test completeness validation passes with complete data."""
    warnings = historical_parser.validate_completeness(mock_pl_model_12_periods)

    assert warnings == []


def test_validate_completeness_insufficient_periods(historical_parser, mock_pl_model_10_periods):
    """Test completeness validation warns on <12 periods."""
    warnings = historical_parser.validate_completeness(mock_pl_model_10_periods)

    assert len(warnings) > 0
    assert any('Insufficient historical periods' in w for w in warnings)
    assert any('found 10 months' in w for w in warnings)


def test_validate_completeness_sparse_account(historical_parser, mock_pl_model_sparse):
    """Test completeness validation warns on sparse account values."""
    warnings = historical_parser.validate_completeness(mock_pl_model_sparse)

    assert len(warnings) > 0
    assert any('Sparse account data' in w for w in warnings)
    assert any('Consulting' in w for w in warnings)


def test_validate_completeness_missing_section(historical_parser, mock_pl_model_missing_section):
    """Test completeness validation warns on missing key section."""
    warnings = historical_parser.validate_completeness(mock_pl_model_missing_section)

    assert len(warnings) > 0
    assert any('Missing key sections' in w for w in warnings)
    assert any('Income' in w for w in warnings)


@patch('src.parsers.historical_data_parser.PLParser')
def test_parse_runs_validation(mock_pl_parser_class, historical_parser, mock_pl_model_12_periods, caplog):
    """Test parse() automatically calls validate_completeness."""
    # Setup mock
    mock_pl_parser_instance = Mock()
    mock_pl_parser_instance.parse.return_value = mock_pl_model_12_periods
    historical_parser._pl_parser = mock_pl_parser_instance

    # Parse file
    result = historical_parser.parse('/path/to/historic.csv')

    # Verify validation ran (check log output)
    assert 'Historical data validation complete' in caplog.text


@patch('src.parsers.historical_data_parser.PLParser')
def test_parse_returns_model_with_warnings(
    mock_pl_parser_class,
    historical_parser,
    mock_pl_model_10_periods,
    caplog
):
    """Test parse() returns PLModel even with validation warnings."""
    # Setup mock with incomplete model
    mock_pl_parser_instance = Mock()
    mock_pl_parser_instance.parse.return_value = mock_pl_model_10_periods
    historical_parser._pl_parser = mock_pl_parser_instance

    # Parse file
    result = historical_parser.parse('/path/to/historic.csv')

    # Verify model returned despite warnings
    assert isinstance(result, PLModel)
    assert 'warning(s) logged' in caplog.text
    assert 'Insufficient historical periods' in caplog.text


def test_module_export():
    """Test HistoricalDataParser importable from parsers module."""
    from src.parsers import HistoricalDataParser as ImportedParser

    assert ImportedParser is HistoricalDataParser


def test_extract_account_names(historical_parser, mock_pl_model_12_periods):
    """Test _extract_account_names correctly walks hierarchy."""
    accounts = historical_parser._extract_account_names(mock_pl_model_12_periods.hierarchy)

    # Should find all named accounts (not sections)
    assert 'Design income' in accounts
    assert 'Plants and Soil' in accounts
    assert 'Cost of Goods Sold' in accounts
    assert 'Advertising' in accounts
    # Parent accounts should be included
    assert 'Landscaping Services' in accounts
    assert 'Job Materials' in accounts


def test_check_sparse_accounts(historical_parser, mock_pl_model_sparse):
    """Test _check_sparse_accounts identifies accounts with missing periods."""
    sparse = historical_parser._check_sparse_accounts(mock_pl_model_sparse.hierarchy, 12)

    # 'Consulting' has only 2 periods, should be flagged
    assert 'Consulting' in sparse
    # 'Design income' has 12 periods, should not be flagged
    assert 'Design income' not in sparse


# Integration Test

def test_parse_real_historical_file(file_loader):
    """
    Integration test: Parse real historic_profit_loss.csv file.

    Tests end-to-end parsing with actual file format and data.
    Verifies 12 periods present, key sections exist, no validation warnings.
    """
    # Path to real historical data file
    file_path = Path('/home/max/projects/QB-Assistant/data/historic_profit_loss.csv')

    # Skip if file doesn't exist (CI environment)
    if not file_path.exists():
        pytest.skip(f"Test data file not found: {file_path}")

    # Create parser and parse file
    parser = HistoricalDataParser(file_loader)
    result = parser.parse(file_path)

    # Verify result is PLModel
    assert isinstance(result, PLModel)

    # Verify 12 periods present
    periods = result.get_periods()
    assert len(periods) == 12, f"Expected 12 periods, got {len(periods)}: {periods}"

    # Verify key sections exist
    income = result.get_income()
    assert income, "Income section missing from historical data"
    assert 'children' in income, "Income section malformed - no children"

    expenses = result.get_expenses()
    assert expenses, "Expenses section missing from historical data"
    assert 'children' in expenses, "Expenses section malformed - no children"

    # COGS is expected in this file (landscaping business)
    cogs = result.get_cogs()
    assert cogs is not None, "Cost of Goods Sold section missing from historical data"

    # Validate completeness - should have no warnings for this known-good file
    warnings = parser.validate_completeness(result)
    assert warnings == [], f"Unexpected validation warnings: {warnings}"

    # Verify hierarchy structure contains expected accounts
    account_names = parser._extract_account_names(result.hierarchy)
    # Check for a few expected accounts from the file
    assert len(account_names) > 0, "No accounts found in hierarchy"

    # Verify periods have data format (check one account)
    first_account = None
    for child in income.get('children', []):
        if 'values' in child:
            first_account = child
            break

    assert first_account is not None, "No accounts with values found in Income"
    assert len(first_account['values']) == 12, "Account should have values for all 12 periods"
