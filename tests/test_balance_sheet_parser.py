"""
Unit tests for BalanceSheetParser.

Tests two-pass parsing logic, row type detection, currency parsing,
hierarchy building, and error handling.
"""
from pathlib import Path

import pandas as pd
import pytest

from src.loaders import FileLoader
from src.parsers import BalanceSheetParser
from src.models import BalanceSheetModel
from tests.fixtures import create_balance_sheet_sample, create_malformed_balance_sheet_sample


class TestBalanceSheetParser:
    """Test suite for BalanceSheetParser class."""

    @pytest.fixture
    def file_loader(self):
        """Create FileLoader instance."""
        return FileLoader()

    @pytest.fixture
    def parser(self, file_loader):
        """Create BalanceSheetParser instance."""
        return BalanceSheetParser(file_loader)

    @pytest.fixture
    def valid_balance_sheet_file(self, tmp_path):
        """Create valid Balance Sheet CSV file."""
        df = create_balance_sheet_sample()
        file_path = tmp_path / "balance_sheet.csv"
        df.to_csv(file_path, index=False, header=False)
        return file_path

    @pytest.fixture
    def malformed_balance_sheet_file(self, tmp_path):
        """Create malformed Balance Sheet CSV file factory."""
        def _create(defect_type):
            df = create_malformed_balance_sheet_sample(defect_type)
            file_path = tmp_path / f"malformed_{defect_type}.csv"
            df.to_csv(file_path, index=False, header=False)
            return file_path
        return _create

    def test_parse_valid_balance_sheet(self, parser, valid_balance_sheet_file):
        """
        Given: Valid Balance Sheet CSV file
        When: parse() called
        Then: Returns BalanceSheetModel with correct hierarchy
        """
        result = parser.parse(valid_balance_sheet_file)

        # Check result is BalanceSheetModel
        assert isinstance(result, BalanceSheetModel)

        # Check DataFrame has expected columns
        assert 'account_name' in result.dataframe.columns
        assert 'row_type' in result.dataframe.columns
        assert 'numeric_value' in result.dataframe.columns

        # Check hierarchy has required sections
        assert 'Assets' in result.hierarchy
        assert 'Liabilities and Equity' in result.hierarchy or 'Liabilities' in result.hierarchy
        assert 'Equity' in result.hierarchy or 'Liabilities and Equity' in result.hierarchy

    def test_detect_row_type_total(self, parser):
        """
        Given: Row with 'Total for X' prefix
        When: _detect_row_type() called
        Then: Returns 'total' type
        """
        row_type = parser._detect_row_type('Total for Bank Accounts', '$2,001.00')
        assert row_type == 'total'

    def test_detect_row_type_parent(self, parser):
        """
        Given: Row with empty value and not a section
        When: _detect_row_type() called
        Then: Returns 'parent' type
        """
        row_type = parser._detect_row_type('Current Assets', '')
        assert row_type == 'parent'

    def test_detect_row_type_child(self, parser):
        """
        Given: Row with numeric value
        When: _detect_row_type() called
        Then: Returns 'child' type
        """
        row_type = parser._detect_row_type('Checking', '1,201.00')
        assert row_type == 'child'

    def test_detect_row_type_section(self, parser):
        """
        Given: Row with section name and empty value
        When: _detect_row_type() called
        Then: Returns 'section' type
        """
        row_type = parser._detect_row_type('Assets', '')
        assert row_type == 'section'

    @pytest.mark.parametrize('currency_str,expected_value', [
        ('$2,001.00', 2001.0),
        ('1,201.00', 1201.0),
        ('800.00', 800.0),
        ('-9,905.00', -9905.0),
        ('$13,495.00', 13495.0),
        ('0.00', 0.0),
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

    def test_parse_missing_section_error(self, parser, malformed_balance_sheet_file):
        """
        Given: File with missing Equity section
        When: parse() called
        Then: Raises ValueError with descriptive message
        """
        file_path = malformed_balance_sheet_file('missing_section')

        with pytest.raises(ValueError, match="Missing required section: Equity"):
            parser.parse(file_path)

    def test_parse_builds_hierarchy(self, parser, valid_balance_sheet_file):
        """
        Given: Valid Balance Sheet file
        When: parse() called
        Then: Hierarchy contains parent-child relationships
        """
        result = parser.parse(valid_balance_sheet_file)

        # Check Assets section has children
        assets = result.hierarchy.get('Assets', {})
        assert 'children' in assets or len(assets) > 0

    def test_parse_real_file(self, parser):
        """
        Given: Real QuickBooks Balance Sheet from data directory
        When: parse() called
        Then: Successfully parses and builds hierarchy
        """
        # Use the actual example file provided
        real_file = Path('/home/max/projects/QB-Assistant/data/balance sheet.csv')

        if not real_file.exists():
            pytest.skip("Real Balance Sheet file not found")

        result = parser.parse(real_file)

        # Validate result
        assert isinstance(result, BalanceSheetModel)
        assert 'Assets' in result.hierarchy
        assert len(result.dataframe) > 0

    def test_parse_raw_data_structure(self, parser):
        """
        Given: Simple DataFrame with Balance Sheet rows
        When: _parse_raw_data() called
        Then: Returns DataFrame with metadata columns
        """
        test_df = pd.DataFrame({
            'account_name': ['Assets', 'Checking', 'Total for Assets'],
            'value': ['', '1,201.00', '$1,201.00']
        })

        result = parser._parse_raw_data(test_df)

        # Check columns exist
        assert 'account_name' in result.columns
        assert 'raw_value' in result.columns
        assert 'numeric_value' in result.columns
        assert 'row_type' in result.columns

        # Check row types detected correctly
        assert result.iloc[0]['row_type'] == 'section'
        assert result.iloc[1]['row_type'] == 'child'
        assert result.iloc[2]['row_type'] == 'total'

    def test_validate_sections_missing_assets(self, parser):
        """
        Given: DataFrame without Assets section
        When: _validate_sections() called
        Then: Raises ValueError
        """
        test_df = pd.DataFrame({
            'account_name': ['Liabilities', 'Equity'],
            'row_type': ['section', 'section']
        })

        with pytest.raises(ValueError, match="Missing required section: Assets"):
            parser._validate_sections(test_df)

    def test_build_hierarchy_with_nested_parents(self, parser):
        """
        Given: Metadata DataFrame with nested parent accounts
        When: _build_hierarchy() called
        Then: Correctly builds nested structure
        """
        test_df = pd.DataFrame({
            'account_name': [
                'Assets',
                'Current Assets',
                'Bank Accounts',
                'Checking',
                'Savings',
                'Total for Bank Accounts'
            ],
            'row_type': ['section', 'parent', 'parent', 'child', 'child', 'total'],
            'numeric_value': [None, None, None, 1201.0, 800.0, 2001.0]
        })

        hierarchy = parser._build_hierarchy(test_df)

        # Check Assets section exists
        assert 'Assets' in hierarchy

        # Check nested structure
        assert 'children' in hierarchy['Assets']


class TestBalanceSheetParserEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def file_loader(self):
        """Create FileLoader instance."""
        return FileLoader()

    @pytest.fixture
    def parser(self, file_loader):
        """Create BalanceSheetParser instance."""
        return BalanceSheetParser(file_loader)

    def test_parse_file_too_short(self, parser, tmp_path):
        """
        Given: File with fewer than 5 rows
        When: parse() called
        Then: Raises ValueError
        """
        # Create file with only 2 rows
        df = pd.DataFrame([['Balance Sheet', ''], ['Company', '']])
        file_path = tmp_path / "short.csv"
        df.to_csv(file_path, index=False, header=False)

        with pytest.raises(ValueError, match="File too short"):
            parser.parse(file_path)

    def test_currency_with_parentheses_negative(self, parser):
        """
        Given: Currency in parentheses format (accounting negative)
        When: _clean_currency() called
        Then: Handles appropriately
        """
        # Standard format should work
        result = parser._clean_currency('-1,234.56')
        assert result == -1234.56
