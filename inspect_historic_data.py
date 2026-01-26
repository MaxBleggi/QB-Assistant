#!/usr/bin/env python3
"""
Detailed inspection of historic data parsing to verify monthly columns are preserved.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.loaders.file_loader import FileLoader
from src.parsers.historical_data_parser import HistoricalDataParser

def main():
    """Inspect historic data parsing in detail"""
    data_file = project_root / 'data' / 'historic_profit_loss.csv'

    print("="*60)
    print("HISTORIC DATA PARSING INSPECTION")
    print("="*60)

    loader = FileLoader()
    parser = HistoricalDataParser(loader)
    result = parser.parse(data_file)

    # Check periods detected
    periods = result.get_periods()
    print(f"\n1. PERIODS DETECTED:")
    print(f"   Count: {len(periods)}")
    print(f"   Labels: {periods[:3]}..." if len(periods) > 3 else f"   Labels: {periods}")

    # Check a sample account's values
    print(f"\n2. SAMPLE ACCOUNT VALUES:")
    income_section = result.get_income()
    if income_section and 'children' in income_section:
        for child in income_section['children'][:2]:  # First 2 income accounts
            if 'values' in child:
                print(f"\n   Account: {child['name']}")
                print(f"   Values count: {len(child['values'])}")
                # Show first 3 period values
                for i, (period, value) in enumerate(list(child['values'].items())[:3]):
                    print(f"     {period}: {value}")
                if len(child['values']) > 3:
                    print(f"     ... and {len(child['values']) - 3} more periods")

    # Check DataFrame columns
    print(f"\n3. DATAFRAME STRUCTURE:")
    print(f"   Shape: {result.shape}")
    print(f"   Columns: {result.columns}")

    # Show sample rows
    print(f"\n4. SAMPLE DATAFRAME ROWS:")
    print(result.head(3).to_string())

    # Check hierarchy structure
    print(f"\n5. HIERARCHY SECTIONS:")
    print(f"   Sections: {list(result.hierarchy.keys())}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
