#!/usr/bin/env python3
"""
Test all parsers against real QuickBooks data files in data/
This will catch edge cases that synthetic data missed.
"""
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.loaders.file_loader import FileLoader
from src.parsers.balance_sheet_parser import BalanceSheetParser
from src.parsers.pl_parser import PLParser
from src.parsers.cash_flow_parser import CashFlowParser
from src.parsers.historical_data_parser import HistoricalDataParser

def test_parser(parser_class, file_path, name):
    """Test a single parser against a file"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"File: {file_path}")
    print(f"{'='*60}")

    try:
        loader = FileLoader()
        parser = parser_class(loader)
        result = parser.parse(file_path)

        print(f"✓ SUCCESS - {name} parsed without errors")
        print(f"  - DataFrame shape: {result.shape}")
        print(f"  - Hierarchy keys: {list(result.hierarchy.keys())}")

        # Show first few rows of parsed data
        print(f"\nFirst 5 rows of parsed data:")
        print(result.head())

        return True, result

    except Exception as e:
        print(f"✗ FAILED - {name}")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        return False, None

def main():
    """Run all parser tests"""
    data_dir = Path(__file__).parent / 'data'

    tests = [
        (BalanceSheetParser, data_dir / 'balance sheet.csv', 'Balance Sheet'),
        (PLParser, data_dir / 'profit_loss.csv', 'Profit & Loss'),
        (CashFlowParser, data_dir / 'cash_flows.csv', 'Cash Flow'),
        (HistoricalDataParser, data_dir / 'historic_profit_loss.csv', 'Historical P&L'),
    ]

    results = []
    for parser_class, file_path, name in tests:
        success, result = test_parser(parser_class, file_path, name)
        results.append((name, success, result))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, _ in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} parsers passed")

    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
