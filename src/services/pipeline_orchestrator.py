"""
PipelineOrchestrator - Coordinates complete financial processing pipeline.

Integrates all Epic 1-6 services into end-to-end workflow:
parse files → calculate metrics → apply budget defaults → run forecasts → generate report.

Provides basic error handling with console logging for debugging.
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from ..loaders.file_loader import FileLoader
from ..parsers.balance_sheet_parser import BalanceSheetParser
from ..parsers.pl_parser import PLParser
from ..parsers.cash_flow_parser import CashFlowParser
from ..parsers.historical_data_parser import HistoricalDataParser
from ..models.global_config import GlobalConfigModel
from ..persistence.config_manager import ConfigManager
from ..metrics.kpi_calculator import KPICalculator
from ..services.budget_defaults import BudgetDefaultsService
from ..services.scenario_forecast_orchestrator import ScenarioForecastOrchestrator, load_scenarios
from ..exporters.base_writer import BaseExcelWriter
from ..exporters.executive_summary_writer import ExecutiveSummaryWriter
from ..exporters.kpi_dashboard_writer import KPIDashboardWriter
from ..exporters.budget_variance_writer import BudgetVarianceReportWriter
from ..exporters.cash_flow_forecast_writer import CashFlowForecastReportWriter
from ..exporters.pl_forecast_writer import PLForecastReportWriter
from ..exporters.metadata_documentation_writer import MetadataDocumentationWriter


class PipelineOrchestrator:
    """
    Orchestrates complete financial processing pipeline from file input to Excel report.

    Coordinates 6 Epic services in sequence with error handling and console logging.
    Returns result dictionary with status, report path, and any errors encountered.
    """

    def __init__(self, project_root: str):
        """
        Initialize orchestrator with project root for ConfigManager.

        Args:
            project_root: Absolute path to project root directory
        """
        self.project_root = Path(project_root)
        self.config_manager = ConfigManager(project_root)

    def _notify_progress(self, progress_callback: Optional[Callable[[str], None]], message: str) -> None:
        """
        Safely invoke progress callback with error handling.

        Wraps callback invocation in try/except to prevent callback errors
        from breaking the pipeline.

        Args:
            progress_callback: Optional callback function (may be None)
            message: Progress message to send to callback
        """
        if progress_callback is not None:
            try:
                progress_callback(message)
            except Exception as e:
                # Callback errors should not break pipeline - log and continue
                print(f"Warning: Progress callback raised exception: {e}")

    def process_pipeline(
        self,
        balance_sheet_path: str,
        pl_path: str,
        cash_flow_path: str,
        historical_path: Optional[str],
        client_name: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute complete processing pipeline from files to report.

        Pipeline stages:
        1. Load global and client configurations
        2. Parse 4 input files (Balance Sheet, P&L, Cash Flow, Historical)
        3. Calculate KPIs from parsed models
        4. Apply budget defaults using historical data
        5. Load forecast scenarios from client config
        6. Run multi-scenario forecasts
        7. Generate Excel report with all 6 writers
        8. Save report to client folder with timestamped filename

        Args:
            balance_sheet_path: Path to Balance Sheet CSV file
            pl_path: Path to P&L CSV file
            cash_flow_path: Path to Cash Flow CSV file
            historical_path: Path to Historical Data CSV file (optional, can be None)
            client_name: Client name for config loading and report saving
            progress_callback: Optional callback function for progress updates (receives status messages)

        Returns:
            Dict with keys:
                - 'status': 'success', 'partial', or 'failed'
                - 'report_path': Path to generated report (None if failed)
                - 'errors': List of error messages (empty if success)
        """
        errors = []
        result = {
            'status': 'failed',
            'report_path': None,
            'errors': errors
        }

        # === STAGE 1: Load Configurations ===
        self._notify_progress(progress_callback, "Loading configurations...")
        print("=== Stage 1: Loading configurations ===")
        try:
            # Load global config for forecast horizon
            global_config = self.config_manager.load_config(
                'config/global_settings.json',
                model_class=GlobalConfigModel
            )
            print(f"Global config loaded: forecast_horizon={global_config.forecast_horizon} months")

            # Load client config
            client_config_path = f'clients/{client_name}/config.yaml'
            client_config = self.config_manager.load_config(
                client_config_path,
                allow_external_path=True
            )
            print(f"Client config loaded for: {client_name}")

        except Exception as e:
            error_msg = f"Configuration loading failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            return result

        # === STAGE 2: Parse Input Files ===
        self._notify_progress(progress_callback, "Parsing Balance Sheet...")
        print("\n=== Stage 2: Parsing input files ===")
        try:
            # Create single FileLoader instance for all parsers
            file_loader = FileLoader()

            # Parse Balance Sheet
            print(f"Parsing Balance Sheet: {balance_sheet_path}")
            bs_parser = BalanceSheetParser(file_loader)
            balance_sheet_model = bs_parser.parse(balance_sheet_path)
            print(f"Balance Sheet parsed successfully")

            # Parse P&L
            self._notify_progress(progress_callback, "Parsing P&L...")
            print(f"Parsing P&L: {pl_path}")
            pl_parser = PLParser(file_loader)
            pl_model = pl_parser.parse(pl_path)
            print(f"P&L parsed successfully")

            # Parse Cash Flow
            self._notify_progress(progress_callback, "Parsing Cash Flow...")
            print(f"Parsing Cash Flow: {cash_flow_path}")
            cf_parser = CashFlowParser(file_loader)
            cash_flow_model = cf_parser.parse(cash_flow_path)
            print(f"Cash Flow parsed successfully")

            # Parse Historical Data (optional)
            historical_model = None
            if historical_path:
                print(f"Parsing Historical Data: {historical_path}")
                hist_parser = HistoricalDataParser(file_loader)
                historical_model = hist_parser.parse(historical_path)
                print(f"Historical Data parsed successfully")
            else:
                print("Historical Data not provided - will use fallback values for budget defaults")

        except Exception as e:
            error_msg = f"File parsing failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            return result

        # === STAGE 3: Calculate Metrics ===
        self._notify_progress(progress_callback, "Calculating financial metrics...")
        print("\n=== Stage 3: Calculating metrics ===")
        try:
            # Initialize KPI calculator with models
            kpi_calculator = KPICalculator(balance_sheet_model, cash_flow_model)
            print("KPI Calculator initialized")

            # KPI calculations are lazy - they'll be invoked by report writers
            print("Metrics calculation ready (lazy evaluation)")

        except Exception as e:
            error_msg = f"Metrics calculation setup failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            return result

        # === STAGE 4: Calculate Budget and Variance ===
        self._notify_progress(progress_callback, "Calculating budget variance...")
        print("\n=== Stage 4: Calculating budget and variance ===")
        variance_model = None
        try:
            # Step 1: Get intelligent defaults from historical data
            defaults_dict = BudgetDefaultsService.calculate_defaults(
                pl_model=historical_model if historical_model else pl_model,
                bs_model=None
            )
            print(f"Budget defaults calculated: {defaults_dict}")

            # Step 2: Create parameter model
            from ..models.parameters import ParameterModel
            param_model = ParameterModel(defaults_dict)

            # Step 3: Generate budget projections from historical data
            if historical_model:
                from ..services.budget_calculator import BudgetCalculator
                budget_calc = BudgetCalculator(historical_model, param_model)
                budget_model = budget_calc.calculate()
                print("Budget model generated from historical data")

                # Step 4: Calculate variance (budget vs current actual)
                from ..services.budget_variance_calculator import BudgetVarianceCalculator
                variance_calc = BudgetVarianceCalculator(budget_model, pl_model)
                variance_model = variance_calc.calculate(
                    threshold_pct=10.0,  # Flag variances > 10%
                    threshold_abs=1000.0  # Flag variances > $1000
                )
                print("Variance model calculated successfully")
            else:
                print("Warning: No historical data - skipping variance calculation")
                variance_model = None

        except Exception as e:
            error_msg = f"Budget variance calculation failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            # Continue with partial status - can still generate report without budget variance
            result['status'] = 'partial'
            variance_model = None

        # === STAGE 5: Load Forecast Scenarios ===
        self._notify_progress(progress_callback, "Loading forecast scenarios...")
        print("\n=== Stage 5: Loading forecast scenarios ===")
        try:
            # Load scenarios from client config directory
            client_config_dir = self.project_root / 'clients' / client_name
            scenarios_collection = load_scenarios(str(client_config_dir))
            scenario_count = len(scenarios_collection.list_scenarios())
            print(f"Loaded {scenario_count} forecast scenarios")

            if scenario_count == 0:
                print("Warning: No forecast scenarios found - forecasting stage will be skipped")

        except Exception as e:
            error_msg = f"Scenario loading failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            # Continue with partial status
            result['status'] = 'partial'
            scenarios_collection = None

        # === STAGE 6: Run Multi-Scenario Forecasts ===
        self._notify_progress(progress_callback, "Running forecast scenarios...")
        print("\n=== Stage 6: Running multi-scenario forecasts ===")
        multi_scenario_result = None
        if scenarios_collection and len(scenarios_collection.list_scenarios()) > 0:
            try:
                # Initialize forecast orchestrator
                forecast_orchestrator = ScenarioForecastOrchestrator(
                    cash_flow_model=cash_flow_model,
                    pl_model=pl_model,
                    scenarios_collection=scenarios_collection,
                    global_config=global_config,
                    anomaly_annotations=None  # Optional - could be loaded from config
                )
                print("Forecast orchestrator initialized")

                # Calculate forecasts for all scenarios
                multi_scenario_result = forecast_orchestrator.calculate_multi_scenario_forecasts()
                print(f"Multi-scenario forecasts calculated: {len(multi_scenario_result.list_scenarios())} scenarios")

            except Exception as e:
                error_msg = f"Forecast calculation failed: {type(e).__name__}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                # Continue with partial status - can generate report without forecasts
                result['status'] = 'partial'
                multi_scenario_result = None
        else:
            print("Skipping forecast stage - no scenarios available")
            result['status'] = 'partial' if result['status'] != 'failed' else result['status']

        # === STAGE 7: Generate Excel Report ===
        self._notify_progress(progress_callback, "Generating Excel report...")
        print("\n=== Stage 7: Generating Excel report ===")
        try:
            # Create base writer with shared workbook
            base_writer = BaseExcelWriter()
            print("Base Excel writer initialized")

            # Executive Summary sheet
            exec_writer = ExecutiveSummaryWriter()
            exec_writer.workbook = base_writer.workbook  # Share workbook
            exec_writer.write(pl_model, balance_sheet_model, cash_flow_model)
            print("Executive Summary sheet written")

            # KPI Dashboard sheet
            kpi_writer = KPIDashboardWriter()
            kpi_writer.workbook = base_writer.workbook
            kpi_writer.write(pl_model, balance_sheet_model, cash_flow_model)
            print("KPI Dashboard sheet written")

            # Budget Variance sheet (if variance model exists)
            if variance_model:
                budget_writer = BudgetVarianceReportWriter()
                budget_writer.workbook = base_writer.workbook
                budget_writer.write(variance_model)
                print("Budget vs Actual sheet written")

            # Cash Flow Forecast sheet (if multi_scenario_result exists)
            if multi_scenario_result:
                cf_forecast_writer = CashFlowForecastReportWriter()
                cf_forecast_writer.workbook = base_writer.workbook
                # Extract cash flow forecasts from multi-scenario result
                cf_forecast_model = self._extract_cash_flow_forecasts(multi_scenario_result)
                cf_forecast_writer.write(cf_forecast_model)
                print("Cash Flow Forecast sheet written")

            # P&L Forecast sheet (if multi_scenario_result exists)
            if multi_scenario_result:
                pl_forecast_writer = PLForecastReportWriter()
                pl_forecast_writer.workbook = base_writer.workbook
                # Extract P&L forecasts from multi-scenario result
                pl_forecast_model = self._extract_pl_forecasts(multi_scenario_result)
                pl_forecast_writer.write(pl_forecast_model)
                print("P&L Forecast sheet written")

            # Metadata Documentation sheets (if multi_scenario_result exists)
            if multi_scenario_result:
                metadata_writer = MetadataDocumentationWriter()
                metadata_writer.workbook = base_writer.workbook
                # Get scenarios and anomalies (use empty if not available)
                scenarios = scenarios_collection.list_scenarios() if scenarios_collection else []
                from ..models.anomaly_annotation import AnomalyAnnotationModel
                anomalies = AnomalyAnnotationModel()  # Empty model if no annotations
                metadata_writer.write(multi_scenario_result, scenarios, anomalies)
                print("Metadata and Methodology sheets written")

        except Exception as e:
            error_msg = f"Report generation failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            return result

        # === STAGE 8: Save Report to Client Folder ===
        self._notify_progress(progress_callback, "Saving report...")
        print("\n=== Stage 8: Saving report to client folder ===")
        try:
            # Create report filename with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d')
            # Replace spaces with underscores in client name
            safe_client_name = client_name.replace(' ', '_')
            report_filename = f"{safe_client_name}_Report_{timestamp}.xlsx"

            # Construct report path in client folder
            client_folder = self.project_root / 'clients' / client_name
            client_folder.mkdir(parents=True, exist_ok=True)
            report_path = client_folder / report_filename

            # Save workbook
            base_writer.save(str(report_path))
            print(f"Report saved successfully: {report_path}")

            # Update result with success
            result['status'] = 'success' if not errors else 'partial'
            result['report_path'] = str(report_path)

        except Exception as e:
            error_msg = f"Report save failed: {type(e).__name__}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            return result

        print("\n=== Pipeline execution complete ===")
        print(f"Status: {result['status']}")
        print(f"Report: {result['report_path']}")
        if errors:
            print(f"Errors encountered: {len(errors)}")
            for error in errors:
                print(f"  - {error}")

        return result

    def _extract_cash_flow_forecasts(self, multi_scenario_result):
        """
        Extract cash flow forecasts from MultiScenarioForecastResult.

        Args:
            multi_scenario_result: MultiScenarioForecastResult with scenario forecasts

        Returns:
            Object compatible with CashFlowForecastReportWriter (with scenarios attribute)
        """
        # Extract cash flow forecast models from each scenario
        scenarios = []
        for scenario_name, forecast_data in multi_scenario_result.scenario_forecasts.items():
            cf_forecast = forecast_data['cash_flow_forecast']
            scenarios.append(cf_forecast)

        # Create wrapper with scenarios attribute for writer
        class MultiScenarioCFWrapper:
            def __init__(self, scenarios_list):
                self.scenarios = scenarios_list

        return MultiScenarioCFWrapper(scenarios)

    def _extract_pl_forecasts(self, multi_scenario_result):
        """
        Extract P&L forecasts from MultiScenarioForecastResult.

        Args:
            multi_scenario_result: MultiScenarioForecastResult with scenario forecasts

        Returns:
            Object compatible with PLForecastReportWriter (with scenarios attribute)
        """
        # Extract P&L forecast models from each scenario
        scenarios = []
        for scenario_name, forecast_data in multi_scenario_result.scenario_forecasts.items():
            pl_forecast = forecast_data['pl_forecast']
            scenarios.append(pl_forecast)

        # Create wrapper with scenarios attribute for writer
        class MultiScenarioPLWrapper:
            def __init__(self, scenarios_list):
                self.scenarios = scenarios_list

        return MultiScenarioPLWrapper(scenarios)
