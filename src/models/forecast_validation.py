"""
Forecast validation models for validation results and threshold configuration.

Provides ForecastValidationResult (validation output with warnings and quality indicators)
and ValidationThresholds (configurable parameters for validation checks).
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator


class ForecastValidationResult(BaseModel):
    """
    Data model for forecast validation results.

    Stores validation status, warning messages, and quality indicators to help
    bookkeeping professionals understand forecast reliability and identify risks.
    """
    validation_status: str
    warnings: List[Dict[str, Any]]
    quality_level: str
    quality_score: float
    quality_explanation: str

    # Optional metadata fields
    historical_months: Optional[int] = None
    volatility_label: Optional[str] = None
    excluded_periods: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "validation_status": "WARNING",
                "warnings": [
                    {
                        "type": "CASH_RUNWAY",
                        "message": "Cash runway 2 months (below 3 month threshold) - monitor burn rate and plan for financing",
                        "runway_months": 2,
                        "threshold": 3
                    }
                ],
                "quality_level": "Medium",
                "quality_score": 65.0,
                "quality_explanation": "Medium confidence (12 months data, medium volatility, 1 anomaly excluded)",
                "historical_months": 12,
                "volatility_label": "medium volatility",
                "excluded_periods": 1
            }
        }
    }


class ValidationThresholds(BaseModel):
    """
    Configuration model for forecast validation thresholds.

    Stores configurable parameters for validation checks with industry-standard defaults
    based on financial forecasting research. Includes validation rules to ensure
    parameter consistency.
    """
    # Threshold fields for business rule validation
    cash_runway_months: int = 3
    margin_decline_pp: float = 10.0
    revenue_growth_monthly_pct: float = 0.30
    margin_compression_months: int = 2

    # Quality scoring component weights (must sum to 1.0)
    data_availability_weight: float = 0.50
    consistency_weight: float = 0.30
    anomaly_weight: float = 0.20

    # Volatility thresholds for CV-based consistency scoring
    volatility_threshold_low: float = 0.3
    volatility_threshold_high: float = 0.7

    # Quality tier thresholds
    tier_threshold_high: int = 70
    tier_threshold_medium: int = 40

    @field_validator('cash_runway_months')
    @classmethod
    def validate_cash_runway_range(cls, v: int) -> int:
        """Validate cash runway is in valid range (1-24 months)."""
        if not 1 <= v <= 24:
            raise ValueError(f"cash_runway_months must be between 1 and 24, got {v}")
        return v

    @field_validator('margin_decline_pp')
    @classmethod
    def validate_margin_decline_range(cls, v: float) -> float:
        """Validate margin decline is in valid range (1.0-50.0 percentage points)."""
        if not 1.0 <= v <= 50.0:
            raise ValueError(f"margin_decline_pp must be between 1.0 and 50.0, got {v}")
        return v

    @field_validator('revenue_growth_monthly_pct')
    @classmethod
    def validate_revenue_growth_range(cls, v: float) -> float:
        """Validate revenue growth is in valid range (0.10-1.00 or 10%-100%)."""
        if not 0.10 <= v <= 1.00:
            raise ValueError(f"revenue_growth_monthly_pct must be between 0.10 and 1.00, got {v}")
        return v

    @field_validator('margin_compression_months')
    @classmethod
    def validate_margin_compression_range(cls, v: int) -> int:
        """Validate margin compression months is in valid range (1-6 months)."""
        if not 1 <= v <= 6:
            raise ValueError(f"margin_compression_months must be between 1 and 6, got {v}")
        return v

    @field_validator('data_availability_weight', 'consistency_weight', 'anomaly_weight')
    @classmethod
    def validate_weight_range(cls, v: float) -> float:
        """Validate weight is in valid range (0.0-1.0)."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator('volatility_threshold_low')
    @classmethod
    def validate_volatility_low_range(cls, v: float) -> float:
        """Validate low volatility threshold is in valid range (0.1-0.5)."""
        if not 0.1 <= v <= 0.5:
            raise ValueError(f"volatility_threshold_low must be between 0.1 and 0.5, got {v}")
        return v

    @field_validator('volatility_threshold_high')
    @classmethod
    def validate_volatility_high_range(cls, v: float) -> float:
        """Validate high volatility threshold is in valid range (0.4-1.5)."""
        if not 0.4 <= v <= 1.5:
            raise ValueError(f"volatility_threshold_high must be between 0.4 and 1.5, got {v}")
        return v

    @field_validator('tier_threshold_high')
    @classmethod
    def validate_tier_high_range(cls, v: int) -> int:
        """Validate high tier threshold is in valid range (50-90)."""
        if not 50 <= v <= 90:
            raise ValueError(f"tier_threshold_high must be between 50 and 90, got {v}")
        return v

    @field_validator('tier_threshold_medium')
    @classmethod
    def validate_tier_medium_range(cls, v: int) -> int:
        """Validate medium tier threshold is in valid range (20-60)."""
        if not 20 <= v <= 60:
            raise ValueError(f"tier_threshold_medium must be between 20 and 60, got {v}")
        return v

    def model_post_init(self, __context: Any) -> None:
        """
        Validate cross-field constraints after all fields are initialized.

        Checks:
        - Weights sum to 1.0 (+/- 0.01 tolerance)
        - volatility_threshold_high > volatility_threshold_low
        - tier_threshold_high > tier_threshold_medium
        """
        # Check weights sum to 1.0
        weight_sum = self.data_availability_weight + self.consistency_weight + self.anomaly_weight
        if not 0.99 <= weight_sum <= 1.01:
            raise ValueError(
                f"Quality scoring weights must sum to 1.0 (±0.01), got {weight_sum:.3f} "
                f"(data={self.data_availability_weight}, consistency={self.consistency_weight}, "
                f"anomaly={self.anomaly_weight})"
            )

        # Check volatility thresholds are ordered correctly
        if self.volatility_threshold_high <= self.volatility_threshold_low:
            raise ValueError(
                f"volatility_threshold_high ({self.volatility_threshold_high}) must be greater than "
                f"volatility_threshold_low ({self.volatility_threshold_low})"
            )

        # Check tier thresholds are ordered correctly
        if self.tier_threshold_high <= self.tier_threshold_medium:
            raise ValueError(
                f"tier_threshold_high ({self.tier_threshold_high}) must be greater than "
                f"tier_threshold_medium ({self.tier_threshold_medium})"
            )

    model_config = {
        "json_schema_extra": {
            "example": {
                "cash_runway_months": 3,
                "margin_decline_pp": 10.0,
                "revenue_growth_monthly_pct": 0.30,
                "margin_compression_months": 2,
                "data_availability_weight": 0.50,
                "consistency_weight": 0.30,
                "anomaly_weight": 0.20,
                "volatility_threshold_low": 0.3,
                "volatility_threshold_high": 0.7,
                "tier_threshold_high": 70,
                "tier_threshold_medium": 40
            }
        }
    }
