"""
Unit tests for AnomalyValidator.

Tests date ordering validation, bounds validation, overlap detection, and warning generation.
"""
import pytest
from src.validators.anomaly_validator import AnomalyValidator


# Fixtures
@pytest.fixture
def sample_annotations_valid():
    """Valid annotations with no issues."""
    return [
        {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'reason': 'January anomaly',
            'exclude_from': 'baseline'
        },
        {
            'start_date': '2024-03-01',
            'end_date': '2024-03-31',
            'reason': 'March anomaly',
            'exclude_from': 'volatility'
        }
    ]


@pytest.fixture
def sample_annotations_invalid_ordering():
    """Annotations with date ordering violations."""
    return [
        {
            'start_date': '2024-03-01',
            'end_date': '2024-02-01',  # end before start
            'reason': 'Invalid order',
            'exclude_from': 'baseline'
        }
    ]


@pytest.fixture
def sample_annotations_overlapping():
    """Overlapping annotations."""
    return [
        {
            'start_date': '2024-01-01',
            'end_date': '2024-01-15',
            'reason': 'First period',
            'exclude_from': 'baseline'
        },
        {
            'start_date': '2024-01-10',
            'end_date': '2024-01-20',
            'reason': 'Overlapping period',
            'exclude_from': 'baseline'
        }
    ]


@pytest.fixture
def historical_bounds():
    """Historical data bounds."""
    return {
        'earliest': '2024-01-01',
        'latest': '2024-12-31'
    }


# Tests
class TestAnomalyValidator:
    """Test suite for AnomalyValidator."""

    def test_validate_ordering_violation(self, sample_annotations_invalid_ordering, historical_bounds):
        """
        start_date >= end_date returns validation error.

        Given: Annotation with start_date='2024-03-01', end_date='2024-02-01' (reversed)
        When: validate() called
        Then: Returns {valid: False, errors: ['Date ordering violation: start >= end'], warnings: []}
        """
        validator = AnomalyValidator(
            sample_annotations_invalid_ordering,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is False
        assert len(result['errors']) == 1
        assert 'ordering violation' in result['errors'][0].lower()

    def test_validate_out_of_bounds(self, historical_bounds):
        """
        Dates outside historical bounds return error.

        Given: Annotation with dates outside historical bounds
        When: validate() called with bounds earliest='2024-01-01', latest='2024-12-31'
        Then: Returns valid=False with bounds violation error
        """
        out_of_bounds_annotations = [
            {
                'start_date': '2023-12-01',  # Before earliest
                'end_date': '2024-01-15',
                'reason': 'Before bounds',
                'exclude_from': 'baseline'
            }
        ]

        validator = AnomalyValidator(
            out_of_bounds_annotations,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is False
        assert len(result['errors']) >= 1
        assert any('before earliest' in err.lower() for err in result['errors'])

    def test_validate_out_of_bounds_end_date(self, historical_bounds):
        """
        End date after latest historical date returns error.

        Given: Annotation with end_date after latest historical date
        When: validate() called
        Then: Returns valid=False with bounds violation error
        """
        out_of_bounds_annotations = [
            {
                'start_date': '2024-12-01',
                'end_date': '2025-01-31',  # After latest
                'reason': 'After bounds',
                'exclude_from': 'baseline'
            }
        ]

        validator = AnomalyValidator(
            out_of_bounds_annotations,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is False
        assert len(result['errors']) >= 1
        assert any('after latest' in err.lower() for err in result['errors'])

    def test_validate_overlaps(self, sample_annotations_overlapping, historical_bounds):
        """
        Overlapping annotations detected using formula.

        Given: Two annotations: A (2024-01-01 to 2024-01-15), B (2024-01-10 to 2024-01-20)
        When: validate() called
        Then: Returns valid=False with overlap error (A.start <= B.end AND B.start <= A.end is true)
        """
        validator = AnomalyValidator(
            sample_annotations_overlapping,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is False
        assert len(result['errors']) >= 1
        assert any('overlap' in err.lower() for err in result['errors'])

    def test_validate_single_day_warning(self, historical_bounds):
        """
        start_date == end_date returns warning (not error).

        Given: Annotation with start_date == end_date
        When: validate() called
        Then: Returns valid=True with warning about single-day exclusion
        """
        single_day_annotation = [
            {
                'start_date': '2024-05-15',
                'end_date': '2024-05-15',  # Same day
                'reason': 'Single day event',
                'exclude_from': 'baseline'
            }
        ]

        validator = AnomalyValidator(
            single_day_annotation,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        # Should be valid (warning, not error)
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert len(result['warnings']) >= 1
        assert any('single-day' in warn.lower() for warn in result['warnings'])

    def test_validate_all_valid(self, sample_annotations_valid, historical_bounds):
        """
        Valid annotations return {valid: True, errors: [], warnings: []}.

        Given: All annotations valid (ordered, within bounds, no overlaps)
        When: validate() called
        Then: Returns {valid: True, errors: [], warnings: []}
        """
        validator = AnomalyValidator(
            sample_annotations_valid,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is True
        assert len(result['errors']) == 0
        # May have warnings (e.g., single-day), but no errors

    def test_validate_empty_annotations(self, historical_bounds):
        """
        Empty annotations list is valid.

        Given: Empty annotations list
        When: validate() called
        Then: Returns {valid: True, errors: [], warnings: []}
        """
        validator = AnomalyValidator(
            [],
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0

    def test_validate_multiple_errors(self, historical_bounds):
        """
        Multiple validation errors are all reported.

        Given: Annotation with multiple issues (ordering AND bounds)
        When: validate() called
        Then: Multiple errors returned
        """
        multi_error_annotations = [
            {
                'start_date': '2024-06-01',
                'end_date': '2024-05-01',  # Ordering violation
                'reason': 'Bad annotation',
                'exclude_from': 'baseline'
            },
            {
                'start_date': '2025-01-01',  # Out of bounds
                'end_date': '2025-02-01',
                'reason': 'Out of range',
                'exclude_from': 'baseline'
            }
        ]

        validator = AnomalyValidator(
            multi_error_annotations,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        assert result['valid'] is False
        # Should have at least 2 errors (ordering + bounds)
        assert len(result['errors']) >= 2

    def test_validate_adjacent_periods_not_overlapping(self, historical_bounds):
        """
        Adjacent periods (end of A == start of B) do not overlap.

        Given: Two annotations that are adjacent but not overlapping
        When: validate() called
        Then: Returns valid=True (no overlap detected)
        """
        adjacent_annotations = [
            {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'reason': 'January',
                'exclude_from': 'baseline'
            },
            {
                'start_date': '2024-02-01',
                'end_date': '2024-02-28',
                'reason': 'February',
                'exclude_from': 'baseline'
            }
        ]

        validator = AnomalyValidator(
            adjacent_annotations,
            historical_bounds['earliest'],
            historical_bounds['latest']
        )

        result = validator.validate()

        # Adjacent periods should be valid (no overlap)
        assert result['valid'] is True
        assert not any('overlap' in err.lower() for err in result['errors'])

    def test_validate_exact_bounds_edge_case(self):
        """
        Annotations exactly matching historical bounds are valid.

        Given: Annotation with start=earliest and end=latest
        When: validate() called
        Then: Returns valid=True
        """
        exact_bounds_annotation = [
            {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'reason': 'Full year',
                'exclude_from': 'baseline'
            }
        ]

        validator = AnomalyValidator(
            exact_bounds_annotation,
            earliest_date='2024-01-01',
            latest_date='2024-12-31'
        )

        result = validator.validate()

        assert result['valid'] is True
        assert len(result['errors']) == 0
