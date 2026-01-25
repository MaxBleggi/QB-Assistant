"""
Metadata and Documentation Excel writer for forecast report transparency.

Generates Report Info sheet (cover page with metadata) and Methodology sheet
(calculation approach, assumptions, excluded periods, confidence intervals) to help
business owners understand how forecasts were calculated.
"""
from typing import List
from datetime import datetime
from .base_writer import BaseExcelWriter
from src.models import ForecastScenarioModel, AnomalyAnnotationModel
from src.models.multi_scenario_forecast_result import MultiScenarioForecastResult


class MetadataDocumentationWriter(BaseExcelWriter):
    """
    Excel writer for Report Info and Methodology documentation sheets.

    Creates two documentation sheets providing transparency about forecast generation:
    - Report Info: Cover page with generation metadata (date, horizon, scenarios)
    - Methodology: Detailed documentation of calculation approach, assumptions,
                   excluded periods, and confidence interval interpretation
    """

    def write(
        self,
        multi_scenario_result: MultiScenarioForecastResult,
        scenarios: List[ForecastScenarioModel],
        anomalies: AnomalyAnnotationModel
    ) -> None:
        """
        Generate Report Info and Methodology documentation sheets.

        Args:
            multi_scenario_result: MultiScenarioForecastResult with forecast metadata
            scenarios: List of ForecastScenarioModel instances with parameters
            anomalies: AnomalyAnnotationModel with exclusion annotations
        """
        self.write_report_info_sheet(multi_scenario_result)
        self.write_methodology_sheet(multi_scenario_result, scenarios, anomalies)

    def write_report_info_sheet(self, multi_scenario_result: MultiScenarioForecastResult) -> None:
        """
        Create Report Info sheet as cover page with generation metadata.

        Args:
            multi_scenario_result: MultiScenarioForecastResult with metadata
        """
        # Create sheet
        ws = self.workbook.create_sheet('Report Info')

        # Track current row
        row = 1

        # === REPORT METADATA SECTION ===
        ws[f'A{row}'] = 'Report Metadata'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Generation date
        ws[f'A{row}'] = 'Generated On:'
        # Parse ISO timestamp to readable date
        try:
            created_dt = datetime.fromisoformat(multi_scenario_result.created_at)
            formatted_date = created_dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError):
            formatted_date = multi_scenario_result.created_at
        ws[f'B{row}'] = formatted_date
        row += 1

        # Forecast horizon
        ws[f'A{row}'] = 'Forecast Horizon:'
        horizon_months = multi_scenario_result.forecast_horizon
        ws[f'B{row}'] = f'{horizon_months} months'
        row += 1

        # Client identifier
        ws[f'A{row}'] = 'Client:'
        client_display = multi_scenario_result.client_id if multi_scenario_result.client_id else '[Client Name]'
        ws[f'B{row}'] = client_display
        row += 1

        row += 1  # Blank row for spacing

        # === INCLUDED SCENARIOS SECTION ===
        ws[f'A{row}'] = 'Included Scenarios'
        self.format_bold(ws, f'A{row}')
        row += 1

        # List all scenarios
        scenario_names = multi_scenario_result.list_scenarios()
        if scenario_names:
            scenarios_text = ', '.join(scenario_names)
            ws[f'A{row}'] = 'Scenarios:'
            ws[f'B{row}'] = scenarios_text
            row += 1
        else:
            ws[f'A{row}'] = 'No scenarios available'
            row += 1

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)

    def write_methodology_sheet(
        self,
        multi_scenario_result: MultiScenarioForecastResult,
        scenarios: List[ForecastScenarioModel],
        anomalies: AnomalyAnnotationModel
    ) -> None:
        """
        Create Methodology sheet with calculation approach, assumptions, and exclusions.

        Args:
            multi_scenario_result: MultiScenarioForecastResult with metadata
            scenarios: List of ForecastScenarioModel instances with parameters
            anomalies: AnomalyAnnotationModel with exclusion annotations
        """
        # Create sheet
        ws = self.workbook.create_sheet('Methodology')

        # Track current row
        row = 1

        # === METHODOLOGY SUMMARY SECTION ===
        ws[f'A{row}'] = 'Methodology Summary'
        self.format_bold(ws, f'A{row}')
        row += 1

        ws[f'A{row}'] = 'Forecast Approach:'
        row += 1
        ws[f'A{row}'] = 'This forecast uses Simple Growth Rate Projection, which applies historical growth rates to recent'
        row += 1
        ws[f'A{row}'] = 'financial data to project future performance. Growth rates are calculated from historical trends'
        row += 1
        ws[f'A{row}'] = 'and can be adjusted based on business expectations and market conditions.'
        row += 1

        row += 1  # Blank row

        # === CONFIDENCE INTERVALS SECTION ===
        ws[f'A{row}'] = 'Confidence Intervals'
        self.format_bold(ws, f'A{row}')
        row += 1

        ws[f'A{row}'] = 'Calculation Method:'
        row += 1
        ws[f'A{row}'] = 'Confidence intervals are calculated using the historical percentiles method, which analyzes'
        row += 1
        ws[f'A{row}'] = 'the historical variability in your financial data to estimate the range of possible outcomes.'
        row += 1

        row += 1  # Blank row

        ws[f'A{row}'] = 'Interpretation Guide:'
        self.format_bold(ws, f'A{row}')
        row += 1
        ws[f'A{row}'] = '80% confidence means we expect actual values to fall between Lower and Upper bounds 80% of the time.'
        row += 1
        ws[f'A{row}'] = 'The wider the confidence interval, the more uncertainty exists in the forecast.'
        row += 1

        row += 1  # Blank row

        # === ASSUMPTIONS SECTION ===
        ws[f'A{row}'] = 'Assumptions'
        self.format_bold(ws, f'A{row}')
        row += 1

        if scenarios:
            for scenario in scenarios:
                # Scenario name header
                ws[f'A{row}'] = f'Scenario: {scenario.scenario_name}'
                self.format_bold(ws, f'A{row}')
                row += 1

                # Description if available
                if scenario.description:
                    ws[f'A{row}'] = f'Description: {scenario.description}'
                    row += 1

                # Extract and display parameters
                parameters = scenario.parameters
                if parameters:
                    ws[f'A{row}'] = 'Parameters:'
                    row += 1

                    # Iterate over parameter key-value pairs
                    for param_key, param_value in parameters.items():
                        # Convert snake_case to Title Case for readability
                        param_label = param_key.replace('_', ' ').title()

                        # Format percentage parameters
                        if 'growth' in param_key.lower() or 'rate' in param_key.lower():
                            if isinstance(param_value, (int, float)):
                                display_value = f'{param_value * 100:.2f}%'
                            else:
                                display_value = str(param_value)
                        else:
                            display_value = str(param_value)

                        ws[f'A{row}'] = f'  {param_label}:'
                        ws[f'B{row}'] = display_value
                        row += 1
                else:
                    ws[f'A{row}'] = 'No parameters defined'
                    row += 1

                row += 1  # Blank row between scenarios
        else:
            ws[f'A{row}'] = 'No scenario assumptions available'
            row += 1

        row += 1  # Blank row

        # === EXCLUDED PERIODS SECTION ===
        ws[f'A{row}'] = 'Excluded Periods'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Get annotations
        annotations = anomalies.get_annotations()

        if annotations:
            ws[f'A{row}'] = 'The following periods were excluded from analysis due to identified anomalies:'
            row += 1
            row += 1

            # Table header
            ws[f'A{row}'] = 'Start Date'
            ws[f'B{row}'] = 'End Date'
            ws[f'C{row}'] = 'Metric'
            ws[f'D{row}'] = 'Reason'
            ws[f'E{row}'] = 'Excluded From'
            self.format_bold(ws, f'A{row}:E{row}')
            row += 1

            # Display each annotation
            for annotation in annotations:
                # Extract fields with fallbacks
                start_date = annotation.get('start_date', 'N/A')
                end_date = annotation.get('end_date', 'N/A')
                metric_name = annotation.get('metric_name', 'N/A')
                reason = annotation.get('reason', 'No reason provided')
                exclude_from = annotation.get('exclude_from', 'N/A')

                # Format dates if they're datetime objects or ISO strings
                if isinstance(start_date, str) and start_date != 'N/A':
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        start_date = start_dt.strftime('%Y-%m-%d')
                    except (ValueError, AttributeError):
                        pass

                if isinstance(end_date, str) and end_date != 'N/A':
                    try:
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        end_date = end_dt.strftime('%Y-%m-%d')
                    except (ValueError, AttributeError):
                        pass

                # Handle exclude_from as list
                if isinstance(exclude_from, list):
                    exclude_from = ', '.join(exclude_from)

                ws[f'A{row}'] = start_date
                ws[f'B{row}'] = end_date
                ws[f'C{row}'] = metric_name
                ws[f'D{row}'] = reason
                ws[f'E{row}'] = exclude_from
                row += 1
        else:
            ws[f'A{row}'] = 'No periods excluded from analysis'
            row += 1

        row += 1  # Blank row

        # === FOOTNOTES SECTION ===
        ws[f'A{row}'] = 'Footnotes'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Define common terms dictionary
        footnotes = {
            'MoM': 'Month-over-Month - Comparison of current month to previous month',
            'P&L': 'Profit & Loss - Statement showing revenues, costs, and expenses over a period',
            'Confidence Interval': 'Range within which we expect the actual value to fall with a given probability',
            'Growth Rate': 'Percentage change in a metric over time, typically month-over-month or year-over-year',
            'Scenario': 'A set of assumptions representing different possible future outcomes (e.g., Conservative, Expected, Optimistic)',
            'Baseline': 'Historical data used as the foundation for forecast calculations',
            'Historical Trend': 'The pattern of change observed in past financial data',
            'Forecast Horizon': 'The time period into the future that the forecast covers (e.g., 6 or 12 months)',
        }

        # Display footnotes
        for term, definition in footnotes.items():
            ws[f'A{row}'] = f'{term}:'
            ws[f'B{row}'] = definition
            row += 1

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)
