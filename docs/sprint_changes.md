# Sprint Changes - Epic 4 Requirement Updates

**Created**: 2026-01-23
**Reason**: Client clarification session revealed new requirements that fundamentally change Epic 4 scope
**Status**: Pending Implementation

---

## Executive Summary

During Sprint 4.1 checkpoint, client provided critical clarifications that change Epic 4's scope:

1. **2+ years of historical data available** (not 3-12 months as assumed)
2. **Variable forecast horizon needed**: 6-month (default) + 12-month (expansion planning)
3. **Confidence intervals required**: Statistical ranges, not just quality indicators
4. **Anomaly annotation capability**: Manual labeling of external events (government shutdowns, tariffs)
5. **Minimal seasonality**: Professional services clients have discrete events, not seasonal patterns
6. **Quarterly update cadence**: Reports generated every 3 months
7. **Multi-scenario preference confirmed**: Conservative/Expected/Optimistic all valued

These requirements have cascading impacts across Epics 4, 5, and 6, requiring roadmap revision.

---

## Critical Gaps Identified

### Gap 1: Epic 4 Scope Fundamentally Changed

**Current Epic 4 Definition**:
- "Generates accurate 6-month Cash Flow forecasts" (hardcoded 6-month)
- "Handles seasonal patterns and trend analysis" (client confirms minimal seasonality)
- Point estimates only (no confidence intervals specified)

**New Reality**:
- Variable horizon: 6-month default, 12-month option (user selectable)
- Confidence intervals: Statistical ranges (e.g., "80% confident $45K-$65K")
- Minimal seasonality handling needed

**Impact**: Epic 4 purpose statement and all sprint descriptions need rewriting.

---

### Gap 2: Sprint 4.4 Misaligned with Client Needs

**Current Sprint 4.4**: "Forecast Validation & Reasonability Checks"
- Provides quality metadata ("high/medium/low confidence based on data availability")

**What Client Actually Wants**: Statistical confidence intervals
- "80% confident cash will be between $45K-$65K"
- Calculated ranges based on historical volatility

**These are different capabilities**:
- Quality indicator = metadata about forecast reliability
- Confidence interval = calculated statistical range

**Solution**: Either expand Sprint 4.4 or create new Sprint 4.5 for confidence intervals.

---

### Gap 3: Anomaly Annotation Missing from Epic 5

**Client Requirement**: "I would be willing to manually label or annotate the date ranges in the historic customer data if you think that will improve the output"

**Epic 5 Status**: DONE (Sprints 5.1-5.4 completed)

**Gap**: No UI exists for anomaly annotation.

**Solution Required**: Epic 5 Sprint 5.5 "Historical Data Anomaly Annotation UI"
- Allow user to mark date ranges: `{start: "2025-01", end: "2025-03", reason: "Government shutdown"}`
- Persist in client configuration
- Integrate with Epic 4 forecasting (exclude from baseline calculation)

**Impact**: Epic 5 must be reopened.

---

### Gap 4: Epic 6 Report Design Assumes Fixed Format

**Current Epic 6.3 Spec**:
- "Display 6-month projections with monthly columns" (hardcoded layout)
- Point estimates only (single value per month)
- Assumes all scenarios have same horizon

**New Requirements Break This**:
- Variable horizon: 6 OR 12 monthly columns (dynamic layout)
- Confidence intervals: Upper/lower bounds per month (how to display?)
- Potentially different horizons per scenario

**Impact**: Epic 6 Sprint 6.3 specification is obsolete before starting.

---

### Gap 5: Sprint 4.3 Complexity Underestimated

**Current**: Estimated Complexity = Standard

**New Reality**:
- Each scenario generates: projected + upper bound + lower bound (3 series)
- 3 scenarios × 3 series = 9 data series to manage
- Variable horizons per scenario (potentially)
- Report generation must handle variable-length arrays

**Corrected**: Estimated Complexity = Complex

---

### Gap 6: Anomaly Identification Workflow Missing

**Epic 5 Sprint 5.5** (proposed) assumes user knows which periods are anomalous.

**Reality**: How does user identify anomalies? No visual data review exists in QB-Assistant.

**Missing Piece**: Epic 1 Sprint 1.6 "Historical Data Visualization & Anomaly Detection"
- Chart historical cash flow trends to visually spot spikes/dips
- Automated flagging: periods >2σ from mean
- Suggest potential anomalies for user confirmation
- User confirms → feeds into Epic 5 Sprint 5.5 annotation

**Why Critical**: Anomaly annotation is useless without anomaly identification. Workflow prerequisite.

---

### Gap 7: Confidence Interval Methodology Unspecified

**Three Approaches**:

**Option A: Parametric (Normal Distribution)**
- Formula: `forecast ± (z-score * volatility * sqrt(horizon))`
- Pros: Simple, fast, well-understood
- Cons: Assumes normal distribution (cash flows often aren't)

**Option B: Bootstrap Resampling**
- Resample historical data 1000+ times, generate forecast distribution
- Pros: No distribution assumptions, robust
- Cons: Computationally expensive

**Option C: Historical Percentiles**
- Use actual historical volatility distribution (10th, 90th percentiles)
- Pros: Distribution-agnostic, accurate with 2 years data
- Cons: Assumes future volatility matches historical

**Recommendation**: **Option C (Historical Percentiles)** - best balance for client's need (accurate + explainable).

**Decision Needed**: Must be specified in Epic 4 requirements before implementation.

---

### Gap 8: Confidence Interval Display in Excel

**Question**: How to visually represent ranges in Excel?

**Options**:
1. **Three rows per metric**: Lower Bound / Projected / Upper Bound
2. **Shaded cell backgrounds**: Lighter shading = uncertainty range
3. **Mini sparkline charts**: With confidence bands
4. **Separate sheet**: "Confidence Ranges" sheet

**Client Context**: Must explain to small business owners (non-technical).

**Recommendation**: **Option 1 (three rows)** - clearest for non-technical audiences.

**Decision Needed**: Must be specified in Epic 6 Sprint 6.3 updated acceptance criteria.

---

### Gap 9: Scenario Horizon Independence Policy

**Question**: Can different scenarios have different horizons?

**Example**:
- Conservative: 6-month (operational focus)
- Optimistic: 12-month (expansion planning)

**Options**:
- **A**: All scenarios use same horizon (user selects 6 or 12 globally)
- **B**: Each scenario has independent horizon (max flexibility, max complexity)

**Implications**:
- Option A: Simpler implementation and report layout
- Option B: More powerful, but Excel side-by-side comparison is complex (6 columns vs 12)

**Recommendation**: **Option A (uniform horizon)** for MVP. User generates two reports if needing both 6-month and 12-month views.

**Decision Needed**: Must be explicitly documented in Epic 4.3 requirements.

---

## Additional Nuances Discovered

### Medium Priority Additions

#### Budget vs Forecast Integration

**Gap**: Epic 3 generates annual budget. Epic 4 generates forecast. No integration.

**Use Case**:
- Budget (Jan 1): "Plan $100K Q2 revenue"
- Forecast (Mar 31): "Now projecting $95K Q2 revenue"
- Variance: -$5K (5% below budget)

**Value**: Alerts when forecast diverges from budget (reforecasting trigger).

**Potential**: Epic 4 Sprint 4.7 "Budget vs Forecast Variance Analysis"
- Compare forecast to budget for overlapping periods
- Flag significant variances (>10%)
- Answer: "Are we on track to meet budget?"

---

#### External Economic Event Parameters

**Client Insight**: Government shutdowns, tariffs, supply chain disruptions affect forecasts.

**Current**: Reactive (annotate historical anomalies after they happen)

**Gap**: What about PLANNED future external events?

**Example**: "New tariffs expected Q3 2026, expect 15% revenue reduction"

**Current ForecastScenario**:
- `major_cash_events`: Internal events (capex, debt)

**Missing**:
- `external_event_adjustments`: External events (policy, economic shocks)

**Potential Parameter**:
```yaml
external_event_adjustments:
  - month: 8
    impact_type: "revenue_reduction"
    magnitude: 0.15
    description: "Expected tariff impact"
```

**Potential**: Epic 5 Sprint 5.6 "External Economic Event Parameters"

---

#### Report Metadata & Explanatory Documentation

**Gap**: Current Epic 6 generates data tables only. No methodology explanation.

**Client Workflow**: Delivers report to business owner who asks "How did you calculate this?"

**Missing**: Report cover page / metadata:
- Forecast methodology summary
- Assumptions made ("Assumes 5% monthly growth")
- Anomalies excluded ("Jan-Mar 2025 excluded: government shutdown")
- Confidence level interpretation ("80% confidence means...")

**Potential**: Epic 6 Sprint 6.4 "Report Metadata & Explanatory Notes"

---

### Low Priority Considerations

#### Year-End Boundary Handling

**Edge Case**: 12-month forecasts crossing fiscal year boundaries.

**Example**: Forecast from Nov 30, 2025 with 12-month horizon
- Forecasts through Nov 30, 2026
- Crosses FY2025 → FY2026

**Questions**:
- Visual separation of fiscal years in report?
- Confidence intervals widen after year boundary?
- Tax year considerations for professional services?

**Where**: Epic 4 edge case handling + Epic 6 formatting (not new sprint, just explicit criteria)

---

#### Median vs Mean Consistency Policy

**Decision for Epic 4**: Use median (not mean) for baseline (outlier robustness).

**Question**: Consistency across epics?
- Epic 3 (Budget): Uses mean for historical average
- Epic 2 (Metrics): Uses mean for YoY growth

**Gap**: No system-wide policy on outlier-robust statistics.

**Solution**: Document as architectural decision, apply consistently.

---

#### Forecast Accuracy Tracking Over Time

**Use Case**: After multiple quarterly forecast cycles:
- March forecast: predicted $50K June cash
- June actual: $45K
- Accuracy: 10% error

**Learning**: "Your conservative scenarios are typically 15% pessimistic"

**Potential**: Epic 4 Sprint 4.8 "Forecast Accuracy Analytics"

**Why Low Priority**: Requires multiple forecast cycles (data accumulation). Not MVP.

---

## Required Changes to Roadmap

### Epic 1: Data Ingestion & Parsing

**Status**: Currently DONE

**Add**:
- **Sprint 1.6**: "Historical Data Visualization & Anomaly Detection"
  - Chart historical cash flow trends
  - Automated anomaly flagging (>2σ from mean)
  - Visual review UI for user confirmation
  - Feed identified anomalies to Epic 5 Sprint 5.5

**Rationale**: Prerequisite for anomaly annotation workflow.

---

### Epic 4: Forecasting Engine

**Status**: NOT STARTED

**Current Purpose**: "Generate 6-month forecasts for both Cash Flow (liquidity) and P&L (growth/expenses)"

**Updated Purpose**: "Generate variable-horizon forecasts (6-12 months) for both Cash Flow and P&L with confidence intervals, driven by user-defined assumptions and anomaly-aware baseline calculation"

**Updated Success Criteria**:
- [x] ~~Generates accurate 6-month Cash Flow forecasts~~ → Generates 6-month OR 12-month Cash Flow forecasts (user selectable)
- [x] ~~Generates 6-month P&L forecasts~~ → Generates 6-month OR 12-month P&L forecasts (user selectable)
- [NEW] Provides confidence intervals (statistical ranges, not just quality indicators)
- [x] Incorporates user-defined assumptions
- [x] Supports multiple scenarios
- [x] Validates forecasts for reasonability
- [x] ~~Handles seasonal patterns~~ → Handles minimal seasonality with discrete event focus
- [NEW] Excludes user-annotated anomalies from baseline calculation
- [NEW] Uses median-based statistics for outlier robustness

**Sprint Changes**:

#### Sprint 4.1: Cash Flow Forecasting Algorithm
**Changes**:
- Add variable horizon parameter (6 or 12 months)
- Add confidence interval calculation (historical percentiles method)
- Add anomaly exclusion logic (integrate with Epic 5 Sprint 5.5 annotations)
- Change baseline calculation from mean to median
- Update complexity: Complex (was Complex, remains Complex but with more scope)

#### Sprint 4.2: Profit & Loss Forecasting Algorithm
**Changes**:
- Add variable horizon parameter (6 or 12 months)
- Add confidence interval calculation (historical percentiles method)
- Add anomaly exclusion logic
- Change baseline calculation from mean to median
- Update complexity: Complex (was Complex, remains Complex but with more scope)

#### Sprint 4.3: Scenario-Based Forecasting
**Changes**:
- Update to handle confidence intervals (3 data series per scenario: lower/projected/upper)
- Add explicit constraint: All scenarios must use same horizon (uniform policy)
- Update complexity: Complex (was Standard, now Complex due to confidence bands)

#### Sprint 4.4: Forecast Validation & Reasonability Checks
**Clarification**:
- Explicitly NOT about confidence intervals (that's in 4.1/4.2)
- Focus: Validation warnings (negative cash, extreme growth, margin decline)
- Quality indicators based on data sufficiency and historical consistency

**Add New Sprints**:

#### Sprint 4.7: Budget vs Forecast Variance Analysis (NEW)
**Description**: Compare forecast projections to budget for overlapping periods. Calculate variances and flag significant deviations (>10%) to alert when business is tracking off-budget.

**Acceptance Criteria**:
- Compare forecast to budget for overlapping months
- Calculate variance ($ and %)
- Flag significant variances (>10%) with warnings
- Include in report output (Epic 6 integration)

**Estimated Complexity**: Standard

---

### Epic 5: Parameter Configuration Interface

**Status**: Currently DONE (Sprints 5.1-5.4)

**Add New Sprints**:

#### Sprint 5.5: Historical Data Anomaly Annotation UI (NEW)
**Description**: Build GUI for users to manually annotate anomalous date ranges in historical data. Allow marking periods affected by external events (government shutdowns, tariffs, one-time contracts) with exclusion rules for baseline and volatility calculations.

**Acceptance Criteria**:
- UI to add/edit/delete anomaly annotations
- Fields: start_date, end_date, reason, exclude_from (baseline/volatility/both)
- Annotations persist in client configuration
- Visual integration with Epic 1 Sprint 1.6 anomaly detection suggestions
- Clear display of annotated periods in historical data view

**Estimated Complexity**: Standard

**Dependencies**: Epic 1 Sprint 1.6 (anomaly detection suggestions)

---

#### Sprint 5.6: External Economic Event Parameters (NEW)
**Description**: Extend ForecastScenario to support planned future external events (tariffs, policy changes, economic shocks). Allow users to specify month, impact type (revenue reduction, cost increase), magnitude, and description for events expected during forecast horizon.

**Acceptance Criteria**:
- GUI form for external event adjustments
- Fields: month (1-12), impact_type, magnitude (%), description
- Supports multiple events per scenario
- Integrates with Epic 4 forecast calculation
- Persists in scenario configuration

**Estimated Complexity**: Standard

---

#### Sprint 5.7: Variable Forecast Horizon Selector (NEW)
**Description**: Add UI control for selecting forecast horizon (6-month vs 12-month). Default to 6-month with clear indication of which horizon is active. Apply uniformly across all scenarios in the report.

**Acceptance Criteria**:
- Radio buttons or dropdown: 6-month / 12-month
- Default: 6-month
- Clear visual indication of selected horizon
- Setting persists in client configuration
- Applies to all scenarios (uniform policy)

**Estimated Complexity**: Simple

---

### Epic 6: Report Generation & Output

**Status**: NOT STARTED

**Sprint Changes**:

#### Sprint 6.3: Budget & Forecast Report Sections
**Updated Acceptance Criteria**:
- Budget vs Actual: (unchanged)
- Forecast sheets: Display **6-month OR 12-month** projections (dynamic column count based on Epic 5 Sprint 5.7 setting)
- **Confidence intervals**: Display as three rows per metric (Lower Bound / Projected / Upper Bound)
- Multiple scenarios: Display side-by-side (all using same horizon per uniform policy)
- Conditional formatting: Highlight significant variances and concerning trends
- Summary rows: Totals and key metrics

**Add New Sprint**:

#### Sprint 6.4: Report Metadata & Explanatory Documentation (NEW)
**Description**: Add report cover page with methodology summary, assumptions documentation, anomaly exclusions, and confidence interval interpretation guide. Provide context so business owners understand how forecasts were calculated.

**Acceptance Criteria**:
- Cover page with report metadata (date generated, horizon, scenarios included)
- Methodology summary (Simple Growth Rate Projection, confidence interval method)
- Assumptions list (growth rates applied, excluded periods with reasons)
- Confidence interval interpretation ("80% confidence means...")
- Footnotes explaining key concepts

**Estimated Complexity**: Simple

---

## Architectural Decisions Required Before Implementation

These must be answered before regenerating Epic 4:

### Decision 1: Confidence Interval Methodology

**Options**:
- A: Parametric (Normal Distribution) - Simple but assumes normality
- B: Bootstrap Resampling - Robust but computationally expensive
- C: Historical Percentiles - Distribution-agnostic, accurate with 2 years data

**Recommendation**: **Option C** - Best balance of accuracy and explainability.

**Status**: PENDING CLIENT/TEAM DECISION

---

### Decision 2: Confidence Interval Display in Excel

**Options**:
- A: Three rows per metric (Lower / Projected / Upper)
- B: Shaded cell backgrounds (lighter = uncertainty)
- C: Mini sparkline charts with bands
- D: Separate "Confidence Ranges" sheet

**Recommendation**: **Option A** - Clearest for non-technical business owners.

**Status**: PENDING CLIENT/TEAM DECISION

---

### Decision 3: Scenario Horizon Independence Policy

**Options**:
- A: Uniform horizon (all scenarios use same 6 or 12 months)
- B: Independent horizons (each scenario can choose 6 or 12)

**Recommendation**: **Option A** - Simpler implementation and report layout for MVP.

**Status**: PENDING CLIENT/TEAM DECISION

---

## Proposed Implementation Order

### Phase 1: Foundation (Epic 1 Extension)
**Prerequisite for all other work**

1. **Epic 1 Sprint 1.6**: Historical Data Visualization & Anomaly Detection
   - Enables user to identify anomalies
   - Feeds Epic 5 Sprint 5.5

**Estimated Duration**: 1 sprint

---

### Phase 2: Parameter Infrastructure (Epic 5 Extensions)
**Must complete before Epic 4 implementation**

2. **Epic 5 Sprint 5.5**: Historical Data Anomaly Annotation UI
   - Depends on: Epic 1 Sprint 1.6
   - Required by: Epic 4 (anomaly-aware baseline)

3. **Epic 5 Sprint 5.7**: Variable Forecast Horizon Selector
   - Simple UI addition
   - Required by: Epic 4, Epic 6

4. **Epic 5 Sprint 5.6**: External Economic Event Parameters
   - Can be parallel with 5.7
   - Required by: Epic 4

**Estimated Duration**: 2-3 sprints (some parallelization possible)

---

### Phase 3: Core Forecasting (Epic 4 - Regenerated)
**Main implementation effort**

5. **Epic 4 Sprint 4.1**: Cash Flow Forecasting Algorithm (Updated)
   - Includes: variable horizon, confidence intervals, anomaly exclusion
   - Depends on: Epic 5 Sprints 5.5, 5.7

6. **Epic 4 Sprint 4.2**: P&L Forecasting Algorithm (Updated)
   - Includes: variable horizon, confidence intervals, anomaly exclusion
   - Depends on: Epic 5 Sprints 5.5, 5.7

7. **Epic 4 Sprint 4.3**: Scenario-Based Forecasting (Updated)
   - Includes: confidence band handling, uniform horizon policy
   - Depends on: Epic 4 Sprints 4.1, 4.2

8. **Epic 4 Sprint 4.4**: Forecast Validation & Reasonability Checks
   - No major changes (clarified scope)

9. **Epic 4 Sprint 4.7**: Budget vs Forecast Variance Analysis (NEW)
   - Integrates Epic 3 and Epic 4
   - Depends on: Epic 4 Sprints 4.1, 4.2

**Estimated Duration**: 5 sprints

---

### Phase 4: Report Generation (Epic 6 - Updated)
**Deliver complete user experience**

10. **Epic 6 Sprint 6.1**: Excel Output Framework
    - No major changes

11. **Epic 6 Sprint 6.2**: Executive Summary & KPI Sheets
    - No major changes

12. **Epic 6 Sprint 6.3**: Budget & Forecast Report Sections (Updated)
    - Includes: variable columns, confidence interval display
    - Depends on: Epic 4 complete

13. **Epic 6 Sprint 6.4**: Report Metadata & Explanatory Documentation (NEW)
    - Cover page, methodology, assumptions
    - Depends on: Epic 6 Sprint 6.3

**Estimated Duration**: 4 sprints

---

### Total Revised Epic 4-6 Effort

**Original Epic 4-6 Estimate**: 4 + 3 = 7 sprints (Epic 4 only, Epic 6 separate)

**Revised Estimate**:
- Epic 1 Sprint 1.6: 1 sprint
- Epic 5 Sprints 5.5-5.7: 2-3 sprints
- Epic 4 Sprints 4.1-4.7: 5 sprints
- Epic 6 Sprints 6.1-6.4: 4 sprints

**Total**: 12-13 sprints (vs original 7)

**Increase**: ~70-85% scope expansion

**Justification**: Confidence intervals, anomaly handling, and variable horizon are substantial new capabilities that provide significant business value (accurate + explainable forecasts for professional services clients).

---

## Key Insights from Client Session

### What Client Values Most

1. **Explainability > Sophistication**: "Option C - accurate + we explain it in simple terms"
2. **Flexibility**: Both 6-month (operational) and 12-month (expansion) forecasts useful
3. **Multiple scenarios**: Conservative/Expected/Optimistic all valued for decision-making
4. **Confidence ranges**: Wants uncertainty quantified, not hidden
5. **Anomaly awareness**: Willing to manually annotate external events to improve accuracy

### Client Context (Professional Services)

- **Clients**: Government contracts, bodyguard services (labor-based businesses)
- **Revenue patterns**: Relatively stable with discrete events (contract wins/losses)
- **External volatility**: Government shutdowns, tariffs, policy changes affect cash flow
- **Seasonality**: Minimal (unlike retail or seasonal services)
- **Update cadence**: Quarterly (every 3 months)
- **Data availability**: 2+ years historical (24+ months)

### Strategic Implications

- Simple Growth Rate Projection **remains correct algorithm choice**
  - No seasonality to model
  - Discrete events can't be predicted algorithmically
  - Explainability critical for client communication
  
- 2 years of data enables robust statistics
  - Median baseline (outlier-resistant)
  - Percentile-based confidence intervals (distribution-agnostic)
  - Anomaly detection (identify 2σ outliers)

- Anomaly annotation is game-changer
  - Bookkeeper knows business context (government shutdown, contract loss)
  - System can't detect this automatically
  - Manual annotation + algorithmic exclusion = best of both worlds

---

## Status: Ready for Roadmap Regeneration

**Next Steps**:

1. **Finalize architectural decisions** (3 decisions above)
2. **Regenerate Epic 4 using vision-to-roadmap** with updated requirements
3. **Manually add Epic 1 Sprint 1.6, Epic 5 Sprints 5.5-5.7, Epic 6 Sprint 6.4**
4. **Update Epic 6 Sprint 6.3 acceptance criteria**
5. **Resume Sprint 4.1 implementation** with correct scope

**Ground Truth**: This document serves as specification for all changes.

---

**Document Owner**: Max (QB-Assistant Product Owner)
**Last Updated**: 2026-01-23
**Version**: 1.0
