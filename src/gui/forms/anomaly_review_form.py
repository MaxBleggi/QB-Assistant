"""
Anomaly review form for visualizing and confirming/dismissing detected anomalies.

Provides time-series charts with statistical anomaly highlighting, allowing users
to confirm genuine anomalies for exclusion from baseline calculations.
"""
import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
from typing import Dict, List, Tuple

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...models.anomaly_annotation import AnomalyAnnotationModel
from ...services.anomaly_detector import AnomalyDetector
from ...services.time_series_visualizer import TimeSeriesVisualizer


class AnomalyReviewForm(tk.Frame):
    """
    Form for reviewing and confirming/dismissing detected anomalies in historical data.

    Loads CashFlowModel and PLModel, runs statistical anomaly detection on key metrics,
    displays charts with anomaly markers, and provides confirm/dismiss functionality.
    """

    CONFIG_FILEPATH = 'config/anomaly_annotations.json'

    def __init__(self, parent):
        """
        Initialize anomaly review form.

        Args:
            parent: Parent widget (should be App instance)
        """
        super().__init__(parent)
        self.parent = parent

        # Initialize services
        self.detector = AnomalyDetector()
        self.visualizer = TimeSeriesVisualizer()

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create title label
        title = tk.Label(
            self,
            text="Historical Data Anomaly Review",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20)

        # Load data and detect anomalies
        self.anomalies_data = []  # List of (metric_name, period_label, period_idx, value, deviation)
        self.load_and_detect()

    def load_and_detect(self) -> None:
        """
        Load financial models, run anomaly detection, and display results.
        """
        try:
            # Load CashFlowModel and PLModel from ConfigManager
            config_mgr = self.parent.get_config_manager()

            try:
                cash_flow_model = config_mgr.load_config('config/cash_flow_model.json')
            except:
                cash_flow_model = None

            try:
                pl_model = config_mgr.load_config('config/pl_model.json')
            except:
                pl_model = None

            # Check if financial data exists
            if cash_flow_model is None and pl_model is None:
                self.display_error("Financial data not found. Please import data first.")
                return

            # Run anomaly detection on key metrics
            self.detect_and_display(cash_flow_model, pl_model)

        except Exception as e:
            self.display_error(f"Error loading data: {str(e)}")

    def detect_and_display(self, cash_flow_model, pl_model) -> None:
        """
        Run anomaly detection on key metrics and display charts and anomaly list.

        Args:
            cash_flow_model: CashFlowModel instance (or None)
            pl_model: PLModel instance (or None)
        """
        charts_frame = tk.Frame(self)
        charts_frame.grid(row=1, column=0, pady=10, sticky='nsew')
        charts_frame.grid_columnconfigure(0, weight=1)

        chart_row = 0

        # Detect anomalies in Cash Flow: "Net Cash Provided by Operating Activities"
        if cash_flow_model is not None:
            try:
                periods = cash_flow_model.get_periods()
                operating = cash_flow_model.get_operating()

                # Find "Net Cash Provided by Operating Activities"
                net_cash_values = None
                for item in operating:
                    if 'account_name' in item and 'Net Cash Provided by Operating Activities' in item['account_name']:
                        if 'values' in item:
                            net_cash_values = [item['values'].get(p, 0) for p in periods]
                            break

                if net_cash_values and len(net_cash_values) >= 3:
                    anomalies = self.detector.detect_anomalies(net_cash_values)
                    metric_name = "Net Cash Provided by Operating Activities"

                    # Store anomaly data
                    for idx, value, deviation in anomalies:
                        self.anomalies_data.append((metric_name, periods[idx], idx, value, deviation))

                    # Create chart
                    anomaly_indices = [idx for idx, _, _ in anomalies]
                    fig = self.visualizer.create_chart(periods, net_cash_values, metric_name, anomaly_indices)

                    # Embed chart in tkinter
                    canvas = FigureCanvasTkAgg(fig, master=charts_frame)
                    canvas.draw()
                    canvas.get_tk_widget().grid(row=chart_row, column=0, pady=10)
                    chart_row += 1

            except Exception as e:
                print(f"Error processing cash flow data: {e}")

        # Detect anomalies in P&L: "Net Income"
        if pl_model is not None:
            try:
                periods = pl_model.get_periods()
                calculated_rows = pl_model.calculated_rows

                # Find "Net Income" from calculated rows
                net_income_values = None
                for row in calculated_rows:
                    if 'account_name' in row and 'Net Income' in row['account_name']:
                        if 'values' in row:
                            net_income_values = [row['values'].get(p, 0) for p in periods]
                            break

                if net_income_values and len(net_income_values) >= 3:
                    anomalies = self.detector.detect_anomalies(net_income_values)
                    metric_name = "Net Income"

                    # Store anomaly data
                    for idx, value, deviation in anomalies:
                        self.anomalies_data.append((metric_name, periods[idx], idx, value, deviation))

                    # Create chart
                    anomaly_indices = [idx for idx, _, _ in anomalies]
                    fig = self.visualizer.create_chart(periods, net_income_values, metric_name, anomaly_indices)

                    # Embed chart in tkinter
                    canvas = FigureCanvasTkAgg(fig, master=charts_frame)
                    canvas.draw()
                    canvas.get_tk_widget().grid(row=chart_row, column=0, pady=10)
                    chart_row += 1

            except Exception as e:
                print(f"Error processing P&L data: {e}")

        # Display anomaly list or "No anomalies detected" message
        if not self.anomalies_data:
            self.display_no_anomalies()
        else:
            self.display_anomaly_list()

    def display_no_anomalies(self) -> None:
        """
        Display message when no anomalies are detected.
        """
        message_label = tk.Label(
            self,
            text="No anomalies detected. All values are within 2σ of the historical mean.",
            font=('Arial', 12),
            fg='#4CAF50'
        )
        message_label.grid(row=2, column=0, pady=20)

        # Add Back to Menu button
        back_btn = tk.Button(
            self,
            text="Back to Menu",
            command=self.on_back_to_menu_clicked,
            width=20,
            bg='#9E9E9E',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        back_btn.grid(row=3, column=0, pady=10)

    def display_anomaly_list(self) -> None:
        """
        Display list of detected anomalies with confirm/dismiss buttons.
        """
        # Anomalies list label
        list_label = tk.Label(
            self,
            text="Detected Anomalies:",
            font=('Arial', 12, 'bold')
        )
        list_label.grid(row=2, column=0, pady=(20, 5))

        # Create listbox with scrollbar
        list_frame = tk.Frame(self)
        list_frame.grid(row=3, column=0, pady=10)

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.anomaly_listbox = Listbox(
            list_frame,
            width=80,
            height=10,
            yscrollcommand=scrollbar.set,
            font=('Courier', 10)
        )
        self.anomaly_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.anomaly_listbox.yview)

        # Populate listbox
        for metric_name, period_label, idx, value, deviation in self.anomalies_data:
            item_text = f"{metric_name} | {period_label} | Value: {value:,.2f} | Deviation: {deviation:.2f}σ"
            self.anomaly_listbox.insert(tk.END, item_text)

        # Buttons frame
        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=4, column=0, pady=20)

        # Confirm button
        confirm_btn = tk.Button(
            buttons_frame,
            text="Confirm Anomaly",
            command=self.on_confirm_clicked,
            width=20,
            bg='#F44336',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        confirm_btn.pack(side=tk.LEFT, padx=10)

        # Dismiss button
        dismiss_btn = tk.Button(
            buttons_frame,
            text="Dismiss Anomaly",
            command=self.on_dismiss_clicked,
            width=20,
            bg='#4CAF50',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        dismiss_btn.pack(side=tk.LEFT, padx=10)

        # Back to Menu button
        back_btn = tk.Button(
            buttons_frame,
            text="Back to Menu",
            command=self.on_back_to_menu_clicked,
            width=20,
            bg='#9E9E9E',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        back_btn.pack(side=tk.LEFT, padx=10)

        # Status label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Arial', 10),
            fg='#666'
        )
        self.status_label.grid(row=5, column=0, pady=10)

    def on_confirm_clicked(self) -> None:
        """
        Handle Confirm Anomaly button click - add annotation with confirmed=True.
        """
        selected_indices = self.anomaly_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an anomaly to confirm")
            return

        idx = selected_indices[0]
        metric_name, period_label, period_idx, value, deviation = self.anomalies_data[idx]

        # Create annotation dict
        annotation = {
            'start_date': period_label,
            'end_date': period_label,
            'metric_name': metric_name,
            'reason': f"Statistical anomaly detected: {deviation:.2f}σ from mean",
            'exclude_from_baseline': True,
            'confirmed': True
        }

        # Save annotation
        self.save_annotation(annotation)

        # Update status and remove from list
        self.status_label.config(text=f"Anomaly confirmed and saved: {metric_name} - {period_label}", fg='#4CAF50')
        self.anomaly_listbox.delete(idx)
        del self.anomalies_data[idx]

        messagebox.showinfo("Success", "Anomaly confirmed and saved")

    def on_dismiss_clicked(self) -> None:
        """
        Handle Dismiss Anomaly button click - add annotation with confirmed=False.
        """
        selected_indices = self.anomaly_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an anomaly to dismiss")
            return

        idx = selected_indices[0]
        metric_name, period_label, period_idx, value, deviation = self.anomalies_data[idx]

        # Create annotation dict
        annotation = {
            'start_date': period_label,
            'end_date': period_label,
            'metric_name': metric_name,
            'reason': f"Statistical anomaly dismissed by user: {deviation:.2f}σ from mean",
            'exclude_from_baseline': False,
            'confirmed': False
        }

        # Save annotation
        self.save_annotation(annotation)

        # Update status and remove from list
        self.status_label.config(text=f"Anomaly dismissed: {metric_name} - {period_label}", fg='#2196F3')
        self.anomaly_listbox.delete(idx)
        del self.anomalies_data[idx]

        messagebox.showinfo("Success", "Anomaly dismissed")

    def save_annotation(self, annotation: Dict) -> None:
        """
        Save anomaly annotation to config file.

        Args:
            annotation: Annotation dict to save
        """
        try:
            config_mgr = self.parent.get_config_manager()

            # Load existing annotations or create new model
            try:
                model = config_mgr.load_config(self.CONFIG_FILEPATH)
                if not isinstance(model, AnomalyAnnotationModel):
                    # Convert if it's a generic ParameterModel
                    model = AnomalyAnnotationModel(parameters=model.parameters)
            except:
                model = AnomalyAnnotationModel()

            # Add annotation and save
            model.add_annotation(annotation)
            config_mgr.save_config(model, self.CONFIG_FILEPATH)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotation: {str(e)}")

    def display_error(self, message: str) -> None:
        """
        Display error message when data loading fails.

        Args:
            message: Error message to display
        """
        error_label = tk.Label(
            self,
            text=message,
            font=('Arial', 12),
            fg='#F44336'
        )
        error_label.grid(row=1, column=0, pady=20)

        # Add Back to Menu button
        back_btn = tk.Button(
            self,
            text="Back to Menu",
            command=self.on_back_to_menu_clicked,
            width=20,
            bg='#9E9E9E',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        back_btn.grid(row=2, column=0, pady=10)

    def on_back_to_menu_clicked(self) -> None:
        """
        Handle Back to Menu button click - navigate to MainMenuForm.
        """
        from .main_menu_form import MainMenuForm
        self.parent.show_form(MainMenuForm)
