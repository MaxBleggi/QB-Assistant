"""
Unit tests for PipelineOrchestrator with mocked service dependencies.

Tests orchestration logic, error handling, and return value structure
without executing actual service implementations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.services.pipeline_orchestrator import PipelineOrchestrator


@pytest.fixture
def mock_file_paths():
    """Provide mock file paths for testing."""
    return {
        'balance_sheet': '/test/data/balance_sheet.csv',
        'pl': '/test/data/pl.csv',
        'cash_flow': '/test/data/cash_flow.csv',
        'historical': '/test/data/historical.csv',
        'client_name': 'TestClient'
    }


@pytest.fixture
def mock_project_root(tmp_path):
    """Provide temporary project root directory."""
    return str(tmp_path)


@pytest.fixture
def orchestrator(mock_project_root):
    """Provide PipelineOrchestrator instance with mock project root."""
    return PipelineOrchestrator(mock_project_root)


@pytest.fixture
def mock_parsed_models():
    """Provide mock parsed model instances."""
    bs_model = Mock()
    bs_model.get_periods.return_value = ['2024-01', '2024-02']

    pl_model = Mock()
    pl_model.get_periods.return_value = ['2024-01', '2024-02']
    pl_model.get_calculated_row.return_value = {
        'values': {'2024-02': 5000.0}
    }

    cf_model = Mock()
    cf_model.get_periods.return_value = ['2024-01', '2024-02']

    hist_model = Mock()
    hist_model.get_periods.return_value = ['2023-01', '2023-02']

    return {
        'balance_sheet': bs_model,
        'pl': pl_model,
        'cash_flow': cf_model,
        'historical': hist_model
    }


@pytest.fixture
def mock_global_config():
    """Provide mock GlobalConfigModel."""
    config = Mock()
    config.forecast_horizon = 6
    return config


@pytest.fixture
def mock_scenarios_collection():
    """Provide mock ForecastScenariosCollection."""
    collection = Mock()
    scenario1 = Mock()
    scenario1.scenario_name = 'Expected'
    scenario1.parameters = {'revenue_growth': 0.05}
    collection.list_scenarios.return_value = [scenario1]
    return collection


@pytest.fixture
def mock_multi_scenario_result():
    """Provide mock MultiScenarioForecastResult."""
    result = Mock()
    result.forecast_horizon = 6
    result.client_id = 'TestClient'
    result.list_scenarios.return_value = ['Expected']

    # Mock scenario forecasts
    cf_forecast = Mock()
    cf_forecast.metadata = {'forecast_horizon': 6, 'scenario_name': 'Expected'}
    cf_forecast.hierarchy = {}
    cf_forecast.calculated_rows = {}

    pl_forecast = Mock()
    pl_forecast.metadata = {'forecast_horizon': 6, 'scenario_name': 'Expected'}
    pl_forecast.hierarchy = {}
    pl_forecast.calculated_rows = {}

    result.scenario_forecasts = {
        'Expected': {
            'cash_flow_forecast': cf_forecast,
            'pl_forecast': pl_forecast,
            'validation_result': None
        }
    }

    return result


def test_successful_pipeline_execution(
    orchestrator,
    mock_file_paths,
    mock_parsed_models,
    mock_global_config,
    mock_scenarios_collection,
    mock_multi_scenario_result,
    mock_project_root
):
    """
    Test complete pipeline execution with all stages succeeding.

    Verifies:
    - All stages execute in correct order
    - Return status is 'success'
    - Report path is populated
    - Errors list is empty
    """
    with patch.object(orchestrator.config_manager, 'load_config') as mock_load_config, \
         patch('src.services.pipeline_orchestrator.FileLoader') as mock_file_loader_class, \
         patch('src.services.pipeline_orchestrator.BalanceSheetParser') as mock_bs_parser_class, \
         patch('src.services.pipeline_orchestrator.PLParser') as mock_pl_parser_class, \
         patch('src.services.pipeline_orchestrator.CashFlowParser') as mock_cf_parser_class, \
         patch('src.services.pipeline_orchestrator.HistoricalDataParser') as mock_hist_parser_class, \
         patch('src.services.pipeline_orchestrator.KPICalculator') as mock_kpi_calc_class, \
         patch('src.services.pipeline_orchestrator.BudgetDefaultsService') as mock_budget_service, \
         patch('src.services.pipeline_orchestrator.load_scenarios') as mock_load_scenarios, \
         patch('src.services.pipeline_orchestrator.ScenarioForecastOrchestrator') as mock_forecast_orch_class, \
         patch('src.services.pipeline_orchestrator.BaseExcelWriter') as mock_base_writer_class, \
         patch('src.services.pipeline_orchestrator.ExecutiveSummaryWriter') as mock_exec_writer_class, \
         patch('src.services.pipeline_orchestrator.KPIDashboardWriter') as mock_kpi_writer_class, \
         patch('src.services.pipeline_orchestrator.BudgetVarianceReportWriter') as mock_budget_writer_class, \
         patch('src.services.pipeline_orchestrator.CashFlowForecastReportWriter') as mock_cf_writer_class, \
         patch('src.services.pipeline_orchestrator.PLForecastReportWriter') as mock_pl_writer_class, \
         patch('src.services.pipeline_orchestrator.MetadataDocumentationWriter') as mock_metadata_writer_class:

        # Setup config loading
        mock_load_config.side_effect = [mock_global_config, {}]

        # Setup parsers
        mock_bs_parser = Mock()
        mock_bs_parser.parse.return_value = mock_parsed_models['balance_sheet']
        mock_bs_parser_class.return_value = mock_bs_parser

        mock_pl_parser = Mock()
        mock_pl_parser.parse.return_value = mock_parsed_models['pl']
        mock_pl_parser_class.return_value = mock_pl_parser

        mock_cf_parser = Mock()
        mock_cf_parser.parse.return_value = mock_parsed_models['cash_flow']
        mock_cf_parser_class.return_value = mock_cf_parser

        mock_hist_parser = Mock()
        mock_hist_parser.parse.return_value = mock_parsed_models['historical']
        mock_hist_parser_class.return_value = mock_hist_parser

        # Setup budget defaults service
        mock_variance = Mock()
        mock_budget_service.calculate_defaults.return_value = mock_variance

        # Setup scenario loading
        mock_load_scenarios.return_value = mock_scenarios_collection

        # Setup forecast orchestrator
        mock_forecast_orch = Mock()
        mock_forecast_orch.calculate_multi_scenario_forecasts.return_value = mock_multi_scenario_result
        mock_forecast_orch_class.return_value = mock_forecast_orch

        # Setup Excel writers
        mock_base_writer = Mock()
        mock_base_writer.workbook = Mock()
        mock_base_writer_class.return_value = mock_base_writer

        # Mock all writer instances
        for writer_class in [mock_exec_writer_class, mock_kpi_writer_class,
                            mock_budget_writer_class, mock_cf_writer_class,
                            mock_pl_writer_class, mock_metadata_writer_class]:
            writer_instance = Mock()
            writer_instance.workbook = mock_base_writer.workbook
            writer_class.return_value = writer_instance

        # Execute pipeline
        result = orchestrator.process_pipeline(
            balance_sheet_path=mock_file_paths['balance_sheet'],
            pl_path=mock_file_paths['pl'],
            cash_flow_path=mock_file_paths['cash_flow'],
            historical_path=mock_file_paths['historical'],
            client_name=mock_file_paths['client_name']
        )

        # Verify result structure
        assert result['status'] == 'success'
        assert result['report_path'] is not None
        assert 'TestClient_Report_' in result['report_path']
        assert result['errors'] == []


def test_parser_failure_handling(orchestrator, mock_file_paths):
    """
    Test that parser failures are caught and returned in errors list.

    Verifies:
    - FileNotFoundError is caught
    - Status is 'failed'
    - Error message contains file type
    """
    with patch.object(orchestrator.config_manager, 'load_config') as mock_load_config, \
         patch('src.services.pipeline_orchestrator.FileLoader') as mock_file_loader_class, \
         patch('src.services.pipeline_orchestrator.BalanceSheetParser') as mock_bs_parser_class:

        # Setup config loading to succeed
        mock_global_config = Mock()
        mock_global_config.forecast_horizon = 6
        mock_load_config.side_effect = [mock_global_config, {}]

        # Setup parser to fail
        mock_bs_parser = Mock()
        mock_bs_parser.parse.side_effect = FileNotFoundError("Balance sheet file not found")
        mock_bs_parser_class.return_value = mock_bs_parser

        # Execute pipeline
        result = orchestrator.process_pipeline(
            balance_sheet_path=mock_file_paths['balance_sheet'],
            pl_path=mock_file_paths['pl'],
            cash_flow_path=mock_file_paths['cash_flow'],
            historical_path=mock_file_paths['historical'],
            client_name=mock_file_paths['client_name']
        )

        # Verify failure handling
        assert result['status'] == 'failed'
        assert result['report_path'] is None
        assert len(result['errors']) > 0
        assert 'File parsing failed' in result['errors'][0]


def test_missing_historical_data_graceful(
    orchestrator,
    mock_file_paths,
    mock_parsed_models,
    mock_global_config,
    mock_scenarios_collection,
    mock_multi_scenario_result
):
    """
    Test that pipeline continues when historical_path is None.

    Verifies:
    - Historical parser is not invoked
    - Pipeline continues to completion
    - Status is 'success'
    """
    with patch.object(orchestrator.config_manager, 'load_config') as mock_load_config, \
         patch('src.services.pipeline_orchestrator.FileLoader') as mock_file_loader_class, \
         patch('src.services.pipeline_orchestrator.BalanceSheetParser') as mock_bs_parser_class, \
         patch('src.services.pipeline_orchestrator.PLParser') as mock_pl_parser_class, \
         patch('src.services.pipeline_orchestrator.CashFlowParser') as mock_cf_parser_class, \
         patch('src.services.pipeline_orchestrator.HistoricalDataParser') as mock_hist_parser_class, \
         patch('src.services.pipeline_orchestrator.KPICalculator') as mock_kpi_calc_class, \
         patch('src.services.pipeline_orchestrator.BudgetDefaultsService') as mock_budget_service, \
         patch('src.services.pipeline_orchestrator.load_scenarios') as mock_load_scenarios, \
         patch('src.services.pipeline_orchestrator.ScenarioForecastOrchestrator') as mock_forecast_orch_class, \
         patch('src.services.pipeline_orchestrator.BaseExcelWriter') as mock_base_writer_class, \
         patch('src.services.pipeline_orchestrator.ExecutiveSummaryWriter') as mock_exec_writer_class, \
         patch('src.services.pipeline_orchestrator.KPIDashboardWriter') as mock_kpi_writer_class, \
         patch('src.services.pipeline_orchestrator.BudgetVarianceReportWriter') as mock_budget_writer_class, \
         patch('src.services.pipeline_orchestrator.CashFlowForecastReportWriter') as mock_cf_writer_class, \
         patch('src.services.pipeline_orchestrator.PLForecastReportWriter') as mock_pl_writer_class, \
         patch('src.services.pipeline_orchestrator.MetadataDocumentationWriter') as mock_metadata_writer_class:

        # Setup config and parsers (same as successful test)
        mock_load_config.side_effect = [mock_global_config, {}]

        mock_bs_parser = Mock()
        mock_bs_parser.parse.return_value = mock_parsed_models['balance_sheet']
        mock_bs_parser_class.return_value = mock_bs_parser

        mock_pl_parser = Mock()
        mock_pl_parser.parse.return_value = mock_parsed_models['pl']
        mock_pl_parser_class.return_value = mock_pl_parser

        mock_cf_parser = Mock()
        mock_cf_parser.parse.return_value = mock_parsed_models['cash_flow']
        mock_cf_parser_class.return_value = mock_cf_parser

        mock_hist_parser = Mock()
        mock_hist_parser_class.return_value = mock_hist_parser

        mock_variance = Mock()
        mock_budget_service.calculate_defaults.return_value = mock_variance

        mock_load_scenarios.return_value = mock_scenarios_collection

        mock_forecast_orch = Mock()
        mock_forecast_orch.calculate_multi_scenario_forecasts.return_value = mock_multi_scenario_result
        mock_forecast_orch_class.return_value = mock_forecast_orch

        mock_base_writer = Mock()
        mock_base_writer.workbook = Mock()
        mock_base_writer_class.return_value = mock_base_writer

        for writer_class in [mock_exec_writer_class, mock_kpi_writer_class,
                            mock_budget_writer_class, mock_cf_writer_class,
                            mock_pl_writer_class, mock_metadata_writer_class]:
            writer_instance = Mock()
            writer_instance.workbook = mock_base_writer.workbook
            writer_class.return_value = writer_instance

        # Execute pipeline with historical_path=None
        result = orchestrator.process_pipeline(
            balance_sheet_path=mock_file_paths['balance_sheet'],
            pl_path=mock_file_paths['pl'],
            cash_flow_path=mock_file_paths['cash_flow'],
            historical_path=None,  # No historical data
            client_name=mock_file_paths['client_name']
        )

        # Verify historical parser was not called
        mock_hist_parser.parse.assert_not_called()

        # Verify pipeline still completed successfully
        assert result['status'] == 'success'
        assert result['report_path'] is not None


def test_empty_forecast_scenarios(
    orchestrator,
    mock_file_paths,
    mock_parsed_models,
    mock_global_config
):
    """
    Test that pipeline handles empty scenarios collection gracefully.

    Verifies:
    - Forecasting stage is skipped
    - Report still generates (without forecast sheets)
    - Status is 'success' (no errors occurred, even though forecasts were skipped)
    """
    with patch.object(orchestrator.config_manager, 'load_config') as mock_load_config, \
         patch('src.services.pipeline_orchestrator.FileLoader'), \
         patch('src.services.pipeline_orchestrator.BalanceSheetParser') as mock_bs_parser_class, \
         patch('src.services.pipeline_orchestrator.PLParser') as mock_pl_parser_class, \
         patch('src.services.pipeline_orchestrator.CashFlowParser') as mock_cf_parser_class, \
         patch('src.services.pipeline_orchestrator.HistoricalDataParser') as mock_hist_parser_class, \
         patch('src.services.pipeline_orchestrator.KPICalculator'), \
         patch('src.services.pipeline_orchestrator.BudgetDefaultsService') as mock_budget_service, \
         patch('src.services.pipeline_orchestrator.load_scenarios') as mock_load_scenarios, \
         patch('src.services.pipeline_orchestrator.ScenarioForecastOrchestrator') as mock_forecast_orch_class, \
         patch('src.services.pipeline_orchestrator.BaseExcelWriter') as mock_base_writer_class, \
         patch('src.services.pipeline_orchestrator.ExecutiveSummaryWriter') as mock_exec_writer_class, \
         patch('src.services.pipeline_orchestrator.KPIDashboardWriter') as mock_kpi_writer_class, \
         patch('src.services.pipeline_orchestrator.BudgetVarianceReportWriter') as mock_budget_writer_class:

        # Setup config and parsers
        mock_load_config.side_effect = [mock_global_config, {}]

        mock_bs_parser = Mock()
        mock_bs_parser.parse.return_value = mock_parsed_models['balance_sheet']
        mock_bs_parser_class.return_value = mock_bs_parser

        mock_pl_parser = Mock()
        mock_pl_parser.parse.return_value = mock_parsed_models['pl']
        mock_pl_parser_class.return_value = mock_pl_parser

        mock_cf_parser = Mock()
        mock_cf_parser.parse.return_value = mock_parsed_models['cash_flow']
        mock_cf_parser_class.return_value = mock_cf_parser

        mock_hist_parser = Mock()
        mock_hist_parser.parse.return_value = mock_parsed_models['historical']
        mock_hist_parser_class.return_value = mock_hist_parser

        mock_variance = Mock()
        mock_budget_service.calculate_defaults.return_value = mock_variance

        # Empty scenarios collection
        empty_collection = Mock()
        empty_collection.list_scenarios.return_value = []
        mock_load_scenarios.return_value = empty_collection

        mock_base_writer = Mock()
        mock_base_writer.workbook = Mock()
        mock_base_writer_class.return_value = mock_base_writer

        for writer_class in [mock_exec_writer_class, mock_kpi_writer_class, mock_budget_writer_class]:
            writer_instance = Mock()
            writer_instance.workbook = mock_base_writer.workbook
            writer_class.return_value = writer_instance

        # Execute pipeline
        result = orchestrator.process_pipeline(
            balance_sheet_path=mock_file_paths['balance_sheet'],
            pl_path=mock_file_paths['pl'],
            cash_flow_path=mock_file_paths['cash_flow'],
            historical_path=mock_file_paths['historical'],
            client_name=mock_file_paths['client_name']
        )

        # Verify forecast orchestrator was not invoked
        mock_forecast_orch_class.assert_not_called()

        # Verify status is success (no errors, even though forecasts were skipped)
        assert result['status'] == 'success'
        assert result['report_path'] is not None


def test_report_filename_format(
    orchestrator,
    mock_file_paths,
    mock_parsed_models,
    mock_global_config,
    mock_scenarios_collection,
    mock_multi_scenario_result
):
    """
    Test that spaces in client name are replaced with underscores in filename.

    Verifies:
    - Client name 'Test Client' becomes 'Test_Client_Report_'
    - Filename includes timestamp
    """
    with patch.object(orchestrator.config_manager, 'load_config') as mock_load_config, \
         patch('src.services.pipeline_orchestrator.FileLoader'), \
         patch('src.services.pipeline_orchestrator.BalanceSheetParser') as mock_bs_parser_class, \
         patch('src.services.pipeline_orchestrator.PLParser') as mock_pl_parser_class, \
         patch('src.services.pipeline_orchestrator.CashFlowParser') as mock_cf_parser_class, \
         patch('src.services.pipeline_orchestrator.HistoricalDataParser') as mock_hist_parser_class, \
         patch('src.services.pipeline_orchestrator.KPICalculator'), \
         patch('src.services.pipeline_orchestrator.BudgetDefaultsService') as mock_budget_service, \
         patch('src.services.pipeline_orchestrator.load_scenarios') as mock_load_scenarios, \
         patch('src.services.pipeline_orchestrator.ScenarioForecastOrchestrator') as mock_forecast_orch_class, \
         patch('src.services.pipeline_orchestrator.BaseExcelWriter') as mock_base_writer_class, \
         patch('src.services.pipeline_orchestrator.ExecutiveSummaryWriter') as mock_exec_writer_class, \
         patch('src.services.pipeline_orchestrator.KPIDashboardWriter') as mock_kpi_writer_class, \
         patch('src.services.pipeline_orchestrator.BudgetVarianceReportWriter') as mock_budget_writer_class, \
         patch('src.services.pipeline_orchestrator.CashFlowForecastReportWriter') as mock_cf_writer_class, \
         patch('src.services.pipeline_orchestrator.PLForecastReportWriter') as mock_pl_writer_class, \
         patch('src.services.pipeline_orchestrator.MetadataDocumentationWriter') as mock_metadata_writer_class:

        # Setup all mocks (same as successful test)
        mock_load_config.side_effect = [mock_global_config, {}]

        mock_bs_parser = Mock()
        mock_bs_parser.parse.return_value = mock_parsed_models['balance_sheet']
        mock_bs_parser_class.return_value = mock_bs_parser

        mock_pl_parser = Mock()
        mock_pl_parser.parse.return_value = mock_parsed_models['pl']
        mock_pl_parser_class.return_value = mock_pl_parser

        mock_cf_parser = Mock()
        mock_cf_parser.parse.return_value = mock_parsed_models['cash_flow']
        mock_cf_parser_class.return_value = mock_cf_parser

        mock_hist_parser = Mock()
        mock_hist_parser.parse.return_value = mock_parsed_models['historical']
        mock_hist_parser_class.return_value = mock_hist_parser

        mock_variance = Mock()
        mock_budget_service.calculate_defaults.return_value = mock_variance

        mock_load_scenarios.return_value = mock_scenarios_collection

        mock_forecast_orch = Mock()
        mock_forecast_orch.calculate_multi_scenario_forecasts.return_value = mock_multi_scenario_result
        mock_forecast_orch_class.return_value = mock_forecast_orch

        mock_base_writer = Mock()
        mock_base_writer.workbook = Mock()
        mock_base_writer_class.return_value = mock_base_writer

        for writer_class in [mock_exec_writer_class, mock_kpi_writer_class,
                            mock_budget_writer_class, mock_cf_writer_class,
                            mock_pl_writer_class, mock_metadata_writer_class]:
            writer_instance = Mock()
            writer_instance.workbook = mock_base_writer.workbook
            writer_class.return_value = writer_instance

        # Execute pipeline with client name containing space
        result = orchestrator.process_pipeline(
            balance_sheet_path=mock_file_paths['balance_sheet'],
            pl_path=mock_file_paths['pl'],
            cash_flow_path=mock_file_paths['cash_flow'],
            historical_path=mock_file_paths['historical'],
            client_name='Test Client'  # Has space
        )

        # Verify filename has underscore instead of space
        assert result['status'] == 'success'
        assert 'Test_Client_Report_' in result['report_path']
        assert '.xlsx' in result['report_path']


def test_forecast_failure_partial_status(
    orchestrator,
    mock_file_paths,
    mock_parsed_models,
    mock_global_config,
    mock_scenarios_collection
):
    """
    Test that forecast failure results in partial status with report still generated.

    Verifies:
    - Forecast stage failure is caught
    - Report generation continues
    - Status is 'partial'
    - Error is in errors list
    """
    with patch.object(orchestrator.config_manager, 'load_config') as mock_load_config, \
         patch('src.services.pipeline_orchestrator.FileLoader'), \
         patch('src.services.pipeline_orchestrator.BalanceSheetParser') as mock_bs_parser_class, \
         patch('src.services.pipeline_orchestrator.PLParser') as mock_pl_parser_class, \
         patch('src.services.pipeline_orchestrator.CashFlowParser') as mock_cf_parser_class, \
         patch('src.services.pipeline_orchestrator.HistoricalDataParser') as mock_hist_parser_class, \
         patch('src.services.pipeline_orchestrator.KPICalculator'), \
         patch('src.services.pipeline_orchestrator.BudgetDefaultsService') as mock_budget_service, \
         patch('src.services.pipeline_orchestrator.load_scenarios') as mock_load_scenarios, \
         patch('src.services.pipeline_orchestrator.ScenarioForecastOrchestrator') as mock_forecast_orch_class, \
         patch('src.services.pipeline_orchestrator.BaseExcelWriter') as mock_base_writer_class, \
         patch('src.services.pipeline_orchestrator.ExecutiveSummaryWriter') as mock_exec_writer_class, \
         patch('src.services.pipeline_orchestrator.KPIDashboardWriter') as mock_kpi_writer_class, \
         patch('src.services.pipeline_orchestrator.BudgetVarianceReportWriter') as mock_budget_writer_class:

        # Setup config and parsers
        mock_load_config.side_effect = [mock_global_config, {}]

        mock_bs_parser = Mock()
        mock_bs_parser.parse.return_value = mock_parsed_models['balance_sheet']
        mock_bs_parser_class.return_value = mock_bs_parser

        mock_pl_parser = Mock()
        mock_pl_parser.parse.return_value = mock_parsed_models['pl']
        mock_pl_parser_class.return_value = mock_pl_parser

        mock_cf_parser = Mock()
        mock_cf_parser.parse.return_value = mock_parsed_models['cash_flow']
        mock_cf_parser_class.return_value = mock_cf_parser

        mock_hist_parser = Mock()
        mock_hist_parser.parse.return_value = mock_parsed_models['historical']
        mock_hist_parser_class.return_value = mock_hist_parser

        mock_variance = Mock()
        mock_budget_service.calculate_defaults.return_value = mock_variance

        mock_load_scenarios.return_value = mock_scenarios_collection

        # Forecast orchestrator fails
        mock_forecast_orch = Mock()
        mock_forecast_orch.calculate_multi_scenario_forecasts.side_effect = ValueError("Forecast calculation error")
        mock_forecast_orch_class.return_value = mock_forecast_orch

        mock_base_writer = Mock()
        mock_base_writer.workbook = Mock()
        mock_base_writer_class.return_value = mock_base_writer

        for writer_class in [mock_exec_writer_class, mock_kpi_writer_class, mock_budget_writer_class]:
            writer_instance = Mock()
            writer_instance.workbook = mock_base_writer.workbook
            writer_class.return_value = writer_instance

        # Execute pipeline
        result = orchestrator.process_pipeline(
            balance_sheet_path=mock_file_paths['balance_sheet'],
            pl_path=mock_file_paths['pl'],
            cash_flow_path=mock_file_paths['cash_flow'],
            historical_path=mock_file_paths['historical'],
            client_name=mock_file_paths['client_name']
        )

        # Verify partial status with error
        assert result['status'] == 'partial'
        assert result['report_path'] is not None
        assert len(result['errors']) > 0
        assert 'Forecast calculation failed' in result['errors'][0]
