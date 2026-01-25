"""
Anomaly annotation form for integrated detection and manual annotation entry.

Combines detected anomaly review (from Sprint 1.6) with manual date range annotation
entry for external events. Provides visual feedback with shaded annotation ranges.
"""
import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
from typing import Dict, List, Tuple

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...models.anomaly_annotation import AnomalyAnnotationModel
from ...services.anomaly_detector import AnomalyDetector
from ...services.time_series_visualizer import TimeSeriesVisualizer
from ...gui.components.form_fields import LabeledEntry, LabeledDropdown


class AnomalyAnnotationForm(tk.Frame):
    """
    Form for reviewing detected anomalies and manually annotating date ranges.

    Combines detected anomaly suggestions with manual entry for external events
    (government shutdowns, tariffs, one-time contracts). Displays shaded ranges
    on chart to show excluded periods.
    """

    CONFIG_FILEPATH = 'config/anomaly_annotations.json'

    def __init__(self, parent):
        """
        Initialize anomaly annotation form.

        Args:
            parent: Parent widget (should be App instance)
        """
        super().__init__(parent)
        self.parent = parent

        # Initialize services
        self.detector = AnomalyDetector()
        self.visualizer = TimeSeriesVisualizer()

        # Data storage
        self.anomalies_data = []  # List of (metric_name, period_label, period_idx, value, deviation)
        self.annotation_model = None
        self.cash_flow_model = None
        self.pl_model = None
        self.current_metric_name = None
        self.current_periods = None
        self.current_values = None
        self.current_anomaly_indices = None

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)

        # Create scrollable container for entire form
        self.create_scrollable_container()

        # Load data and build form
        self.load_data_and_build_form()

    def create_scrollable_container(self) -> None:
        """
        Create scrollable canvas container for form content.
        """
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)

    def load_data_and_build_form(self) -> None:
        """
        Load financial models, annotation model, and build form sections.
        """
        try:
            # Load ConfigManager
            config_mgr = self.parent.get_config_manager()

            # Load financial models
            try:
                self.cash_flow_model = config_mgr.load_config('config/cash_flow_model.json')
            except:
                self.cash_flow_model = None

            try:
                self.pl_model = config_mgr.load_config('config/pl_model.json')
            except:
                self.pl_model = None

            # Check if financial data exists
            if self.cash_flow_model is None and self.pl_model is None:
                self.display_error("Financial data not found. Please import data first.")
                return

            # Load annotation model
            try:
                loaded_model = config_mgr.load_config(self.CONFIG_FILEPATH)
                if isinstance(loaded_model, AnomalyAnnotationModel):
                    self.annotation_model = loaded_model
                else:
                    # Convert if it's a generic ParameterModel
                    self.annotation_model = AnomalyAnnotationModel(parameters=loaded_model.parameters)
            except:
                self.annotation_model = AnomalyAnnotationModel()

            # Build form sections
            self.build_form_sections()

        except Exception as e:
            self.display_error(f"Error loading data: {str(e)}")

    def build_form_sections(self) -> None:
        """
        Build all form sections: title, detected anomalies, manual entry, saved annotations.
        """
        # Title
        title = tk.Label(
            self.scrollable_frame,
            text="Historical Data Anomaly Annotation",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, pady=20, sticky='ew')

        # Section 1: Detected Anomalies
        self.create_detected_anomalies_section(start_row=1)

        # Section 2: Manual Annotation Entry
        self.create_manual_entry_section(start_row=10)

        # Section 3: Saved Annotations List
        self.create_saved_annotations_section(start_row=20)

        # Back to Menu button
        back_btn = tk.Button(
            self.scrollable_frame,
            text="Back to Menu",
            command=self.on_back_to_menu_clicked,
            width=20,
            bg='#9E9E9E',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        back_btn.grid(row=30, column=0, pady=20)

    def create_detected_anomalies_section(self, start_row: int) -> None:
        """
        Create detected anomalies section with chart and listbox.

        Args:
            start_row: Grid row number to start section
        """
        # Section label
        section_label = tk.Label(
            self.scrollable_frame,
            text="Detected Anomalies",
            font=('Arial', 14, 'bold')
        )
        section_label.grid(row=start_row, column=0, pady=(10, 5), sticky='w', padx=20)

        # Run anomaly detection and display
        self.detect_and_display_anomalies(start_row + 1)

    def detect_and_display_anomalies(self, chart_row: int) -> None:
        """
        Run anomaly detection and display chart with annotation ranges.

        Args:
            chart_row: Grid row number for chart
        """
        charts_frame = tk.Frame(self.scrollable_frame)
        charts_frame.grid(row=chart_row, column=0, pady=10, sticky='nsew')
        charts_frame.grid_columnconfigure(0, weight=1)

        current_chart_row = 0

        # Detect anomalies in Cash Flow: "Net Cash Provided by Operating Activities"
        if self.cash_flow_model is not None:
            try:
                periods = self.cash_flow_model.get_periods()
                operating = self.cash_flow_model.get_operating()

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

                    # Store data for manual entry validation
                    self.current_metric_name = metric_name
                    self.current_periods = periods
                    self.current_values = net_cash_values

                    # Create chart with annotation ranges
                    anomaly_indices = [idx for idx, _, _ in anomalies]
                    annotation_ranges = self.annotation_model.get_annotations()
                    fig = self.visualizer.create_chart_with_annotation_ranges(
                        periods, net_cash_values, metric_name, anomaly_indices, annotation_ranges
                    )

                    # Embed chart in tkinter
                    self.chart_canvas = FigureCanvasTkAgg(fig, master=charts_frame)
                    self.chart_canvas.draw()
                    self.chart_canvas.get_tk_widget().grid(row=current_chart_row, column=0, pady=10)
                    current_chart_row += 1

            except Exception as e:
                print(f"Error processing cash flow data: {e}")

        # Detect anomalies in P&L: "Net Income"
        if self.pl_model is not None:
            try:
                periods = self.pl_model.get_periods()
                calculated_rows = self.pl_model.calculated_rows

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

                    # Update current data if not already set
                    if self.current_metric_name is None:
                        self.current_metric_name = metric_name
                        self.current_periods = periods
                        self.current_values = net_income_values

                    # Create chart with annotation ranges
                    anomaly_indices = [idx for idx, _, _ in anomalies]
                    annotation_ranges = self.annotation_model.get_annotations()
                    fig = self.visualizer.create_chart_with_annotation_ranges(
                        periods, net_income_values, metric_name, anomaly_indices, annotation_ranges
                    )

                    # Embed chart in tkinter
                    canvas = FigureCanvasTkAgg(fig, master=charts_frame)
                    canvas.draw()
                    canvas.get_tk_widget().grid(row=current_chart_row, column=0, pady=10)
                    current_chart_row += 1

            except Exception as e:
                print(f"Error processing P&L data: {e}")

        # Display anomaly listbox
        self.display_anomaly_list(chart_row + 1)

    def display_anomaly_list(self, list_row: int) -> None:
        """
        Display list of detected anomalies with confirm/dismiss buttons.

        Args:
            list_row: Grid row number for list
        """
        if not self.anomalies_data:
            # No anomalies detected
            message_label = tk.Label(
                self.scrollable_frame,
                text="No anomalies detected. All values are within 2σ of the historical mean.",
                font=('Arial', 11),
                fg='#4CAF50'
            )
            message_label.grid(row=list_row, column=0, pady=10, padx=20)
            return

        # Anomalies list label
        list_label = tk.Label(
            self.scrollable_frame,
            text="Detected Anomalies:",
            font=('Arial', 11, 'bold')
        )
        list_label.grid(row=list_row, column=0, pady=(10, 5), sticky='w', padx=20)

        # Create listbox with scrollbar
        list_frame = tk.Frame(self.scrollable_frame)
        list_frame.grid(row=list_row + 1, column=0, pady=10, padx=20)

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.anomaly_listbox = Listbox(
            list_frame,
            width=80,
            height=6,
            yscrollcommand=scrollbar.set,
            font=('Courier', 9)
        )
        self.anomaly_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.anomaly_listbox.yview)

        # Populate listbox
        for metric_name, period_label, idx, value, deviation in self.anomalies_data:
            item_text = f"{metric_name} | {period_label} | Value: {value:,.2f} | Deviation: {deviation:.2f}σ"
            self.anomaly_listbox.insert(tk.END, item_text)

        # Buttons frame
        buttons_frame = tk.Frame(self.scrollable_frame)
        buttons_frame.grid(row=list_row + 2, column=0, pady=10)

        # Confirm button
        confirm_btn = tk.Button(
            buttons_frame,
            text="Confirm Anomaly",
            command=self.on_confirm_clicked,
            width=18,
            bg='#F44336',
            fg='black',
            font=('Arial', 9, 'bold')
        )
        confirm_btn.pack(side=tk.LEFT, padx=5)

        # Dismiss button
        dismiss_btn = tk.Button(
            buttons_frame,
            text="Dismiss Anomaly",
            command=self.on_dismiss_clicked,
            width=18,
            bg='#4CAF50',
            fg='black',
            font=('Arial', 9, 'bold')
        )
        dismiss_btn.pack(side=tk.LEFT, padx=5)

    def create_manual_entry_section(self, start_row: int) -> None:
        """
        Create manual annotation entry section with form fields.

        Args:
            start_row: Grid row number to start section
        """
        # Section separator
        separator = tk.Frame(self.scrollable_frame, height=2, bg='#CCCCCC')
        separator.grid(row=start_row, column=0, pady=20, sticky='ew', padx=20)

        # Section label
        section_label = tk.Label(
            self.scrollable_frame,
            text="Manual Annotation Entry",
            font=('Arial', 14, 'bold')
        )
        section_label.grid(row=start_row + 1, column=0, pady=(10, 5), sticky='w', padx=20)

        # Description
        desc_label = tk.Label(
            self.scrollable_frame,
            text="Annotate date ranges affected by external events (government shutdowns, tariffs, one-time contracts)",
            font=('Arial', 10),
            fg='#666'
        )
        desc_label.grid(row=start_row + 2, column=0, pady=(0, 10), sticky='w', padx=20)

        # Form fields frame
        fields_frame = tk.Frame(self.scrollable_frame)
        fields_frame.grid(row=start_row + 3, column=0, pady=10, padx=20)

        # Start Date field
        self.start_date_field = LabeledEntry(fields_frame, "Start Date (e.g., Q1 2023):", "")
        self.start_date_field.pack(pady=5)

        # End Date field
        self.end_date_field = LabeledEntry(fields_frame, "End Date (e.g., Q2 2023):", "")
        self.end_date_field.pack(pady=5)

        # Reason field
        self.reason_field = LabeledEntry(fields_frame, "Reason/Description:", "")
        self.reason_field.pack(pady=5)

        # Exclude From dropdown
        self.exclude_from_field = LabeledDropdown(
            fields_frame,
            "Exclude From:",
            options=['baseline', 'volatility', 'both'],
            default_value='both'
        )
        self.exclude_from_field.pack(pady=5)

        # Add Annotation button
        add_btn = tk.Button(
            self.scrollable_frame,
            text="Add Annotation",
            command=self.on_add_annotation_clicked,
            width=20,
            bg='#2196F3',
            fg='black',
            font=('Arial', 10, 'bold')
        )
        add_btn.grid(row=start_row + 4, column=0, pady=10)

        # Status label
        self.manual_status_label = tk.Label(
            self.scrollable_frame,
            text="",
            font=('Arial', 9),
            fg='#666'
        )
        self.manual_status_label.grid(row=start_row + 5, column=0, pady=5)

    def create_saved_annotations_section(self, start_row: int) -> None:
        """
        Create saved annotations list section with edit/delete functionality.

        Args:
            start_row: Grid row number to start section
        """
        # Section separator
        separator = tk.Frame(self.scrollable_frame, height=2, bg='#CCCCCC')
        separator.grid(row=start_row, column=0, pady=20, sticky='ew', padx=20)

        # Section label
        section_label = tk.Label(
            self.scrollable_frame,
            text="Saved Annotations",
            font=('Arial', 14, 'bold')
        )
        section_label.grid(row=start_row + 1, column=0, pady=(10, 5), sticky='w', padx=20)

        # Create listbox with scrollbar
        list_frame = tk.Frame(self.scrollable_frame)
        list_frame.grid(row=start_row + 2, column=0, pady=10, padx=20)

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.saved_annotations_listbox = Listbox(
            list_frame,
            width=90,
            height=8,
            yscrollcommand=scrollbar.set,
            font=('Courier', 9)
        )
        self.saved_annotations_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.saved_annotations_listbox.yview)

        # Populate listbox with saved annotations
        self.refresh_saved_annotations_list()

        # Buttons frame
        buttons_frame = tk.Frame(self.scrollable_frame)
        buttons_frame.grid(row=start_row + 3, column=0, pady=10)

        # Delete button
        delete_btn = tk.Button(
            buttons_frame,
            text="Delete Selected",
            command=self.on_delete_annotation_clicked,
            width=18,
            bg='#F44336',
            fg='black',
            font=('Arial', 9, 'bold')
        )
        delete_btn.pack(side=tk.LEFT, padx=5)

    def refresh_saved_annotations_list(self) -> None:
        """
        Refresh the saved annotations listbox with current data.
        """
        self.saved_annotations_listbox.delete(0, tk.END)

        annotations = self.annotation_model.get_annotations()
        for annotation in annotations:
            start = annotation.get('start_date', 'N/A')
            end = annotation.get('end_date', 'N/A')
            reason = annotation.get('reason', 'N/A')
            exclude_from = annotation.get('exclude_from', 'both')
            confirmed = annotation.get('confirmed', False)
            status = "Confirmed" if confirmed else "Dismissed"

            item_text = f"{start} to {end} | {reason[:40]} | Exclude: {exclude_from} | {status}"
            self.saved_annotations_listbox.insert(tk.END, item_text)

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

        # Create annotation dict with exclude_from field
        annotation = {
            'start_date': period_label,
            'end_date': period_label,
            'metric_name': metric_name,
            'reason': f"Statistical anomaly detected: {deviation:.2f}σ from mean",
            'exclude_from': 'both',
            'confirmed': True
        }

        # Save annotation
        self.save_annotation(annotation)

        # Remove from list
        self.anomaly_listbox.delete(idx)
        del self.anomalies_data[idx]

        # Refresh saved annotations list and chart
        self.refresh_saved_annotations_list()
        self.refresh_chart()

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

        # Create annotation dict with exclude_from field
        annotation = {
            'start_date': period_label,
            'end_date': period_label,
            'metric_name': metric_name,
            'reason': f"Statistical anomaly dismissed by user: {deviation:.2f}σ from mean",
            'exclude_from': 'baseline',  # Dismissed annotations still tracked but minimal exclusion
            'confirmed': False
        }

        # Save annotation
        self.save_annotation(annotation)

        # Remove from list
        self.anomaly_listbox.delete(idx)
        del self.anomalies_data[idx]

        # Refresh saved annotations list
        self.refresh_saved_annotations_list()

        messagebox.showinfo("Success", "Anomaly dismissed")

    def on_add_annotation_clicked(self) -> None:
        """
        Handle Add Annotation button click - validate and save manual annotation.
        """
        try:
            # Get field values
            start_date = self.start_date_field.get_value().strip()
            end_date = self.end_date_field.get_value().strip()
            reason = self.reason_field.get_value().strip()
            exclude_from = self.exclude_from_field.get_value()

            # Validate required fields
            if not start_date:
                messagebox.showerror("Validation Error", "Start Date is required")
                return
            if not end_date:
                messagebox.showerror("Validation Error", "End Date is required")
                return
            if not reason:
                messagebox.showerror("Validation Error", "Reason/Description is required")
                return

            # Validate period labels exist in loaded data
            valid_periods = self.current_periods if self.current_periods else []
            if start_date not in valid_periods:
                messagebox.showerror(
                    "Validation Error",
                    f"Start Date '{start_date}' not found in financial data periods.\nValid periods: {', '.join(valid_periods)}"
                )
                return
            if end_date not in valid_periods:
                messagebox.showerror(
                    "Validation Error",
                    f"End Date '{end_date}' not found in financial data periods.\nValid periods: {', '.join(valid_periods)}"
                )
                return

            # Create annotation dict
            annotation = {
                'start_date': start_date,
                'end_date': end_date,
                'metric_name': self.current_metric_name if self.current_metric_name else 'Manual Entry',
                'reason': reason,
                'exclude_from': exclude_from,
                'confirmed': True  # Manual entries are always confirmed
            }

            # Save annotation
            self.save_annotation(annotation)

            # Clear form fields
            self.start_date_field.set_value("")
            self.end_date_field.set_value("")
            self.reason_field.set_value("")
            self.exclude_from_field.set_value("both")

            # Update status
            self.manual_status_label.config(
                text=f"Annotation added: {start_date} to {end_date}",
                fg='#4CAF50'
            )

            # Refresh saved annotations list and chart
            self.refresh_saved_annotations_list()
            self.refresh_chart()

            messagebox.showinfo("Success", "Annotation added successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add annotation: {str(e)}")

    def on_delete_annotation_clicked(self) -> None:
        """
        Handle Delete Selected button click - remove annotation from model.
        """
        selected_indices = self.saved_annotations_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an annotation to delete")
            return

        idx = selected_indices[0]

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this annotation?"
        )
        if not result:
            return

        try:
            # Remove annotation from model
            annotations = self.annotation_model.get_annotations()
            if 0 <= idx < len(annotations):
                del annotations[idx]

                # Save updated model
                config_mgr = self.parent.get_config_manager()
                config_mgr.save_config(self.annotation_model, self.CONFIG_FILEPATH)

                # Refresh list and chart
                self.refresh_saved_annotations_list()
                self.refresh_chart()

                messagebox.showinfo("Success", "Annotation deleted")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete annotation: {str(e)}")

    def save_annotation(self, annotation: Dict) -> None:
        """
        Save anomaly annotation to config file.

        Args:
            annotation: Annotation dict to save
        """
        try:
            # Add annotation and save
            self.annotation_model.add_annotation(annotation)

            config_mgr = self.parent.get_config_manager()
            config_mgr.save_config(self.annotation_model, self.CONFIG_FILEPATH)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save annotation: {str(e)}")

    def refresh_chart(self) -> None:
        """
        Refresh the chart to show updated annotation ranges.
        """
        if self.current_periods and self.current_values and self.current_metric_name:
            # Get current anomaly indices (from remaining anomalies_data)
            anomaly_indices = [period_idx for _, _, period_idx, _, _ in self.anomalies_data]

            # Get annotation ranges
            annotation_ranges = self.annotation_model.get_annotations()

            # Create new chart
            fig = self.visualizer.create_chart_with_annotation_ranges(
                self.current_periods,
                self.current_values,
                self.current_metric_name,
                anomaly_indices,
                annotation_ranges
            )

            # Update chart canvas
            if hasattr(self, 'chart_canvas'):
                self.chart_canvas.figure = fig
                self.chart_canvas.draw()

    def display_error(self, message: str) -> None:
        """
        Display error message when data loading fails.

        Args:
            message: Error message to display
        """
        error_label = tk.Label(
            self.scrollable_frame,
            text=message,
            font=('Arial', 12),
            fg='#F44336'
        )
        error_label.grid(row=1, column=0, pady=20)

        # Add Back to Menu button
        back_btn = tk.Button(
            self.scrollable_frame,
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
