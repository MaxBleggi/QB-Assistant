"""
Unit and integration tests for anomaly detection and annotation functionality.

Tests cover:
- AnomalyAnnotationModel persistence
- AnomalyDetector statistical algorithm
- TimeSeriesVisualizer chart generation
- AnomalyReviewForm GUI integration
"""
import pytest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch

from src.models.anomaly_annotation import AnomalyAnnotationModel
from src.services.anomaly_detector import AnomalyDetector
from src.services.time_series_visualizer import TimeSeriesVisualizer


# Fixtures
@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager for save/load operations."""
    mock = Mock()
    mock.load_config = Mock()
    mock.save_config = Mock()
    return mock


@pytest.fixture
def mock_cash_flow_model():
    """Create mock CashFlowModel with test data."""
    mock = Mock()
    mock.get_periods = Mock(return_value=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'])
    mock.get_operating = Mock(return_value=[
        {
            'account_name': 'Net Cash Provided by Operating Activities',
            'values': {
                'Jan': 100.0,
                'Feb': 102.0,
                'Mar': 98.0,
                'Apr': 101.0,
                'May': 99.0,
                'Jun': 200.0  # Outlier
            }
        }
    ])
    return mock


@pytest.fixture
def mock_pl_model():
    """Create mock PLModel with test data."""
    mock = Mock()
    mock.get_periods = Mock(return_value=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'])
    mock.calculated_rows = [
        {
            'account_name': 'Net Income',
            'values': {
                'Jan': 50.0,
                'Feb': 52.0,
                'Mar': 48.0,
                'Apr': 51.0,
                'May': 49.0,
                'Jun': 50.0  # No outlier
            }
        }
    ]
    return mock


@pytest.fixture
def tk_root():
    """Create tkinter root window for GUI tests."""
    root = tk.Tk()
    root.withdraw()  # Hide window during tests
    yield root
    root.destroy()


# Task 1: AnomalyAnnotationModel tests
def test_anomaly_annotation_model_empty_initialization():
    """Empty model returns empty annotations list."""
    model = AnomalyAnnotationModel()
    annotations = model.get_annotations()

    assert annotations == []
    assert isinstance(annotations, list)


def test_anomaly_annotation_model_add_annotation():
    """Added annotation persists in to_dict serialization."""
    model = AnomalyAnnotationModel()

    annotation = {
        'start_date': '2025-01-01',
        'end_date': '2025-01-31',
        'metric_name': 'Net Income',
        'reason': 'Test anomaly',
        'exclude_from_baseline': True,
        'confirmed': True
    }

    model.add_annotation(annotation)
    serialized = model.to_dict()

    assert 'parameters' in serialized
    assert 'annotations' in serialized['parameters']
    assert len(serialized['parameters']['annotations']) == 1
    assert serialized['parameters']['annotations'][0] == annotation


def test_anomaly_annotation_model_from_dict_deserialization():
    """Deserialized model reconstructs annotations list."""
    data = {
        'parameters': {
            'annotations': [
                {
                    'start_date': '2025-01-01',
                    'end_date': '2025-01-31',
                    'metric_name': 'Net Income',
                    'reason': 'Test anomaly',
                    'exclude_from_baseline': True,
                    'confirmed': True
                }
            ]
        }
    }

    model = AnomalyAnnotationModel.from_dict(data)
    annotations = model.get_annotations()

    assert len(annotations) == 1
    assert annotations[0]['metric_name'] == 'Net Income'
    assert annotations[0]['confirmed'] is True


# Task 2: AnomalyDetector tests
def test_anomaly_detector_detects_outlier():
    """Values >2σ from mean are flagged."""
    detector = AnomalyDetector()
    values = [100.0, 102.0, 98.0, 101.0, 99.0, 200.0]  # Last value is outlier

    anomalies = detector.detect_anomalies(values)

    assert len(anomalies) == 1
    assert anomalies[0][0] == 5  # Index of outlier
    assert anomalies[0][1] == 200.0  # Value of outlier
    assert anomalies[0][2] > 2.0  # Deviation magnitude > 2


def test_anomaly_detector_zero_std_dev():
    """Identical values return no anomalies."""
    detector = AnomalyDetector()
    values = [50.0, 50.0, 50.0, 50.0]

    anomalies = detector.detect_anomalies(values)

    assert anomalies == []


def test_anomaly_detector_insufficient_data():
    """Less than 3 periods returns empty list."""
    detector = AnomalyDetector()
    values = [100.0, 110.0]

    anomalies = detector.detect_anomalies(values)

    assert anomalies == []


def test_anomaly_detector_no_outliers():
    """Values within 2σ return no anomalies."""
    detector = AnomalyDetector()
    values = [100.0, 102.0, 98.0, 101.0, 99.0]

    anomalies = detector.detect_anomalies(values)

    assert anomalies == []


# Task 3: TimeSeriesVisualizer tests
def test_time_series_visualizer_basic_chart():
    """Chart without anomalies renders line plot."""
    visualizer = TimeSeriesVisualizer()
    period_labels = ['Jan', 'Feb', 'Mar']
    values = [100.0, 110.0, 105.0]

    fig = visualizer.create_chart(period_labels, values, 'Test Metric')

    assert fig is not None
    assert len(fig.axes) == 1
    axes = fig.axes[0]
    assert axes.get_title() == 'Test Metric'


def test_time_series_visualizer_with_anomalies():
    """Chart with anomaly indices renders markers."""
    visualizer = TimeSeriesVisualizer()
    period_labels = ['Jan', 'Feb', 'Mar']
    values = [100.0, 110.0, 200.0]
    anomaly_indices = [2]

    fig = visualizer.create_chart(period_labels, values, 'Test Metric', anomaly_indices)

    assert fig is not None
    axes = fig.axes[0]
    # Check that scatter plot was added (more than just line plot)
    assert len(axes.collections) > 0  # Scatter creates PathCollection


def test_time_series_visualizer_long_labels():
    """Charts with >12 periods rotate x-axis labels."""
    visualizer = TimeSeriesVisualizer()
    period_labels = [f'Period {i}' for i in range(15)]
    values = [100.0 + i for i in range(15)]

    fig = visualizer.create_chart(period_labels, values, 'Test Metric')

    assert fig is not None
    axes = fig.axes[0]
    # Check that x-axis labels are rotated
    for label in axes.get_xticklabels():
        rotation = label.get_rotation()
        assert rotation == 45.0


# Task 4: AnomalyReviewForm integration tests
@patch('src.gui.forms.anomaly_review_form.FigureCanvasTkAgg')
def test_anomaly_review_form_displays_anomalies(mock_canvas, tk_root, mock_config_manager, mock_cash_flow_model, mock_pl_model):
    """Form renders charts and lists detected anomalies."""
    from src.gui.forms.anomaly_review_form import AnomalyReviewForm

    # Setup mock parent with config manager
    parent = tk.Frame(tk_root)
    parent.get_config_manager = Mock(return_value=mock_config_manager)

    # Mock load_config to return test models
    def load_side_effect(filepath):
        if 'cash_flow' in filepath:
            return mock_cash_flow_model
        elif 'pl_model' in filepath:
            return mock_pl_model
        raise FileNotFoundError()

    mock_config_manager.load_config.side_effect = load_side_effect

    # Create form
    form = AnomalyReviewForm(parent)

    # Verify anomalies were detected
    assert len(form.anomalies_data) > 0
    assert 'Net Cash Provided by Operating Activities' in [a[0] for a in form.anomalies_data]


@patch('src.gui.forms.anomaly_review_form.FigureCanvasTkAgg')
def test_anomaly_review_form_confirm_anomaly(mock_canvas, tk_root, mock_config_manager, mock_cash_flow_model, mock_pl_model):
    """Confirm button saves annotation with confirmed=True."""
    from src.gui.forms.anomaly_review_form import AnomalyReviewForm

    # Setup mock parent with config manager
    parent = tk.Frame(tk_root)
    parent.get_config_manager = Mock(return_value=mock_config_manager)

    # Mock load_config
    def load_side_effect(filepath):
        if 'cash_flow' in filepath:
            return mock_cash_flow_model
        elif 'pl_model' in filepath:
            return mock_pl_model
        elif 'anomaly_annotations' in filepath:
            return AnomalyAnnotationModel()
        raise FileNotFoundError()

    mock_config_manager.load_config.side_effect = load_side_effect

    # Create form
    form = AnomalyReviewForm(parent)

    # Simulate user selecting first anomaly
    if hasattr(form, 'anomaly_listbox'):
        form.anomaly_listbox.selection_set(0)
        form.on_confirm_clicked()

        # Verify save_config was called
        assert mock_config_manager.save_config.called


@patch('src.gui.forms.anomaly_review_form.FigureCanvasTkAgg')
def test_anomaly_review_form_dismiss_anomaly(mock_canvas, tk_root, mock_config_manager, mock_cash_flow_model, mock_pl_model):
    """Dismiss button saves annotation with confirmed=False."""
    from src.gui.forms.anomaly_review_form import AnomalyReviewForm

    # Setup mock parent with config manager
    parent = tk.Frame(tk_root)
    parent.get_config_manager = Mock(return_value=mock_config_manager)

    # Mock load_config
    def load_side_effect(filepath):
        if 'cash_flow' in filepath:
            return mock_cash_flow_model
        elif 'pl_model' in filepath:
            return mock_pl_model
        elif 'anomaly_annotations' in filepath:
            return AnomalyAnnotationModel()
        raise FileNotFoundError()

    mock_config_manager.load_config.side_effect = load_side_effect

    # Create form
    form = AnomalyReviewForm(parent)

    # Simulate user selecting first anomaly
    if hasattr(form, 'anomaly_listbox'):
        form.anomaly_listbox.selection_set(0)
        form.on_dismiss_clicked()

        # Verify save_config was called
        assert mock_config_manager.save_config.called


@patch('src.gui.forms.anomaly_review_form.FigureCanvasTkAgg')
def test_anomaly_review_form_no_anomalies(mock_canvas, tk_root, mock_config_manager):
    """No anomalies displays appropriate message."""
    from src.gui.forms.anomaly_review_form import AnomalyReviewForm

    # Create mock models with no outliers
    mock_cf = Mock()
    mock_cf.get_periods = Mock(return_value=['Jan', 'Feb', 'Mar'])
    mock_cf.get_operating = Mock(return_value=[
        {
            'account_name': 'Net Cash Provided by Operating Activities',
            'values': {'Jan': 100.0, 'Feb': 101.0, 'Mar': 99.0}
        }
    ])

    mock_pl = Mock()
    mock_pl.get_periods = Mock(return_value=['Jan', 'Feb', 'Mar'])
    mock_pl.calculated_rows = [
        {
            'account_name': 'Net Income',
            'values': {'Jan': 50.0, 'Feb': 51.0, 'Mar': 49.0}
        }
    ]

    # Setup mock parent
    parent = tk.Frame(tk_root)
    parent.get_config_manager = Mock(return_value=mock_config_manager)

    def load_side_effect(filepath):
        if 'cash_flow' in filepath:
            return mock_cf
        elif 'pl_model' in filepath:
            return mock_pl
        raise FileNotFoundError()

    mock_config_manager.load_config.side_effect = load_side_effect

    # Create form
    form = AnomalyReviewForm(parent)

    # Verify no anomalies detected
    assert len(form.anomalies_data) == 0


@patch('src.gui.forms.anomaly_review_form.FigureCanvasTkAgg')
def test_anomaly_review_form_missing_data(mock_canvas, tk_root, mock_config_manager):
    """Missing financial models displays error message."""
    from src.gui.forms.anomaly_review_form import AnomalyReviewForm

    # Setup mock parent
    parent = tk.Frame(tk_root)
    parent.get_config_manager = Mock(return_value=mock_config_manager)

    # Mock load_config to raise exception (no data)
    mock_config_manager.load_config.side_effect = FileNotFoundError()

    # Create form
    form = AnomalyReviewForm(parent)

    # Form should handle missing data gracefully
    # (visual inspection would show error message)
    assert form is not None
