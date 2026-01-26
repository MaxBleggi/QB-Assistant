#!/usr/bin/env python3
"""
End-to-end pipeline test with real QuickBooks data.
Tests all stages: parsing → metrics → budget → forecasting → report generation.
"""
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.pipeline_orchestrator import PipelineOrchestrator
from src.persistence.config_manager import ConfigManager
import json

def create_test_config(config_dir: Path):
    """Create a minimal test configuration"""
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal config structure matching existing configs
    config_data = {
        "budget_parameters": {
            "revenue_growth_rate": 0.05,
            "budget_methodology": "Growth from Prior Year",
            "category_growth_rates": {},
            "expense_adjustment_factor": 1.0
        },
        "forecast_scenarios": {
            "scenarios": [
                {
                    "scenario_id": "test_scenario_1",
                    "scenario_name": "Realistic",
                    "description": "Test scenario for pipeline validation",
                    "created_date": datetime.now().isoformat(),
                    "parameters": {
                        "revenue_growth_rates": {
                            "monthly_rate": 0.05,
                            "use_averaged": True
                        },
                        "expense_trend_adjustments": {
                            "cogs_trend": 0.04,
                            "opex_trend": 0.03
                        },
                        "cash_flow_timing_params": {
                            "collection_period_days": 45,
                            "payment_terms_days": 30
                        },
                        "major_cash_events": {
                            "planned_capex": [],
                            "debt_payments": []
                        }
                    }
                }
            ]
        },
        "global_settings": {
            "forecast_horizon_months": 6,
            "confidence_level": 0.80
        }
    }

    # Write config file directly
    config_path = config_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)

    return config_data

def run_pipeline_test():
    """Run full pipeline with real data"""
    print("="*60)
    print("FULL PIPELINE TEST WITH REAL DATA")
    print("="*60)

    # Setup paths
    data_dir = project_root / 'data'
    test_client_dir = project_root / 'clients' / 'pipeline_test'
    config_dir = test_client_dir / 'config'
    output_dir = test_client_dir / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Data files
    balance_sheet_path = str(data_dir / 'balance sheet.csv')
    pl_path = str(data_dir / 'profit_loss.csv')
    cash_flow_path = str(data_dir / 'cash_flows.csv')
    historic_path = str(data_dir / 'historic_profit_loss.csv')

    # Create test config
    print("\n1. Creating test configuration...")
    config = create_test_config(config_dir)
    print(f"   ✓ Config created at {config_dir}")

    # Initialize orchestrator
    print("\n2. Initializing pipeline orchestrator...")
    orchestrator = PipelineOrchestrator(str(project_root))
    print(f"   ✓ Orchestrator initialized")

    # Run pipeline
    print("\n3. Running pipeline...")
    print(f"   - Balance Sheet: {Path(balance_sheet_path).name}")
    print(f"   - P&L: {Path(pl_path).name}")
    print(f"   - Cash Flow: {Path(cash_flow_path).name}")
    print(f"   - Historic: {Path(historic_path).name}")

    try:
        result = orchestrator.process_pipeline(
            balance_sheet_path=balance_sheet_path,
            pl_path=pl_path,
            cash_flow_path=cash_flow_path,
            historical_path=historic_path,
            client_name='pipeline_test',
            progress_callback=lambda msg: print(f"   {msg}")
        )

        print("\n4. RESULTS:")
        print(f"   Status: {result['status']}")

        if result['status'] == 'success':
            print(f"   ✓ Report generated: {result['report_path']}")
            print(f"\n   SUCCESS - Full pipeline completed without errors!")
            return 0
        elif result['status'] == 'partial':
            print(f"   ⚠ Partial success - some stages failed")
            print(f"   Report path: {result.get('report_path', 'N/A')}")
            print(f"\n   Errors encountered:")
            for error in result.get('errors', []):
                print(f"     - {error}")
            return 1
        else:
            print(f"   ✗ Pipeline failed")
            print(f"\n   Errors encountered:")
            for error in result.get('errors', []):
                print(f"     - {error}")
            return 1

    except Exception as e:
        print(f"\n   ✗ FATAL ERROR during pipeline execution:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print(f"\n   Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(run_pipeline_test())
