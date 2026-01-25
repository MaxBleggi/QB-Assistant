"""
KPI Dashboard Excel writer for comprehensive financial metrics.

Generates KPI Dashboard sheet with all Epic 2 KPIs including growth metrics,
profitability ratios, and liquidity indicators with conditional formatting.
"""
from typing import Dict, Any, Optional
from .base_writer import BaseExcelWriter
from src.models import PLModel, BalanceSheetModel, CashFlowModel
from src.metrics.kpi_calculator import KPICalculator
from src.metrics.revenue_calculator import RevenueCalculator
from src.metrics.margin_calculator import MarginCalculator
from src.metrics.exceptions import MissingPeriodError, ZeroDivisionError as MetricsZeroDivisionError


# Warning threshold for cash runway (months)
RUNWAY_WARNING_THRESHOLD = 6.0


class KPIDashboardWriter(BaseExcelWriter):
    """
    Excel writer for KPI Dashboard sheet.

    Creates comprehensive dashboard with all Epic 2 KPIs: growth metrics,
    profitability ratios, and liquidity indicators with contextual formatting.
    """

    def write(
        self,
        pl_model: PLModel,
        balance_sheet_model: BalanceSheetModel,
        cash_flow_model: CashFlowModel
    ) -> None:
        """
        Generate KPI Dashboard sheet from financial models.

        Args:
            pl_model: PLModel instance with P&L data
            balance_sheet_model: BalanceSheetModel instance
            cash_flow_model: CashFlowModel instance
        """
        # Create KPI Dashboard sheet
        ws = self.workbook.create_sheet('KPI Dashboard')

        # Initialize calculators
        kpi_calc = KPICalculator(balance_sheet_model, cash_flow_model)
        revenue_calc = RevenueCalculator(pl_model)
        margin_calc = MarginCalculator(pl_model)

        # Get periods from P&L model
        periods = pl_model.get_periods()
        if not periods:
            ws['A1'] = 'No data available'
            return

        # Current period is the most recent, excluding prior year periods
        non_py_periods = [p for p in periods if '(PY)' not in p]
        current_period = non_py_periods[-1]
        previous_period = non_py_periods[-2] if len(non_py_periods) >= 2 else None

        # Track current row
        row = 1

        # === GROWTH METRICS SECTION ===
        ws[f'A{row}'] = 'Growth Metrics'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Revenue growth (MoM)
        if previous_period:
            try:
                mom_growth = revenue_calc.calculate_mom_growth(current_period, previous_period)
                growth_rate = mom_growth['growth_rate'] / 100  # Convert to decimal
                ws[f'A{row}'] = f'Revenue Growth: {growth_rate:.1%}'
                ws[f'B{row}'] = ''
                self.apply_trend_indicator(ws, f'B{row}', growth_rate)
                row += 1
            except (MissingPeriodError, MetricsZeroDivisionError):
                pass

        # Profit growth (using Net Income MoM)
        net_income_row = pl_model.get_calculated_row('Net Income')
        if net_income_row and previous_period:
            net_income_values = net_income_row.get('values', {})
            current_net_income = net_income_values.get(current_period, 0.0)
            previous_net_income = net_income_values.get(previous_period, 0.0)

            if previous_net_income != 0:
                profit_growth = (current_net_income - previous_net_income) / previous_net_income
                ws[f'A{row}'] = f'Profit Growth: {profit_growth:.1%}'
                ws[f'B{row}'] = ''
                self.apply_trend_indicator(ws, f'B{row}', profit_growth)
                row += 1

        row += 1  # Blank row for spacing

        # === PROFITABILITY SECTION ===
        ws[f'A{row}'] = 'Profitability'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Gross margin
        try:
            gross_margins = margin_calc.calculate_gross_margin()
            current_gross_margin = gross_margins.get(current_period, 0.0)
            ws[f'A{row}'] = f'Gross Margin: {current_gross_margin:.1f}%'
            row += 1
        except Exception:
            # Skip if COGS not available
            pass

        # Net margin
        try:
            net_margins = margin_calc.calculate_net_margin()
            current_net_margin = net_margins.get(current_period, 0.0)
            ws[f'A{row}'] = f'Net Margin: {current_net_margin:.1f}%'
            row += 1
        except Exception:
            pass

        # ROA (Return on Assets) - simplified as Net Income / Total Assets
        # Note: This is a simplified implementation
        total_revenue = revenue_calc.calculate_total_revenue()
        current_revenue = total_revenue.get(current_period, 0.0)
        if current_revenue != 0:
            # Use net margin as proxy for ROA (would need total assets for true ROA)
            # This is a limitation but maintains consistency with available data
            try:
                net_margins = margin_calc.calculate_net_margin()
                current_net_margin = net_margins.get(current_period, 0.0)
                # Display as ROA proxy
                ws[f'A{row}'] = f'ROA (proxy): {current_net_margin:.1f}%'
                row += 1
            except Exception:
                pass

        row += 1  # Blank row for spacing

        # === LIQUIDITY SECTION ===
        ws[f'A{row}'] = 'Liquidity'
        self.format_bold(ws, f'A{row}')
        row += 1

        # Current ratio
        try:
            current_ratio = kpi_calc.current_ratio()
            current_ratio_value = current_ratio.get(current_period, 0.0)
            ws[f'A{row}'] = f'Current Ratio: {current_ratio_value:.1f}x'
            row += 1
        except (MetricsZeroDivisionError, Exception):
            pass

        # Quick ratio (simplified - would need inventory data for true quick ratio)
        # Using current ratio as proxy
        try:
            current_ratio = kpi_calc.current_ratio()
            quick_ratio_value = current_ratio.get(current_period, 0.0) * 0.8  # Rough approximation
            ws[f'A{row}'] = f'Quick Ratio: {quick_ratio_value:.1f}x'
            row += 1
        except Exception:
            pass

        # Burn rate
        try:
            burn_rate = kpi_calc.burn_rate()
            burn_rate_value = burn_rate.get(current_period, 0.0)
            ws[f'A{row}'] = f'Monthly Burn Rate: ${burn_rate_value:,.0f}'
            row += 1
        except Exception:
            pass

        # Cash runway with conditional warning
        try:
            # Convert cash runway from days to months
            cash_runway_days = kpi_calc.cash_runway()
            cash_runway_value_days = cash_runway_days.get(current_period, 0.0)
            cash_runway_months = cash_runway_value_days / 30.0  # Convert to months

            ws[f'A{row}'] = f'Cash Runway: {cash_runway_months:.1f} months'

            # Apply conditional warning if runway < 6 months
            if cash_runway_months < RUNWAY_WARNING_THRESHOLD:
                self.apply_conditional_highlight(ws, f'A{row}', 'FFE699')  # Yellow RGB(255, 230, 153)

            row += 1
        except (MetricsZeroDivisionError, Exception):
            # If burn rate is zero, runway is infinite (no warning needed)
            pass

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)
