"""
KPI Dashboard Excel writer for financial metrics.

Generates KPI Dashboard sheet with financial metrics (current_ratio, burn_rate, cash_runway)
formatted as percentages or currency across periods.
"""
from typing import Dict, Any, Optional
from .base_writer import BaseExcelWriter
from src.metrics.kpi_calculator import KPICalculator


class KPIDashboardWriter(BaseExcelWriter):
    """
    Excel writer for KPI Dashboard sheet.

    Creates a sheet with financial metrics displayed as rows with periods as columns.
    Applies appropriate formatting (percentage for ratios, currency for cash metrics).
    """

    def write(
        self,
        balance_sheet_model,
        cash_flow_model
    ) -> None:
        """
        Generate KPI Dashboard sheet from balance sheet and cash flow models.

        Args:
            balance_sheet_model: BalanceSheetModel instance
            cash_flow_model: CashFlowModel instance
        """
        # Create KPI Dashboard sheet
        ws = self.workbook.create_sheet('KPI Dashboard')

        # Initialize KPICalculator
        kpi_calc = KPICalculator(balance_sheet_model, cash_flow_model)

        # Get KPI metrics
        current_ratio = kpi_calc.current_ratio()
        burn_rate = kpi_calc.burn_rate()
        cash_runway = kpi_calc.cash_runway()

        # Extract period labels from current_ratio (should be same for all metrics)
        periods = list(current_ratio.keys()) if current_ratio else []

        # Write header row
        ws['A1'] = 'Metric'
        for idx, period in enumerate(periods, start=2):
            ws.cell(row=1, column=idx, value=period)

        # Apply header style to entire header row
        header_range = f'A1:{chr(65 + len(periods))}1'
        self.apply_header_style(ws, header_range)

        # Write Current Ratio row
        ws['A2'] = 'Current Ratio'
        for idx, period in enumerate(periods, start=2):
            value = current_ratio.get(period)
            if value is not None:
                ws.cell(row=2, column=idx, value=value)

        # Format Current Ratio as percentage
        if periods:
            ratio_range = f'B2:{chr(65 + len(periods))}2'
            self.format_percentage(ws, ratio_range)

        # Write Burn Rate row
        ws['A3'] = 'Burn Rate'
        for idx, period in enumerate(periods, start=2):
            value = burn_rate.get(period)
            if value is not None:
                ws.cell(row=3, column=idx, value=value)

        # Format Burn Rate as currency
        if periods:
            burn_range = f'B3:{chr(65 + len(periods))}3'
            self.format_currency(ws, burn_range)

        # Write Cash Runway row
        ws['A4'] = 'Cash Runway (Days)'
        for idx, period in enumerate(periods, start=2):
            value = cash_runway.get(period)
            if value is not None:
                ws.cell(row=4, column=idx, value=value)

        # Cash Runway is in days (no special formatting, just number)
        # But we can apply currency format if desired, or leave as number

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)
