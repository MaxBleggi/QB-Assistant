# Epic 4: Forecasting Engine

**Status**: IN PROGRESS
**Priority**: High
**Dependencies**: Epic 1 (requires parsed financial data), Epic 5 Sprint 5.5 (requires anomaly annotation UI), Epic 5 Sprint 5.7 (requires variable horizon selector)

---

## Purpose

This epic implements a comprehensive forecasting engine that projects financial performance over variable horizons (6-month default for operational planning, 12-month option for expansion planning). It generates Cash Flow forecasts (predicting liquidity and bank account balances) and Profit & Loss forecasts (projecting revenue growth and expenses) with statistical confidence intervals to quantify uncertainty.

The forecasting system is designed for professional services bookkeeping clients with 2+ years of historical data. It uses anomaly-aware baseline calculation that excludes user-annotated external events (government shutdowns, tariffs, supply chain disruptions), employs median-based statistics for outlier robustness, and handles minimal seasonality (discrete events rather than seasonal patterns).

Supports multiple scenarios (Conservative, Expected, Optimistic) with independent parameter sets but uniform forecast horizon. Includes budget vs forecast variance analysis to alert when business is tracking off-budget. All forecasts are explainable to non-technical small business owners.

## Success Criteria

- [ ] Generates 6-month OR 12-month Cash Flow forecasts (user-selectable horizon)
- [ ] Generates 6-month OR 12-month P&L forecasts (user-selectable horizon)
- [ ] Provides statistical confidence intervals (80% default, using historical percentiles method)
- [ ] Excludes user-annotated anomalies from baseline and volatility calculations
- [ ] Uses median-based statistics for outlier robustness
- [ ] Supports multiple named scenarios with independent parameters
- [ ] Enforces uniform horizon policy (all scenarios use same 6 or 12 month setting)
- [ ] Validates forecasts for reasonability and provides warnings for concerning trends
- [ ] Compares forecast to budget for overlapping periods (variance analysis)
- [ ] Handles minimal seasonality with discrete event focus
- [ ] All forecasts explainable to small business owners (not black-box algorithms)

---

## Sprint Breakdown

### Sprint 4.1: Cash Flow Forecasting with Variable Horizon & Confidence Intervals

**Status**: [x] Done

**Description**:
Build cash flow forecasting algorithm that generates monthly projections for variable horizons (6-month default, 12-month for expansion planning). Use Simple Growth Rate Projection with compound monthly growth formula: `projected[M] = baseline * (1 + monthly_rate)^M`. Calculate baseline using median of historical data (outlier-robust) with exclusion of user-annotated anomalous periods. Generate confidence intervals using historical percentiles method (10th and 90th percentiles for 80% confidence). Project three activity sections independently: Operating Activities (with collection timing lag), Investing Activities (with major capex events), and Financing Activities (with debt payment events). Calculate beginning cash (from previous month's ending cash) and ending cash (beginning + all activities) for each forecast month. Detect and flag negative cash positions as liquidity warnings. Support ForecastScenario parameters: monthly_rate, collection_period_days, planned_capex, debt_payments. Return CashFlowForecastModel with projected values, lower/upper confidence bounds, and metadata (confidence level, excluded periods, warnings).

**Acceptance Criteria**:
- Projects cash balance for 6 OR 12 months forward (user-selectable via Epic 5 Sprint 5.7 parameter)
- Generates three data series per scenario: lower bound / projected / upper bound
- Uses median baseline calculation (excludes anomalies from Epic 5 Sprint 5.5 annotations)
- Applies compound growth: `projected[M] = baseline * (1 + monthly_rate)^M`
- Calculates confidence intervals using historical percentiles (10th/90th for 80% confidence)
- Handles collection period timing lag using fractional month distribution
- Integrates major cash events (capex, debt payments) by month
- Detects negative ending cash and flags as liquidity warning
- Returns structured model with hierarchy, calculated_rows, and confidence_metadata

**Estimated Complexity**: Complex

**Notes**: 
- Core algorithm is Simple Growth Rate (not regression/ARIMA) for explainability
- Historical percentiles method requires 6+ data points; with 2+ years data (24+ months) this is robust
- Timing lag uses fractional distribution: `lag_fraction = collection_period_days / 30.0`, split across adjacent months
- Anomaly exclusion requires Epic 5 Sprint 5.5 to be complete first
- Confidence interval width increases with forecast horizon (sqrt(M) scaling typical)

---

### Sprint 4.2: Profit & Loss Forecasting with Variable Horizon & Confidence Intervals

**Status**: [x] Done

**Description**:
Implement Profit & Loss forecasting for revenue and expenses over variable horizons (6 or 12 months). Use compound growth projection with category-specific growth rates: revenue growth, COGS trend, OpEx trend from ForecastScenario parameters. Calculate baseline using median of historical P&L data with anomaly exclusion (same periods excluded as in Sprint 4.1). Generate confidence intervals using historical percentiles method for revenue and expense volatility. Support both top-down forecasting (apply single growth rate to total revenue) and category-specific forecasting (revenue, COGS, OpEx grow independently). Calculate forecasted gross margin, operating expenses, EBITDA, and net income for each month. Handle expense categories appropriately: some grow with revenue (variable costs like COGS), others are relatively fixed (rent, insurance), others have custom growth rates (OpEx trend). Return PLForecastModel with monthly projections, confidence bounds, and calculated margins.

**Acceptance Criteria**:
- Forecasts revenue for 6 OR 12 months using compound growth with category-specific rates
- Projects expenses with category-appropriate methods (COGS tied to revenue, OpEx has independent trend)
- Calculates forecasted margins (gross margin %, operating margin %) and net income monthly
- Generates confidence intervals for revenue and expenses using historical percentiles
- Uses median baseline with anomaly exclusion (consistent with Sprint 4.1 methodology)
- Provides month-by-month P&L forecast detail with lower/upper bounds
- Returns structured model compatible with Epic 6 report generation

**Estimated Complexity**: Complex

**Notes**:
- Category-specific growth allows modeling reality: COGS typically grows with revenue (variable), OpEx grows slower (semi-fixed)
- Confidence intervals for P&L are typically wider than cash flow (more volatility in revenue recognition vs cash timing)
- Uses same anomaly exclusion list as Sprint 4.1 for consistency
- Margin calculations use projected values (not confidence bounds) for simplicity

---

### Sprint 4.3: Scenario-Based Forecasting with Confidence Bands

**Status**: [x] Done

**Description**:
Extend forecasting engine to support multiple named scenarios (Conservative, Expected, Optimistic) with independent assumption sets. Each scenario has separate parameters: revenue_growth_rates, expense_trend_adjustments, cash_flow_timing_params, major_cash_events. Generate separate Cash Flow and P&L forecasts for each scenario using Sprints 4.1 and 4.2 algorithms. Each scenario produces three data series: lower bound, projected, upper bound (from confidence interval calculation). Enforce uniform horizon policy: all scenarios in a report use the same forecast horizon (6 or 12 months) as selected in Epic 5 Sprint 5.7. Store scenario definitions in client configuration for persistence across report runs. Provide side-by-side scenario comparison data structure for Epic 6 report generation. Handle scenario templates (Conservative defaults to 2% growth, Expected to 5%, Optimistic to 10%) with full user customization.

**Acceptance Criteria**:
- Supports multiple named scenarios with independent parameter sets (minimum 3: Conservative/Expected/Optimistic)
- Generates separate Cash Flow and P&L forecasts for each scenario
- Each scenario includes confidence intervals (3 series: lower/projected/upper)
- Enforces uniform horizon policy (all scenarios use same 6 or 12 month setting)
- Scenario definitions persist in client configuration (save/load via Epic 5 infrastructure)
- Provides comparison data structure showing all scenarios side-by-side for Epic 6
- Scenario templates available with reasonable defaults (user-customizable)

**Estimated Complexity**: Complex

**Notes**:
- 3 scenarios × 3 series (lower/projected/upper) = 9 data series total to manage for Cash Flow, 9 for P&L
- Uniform horizon simplifies report layout (all scenarios have same column count)
- If user wants both 6-month and 12-month views, they generate two separate reports
- Scenario comparison enables "what-if" analysis: "If growth is 2% (conservative) vs 10% (optimistic), cash position differs by $X"
- Confidence intervals per scenario reflect parameter differences (optimistic scenario may have wider bounds due to higher growth volatility)

---

### Sprint 4.4: Forecast Validation & Reasonability Checks

**Status**: [ ] Not Started

**Description**:
Add validation layer to forecasts that detects unreasonable projections and provides warnings. Implement checks for concerning trends: projected negative cash balances, cash runway less than 3 months, revenue growth rates exceeding industry norms (>30% monthly sustained growth is unusual for stable businesses), expenses growing faster than revenue (margin compression), and margins declining significantly (>10 percentage points). Provide quality indicators for forecast reliability based on: data availability (more historical data = higher confidence), historical consistency (low volatility = more reliable), and anomaly count (many excluded periods = lower confidence). Generate clear warning messages that appear in report output. Validate that confidence intervals are sensible (lower bound < projected < upper bound, bounds don't cross zero inappropriately). This sprint focuses on VALIDATION WARNINGS, not confidence interval calculation (that's in Sprints 4.1/4.2).

**Acceptance Criteria**:
- Validates forecast outputs for reasonability (flags impossible projections like negative revenue)
- Warns on concerning trends: negative cash, cash runway < 3 months, margin decline >10pp, expenses growing faster than revenue
- Provides quality indicators based on: historical data count, volatility level, anomaly exclusion count
- Validation messages are clear and actionable (e.g., "Cash shortfall projected Month 4: -$5,000 - consider financing")
- Checks confidence interval sanity (lower < projected < upper, mathematically sound)
- Warning thresholds are configurable (default: cash runway 3 months, margin decline 10pp, growth cap 30% monthly)

**Estimated Complexity**: Standard

**Notes**:
- This sprint is about VALIDATION CHECKS, distinct from confidence interval calculation
- Quality indicators help user understand forecast reliability: "High confidence (24 months data, low volatility)" vs "Low confidence (6 months data, 3 anomalies excluded)"
- Warnings should be helpful, not alarmist: frame negative cash as "projected cash shortfall - plan for financing" not "business will fail"
- Thresholds (3 months runway, 10pp margin decline) are reasonable defaults but should be user-configurable in Epic 5

---

### Sprint 4.5: Statistical Volatility Analysis & Percentile Calculation

**Status**: [ ] Not Started

**Description**:
Implement statistical methodology for calculating confidence intervals using historical percentiles method. Calculate historical volatility for cash flow and P&L metrics using 2+ years of data (24+ monthly observations). For each forecasted metric (operating cash, revenue, expenses), compute historical month-over-month percent changes, calculate 10th and 90th percentiles of these changes (representing 80% confidence interval), and apply percentile-based bounds to projected values. Handle sparse data edge cases: require minimum 6 historical periods for percentile calculation, warn user if data is insufficient, use wider default bounds (±25%) when data is limited. Support configurable confidence levels (default 80%, range 50-95%) by adjusting percentile thresholds (90% confidence uses 5th/95th percentiles). Exclude anomalous periods from volatility calculation (consistent with baseline exclusion). Return volatility statistics in forecast metadata for transparency.

**Acceptance Criteria**:
- Calculates historical volatility using 2+ years of month-over-month percent changes
- Implements percentile-based confidence intervals (10th/90th percentiles for 80% confidence)
- Handles sparse data: requires minimum 6 periods, warns if insufficient, uses default bounds (±25%) as fallback
- Supports configurable confidence levels (50-95%) by adjusting percentile thresholds
- Excludes anomalous periods from volatility calculation (same exclusion list as baseline)
- Returns volatility metadata: sample size, percentile values, confidence level, excluded period count
- Confidence interval width scales with forecast horizon (wider bounds for Month 12 than Month 1)

**Estimated Complexity**: Standard

**Notes**:
- Historical percentiles method is distribution-agnostic (doesn't assume normal distribution like parametric methods)
- With 24+ months data, percentile estimates are robust
- Excluding anomalies from volatility calculation prevents distorted bounds (e.g., government shutdown shouldn't inflate normal volatility)
- Confidence level configuration allows user to trade off certainty vs precision (95% confidence = wider bands but higher certainty)
- Horizon scaling reflects reality: near-term forecasts (Month 1-3) more certain than long-term (Month 10-12)

---

### Sprint 4.6: Anomaly Exclusion Logic & Median-Based Statistics

**Status**: [ ] Not Started

**Description**:
Integrate with user-annotated anomaly date ranges from Epic 5 Sprint 5.5. Load anomaly annotations from client configuration: array of `{start_date, end_date, reason, exclude_from: ['baseline', 'volatility', 'both']}`. Filter historical data to exclude anomalous periods before baseline calculation and volatility analysis. Implement median-based statistics for baseline calculation (robust to outliers even with exclusions). Apply exclusions consistently across Cash Flow and P&L forecasting. Validate anomaly date ranges (ensure start < end, dates are within historical data range, no overlapping periods). Include excluded period information in forecast metadata for transparency in reports. Handle edge cases: if too many periods excluded (>50% of data), warn user that forecast reliability is low; if all data excluded, return error.

**Acceptance Criteria**:
- Loads anomaly annotations from Epic 5 Sprint 5.5 client configuration
- Filters historical data excluding annotated periods based on exclude_from setting (baseline/volatility/both)
- Implements median-based baseline calculation (uses median, not mean, for outlier robustness)
- Applies exclusions consistently to both Cash Flow (Sprint 4.1) and P&L (Sprint 4.2)
- Validates anomaly date ranges: start < end, within historical bounds, no overlaps
- Includes excluded period metadata in forecast output (dates, reasons, count)
- Warns if >50% data excluded (low reliability), errors if all data excluded (impossible to forecast)

**Estimated Complexity**: Standard

**Notes**:
- Anomaly exclusion is game-changer for professional services clients (government shutdowns, contract losses are knowable and excludable)
- Median vs mean: median is robust to remaining outliers even after exclusion
- exclude_from flexibility allows nuanced handling: exclude from baseline but include in volatility (captures real-world uncertainty)
- Metadata transparency critical: report must show "Excluded Jan-Mar 2025 (government shutdown)" so user can explain to client
- Edge case of >50% exclusion is red flag: user may be over-excluding, or data is too volatile for reliable forecasting

---

### Sprint 4.7: Budget vs Forecast Variance Analysis

**Status**: [ ] Not Started

**Description**:
Compare forecast projections to budget for overlapping periods to identify when business is tracking off-budget. Load budget data from Epic 3 BudgetModel for the current fiscal year. For each forecast month that has a corresponding budget month (e.g., if forecasting Apr-Sep and budget covers Jan-Dec, overlap is Apr-Sep), calculate variance: `variance_$ = forecast_projected - budget`, `variance_% = (forecast_projected - budget) / budget * 100`. Flag significant variances (default threshold: >10% deviation) with warnings: "Revenue forecast $45K is 12% below budget $51K for June - reforecasting may be needed". Generate variance report data structure compatible with Epic 6 report generation. Handle edge cases: forecast horizon extends beyond budget period (only compare overlapping months), budget doesn't exist yet (skip variance analysis with note), multiple scenarios (calculate variance for Expected scenario only by default, optionally for all scenarios).

**Acceptance Criteria**:
- Compares forecast projections to budget for overlapping months only
- Calculates variance in both absolute ($) and percentage (%) terms
- Flags significant variances (>10% threshold configurable) with clear warning messages
- Generates variance report data compatible with Epic 6 integration
- Handles edge cases: forecast beyond budget period (partial comparison), no budget (skip with note), multiple scenarios (Expected scenario default)
- Variance warnings are actionable: "Revenue tracking 15% below budget - consider revising growth assumptions"

**Estimated Complexity**: Standard

**Notes**:
- Budget vs Forecast variance is early warning system: alerts when business isn't tracking to plan
- Overlapping periods only: if budget is Jan-Dec, forecast is Jul-Dec, compare only Jul-Dec months
- >10% threshold is industry standard for "significant variance" but should be configurable
- Multiple scenarios handling: default to Expected scenario for variance (Conservative will always show negative variance, Optimistic always positive)
- Integration with Epic 3: reads BudgetModel output, doesn't modify budget
- Epic 6 will display this as separate report section: "Budget vs Forecast Variance" table

---

## Epic-Level Notes

### Architectural Decisions

**Confidence Interval Methodology**: Historical Percentiles (Option C)
- Rationale: With 2+ years data (24+ months), percentile-based method is robust and distribution-agnostic. More accurate than parametric assumptions (normal distribution) and more explainable than bootstrap resampling.

**Display Format**: Three rows per metric (Lower Bound / Projected / Upper Bound)
- Rationale: Clearest presentation for non-technical small business owners. User can say "We project $50K, with a likely range of $42K to $58K."

**Scenario Horizon Policy**: Uniform (all scenarios use same 6 or 12 month setting)
- Rationale: Simplifies implementation and report layout. User generates two separate reports if they need both 6-month and 12-month views.

### Key Implementation Patterns

**Baseline Calculation**: Median of historical data excluding anomalous periods
- More robust than mean (outlier-resistant)
- Exclusion list from Epic 5 Sprint 5.5 annotations
- Consistent across Cash Flow and P&L

**Growth Application**: Compound monthly: `projected[M] = baseline * (1 + monthly_rate)^M`
- Simple, explainable, matches user mental model
- Not regression/ARIMA (too complex, black-box for this use case)

**Confidence Intervals**: Historical percentiles (10th/90th for 80% confidence)
- Width increases with horizon: `width[M] ∝ sqrt(M)`
- Excludes anomalies from volatility calculation
- Configurable confidence level (50-95%)

### Integration Dependencies

**Requires from Epic 5**:
- Sprint 5.5: Anomaly annotation UI (user marks government shutdowns, tariffs, etc.)
- Sprint 5.7: Variable horizon selector (6-month vs 12-month radio button)

**Provides to Epic 6**:
- Forecast data with confidence intervals (3 series per scenario per metric)
- Scenario comparison data structure
- Budget vs forecast variance data
- Validation warnings and quality indicators

### Client Context

**Professional Services Clients**:
- Government contracts, labor-based services (bodyguards, consultants)
- Revenue patterns: Stable baseline with discrete events (contract wins/losses)
- Minimal seasonality (unlike retail, restaurants)
- External volatility: Government policy, economic events affect cash flow

**Data Characteristics**:
- 2+ years historical data available (24+ months)
- Quarterly update cadence (forecast regenerated every 3 months)
- Anomalies are identifiable (user knows when government shutdown occurred)

**Explainability Requirement**:
- Bookkeeper must explain to small business owner
- "We applied 5% growth to your baseline" is understandable
- "80% confidence range accounts for historical volatility" is explainable
- Statistical model details hidden from end user (implementation detail)

### Testing Strategy

**Unit Tests** (per sprint):
- Sprint 4.1: Test compound growth calculation, timing lag distribution, confidence interval generation
- Sprint 4.2: Test category-specific growth, margin calculations, P&L confidence intervals
- Sprint 4.3: Test multiple scenarios, enforce uniform horizon, scenario persistence
- Sprint 4.4: Test validation rules (negative cash detection, margin decline, growth caps)
- Sprint 4.5: Test percentile calculation, volatility analysis, horizon scaling
- Sprint 4.6: Test anomaly filtering, median calculation, exclusion metadata
- Sprint 4.7: Test variance calculation, overlapping period logic, threshold flagging

**Integration Tests** (Epic-level):
- End-to-end: Load historical data → exclude anomalies → calculate forecast with confidence intervals → generate all scenarios → produce variance analysis
- Edge cases: Sparse data (<6 months), excessive anomalies (>50% excluded), extreme growth rates (>50%)
- Consistency: Cash flow ending cash continuity, P&L margin calculations, scenario comparison alignment

### Performance Considerations

**With 24+ months data**:
- Percentile calculation: O(n log n) for sorting, negligible for n=24
- Forecast generation: 3 scenarios × 12 months × 3 series = 108 data points (trivial)
- Memory: All forecasts fit in memory easily

**Optimization not needed for MVP** - focus on correctness and explainability.

---

**Status**: Ready for implementation once Epic 5 Sprints 5.5 and 5.7 are complete.
