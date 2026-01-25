"""
Cash Flow Forecast Excel writer with confidence intervals.

Generates Cash Flow Forecast sheet with operating, investing, and financing activity
sections showing projected, lower_bound, and upper_bound values for each period.
"""
from typing import List, Dict, Any
from .base_writer import BaseExcelWriter
from openpyxl.styles import Alignment


class CashFlowForecastWriter(BaseExcelWriter):
    """
    Excel writer for Cash Flow Forecast sheet with confidence intervals.

    Creates a sheet with operating, investing, and financing activities from
    CashFlowForecastModel, showing three value columns per period (projected,
    lower bound, upper bound).
    """

    def write(self, cash_flow_forecast_model) -> None:
        """
        Generate Cash Flow Forecast sheet from CashFlowForecastModel.

        Args:
            cash_flow_forecast_model: CashFlowForecastModel instance with hierarchy and calculated_rows
        """
        # Create Cash Flow Forecast sheet
        ws = self.workbook.create_sheet('Cash Flow Forecast')

        # Extract sections from model
        operating = cash_flow_forecast_model.get_operating()
        investing = cash_flow_forecast_model.get_investing()
        financing = cash_flow_forecast_model.get_financing()

        # Determine periods from first available section
        periods = []
        first_section = operating or investing or financing
        if first_section and len(first_section) > 0:
            first_item = first_section[0]
            if 'projected' in first_item:
                periods = list(first_item['projected'].keys())

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

        # Write Operating Activities section
        if operating:
            current_row = self._write_section(
                ws, 'Operating Activities', operating, periods, current_row
            )

        # Write Investing Activities section
        if investing:
            current_row = self._write_section(
                ws, 'Investing Activities', investing, periods, current_row
            )

        # Write Financing Activities section
        if financing:
            current_row = self._write_section(
                ws, 'Financing Activities', financing, periods, current_row
            )

        # Write calculated rows (beginning_cash, ending_cash) if available
        calculated_rows = cash_flow_forecast_model.calculated_rows
        if calculated_rows:
            # Add blank row for separation
            current_row += 1

            # Write beginning_cash if available
            if 'beginning_cash' in calculated_rows:
                current_row = self._write_calculated_row(
                    ws, 'Beginning Cash', calculated_rows['beginning_cash'], periods, current_row
                )

            # Write ending_cash if available
            if 'ending_cash' in calculated_rows:
                current_row = self._write_calculated_row(
                    ws, 'Ending Cash', calculated_rows['ending_cash'], periods, current_row
                )

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

    def _write_section(
        self,
        ws,
        section_name: str,
        section_data: List[Dict[str, Any]],
        periods: List[str],
        start_row: int
    ) -> int:
        """
        Write a cash flow section (Operating/Investing/Financing Activities).

        Args:
            ws: Worksheet to write to
            section_name: Name of the section
            section_data: List of activity items from model
            periods: List of period labels
            start_row: Row to start writing at

        Returns:
            Next available row number
        """
        # Write section header
        ws.cell(row=start_row, column=1, value=section_name)
        ws.cell(row=start_row, column=1).font = ws.cell(row=1, column=1).font
        start_row += 1

        # Process each item in section
        for item in section_data:
            # Traverse hierarchy for this item
            for indent_level, name, projected, lower_bound, upper_bound in self.traverse_hierarchy(
                item, indent_level=0, forecast=True
            ):
                # Write account name with indentation
                cell = ws.cell(row=start_row, column=1, value=name)
                cell.alignment = Alignment(indent=indent_level + 1)

                # Write three value columns for each period
                col_idx = 2
                for period in periods:
                    ws.cell(row=start_row, column=col_idx, value=projected.get(period))
                    ws.cell(row=start_row, column=col_idx + 1, value=lower_bound.get(period))
                    ws.cell(row=start_row, column=col_idx + 2, value=upper_bound.get(period))
                    col_idx += 3

                start_row += 1

        return start_row

    def _write_calculated_row(
        self,
        ws,
        row_name: str,
        row_data: Dict[str, Any],
        periods: List[str],
        row_num: int
    ) -> int:
        """
        Write a calculated row (beginning_cash or ending_cash).

        Args:
            ws: Worksheet to write to
            row_name: Name of the calculated row
            row_data: Dict with 'projected', 'lower_bound', 'upper_bound' dicts
            periods: List of period labels
            row_num: Row number to write at

        Returns:
            Next available row number
        """
        # Write row name
        ws.cell(row=row_num, column=1, value=row_name)
        ws.cell(row=row_num, column=1).font = ws.cell(row=1, column=1).font

        # Extract three value series
        projected = row_data.get('projected', {})
        lower_bound = row_data.get('lower_bound', {})
        upper_bound = row_data.get('upper_bound', {})

        # Write three value columns for each period
        col_idx = 2
        for period in periods:
            ws.cell(row=row_num, column=col_idx, value=projected.get(period))
            ws.cell(row=row_num, column=col_idx + 1, value=lower_bound.get(period))
            ws.cell(row=row_num, column=col_idx + 2, value=upper_bound.get(period))
            col_idx += 3

        return row_num + 1
