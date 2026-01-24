"""
Time-series visualization service using matplotlib.

Generates line charts with anomaly highlighting for historical data review.
"""
from typing import List
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class TimeSeriesVisualizer:
    """
    Service for creating time-series charts with anomaly highlighting.

    Uses matplotlib to generate static charts suitable for embedding in tkinter.
    """

    @staticmethod
    def create_chart(
        period_labels: List[str],
        values: List[float],
        metric_name: str,
        anomaly_indices: List[int] = None
    ) -> Figure:
        """
        Create time-series chart with optional anomaly markers.

        Args:
            period_labels: List of period label strings for x-axis
            values: List of numeric values for y-axis
            metric_name: Title for the chart
            anomaly_indices: List of indices to highlight as anomalies (default: None)

        Returns:
            matplotlib Figure object (not shown - for embedding in tkinter)
        """
        if anomaly_indices is None:
            anomaly_indices = []

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot time series as line
        ax.plot(period_labels, values, marker='o', linestyle='-', linewidth=2, markersize=6)

        # Overlay anomaly markers with higher zorder
        if anomaly_indices:
            anomaly_labels = [period_labels[i] for i in anomaly_indices]
            anomaly_values = [values[i] for i in anomaly_indices]
            ax.scatter(
                anomaly_labels,
                anomaly_values,
                color='red',
                s=150,
                marker='o',
                zorder=5,
                label='Anomaly Detected'
            )
            ax.legend()

        # Set chart title and labels
        ax.set_title(metric_name, fontsize=14, fontweight='bold')
        ax.set_xlabel('Period', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)

        # Rotate x-axis labels if more than 12 periods
        if len(period_labels) > 12:
            ax.tick_params(axis='x', rotation=45)
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        # Add grid for readability
        ax.grid(True, alpha=0.3)

        # Tight layout to prevent label cutoff
        fig.tight_layout()

        return fig
