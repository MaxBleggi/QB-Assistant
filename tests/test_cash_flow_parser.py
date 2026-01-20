"""
Unit tests for CashFlowParser.

Tests two-pass parsing logic, row type detection (with calculated row priority),
currency parsing, hierarchy building, and error handling.
"""
from pathlib import Path

import pandas as pd
import pytest

from src.loaders import FileLoader
from src.parsers import CashFlowParser
from src.models import CashFlowModel
from tests.fixtures import create_cash_flow_sample, create_malformed_cash_flow_sample


class TestCashFlowParser:
    """Test suite for CashFlowParser class."""

    @pytest.fixture
    def file_loader(self):
        """Create FileLoader instance."""
        return FileLoader()

    @pytest.fixture
    def parser(self, file_loader):
        """Create CashFlowParser instance."""
        return CashFlowParser(file_loader)

    @pytest.fixture
    def valid_cash_flow_file(self, tmp_path):
        """Create valid Cash Flow Statement CSV file."""
        df = create_cash_flow_sample()
        file_path = tmp_path / "cash_flow.csv"
        df.to_csv(file_path, index=False, header=False)
        return file_path

    @pytest.fixture
    def malformed_cash_flow_file(self, tmp_path):
        """Create malformed Cash Flow Statement CSV file factory."""
        def _create(defect_type):
            df = create_malformed_cash_flow_sample(defect_type)
            file_path = tmp_path / f"malformed_{defect_type}.csv"
            df.to_csv(file_path, index=False, header=False)
            return file_path
        return _create

    def test_parse_valid_cash_flow(self, parser, valid_cash_flow_file):
        """
        Given: Valid Cash Flow Statement CSV file
        When: parse() called
        Then: Returns CashFlowModel with three hierarchy sections and 6 calculated rows
        """
        result = parser.parse(valid_cash_flow_file)

        # Check result is CashFlowModel
        assert isinstance(result, CashFlowModel)

        # Check DataFrame has expected columns
        assert 'account_name' in result.dataframe.columns
        assert 'row_type' in result.dataframe.columns
        assert 'numeric_value' in result.dataframe.columns

        # Check hierarchy has all three required sections
        assert 'OPERATING ACTIVITIES' in result.hierarchy
        assert 'INVESTING ACTIVITIES' in result.hierarchy
        assert 'FINANCING ACTIVITIES' in result.hierarchy

        # Check calculated rows exist
        assert len(result.calculated_rows) >= 4  # At minimum: 3 net cash + net increase

        # Verify calculated rows are NOT in hierarchy
        calc_names = {row['account_name'] for row in result.calculated_rows}
        for section_items in result.hierarchy.values():
            for item in section_items:
                assert item.get('name') not in calc_names

    def test_section_marker_detection(self, parser):
        """
        Given: Section marker 'OPERATING ACTIVITIES' with empty value
        When: _detect_row_type() called
        Then: Returns 'section' type
        """
        row_type = parser._detect_row_type('OPERATING ACTIVITIES', '')
        assert row_type == 'section'

        row_type = parser._detect_row_type('INVESTING ACTIVITIES', '')
        assert row_type == 'section'

        row_type = parser._detect_row_type('FINANCING ACTIVITIES', '')
        assert row_type == 'section'

    def test_calculated_row_detection(self, parser):
        """
        Given: Data with 'Net cash provided by operating activities' and value
        When: _detect_row_type() called
        Then: Returns 'calculated' type, not 'child'
        """
        # Test all calculated rows are detected correctly
        row_type = parser._detect_row_type('Net cash provided by operating activities', '$1,887.47')
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('Net cash provided by investing activities', '0.00')
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('Net cash provided by financing activities', '-$2,832.50')
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('NET CASH INCREASE FOR PERIOD', '-$945.03')
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('Cash at beginning of period', '$5,008.55')
        assert row_type == 'calculated'

        row_type = parser._detect_row_type('CASH AT END OF PERIOD', '$4,063.52')
        assert row_type == 'calculated'

    def test_calculated_row_type_priority(self, parser):
        """
        Given: Row with name 'Net cash provided by operating activities' and value '1887.47'
        When: _detect_row_type() called
        Then: Returns 'calculated' before checking if it's a child row
        """
        # This test verifies calculated rows are checked FIRST (before child type)
        # Even though the row has a value (which would normally make it a child),
        # it should be classified as calculated
        row_type = parser._detect_row_type('Net cash provided by operating activities', '1887.47')
        assert row_type == 'calculated'
        assert row_type != 'child'

    def test_detect_row_type_parent(self, parser):
        """
        Given: Row with name 'Adjustments to reconcile...' and empty value
        When: _detect_row_type() called
        Then: Returns 'parent'
        """
        row_type = parser._detect_row_type(
            'Adjustments to reconcile Net Income to Net Cash provided by operations:', ''
        )
        assert row_type == 'parent'

    def test_detect_row_type_child(self, parser):
        """
        Given: Row with account name and numeric value
        When: _detect_row_type() called
        Then: Returns 'child'
        """
        row_type = parser._detect_row_type('Accounts Payable (A/P)', '-369.72')
        assert row_type == 'child'

        row_type = parser._detect_row_type('Net Income', '1,481.28')
        assert row_type == 'child'

    def test_detect_row_type_total(self, parser):
        """
        Given: Row with 'Total for X' prefix
        When: _detect_row_type() called
        Then: Returns 'total'
        """
        row_type = parser._detect_row_type(
            'Total for Adjustments to reconcile Net Income to Net Cash provided by operations:',
            '$406.19'
        )
        assert row_type == 'total'

    def test_currency_cleaning_positive(self, parser):
        """
        Given: Currency string '$1,887.47'
        When: _clean_currency() called
        Then: Returns float 1887.47
        """
        result = parser._clean_currency('$1,887.47')
        assert result == 1887.47

        result = parser._clean_currency('1,481.28')
        assert result == 1481.28

    def test_currency_cleaning_negative(self, parser):
        """
        Given: Negative currency '-2,853.02'
        When: _clean_currency() called
        Then: Returns float -2853.02
        """
        result = parser._clean_currency('-2,853.02')
        assert result == -2853.02

        result = parser._clean_currency('-$2,832.50')
        assert result == -2832.50

    def test_currency_cleaning_invalid(self, parser):
        """
        Given: Invalid currency 'abc'
        When: _clean_currency() called
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="Cannot parse currency value"):
            parser._clean_currency('abc')

        with pytest.raises(ValueError):
            parser._clean_currency('invalid_amount')

    def test_parent_child_hierarchy(self, parser, valid_cash_flow_file):
        """
        Given: Section with parent 'Adjustments to reconcile...' and 3+ children and 'Total for Adjustments' row
        When: parse() called
        Then: Returns parent dict with children in children array and total value set
        """
        result = parser.parse(valid_cash_flow_file)

        # Get operating activities section
        operating = result.get_operating()
        assert len(operating) > 0

        # Find the parent entry
        parent = None
        for item in operating:
            if item.get('parent') and 'Adjustments to reconcile' in item.get('name', ''):
                parent = item
                break

        assert parent is not None, "Should find parent 'Adjustments to reconcile...'"
        assert 'children' in parent
        assert len(parent['children']) >= 3  # At least 3 child accounts
        assert parent['total'] is not None  # Total should be set

    def test_empty_section_handling(self, parser, valid_cash_flow_file):
        """
        Given: INVESTING ACTIVITIES section with no child rows
        When: parse() called
        Then: Returns {'INVESTING ACTIVITIES': []} (empty list, no error)
        """
        result = parser.parse(valid_cash_flow_file)

        # Get investing activities section
        investing = result.get_investing()

        # Should be empty list (not None, not error)
        assert investing == []
        assert isinstance(investing, list)

    def test_calculated_rows_excluded_from_hierarchy(self, parser, valid_cash_flow_file):
        """
        Given: Calculated row 'Net cash provided by operating activities' in data
        When: parse() called
        Then: Row excluded from hierarchy, stored in calculated_rows list instead
        """
        result = parser.parse(valid_cash_flow_file)

        # Check calculated row exists in calculated_rows
        calc_names = [row['account_name'] for row in result.calculated_rows]
        assert 'Net cash provided by operating activities' in calc_names

        # Check it's NOT in hierarchy
        operating = result.get_operating()
        for item in operating:
            assert item.get('name') != 'Net cash provided by operating activities'

    def test_beginning_ending_cash_extraction(self, parser, valid_cash_flow_file):
        """
        Given: Valid cash flow data with beginning and ending cash rows
        When: parse() called
        Then: calculated_rows list contains cash position rows
        """
        result = parser.parse(valid_cash_flow_file)

        # Check beginning cash in calculated rows
        beginning_cash_found = False
        ending_cash_found = False

        for row in result.calculated_rows:
            if row['account_name'] == 'Cash at beginning of period':
                beginning_cash_found = True
                assert row['value'] is not None
            if row['account_name'] == 'CASH AT END OF PERIOD':
                ending_cash_found = True
                assert row['value'] is not None

        assert beginning_cash_found, "Should find 'Cash at beginning of period' in calculated rows"
        assert ending_cash_found, "Should find 'CASH AT END OF PERIOD' in calculated rows"

    def test_malformed_file_missing_section(self, parser, malformed_cash_flow_file):
        """
        Given: Malformed sample missing OPERATING ACTIVITIES section
        When: parse() called
        Then: Raises ValueError with clear message
        """
        file_path = malformed_cash_flow_file('missing_section')

        with pytest.raises(ValueError, match="Missing required section"):
            parser.parse(file_path)

    def test_file_too_short(self, parser, tmp_path):
        """
        Given: File with fewer than 5 rows
        When: parse() called
        Then: Raises ValueError
        """
        # Create file with only 2 rows
        df = pd.DataFrame([['row1', ''], ['row2', '']])
        file_path = tmp_path / "short.csv"
        df.to_csv(file_path, index=False, header=False)

        with pytest.raises(ValueError, match="File too short"):
            parser.parse(file_path)

    def test_hierarchy_structure(self, parser, valid_cash_flow_file):
        """
        Given: Valid cash flow file
        When: parse() called
        Then: Hierarchy has correct structure with sections as lists
        """
        result = parser.parse(valid_cash_flow_file)

        # Check all sections are lists
        assert isinstance(result.hierarchy['OPERATING ACTIVITIES'], list)
        assert isinstance(result.hierarchy['INVESTING ACTIVITIES'], list)
        assert isinstance(result.hierarchy['FINANCING ACTIVITIES'], list)

        # Operating should have items
        assert len(result.hierarchy['OPERATING ACTIVITIES']) > 0

        # Financing should have items
        assert len(result.hierarchy['FINANCING ACTIVITIES']) > 0

    def test_parse_returns_model_with_all_components(self, parser, valid_cash_flow_file):
        """
        Given: Valid cash flow sample data
        When: parse() called
        Then: Returns CashFlowModel with df, hierarchy, calculated_rows, metadata
        """
        result = parser.parse(valid_cash_flow_file)

        assert isinstance(result, CashFlowModel)
        assert result.dataframe is not None
        assert isinstance(result.dataframe, pd.DataFrame)
        assert result.hierarchy is not None
        assert isinstance(result.hierarchy, dict)
        assert result.calculated_rows is not None
        assert isinstance(result.calculated_rows, list)
        assert result.metadata is not None
        assert isinstance(result.metadata, dict)
