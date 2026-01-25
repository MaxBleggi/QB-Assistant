"""
Budget vs Actual variance Excel writer.

Generates Budget vs Actual sheet comparing budgeted amounts with actual results,
showing both absolute and percentage variances.
"""
from typing import Dict, Any, Union
from .base_writer import BaseExcelWriter
from openpyxl.styles import Alignment


class BudgetVarianceWriter(BaseExcelWriter):
    """
    Excel writer for Budget vs Actual variance sheet.

    Creates a sheet comparing budget data with actuals, calculating absolute
    and percentage variances. Handles missing actuals gracefully.
    """

    def write(
        self,
        budget_model,
        actuals: Union[Dict[str, float], Any]
    ) -> None:
        """
        Generate Budget vs Actual sheet from BudgetModel and actuals data.

        Args:
            budget_model: BudgetModel instance with budget hierarchy
            actuals: Dict mapping account names to actual values, or a model with accessor methods
        """
        # Create Budget vs Actual sheet
        ws = self.workbook.create_sheet('Budget vs Actual')

        # Convert actuals to dict if it's a model
        actuals_dict = self._extract_actuals_dict(actuals)

        # Write header row
        ws['A1'] = 'Account'
        ws['B1'] = 'Budget'
        ws['C1'] = 'Actual'
        ws['D1'] = 'Variance'
        ws['E1'] = 'Variance %'

        # Apply header style
        self.apply_header_style(ws, 'A1:E1')

        # Track current row
        current_row = 2

        # Get budget hierarchy
        budget_hierarchy = budget_model.hierarchy

        # Traverse budget hierarchy and write rows
        for indent_level, name, values in self.traverse_hierarchy(budget_hierarchy):
            # Calculate budget total for this account (sum across periods)
            budget_total = sum(values.values()) if values else 0

            # Look up actual value by account name
            actual_value = actuals_dict.get(name, None)

            # Calculate variance
            variance = None
            variance_pct = None
            if actual_value is not None:
                variance = actual_value - budget_total
                # Calculate variance percentage (avoid division by zero)
                if budget_total != 0:
                    variance_pct = variance / budget_total

            # Write account name with indentation
            cell = ws.cell(row=current_row, column=1, value=name)
            cell.alignment = Alignment(indent=indent_level)

            # Write budget total
            ws.cell(row=current_row, column=2, value=budget_total)

            # Write actual value (or leave empty if not available)
            if actual_value is not None:
                ws.cell(row=current_row, column=3, value=actual_value)

            # Write variance
            if variance is not None:
                ws.cell(row=current_row, column=4, value=variance)

            # Write variance percentage
            if variance_pct is not None:
                ws.cell(row=current_row, column=5, value=variance_pct)

            current_row += 1

        # Apply currency formatting to Budget, Actual, and Variance columns
        if current_row > 2:
            self.format_currency(ws, f'B2:B{current_row - 1}')
            self.format_currency(ws, f'C2:C{current_row - 1}')
            self.format_currency(ws, f'D2:D{current_row - 1}')

        # Apply percentage formatting to Variance % column
        if current_row > 2:
            self.format_percentage(ws, f'E2:E{current_row - 1}')

        # Apply borders to entire table
        if current_row > 1:
            self.apply_borders(ws, f'A1:E{current_row - 1}')

        # Auto-adjust column widths
        self.auto_adjust_column_widths(ws)

    def _extract_actuals_dict(self, actuals: Union[Dict[str, float], Any]) -> Dict[str, float]:
        """
        Extract actuals as dict from various input types.

        Args:
            actuals: Dict mapping account names to values, or a model

        Returns:
            Dict mapping account names to actual values
        """
        # If already a dict, return as-is
        if isinstance(actuals, dict):
            return actuals

        # If it's a model with hierarchy, extract values
        if hasattr(actuals, 'hierarchy'):
            actuals_dict = {}
            for indent_level, name, values in self.traverse_hierarchy(actuals.hierarchy):
                # Sum values across periods for this account
                total = sum(values.values()) if values else 0
                actuals_dict[name] = total
            return actuals_dict

        # Otherwise, return empty dict (no actuals available)
        return {}
