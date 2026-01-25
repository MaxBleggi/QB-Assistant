"""
Unit tests for AnomalyDataFilter service.

Tests date range filtering, exclusion type matching, metadata generation,
and data sufficiency thresholds.
"""
import pytest
import pandas as pd
from datetime import datetime

from src.services.anomaly_data_filter import AnomalyDataFilter


# Fixtures
@pytest.fixture
def sample_datetime_series():
    """Create a sample pandas Series with datetime index."""
    dates = pd.date_range('2024-01-01', periods=12, freq='MS')
    values = [100, 110, 105, 115, 120, 125, 130, 135, 140, 145, 150, 155]
    return pd.Series(values, index=dates)


@pytest.fixture
def sample_annotations_baseline():
    """Sample annotations for baseline exclusion."""
    return [
        {
            'start_date': '2024-03-01',
            'end_date': '2024-05-31',
            'reason': 'Q1 promotion anomaly',
            'exclude_from': 'baseline'
        }
    ]


@pytest.fixture
def sample_annotations_volatility():
    """Sample annotations for volatility exclusion."""
    return [
        {
            'start_date': '2024-06-01',
            'end_date': '2024-07-31',
            'reason': 'Summer volatility spike',
            'exclude_from': 'volatility'
        }
    ]


@pytest.fixture
def sample_annotations_both():
    """Sample annotations with 'both' exclusion type."""
    return [
        {
            'start_date': '2024-08-01',
            'end_date': '2024-09-30',
            'reason': 'Major market disruption',
            'exclude_from': 'both'
        }
    ]


# Tests
class TestAnomalyDataFilter:
    """Test suite for AnomalyDataFilter."""

    def test_filter_single_annotation_baseline(self, sample_datetime_series, sample_annotations_baseline):
        """
        Single baseline annotation excludes correct periods.

        Given: pandas Series with 12 periods, annotation excluding periods 3-5 with exclude_from='baseline'
        When: filter() called with exclusion_type='baseline'
        Then: Returns filtered Series with 9 periods, metadata shows excluded_count=3, exclusion_percentage=0.25
        """
        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            sample_annotations_baseline,
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # Check filtered series has 9 periods (12 - 3)
        assert len(result['filtered_series']) == 9

        # Check metadata
        assert result['metadata']['excluded_count'] == 3
        assert result['metadata']['total_count'] == 12
        assert result['metadata']['exclusion_percentage'] == 0.25
        assert len(result['metadata']['excluded_periods']) == 1
        assert result['metadata']['warning'] is False

    def test_filter_exclusion_type_both(self, sample_datetime_series, sample_annotations_both):
        """
        Annotation with exclude_from='both' matches any exclusion_type.

        Given: pandas Series with 10 periods, annotation with exclude_from='both'
        When: filter() called with exclusion_type='baseline'
        Then: Annotation is matched and applied (because exclude_from='both')
        """
        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            sample_annotations_both,
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # August and September should be excluded (2 months)
        assert result['metadata']['excluded_count'] == 2
        assert len(result['filtered_series']) == 10

    def test_filter_warning_threshold(self, sample_datetime_series):
        """
        >50% exclusion sets warning flag in metadata.

        Given: pandas Series with 10 periods, 8 periods excluded
        When: filter() called
        Then: metadata contains warning flag (exclusion_percentage=0.8 > 0.5)
        """
        # Create annotation excluding 8 months (Jan-Aug)
        high_exclusion_annotation = [
            {
                'start_date': '2024-01-01',
                'end_date': '2024-08-31',
                'reason': 'Major exclusion',
                'exclude_from': 'baseline'
            }
        ]

        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            high_exclusion_annotation,
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # Check warning flag is True
        assert result['metadata']['warning'] is True
        assert result['metadata']['exclusion_percentage'] > 0.5
        assert result['metadata']['excluded_count'] == 8

    def test_filter_100_percent_error(self, sample_datetime_series):
        """
        100% exclusion raises ValueError.

        Given: pandas Series with 10 periods, all 10 periods excluded
        When: filter() called
        Then: Raises ValueError with message about insufficient data
        """
        # Create annotation excluding all 12 months
        full_exclusion_annotation = [
            {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'reason': 'Full year exclusion',
                'exclude_from': 'baseline'
            }
        ]

        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            full_exclusion_annotation,
            exclusion_type='baseline'
        )

        with pytest.raises(ValueError, match='All .* periods would be excluded'):
            filter_service.filter()

    def test_filter_empty_annotations(self, sample_datetime_series):
        """
        Empty annotations list returns original Series.

        Given: Empty annotations list
        When: filter() called
        Then: Returns original Series unchanged with metadata showing excluded_count=0
        """
        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            [],
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # Check no filtering occurred
        assert len(result['filtered_series']) == len(sample_datetime_series)
        assert result['metadata']['excluded_count'] == 0
        assert result['metadata']['exclusion_percentage'] == 0.0
        assert len(result['metadata']['excluded_periods']) == 0

    def test_filter_date_range_matching(self, sample_datetime_series):
        """
        Date range filtering uses >= start and <= end logic.

        Given: Series with monthly data, annotation for specific date range
        When: filter() applied
        Then: Only periods within date range are excluded (inclusive)
        """
        annotation = [
            {
                'start_date': '2024-02-01',
                'end_date': '2024-04-30',
                'reason': 'Q1 anomaly',
                'exclude_from': 'baseline'
            }
        ]

        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            annotation,
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # Feb, Mar, Apr should be excluded (3 months)
        assert result['metadata']['excluded_count'] == 3

        # Check that Jan and May are included
        filtered_dates = result['filtered_series'].index
        assert pd.Timestamp('2024-01-01') in filtered_dates
        assert pd.Timestamp('2024-05-01') in filtered_dates
        # Check that Feb, Mar, Apr are excluded
        assert pd.Timestamp('2024-02-01') not in filtered_dates
        assert pd.Timestamp('2024-03-01') not in filtered_dates
        assert pd.Timestamp('2024-04-01') not in filtered_dates

    def test_filter_metadata_format(self, sample_datetime_series, sample_annotations_baseline):
        """
        Metadata includes excluded_count, total_count, exclusion_percentage, excluded_periods.

        Given: Filter applied with annotations
        When: result metadata examined
        Then: All required metadata fields are present and correctly formatted
        """
        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            sample_annotations_baseline,
            exclusion_type='baseline'
        )

        result = filter_service.filter()
        metadata = result['metadata']

        # Check all required fields exist
        assert 'excluded_count' in metadata
        assert 'total_count' in metadata
        assert 'exclusion_percentage' in metadata
        assert 'excluded_periods' in metadata
        assert 'warning' in metadata

        # Check excluded_periods format
        assert isinstance(metadata['excluded_periods'], list)
        if metadata['excluded_periods']:
            period = metadata['excluded_periods'][0]
            assert 'start_date' in period
            assert 'end_date' in period
            assert 'reason' in period

    def test_filter_no_matching_exclusion_type(self, sample_datetime_series, sample_annotations_volatility):
        """
        Annotations with non-matching exclusion type are ignored.

        Given: Annotation with exclude_from='volatility'
        When: filter() called with exclusion_type='baseline'
        Then: No filtering occurs, all data retained
        """
        filter_service = AnomalyDataFilter(
            sample_datetime_series,
            sample_annotations_volatility,
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # No filtering should occur
        assert len(result['filtered_series']) == len(sample_datetime_series)
        assert result['metadata']['excluded_count'] == 0

    def test_filter_invalid_exclusion_type(self, sample_datetime_series):
        """
        Invalid exclusion_type raises ValueError.

        Given: Invalid exclusion_type
        When: AnomalyDataFilter instantiated
        Then: Raises ValueError
        """
        with pytest.raises(ValueError, match="exclusion_type must be"):
            AnomalyDataFilter(
                sample_datetime_series,
                [],
                exclusion_type='invalid'
            )

    def test_filter_string_index_conversion(self):
        """
        String period index converted to datetime for filtering.

        Given: Series with string index like '2024-01', '2024-02'
        When: filter() called
        Then: Index converted to datetime for proper date comparison
        """
        # Create series with string index
        string_series = pd.Series(
            [100, 110, 120, 130],
            index=['2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01']
        )

        annotation = [
            {
                'start_date': '2024-02-01',
                'end_date': '2024-03-31',
                'reason': 'Test',
                'exclude_from': 'baseline'
            }
        ]

        filter_service = AnomalyDataFilter(
            string_series,
            annotation,
            exclusion_type='baseline'
        )

        result = filter_service.filter()

        # Feb and Mar should be excluded
        assert result['metadata']['excluded_count'] == 2
        assert len(result['filtered_series']) == 2
