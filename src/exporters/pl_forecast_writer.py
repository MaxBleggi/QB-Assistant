"""
P&L Forecast Excel writer with confidence intervals.

Generates P&L Forecast sheet with income and expense hierarchies showing
projected, lower_bound, and upper_bound values for each period.
"""
from typing import Optional
from .base_writer import BaseExcelWriter
from openpyxl.styles import Alignment, Font


class PLForecastWriter(BaseExcelWriter):
    """
    Excel writer for P&L Forecast sheet with confidence intervals.

    Creates a sheet with income and expense sections from PLForecastModel,
    showing three value columns per period (projected, lower bound, upper bound).
    Includes calculated margin rows (gross_profit, operating_income, net_income).
    """

    def write(self, pl_forecast_model) -> None:
        """
        Generate P&L Forecast sheet from PLForecastModel.

        Args:
            pl_forecast_model: PLForecastModel instance with hierarchy and calculated_rows
        """
        # Create P&L Forecast sheet
        ws = self.workbook.create_sheet('P&L Forecast')

        # Extract sections from model
        income_section = pl_forecast_model.get_income()
        expenses_section = pl_forecast_model.get_expenses()
        margins = pl_forecast_model.get_margins()

        # Determine periods from income section
        periods = []
        if income_section and 'projected' in income_section:
            periods = list(income_section['projected'].keys())

        # Write header row: Account | Period1_Projected | Period1_Lower | Period1_Upper | ...
        current_col = 1
        ws.cell(row=1, column=current_col, value='Account')
        current_col += 1

        for period in periods:
            ws.cell(row=1, column=current_col, value=f'{period} (Projected)')
            ws.cell(row=1, column=current_col + 1, value=f'{period} (Lower)')
            ws.cell(row=1, column=current_col + 2, value=f'{period} (Upper)')
            current_col += 3

        # Apply header style to header row
        last_col_letter = chr(64 + current_col - 1)
        self.apply_header_style(ws, f'A1:{last_col_letter}1')

        # Track current row
        current_row = 2

        # Write Income section
        if income_section:
            # Write section header
            ws.cell(row=current_row, column=1, value='Income')
            ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
            current_row += 1

            # Traverse income hierarchy
            for indent_level, name, projected, lower_bound, upper_bound in self.traverse_hierarchy(
                income_section, indent_level=0, forecast=True
            ):
                # Write account name with indentation
                cell = ws.cell(row=current_row, column=1, value=name)
                cell.alignment = Alignment(indent=indent_level + 1)

                # Write three value columns for each period
                col_idx = 2
                for period in periods:
                    ws.cell(row=current_row, column=col_idx, value=projected.get(period))
                    ws.cell(row=current_row, column=col_idx + 1, value=lower_bound.get(period))
                    ws.cell(row=current_row, column=col_idx + 2, value=upper_bound.get(period))
                    col_idx += 3

                current_row += 1

        # Write Expenses section
        if expenses_section:
            # Write section header
            ws.cell(row=current_row, column=1, value='Expenses')
            ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)
            current_row += 1

            # Traverse expenses hierarchy
            for indent_level, name, projected, lower_bound, upper_bound in self.traverse_hierarchy(
                expenses_section, indent_level=0, forecast=True
            ):
                # Write account name with indentation
                cell = ws.cell(row=current_row, column=1, value=name)
                cell.alignment = Alignment(indent=indent_level + 1)

                # Write three value columns for each period
                col_idx = 2
                for period in periods:
                    ws.cell(row=current_row, column=col_idx, value=projected.get(period))
                    ws.cell(row=current_row, column=col_idx + 1, value=lower_bound.get(period))
                    ws.cell(row=current_row, column=col_idx + 2, value=upper_bound.get(period))
                    col_idx += 3

                current_row += 1

        # Write Margin rows
        if margins:
            # Add blank row for separation
            current_row += 1

            # Write margin metrics
            margin_names = {
                'gross_profit': 'Gross Profit',
                'operating_income': 'Operating Income',
                'net_income': 'Net Income'
            }

            for margin_key, margin_label in margin_names.items():
                if margin_key in margins:
                    margin_data = margins[margin_key]

                    # Write margin name
                    ws.cell(row=current_row, column=1, value=margin_label)
                    ws.cell(row=current_row, column=1).font = Font(bold=True, size=11)

                    # Write three value columns for each period
                    col_idx = 2
                    for period in periods:
                        projected = margin_data.get('projected', {})
                        lower_bound = margin_data.get('lower_bound', {})
                        upper_bound = margin_data.get('upper_bound', {})

                        ws.cell(row=current_row, column=col_idx, value=projected.get(period))
                        ws.cell(row=current_row, column=col_idx + 1, value=lower_bound.get(period))
                        ws.cell(row=current_row, column=col_idx + 2, value=upper_bound.get(period))
                        col_idx += 3

                    current_row += 1

        # Apply currency formatting to all value columns
        if current_row > 2:
            value_range = f'B2:{last_col_letter}{current_row - 1}'
            self.format_currency(ws, value_range)

        # Apply borders to entire table
        if current_row > 1:
            table_range = f'A1:{last_col_letter}{current_row - 1}'
            self.apply_borders(ws, table_range)

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)
