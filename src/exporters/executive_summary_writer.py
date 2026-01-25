"""
Executive Summary Excel writer for high-level financial overview.

Generates Executive Summary sheet with key-value pairs of financial metrics,
applying appropriate formatting based on value type.
"""
from typing import Dict, Any
from .base_writer import BaseExcelWriter


class ExecutiveSummaryWriter(BaseExcelWriter):
    """
    Excel writer for Executive Summary sheet.

    Creates a simple key-value pairs table with financial highlights,
    automatically detecting whether values should be formatted as currency
    or percentages.
    """

    def write(self, summary_data: Dict[str, Any]) -> None:
        """
        Generate Executive Summary sheet from summary data dict.

        Args:
            summary_data: Dict mapping labels to values (numeric or string)
        """
        # Create Executive Summary sheet
        ws = self.workbook.create_sheet('Executive Summary')

        # Write header row
        ws['A1'] = 'Metric'
        ws['B1'] = 'Value'

        # Apply header style
        self.apply_header_style(ws, 'A1:B1')

        # Track current row
        current_row = 2

        # Write each key-value pair
        for label, value in summary_data.items():
            # Write label
            ws.cell(row=current_row, column=1, value=label)

            # Write value
            ws.cell(row=current_row, column=2, value=value)

            # Apply appropriate formatting based on value type
            if isinstance(value, (int, float)):
                # Detect if it's a percentage (value between 0 and 1)
                if 0 < value < 1:
                    self.format_percentage(ws, f'B{current_row}')
                else:
                    # Assume currency for other numeric values
                    self.format_currency(ws, f'B{current_row}')

            current_row += 1

        # Apply borders to entire table
        if current_row > 1:
            self.apply_borders(ws, f'A1:B{current_row - 1}')

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)
