"""
MarginCalculator for computing profit margins.

Provides methods for calculating gross margin, EBITDA margin, and net margin
from PLModel data.
"""
from typing import Any, Dict

from src.models import PLModel
from .exceptions import InvalidDataError, ZeroDivisionError
from .revenue_calculator import RevenueCalculator


class MarginCalculator:
    """
    Calculator for profit margin analysis.

    Computes various margin percentages (gross, EBITDA, net) by dividing
    profit metrics by revenue.
    """

    def __init__(self, pl_model: PLModel):
        """
        Initialize calculator with PLModel instance.

        Args:
            pl_model: PLModel instance with P&L data
        """
        self.pl_model = pl_model
        self.revenue_calculator = RevenueCalculator(pl_model)

    def calculate_gross_margin(self) -> Dict[str, float]:
        """
        Calculate gross margin for all periods.

        Formula: ((revenue - COGS) / revenue) * 100

        Requires COGS to be present in P&L data. Service businesses without COGS
        will raise InvalidDataError.

        Returns:
            Dict mapping period labels to gross margin percentages
            Example: {'Nov 2025': 40.0, 'Nov 2024 (PY)': 35.0}

        Raises:
            InvalidDataError: If COGS section not present in P&L
            ZeroDivisionError: If revenue is zero for any period
        """
        # Validate COGS exists
        cogs_section = self.pl_model.get_cogs()
        if cogs_section is None:
            raise InvalidDataError(
                data_type='Cost of Goods Sold (COGS)',
                calculation_type='gross margin',
                pl_model=self.pl_model
            )

        # Get total revenue for all periods
        total_revenue = self.revenue_calculator.calculate_total_revenue()

        # Sum COGS values for all periods (same recursive logic as revenue)
        cogs_totals: Dict[str, float] = {}

        def sum_cogs_recursive(node: Any) -> None:
            """
            Recursively traverse COGS tree and accumulate leaf node values.

            Args:
                node: Current node in hierarchy tree
            """
            if isinstance(node, dict):
                # If node has children, traverse them
                if 'children' in node:
                    for child in node['children']:
                        sum_cogs_recursive(child)
                # If leaf node
                elif 'values' in node and isinstance(node['values'], dict) and not node.get('parent', False):
                    for period, value in node['values'].items():
                        if period not in cogs_totals:
                            cogs_totals[period] = 0.0
                        cogs_totals[period] += value
            elif isinstance(node, list):
                for item in node:
                    sum_cogs_recursive(item)

        # Traverse COGS section
        sum_cogs_recursive(cogs_section)

        # Calculate gross margin for each period
        gross_margins: Dict[str, float] = {}

        for period in total_revenue.keys():
            revenue = total_revenue[period]

            # Check for zero revenue
            if revenue == 0:
                raise ZeroDivisionError(
                    denominator_type='revenue',
                    calculation_type='gross margin',
                    period=period,
                    pl_model=self.pl_model
                )

            cogs = cogs_totals.get(period, 0.0)
            gross_margin = ((revenue - cogs) / revenue) * 100

            gross_margins[period] = gross_margin

        return gross_margins

    def calculate_ebitda_margin(self) -> Dict[str, float]:
        """
        Calculate EBITDA margin for all periods.

        Formula: (EBITDA / revenue) * 100

        Note: This implementation uses Net Income as a proxy for EBITDA when
        depreciation and amortization are not separately reported in the P&L.
        This is a limitation of the available data structure.

        Returns:
            Dict mapping period labels to EBITDA margin percentages
            Example: {'Nov 2025': 15.0, 'Nov 2024 (PY)': 12.0}

        Raises:
            ZeroDivisionError: If revenue is zero for any period
        """
        # Get Net Income as EBITDA proxy
        net_income_row = self.pl_model.get_calculated_row('Net Income')

        if net_income_row is None:
            # If Net Income not found, try to use it from other calculated rows
            # For now, assume it exists based on P&L structure
            net_income_values: Dict[str, float] = {}
        else:
            net_income_values = net_income_row.get('values', {})

        # Get total revenue
        total_revenue = self.revenue_calculator.calculate_total_revenue()

        # Calculate EBITDA margin for each period
        ebitda_margins: Dict[str, float] = {}

        for period in total_revenue.keys():
            revenue = total_revenue[period]

            # Check for zero revenue
            if revenue == 0:
                raise ZeroDivisionError(
                    denominator_type='revenue',
                    calculation_type='EBITDA margin',
                    period=period,
                    pl_model=self.pl_model
                )

            # Use Net Income as EBITDA proxy
            ebitda = net_income_values.get(period, 0.0)
            ebitda_margin = (ebitda / revenue) * 100

            ebitda_margins[period] = ebitda_margin

        return ebitda_margins

    def calculate_net_margin(self) -> Dict[str, float]:
        """
        Calculate net profit margin for all periods.

        Formula: (Net Income / revenue) * 100

        Negative margins are valid and represent loss scenarios.

        Returns:
            Dict mapping period labels to net margin percentages
            Example: {'Nov 2025': 10.0, 'Nov 2024 (PY)': -5.0}

        Raises:
            ZeroDivisionError: If revenue is zero for any period
        """
        # Get Net Income
        net_income_row = self.pl_model.get_calculated_row('Net Income')

        if net_income_row is None:
            net_income_values: Dict[str, float] = {}
        else:
            net_income_values = net_income_row.get('values', {})

        # Get total revenue
        total_revenue = self.revenue_calculator.calculate_total_revenue()

        # Calculate net margin for each period
        net_margins: Dict[str, float] = {}

        for period in total_revenue.keys():
            revenue = total_revenue[period]

            # Check for zero revenue
            if revenue == 0:
                raise ZeroDivisionError(
                    denominator_type='revenue',
                    calculation_type='net margin',
                    period=period,
                    pl_model=self.pl_model
                )

            net_income = net_income_values.get(period, 0.0)
            net_margin = (net_income / revenue) * 100

            net_margins[period] = net_margin

        return net_margins
