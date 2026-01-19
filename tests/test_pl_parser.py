"""
Unit tests for PLParser.

Tests period header parsing, row type detection, multi-period metadata extraction,
hierarchy building with period data, and real file integration.
"""
from pathlib import Path

import pandas as pd
import pytest

from src.loaders import FileLoader
from src.parsers import PLParser
from src.models import PLModel


def create_pl_sample_two_periods() -> pd.DataFrame:
    """
    Create a valid QuickBooks P&L sample with two periods.

    Matches real QuickBooks format with:
    - Metadata rows (title, company, date range)
    - Column headers
    - Period headers in row 6
    - Sections: Income, COGS, Expenses, Other Expenses
    - Calculated rows: Gross Profit, Net Operating Income, Net Other Income, Net Income
    - Parent accounts with empty values
    - Child accounts with numeric values
    - Total rows
    - Footer with timestamp

    Note: Real QuickBooks files have a blank line after metadata, but pandas
    skip_blank_lines=True removes it during load. This fixture matches the
    post-pandas DataFrame structure that the parser actually receives.
    """
    rows = [
        # Metadata rows (1-3)
        ['Profit and Loss', '', ''],
        ["Craig's Design and Landscaping Services", '', ''],
        ['"November 1-30, 2025"', '', ''],
        # Blank row removed - pandas skips it in real files with skip_blank_lines=True
        # Column header
        ['Distribution account', 'Total', ''],
        # Period headers (row 5 after blank line removed)
        ['', 'Nov 1 - Nov 30 2025', 'Nov 1 - Nov 30 2024 (PY)'],
        # Income section
        ['Income', '', ''],
        ['Design income', '637.50', '500.00'],
        ['Landscaping Services', '', ''],
        ['Job Materials', '', ''],
        ['Fountains and Garden Lighting', '406.80', '300.00'],
        ['Plants and Soil', '1,766.98', '1,500.00'],
        ['Total for Job Materials', '$2,173.78', '$1,800.00'],
        ['Total for Landscaping Services', '$2,173.78', '$1,800.00'],
        ['Total for Income', '$2,811.28', '$2,300.00'],
        # Cost of Goods Sold
        ['Cost of Goods Sold', '', ''],
        ['Cost of Goods Sold', '228.75', '200.00'],
        ['Total for Cost of Goods Sold', '$228.75', '$200.00'],
        # Calculated: Gross Profit
        ['Gross Profit', '$2,582.53', '$2,100.00'],
        # Expenses
        ['Expenses', '', ''],
        ['Advertising', '74.86', '50.00'],
        ['Automobile', '', ''],
        ['Fuel', '167.85', '150.00'],
        ['Total for Automobile', '$167.85', '$150.00'],
        ['Equipment Rental', '112.00', '100.00'],
        ['Total for Expenses', '$354.71', '$300.00'],
        # Calculated: Net Operating Income
        ['Net Operating Income', '$2,227.82', '$1,800.00'],
        # Other Expenses
        ['Other Expenses', '', ''],
        ['Miscellaneous', '2,666.00', '2,000.00'],
        ['Total for Other Expenses', '$2,666.00', '$2,000.00'],
        # Calculated: Net Other Income
        ['Net Other Income', '-$2,666.00', '-$2,000.00'],
        # Calculated: Net Income
        ['Net Income', '-$438.18', '-$200.00'],
        # Footer (blank line removed - pandas skips it)
        ['Cash Basis Monday, January 19, 2026 04:28 PM GMTZ', '', ''],
    ]

    return pd.DataFrame(rows)


def create_pl_sample_single_period() -> pd.DataFrame:
    """
    Create P&L sample with single period column.

    Note: Blank rows removed to match post-pandas structure (skip_blank_lines=True).
    """
    rows = [
        ['Profit and Loss', ''],
        ["Craig's Design and Landscaping Services", ''],
        ['"November 1-30, 2025"', ''],
        # Blank row removed - pandas skips it in real files
        ['Distribution account', 'Total'],
        ['', 'Nov 1 - Nov 30 2025'],
        ['Income', ''],
        ['Design income', '637.50'],
        ['Total for Income', '$637.50'],
        ['Gross Profit', '$637.50'],
        ['Expenses', ''],
        ['Advertising', '74.86'],
        ['Total for Expenses', '$74.86'],
        ['Net Operating Income', '$562.64'],
        ['Net Income', '$562.64'],
        # Footer blank line removed - pandas skips it
        ['Cash Basis Monday, January 19, 2026 04:28 PM GMTZ', ''],
    ]

    return pd.DataFrame(rows)


def create_pl_sample_missing_cogs() -> pd.DataFrame:
    """
    Create P&L sample without COGS section (service business).

    Note: Blank rows removed to match post-pandas structure (skip_blank_lines=True).
    """
    rows = [
        ['Profit and Loss', '', ''],
        ["Craig's Design and Landscaping Services", '', ''],
        ['"November 1-30, 2025"', '', ''],
        # Blank row removed - pandas skips it in real files
        ['Distribution account', 'Total', ''],
        ['', 'Nov 1 - Nov 30 2025', 'Nov 1 - Nov 30 2024 (PY)'],
        ['Income', '', ''],
        ['Design income', '637.50', '500.00'],
        ['Total for Income', '$637.50', '$500.00'],
        # No COGS section - skip directly to Gross Profit
        ['Gross Profit', '$637.50', '$500.00'],
        ['Expenses', '', ''],
        ['Advertising', '74.86', '50.00'],
        ['Total for Expenses', '$74.86', '$50.00'],
        ['Net Operating Income', '$562.64', '$450.00'],
        ['Net Income', '$562.64', '$450.00'],
        # Footer blank line removed - pandas skips it
        ['Cash Basis Monday, January 19, 2026 04:28 PM GMTZ', '', ''],
    ]

    return pd.DataFrame(rows)


class TestPLParser:
    """Test suite for PLParser class."""

    @pytest.fixture
    def file_loader(self):
        """Create FileLoader instance."""
        return FileLoader()

    @pytest.fixture
    def parser(self, file_loader):
        """Create PLParser instance."""
        return PLParser(file_loader)

    @pytest.fixture
    def valid_pl_file_two_periods(self, tmp_path):
        """Create valid P&L CSV file with two periods."""
        df = create_pl_sample_two_periods()
        file_path = tmp_path / "pl_two_periods.csv"
        df.to_csv(file_path, index=False, header=False)
        return file_path

    @pytest.fixture
    def valid_pl_file_single_period(self, tmp_path):
        """Create valid P&L CSV file with single period."""
        df = create_pl_sample_single_period()
        file_path = tmp_path / "pl_single_period.csv"
        df.to_csv(file_path, index=False, header=False)
        return file_path

    @pytest.fixture
    def valid_pl_file_missing_cogs(self, tmp_path):
        """Create valid P&L CSV file without COGS section."""
        df = create_pl_sample_missing_cogs()
        file_path = tmp_path / "pl_no_cogs.csv"
        df.to_csv(file_path, index=False, header=False)
        return file_path

    def test_parse_valid_pl_two_periods(self, parser, valid_pl_file_two_periods):
        """
        Given: Valid P&L CSV file with two periods
        When: parse() called
        Then: Returns PLModel with correct hierarchy and calculated rows
        """
        result = parser.parse(valid_pl_file_two_periods)

        # Check result is PLModel
        assert isinstance(result, PLModel)

        # Check DataFrame has expected columns
        assert 'account_name' in result.dataframe.columns
        assert 'values' in result.dataframe.columns
        assert 'row_type' in result.dataframe.columns

        # Check hierarchy has required sections
        assert 'Income' in result.hierarchy
        assert 'Cost of Goods Sold' in result.hierarchy
        assert 'Expenses' in result.hierarchy
        assert 'Other Expenses' in result.hierarchy

        # Check calculated rows exist
        assert len(result.calculated_rows) > 0
        calculated_names = [row['account_name'] for row in result.calculated_rows]
        assert 'Gross Profit' in calculated_names
        assert 'Net Income' in calculated_names

    def test_period_header_parsing(self, parser, valid_pl_file_two_periods):
        """
        Given: CSV with 2 period columns at indices 1 and 2
        When: _parse_period_headers() called
        Then: period_columns dict has 2 entries with correct labels
        """
        # Load and skip to period header row
        df = parser.file_loader.load(valid_pl_file_two_periods)
        df = df.iloc[2:].reset_index(drop=True)
        # Row 0 = column headers, Row 1 = period headers (blank rows removed from fixture)
        period_row = df.iloc[1]

        period_columns = parser._parse_period_headers(period_row)

        # Check we got 2 periods
        assert len(period_columns) == 2
        assert 1 in period_columns
        assert 2 in period_columns
        assert period_columns[1] == 'Nov 1 - Nov 30 2025'
        assert period_columns[2] == 'Nov 1 - Nov 30 2024 (PY)'

    def test_multi_period_value_extraction(self, parser, valid_pl_file_two_periods):
        """
        Given: Account row with values $637.50 and $500.00 in columns 1 and 2
        When: metadata extracted
        Then: values dict has both period keys with correct numeric values
        """
        result = parser.parse(valid_pl_file_two_periods)

        # Find Design income row
        design_row = result.dataframe[result.dataframe['account_name'] == 'Design income'].iloc[0]

        # Check values dict
        assert isinstance(design_row['values'], dict)
        assert len(design_row['values']) == 2
        assert 'Nov 1 - Nov 30 2025' in design_row['values']
        assert 'Nov 1 - Nov 30 2024 (PY)' in design_row['values']
        assert design_row['values']['Nov 1 - Nov 30 2025'] == 637.50
        assert design_row['values']['Nov 1 - Nov 30 2024 (PY)'] == 500.00

    def test_missing_period_value_handling(self, parser):
        """
        Given: Account row with value in column 1 but empty in column 2
        When: metadata extracted
        Then: values dict contains only key for column 1 period
        """
        # Create test DataFrame with missing value
        rows = [
            ['Profit and Loss', '', ''],
            ["Company", '', ''],
            ['"November 2025"', '', ''],
            # Blank row removed - matches post-pandas structure
            ['Distribution account', 'Total', ''],
            ['', 'Nov 1 - Nov 30 2025', 'Nov 1 - Nov 30 2024 (PY)'],
            ['Income', '', ''],
            ['Design income', '637.50', ''],  # Missing second period value
            ['Total for Income', '$637.50', ''],
            ['Expenses', '', ''],
            ['Advertising', '74.86', ''],
            ['Total for Expenses', '$74.86', ''],
            ['Net Income', '$562.64', ''],
            # Footer blank line removed - matches post-pandas structure
            ['Cash Basis Monday, January 19, 2026 04:28 PM GMTZ', '', ''],
        ]

        df = pd.DataFrame(rows)
        file_path = Path('/tmp/test_pl_missing_value.csv')
        df.to_csv(file_path, index=False, header=False)

        result = parser.parse(file_path)

        # Find Design income row
        design_row = result.dataframe[result.dataframe['account_name'] == 'Design income'].iloc[0]

        # Check values dict has only first period
        assert len(design_row['values']) == 1
        assert 'Nov 1 - Nov 30 2025' in design_row['values']
        assert 'Nov 1 - Nov 30 2024 (PY)' not in design_row['values']

    def test_section_row_detection(self, parser):
        """
        Given: Row with account_name='Income' and empty values dict
        When: _detect_row_type() called
        Then: returns 'section'
        """
        row_type = parser._detect_row_type('Income', {})
        assert row_type == 'section'

        row_type = parser._detect_row_type('Expenses', {})
        assert row_type == 'section'

        row_type = parser._detect_row_type('Cost of Goods Sold', {})
        assert row_type == 'section'

    def test_calculated_row_detection(self, parser):
        """
        Given: Row with account_name='Gross Profit' and values dict present
        When: _detect_row_type() called
        Then: returns 'calculated'
        """
        values = {'Nov 1 - Nov 30 2025': 2582.53}
        row_type = parser._detect_row_type('Gross Profit', values)
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('Net Income', values)
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('Net Operating Income', values)
        assert row_type == 'calculated'

    def test_child_row_detection(self, parser):
        """
        Given: Row with account_name='Sales' and values dict present
        When: _detect_row_type() called
        Then: returns 'child'
        """
        values = {'Nov 1 - Nov 30 2025': 637.50}
        row_type = parser._detect_row_type('Design income', values)
        assert row_type == 'child'

    def test_parent_row_detection(self, parser):
        """
        Given: Row with account_name='Operating Expenses' and empty values dict
        When: _detect_row_type() called
        Then: returns 'parent'
        """
        row_type = parser._detect_row_type('Landscaping Services', {})
        assert row_type == 'parent'

        row_type = parser._detect_row_type('Automobile', {})
        assert row_type == 'parent'

    def test_total_row_detection(self, parser):
        """
        Given: Row with 'Total for X' prefix
        When: _detect_row_type() called
        Then: returns 'total'
        """
        values = {'Nov 1 - Nov 30 2025': 2811.28}
        row_type = parser._detect_row_type('Total for Income', values)
        assert row_type == 'total'

    def test_hierarchy_with_period_values(self, parser, valid_pl_file_two_periods):
        """
        Given: Metadata with Income section and child 'Design income' with values dict
        When: parse() called
        Then: Income section node contains child with values dict preserved
        """
        result = parser.parse(valid_pl_file_two_periods)

        # Get Income section
        income = result.hierarchy['Income']

        # Check children exist
        assert 'children' in income

        # Find Design income child
        design_income = None
        for child in income['children']:
            if child.get('name') == 'Design income':
                design_income = child
                break

        assert design_income is not None
        assert 'values' in design_income
        assert isinstance(design_income['values'], dict)
        assert 'Nov 1 - Nov 30 2025' in design_income['values']
        assert design_income['values']['Nov 1 - Nov 30 2025'] == 637.50

    def test_calculated_rows_excluded_from_hierarchy(self, parser, valid_pl_file_two_periods):
        """
        Given: Metadata with 'Gross Profit' row (calculated type)
        When: parse() called
        Then: Gross Profit not in hierarchy tree, stored in calculated_rows
        """
        result = parser.parse(valid_pl_file_two_periods)

        # Check Gross Profit not in hierarchy sections
        assert 'Gross Profit' not in result.hierarchy

        # Check it's in calculated_rows
        calculated_names = [row['account_name'] for row in result.calculated_rows]
        assert 'Gross Profit' in calculated_names

        # Get the calculated row
        gross_profit = next(row for row in result.calculated_rows if row['account_name'] == 'Gross Profit')
        assert 'values' in gross_profit
        assert isinstance(gross_profit['values'], dict)

    def test_nested_hierarchy_with_periods(self, parser, valid_pl_file_two_periods):
        """
        Given: Metadata with parent 'Landscaping Services' and children
        When: parse() called
        Then: Section/parent/child nesting preserves period values
        """
        result = parser.parse(valid_pl_file_two_periods)

        # Get Income section
        income = result.hierarchy['Income']

        # Find Landscaping Services parent
        landscaping = None
        for child in income['children']:
            if child.get('name') == 'Landscaping Services':
                landscaping = child
                break

        assert landscaping is not None
        assert landscaping.get('parent') is True
        assert 'children' in landscaping

        # Find Job Materials nested parent
        job_materials = None
        for child in landscaping['children']:
            if child.get('name') == 'Job Materials':
                job_materials = child
                break

        assert job_materials is not None
        assert 'children' in job_materials

        # Find Fountains child
        fountains = None
        for child in job_materials['children']:
            if child.get('name') == 'Fountains and Garden Lighting':
                fountains = child
                break

        assert fountains is not None
        assert 'values' in fountains
        assert fountains['values']['Nov 1 - Nov 30 2025'] == 406.80

    def test_single_period_parsing(self, parser, valid_pl_file_single_period):
        """
        Given: CSV with single period column
        When: parse() called
        Then: hierarchy contains single-period values dicts
        """
        result = parser.parse(valid_pl_file_single_period)

        # Check periods
        periods = result.get_periods()
        assert len(periods) == 1
        assert periods[0] == 'Nov 1 - Nov 30 2025'

        # Check values have single period
        design_row = result.dataframe[result.dataframe['account_name'] == 'Design income'].iloc[0]
        assert len(design_row['values']) == 1

    def test_optional_cogs_section(self, parser, valid_pl_file_missing_cogs):
        """
        Given: CSV without COGS section
        When: parse() called
        Then: Parser succeeds, COGS not in hierarchy
        """
        result = parser.parse(valid_pl_file_missing_cogs)

        # Check required sections exist
        assert 'Income' in result.hierarchy
        assert 'Expenses' in result.hierarchy

        # Check COGS is not present
        assert 'Cost of Goods Sold' not in result.hierarchy

    def test_real_pl_file_parsing(self, parser):
        """
        Given: Real QuickBooks P&L from data directory
        When: parse() called
        Then: Successfully parses and builds hierarchy with periods
        """
        # Use the actual example file provided
        real_file = Path('/home/max/projects/QB-Assistant/data/profit_loss.csv')

        if not real_file.exists():
            pytest.skip("Real P&L file not found")

        result = parser.parse(real_file)

        # Validate result
        assert isinstance(result, PLModel)
        assert 'Income' in result.hierarchy
        assert len(result.dataframe) > 0

        # Check periods parsed
        periods = result.get_periods()
        assert len(periods) > 0

        # Check calculated rows
        assert len(result.calculated_rows) > 0

    @pytest.mark.parametrize('currency_str,expected_value', [
        ('$2,001.00', 2001.0),
        ('1,201.00', 1201.0),
        ('800.00', 800.0),
        ('-9,905.00', -9905.0),
        ('$13,495.00', 13495.0),
        ('0.00', 0.0),
        ('-$2,666.00', -2666.0),
    ])
    def test_clean_currency_formats(self, parser, currency_str, expected_value):
        """
        Given: Various currency format strings
        When: _clean_currency() called
        Then: Returns correct float value
        """
        result = parser._clean_currency(currency_str)
        assert result == expected_value

    def test_clean_currency_invalid(self, parser):
        """
        Given: Invalid currency string
        When: _clean_currency() called
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="Cannot parse currency value"):
            parser._clean_currency('invalid')

    def test_parse_missing_income_section_error(self, parser, tmp_path):
        """
        Given: File with missing Income section
        When: parse() called
        Then: Raises ValueError with descriptive message
        """
        rows = [
            ['Profit and Loss', '', ''],
            ["Company", '', ''],
            ['"November 2025"', '', ''],
            # Blank row removed - matches post-pandas structure
            ['Distribution account', 'Total', ''],
            ['', 'Nov 1 - Nov 30 2025', 'Nov 1 - Nov 30 2024 (PY)'],
            # Missing Income section - start with Expenses
            ['Expenses', '', ''],
            ['Advertising', '74.86', '50.00'],
            ['Total for Expenses', '$74.86', '$50.00'],
            ['Net Income', '$74.86', '$50.00'],
            # Footer blank line removed - matches post-pandas structure
            ['Cash Basis Monday, January 19, 2026 04:28 PM GMTZ', '', ''],
        ]

        df = pd.DataFrame(rows)
        file_path = tmp_path / "missing_income.csv"
        df.to_csv(file_path, index=False, header=False)

        with pytest.raises(ValueError, match="Missing required section: Income"):
            parser.parse(file_path)

    def test_parse_file_too_short(self, parser, tmp_path):
        """
        Given: File with fewer than 6 rows
        When: parse() called
        Then: Raises ValueError
        """
        df = pd.DataFrame([['Profit and Loss', ''], ['Company', '']])
        file_path = tmp_path / "short.csv"
        df.to_csv(file_path, index=False, header=False)

        with pytest.raises(ValueError, match="File too short"):
            parser.parse(file_path)
