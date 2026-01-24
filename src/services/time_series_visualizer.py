"""
Time-series visualization service using matplotlib.

Generates line charts with anomaly highlighting for historical data review.
"""
from typing import List, Dict, Any
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

    @staticmethod
    def create_chart_with_annotation_ranges(
        period_labels: List[str],
        values: List[float],
        metric_name: str,
        anomaly_indices: List[int] = None,
        annotation_ranges: List[Dict[str, Any]] = None
    ) -> Figure:
        """
        Create time-series chart with optional anomaly markers and annotation range shading.

        Args:
            period_labels: List of period label strings for x-axis
            values: List of numeric values for y-axis
            metric_name: Title for the chart
            anomaly_indices: List of indices to highlight as anomalies (default: None)
            annotation_ranges: List of annotation dicts with start_date, end_date, exclude_from fields

        Returns:
            matplotlib Figure object (not shown - for embedding in tkinter)
        """
        if anomaly_indices is None:
            anomaly_indices = []
        if annotation_ranges is None:
            annotation_ranges = []

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Draw annotation ranges FIRST (lowest z-order)
        # Map period labels to indices for position lookup
        period_to_index = {label: idx for idx, label in enumerate(period_labels)}

        # Define color scheme for exclusion types
        exclusion_colors = {
            'baseline': '#BBDEFB',      # Light blue
            'volatility': '#FFF9C4',    # Light yellow
            'both': '#FFE0B2'           # Light orange
        }

        for annotation in annotation_ranges:
            start_date = annotation.get('start_date')
            end_date = annotation.get('end_date')
            exclude_from = annotation.get('exclude_from', 'both')

            # Find indices for start and end dates
            if start_date in period_to_index and end_date in period_to_index:
                start_idx = period_to_index[start_date]
                end_idx = period_to_index[end_date]

                # Draw shaded region using axvspan
                # Use -0.5 and +0.5 to extend to edges of bar positions
                color = exclusion_colors.get(exclude_from, '#E0E0E0')
                ax.axvspan(
                    start_idx - 0.5,
                    end_idx + 0.5,
                    alpha=0.25,
                    color=color,
                    zorder=1
                )

        # Plot time series as line (zorder=2 by default)
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
