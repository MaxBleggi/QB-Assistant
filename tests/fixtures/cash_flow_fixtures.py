"""
Test data fixture utilities for creating sample Cash Flow Statement CSV files.

Provides factory functions for generating test files matching QuickBooks cash flow format
with various scenarios (valid data, malformed data, empty sections).
"""
import pandas as pd


def create_cash_flow_sample() -> pd.DataFrame:
    """
    Create a valid QuickBooks Cash Flow Statement sample.

    Matches real QuickBooks format from /home/max/projects/QB-Assistant/data/cash_flows.csv:
    - Metadata rows (title, company, date)
    - Column headers
    - Three activity sections: OPERATING ACTIVITIES, INVESTING ACTIVITIES, FINANCING ACTIVITIES
    - Parent-child structure (Adjustments to reconcile...)
    - All 6 calculated rows (3x Net cash provided by..., NET CASH INCREASE, Cash at beginning/end)
    - Mixed currency formats: $1,887.47, 1,481.28, -2,853.02, -$2,832.50
    - Footer with timestamp

    Returns:
        DataFrame with QuickBooks Cash Flow Statement format
    """
    # Create list of rows matching QuickBooks format
    rows = [
        # Metadata rows (1-3)
        ['Statement of Cash Flows', ''],
        ["Craig's Design and Landscaping Services", ''],
        ['November 1-30, 2025', ''],
        # Blank row
        ['', ''],
        # Column header
        ['Full name', 'Total'],
        # OPERATING ACTIVITIES section
        ['OPERATING ACTIVITIES', ''],
        ['Net Income', '1,481.28'],
        ['Adjustments to reconcile Net Income to Net Cash provided by operations:', ''],
        ['Accounts Payable (A/P)', '-369.72'],
        ['Accounts Receivable (A/R)', '-2,853.02'],
        ['Board of Equalization Payable', '324.54'],
        ['Inventory Asset', '-596.25'],
        ['Loan Payable', '4,000.00'],
        ['Mastercard', '-99.36'],
        ['Total for Adjustments to reconcile Net Income to Net Cash provided by operations:', '$406.19'],
        ['Net cash provided by operating activities', '$1,887.47'],
        # INVESTING ACTIVITIES section (empty)
        ['INVESTING ACTIVITIES', ''],
        # FINANCING ACTIVITIES section
        ['FINANCING ACTIVITIES', ''],
        ['Notes Payable', '25,000.00'],
        ['Opening Balance Equity', '-27,832.50'],
        ['Net cash provided by financing activities', '-$2,832.50'],
        # Calculated summary rows
        ['NET CASH INCREASE FOR PERIOD', '-$945.03'],
        ['Cash at beginning of period', '$5,008.55'],
        ['CASH AT END OF PERIOD', '$4,063.52'],
        # Blank rows
        ['', ''],
        ['', ''],
        ['', ''],
        # Footer
        [' Monday, January 19, 2026 04:29 PM GMTZ', ''],
    ]

    # Create DataFrame
    df = pd.DataFrame(rows)
    return df


def create_malformed_cash_flow_sample(defect_type: str = 'missing_section') -> pd.DataFrame:
    """
    Create malformed Cash Flow Statement sample with specific defect.

    Args:
        defect_type: Type of defect to introduce. Options:
                    'missing_section' - Remove OPERATING ACTIVITIES section marker
                    'invalid_currency' - Add unparseable currency value
                    'missing_calculated' - Remove cash position rows

    Returns:
        DataFrame with specified defect
    """
    if defect_type == 'missing_section':
        # Create sample without OPERATING ACTIVITIES section marker
        rows = [
            ['Statement of Cash Flows', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['November 1-30, 2025', ''],
            ['', ''],
            ['Full name', 'Total'],
            # Missing OPERATING ACTIVITIES section marker
            ['Net Income', '1,481.28'],
            # INVESTING ACTIVITIES section (empty)
            ['INVESTING ACTIVITIES', ''],
            # FINANCING ACTIVITIES section
            ['FINANCING ACTIVITIES', ''],
            ['Notes Payable', '25,000.00'],
            ['Net cash provided by financing activities', '$25,000.00'],
            ['NET CASH INCREASE FOR PERIOD', '$25,000.00'],
            ['Cash at beginning of period', '$5,008.55'],
            ['CASH AT END OF PERIOD', '$30,008.55'],
            ['', ''],
            [' Monday, January 19, 2026 04:29 PM GMTZ', ''],
        ]

    elif defect_type == 'invalid_currency':
        # Create sample with invalid currency value
        rows = [
            ['Statement of Cash Flows', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['November 1-30, 2025', ''],
            ['', ''],
            ['Full name', 'Total'],
            ['OPERATING ACTIVITIES', ''],
            ['Net Income', 'invalid_amount'],  # Invalid currency
            ['Net cash provided by operating activities', '$1,887.47'],
            ['INVESTING ACTIVITIES', ''],
            ['FINANCING ACTIVITIES', ''],
            ['NET CASH INCREASE FOR PERIOD', '-$945.03'],
            ['Cash at beginning of period', '$5,008.55'],
            ['CASH AT END OF PERIOD', '$4,063.52'],
            ['', ''],
            [' Monday, January 19, 2026 04:29 PM GMTZ', ''],
        ]

    elif defect_type == 'missing_calculated':
        # Create sample without cash position rows
        rows = [
            ['Statement of Cash Flows', ''],
            ["Craig's Design and Landscaping Services", ''],
            ['November 1-30, 2025', ''],
            ['', ''],
            ['Full name', 'Total'],
            ['OPERATING ACTIVITIES', ''],
            ['Net Income', '1,481.28'],
            ['Net cash provided by operating activities', '$1,887.47'],
            ['INVESTING ACTIVITIES', ''],
            ['FINANCING ACTIVITIES', ''],
            ['Notes Payable', '25,000.00'],
            ['Net cash provided by financing activities', '$25,000.00'],
            # Missing: NET CASH INCREASE, Cash at beginning, CASH AT END
            ['', ''],
            [' Monday, January 19, 2026 04:29 PM GMTZ', ''],
        ]

    else:
        raise ValueError(f"Unknown defect type: {defect_type}")

    return pd.DataFrame(rows)
