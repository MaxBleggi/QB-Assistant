"""
Executive Summary Excel writer for high-level financial overview.

Generates Executive Summary sheet with current month metrics including revenue,
gross margin, operating cash flow, and net income with MoM/YoY trends.
"""
from typing import Optional
from .base_writer import BaseExcelWriter
from src.models import PLModel, BalanceSheetModel, CashFlowModel
from src.metrics.revenue_calculator import RevenueCalculator
from src.metrics.margin_calculator import MarginCalculator
from src.metrics.cash_flow_calculator import CashFlowCalculator
from src.metrics.exceptions import MissingPeriodError, ZeroDivisionError as MetricsZeroDivisionError


class ExecutiveSummaryWriter(BaseExcelWriter):
    """
    Excel writer for Executive Summary sheet.

    Creates comprehensive executive summary with revenue, profitability, and
    cash flow metrics with MoM/YoY growth trends and visual hierarchy.
    """

    def write(
        self,
        pl_model: PLModel,
        balance_sheet_model: BalanceSheetModel,
        cash_flow_model: CashFlowModel
    ) -> None:
        """
        Generate Executive Summary sheet from financial models.

        Args:
            pl_model: PLModel instance with P&L data
            balance_sheet_model: BalanceSheetModel instance with balance sheet data
            cash_flow_model: CashFlowModel instance with cash flow data
        """
        # Create Executive Summary sheet
        ws = self.workbook.create_sheet('Executive Summary')

        # Initialize calculators
        revenue_calc = RevenueCalculator(pl_model)
        margin_calc = MarginCalculator(pl_model)
        cash_flow_calc = CashFlowCalculator(cash_flow_model)

        # Get periods
        periods = pl_model.get_periods()
        if not periods:
            # No data - create empty sheet
            ws['A1'] = 'No data available'
            return

        # Current period is the most recent (last in list), excluding prior year periods
        non_py_periods = [p for p in periods if '(PY)' not in p]
        current_period = non_py_periods[-1]

        # Previous period for MoM comparison (if available)
        previous_period = non_py_periods[-2] if len(non_py_periods) >= 2 else None

        # Get total revenue for all periods
        total_revenue = revenue_calc.calculate_total_revenue()
        current_revenue = total_revenue.get(current_period, 0.0)

        # Track current row
        row = 1

        # === REVENUE SECTION ===
        ws[f'A{row}'] = 'Revenue'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Current revenue
        ws[f'A{row}'] = 'Current Period Revenue'
        ws[f'B{row}'] = current_revenue
        self.format_currency(ws, f'B{row}')
        row += 1

        # MoM growth
        if previous_period:
            try:
                mom_growth = revenue_calc.calculate_mom_growth(current_period, previous_period)
                growth_rate = mom_growth['growth_rate'] / 100  # Convert percentage to decimal
                ws[f'A{row}'] = 'MoM Growth'
                ws[f'B{row}'] = growth_rate
                self.format_percentage(ws, f'B{row}')
                # Add trend indicator
                ws[f'C{row}'] = ''  # Will be populated by apply_trend_indicator
                self.apply_trend_indicator(ws, f'C{row}', growth_rate)
                row += 1
            except (MissingPeriodError, MetricsZeroDivisionError):
                # Skip MoM if not calculable
                pass

        # YoY growth
        try:
            yoy_growth = revenue_calc.calculate_yoy_growth(current_period)
            growth_rate = yoy_growth['growth_rate'] / 100  # Convert percentage to decimal
            ws[f'A{row}'] = 'YoY Growth'
            ws[f'B{row}'] = growth_rate
            self.format_percentage(ws, f'B{row}')
            # Add trend indicator
            ws[f'C{row}'] = ''
            self.apply_trend_indicator(ws, f'C{row}', growth_rate)
            row += 1
        except (MissingPeriodError, MetricsZeroDivisionError):
            # Skip YoY if not calculable
            pass

        row += 1  # Blank row for spacing

        # === PROFITABILITY SECTION ===
        ws[f'A{row}'] = 'Profitability'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Gross margin
        try:
            gross_margins = margin_calc.calculate_gross_margin()
            current_gross_margin = gross_margins.get(current_period, 0.0) / 100  # Convert to decimal
            ws[f'A{row}'] = 'Gross Margin'
            ws[f'B{row}'] = current_gross_margin
            self.format_percentage(ws, f'B{row}')
            row += 1
        except Exception:
            # Skip if COGS not available (service business)
            pass

        # Net income with margin
        net_income_row = pl_model.get_calculated_row('Net Income')
        if net_income_row:
            net_income_values = net_income_row.get('values', {})
            current_net_income = net_income_values.get(current_period, 0.0)

            # Calculate net margin percentage
            net_margin = 0.0
            if current_revenue != 0:
                net_margin = current_net_income / current_revenue

            ws[f'A{row}'] = 'Net Income'
            ws[f'B{row}'] = current_net_income
            self.format_currency(ws, f'B{row}')

            # Add margin in parentheses in next cell
            ws[f'C{row}'] = f'({net_margin:.1%} margin)'
            row += 1

        row += 1  # Blank row for spacing

        # === CASH FLOW SECTION ===
        ws[f'A{row}'] = 'Cash Flow'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Operating cash flow
        operating_cf = cash_flow_calc.get_operating_cash_flow()
        current_operating_cf = operating_cf.get(current_period, 0.0)
        ws[f'A{row}'] = 'Operating Cash Flow'
        ws[f'B{row}'] = current_operating_cf
        self.format_currency(ws, f'B{row}')
        row += 1

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)
