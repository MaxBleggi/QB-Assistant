# Epic 4: Forecasting Engine

**Status**: NOT STARTED
**Priority**: High
**Dependencies**: Epic 1 (requires parsed financial data), Epic 5 Sprint 5.1 (requires parameter input infrastructure)

---

## Purpose

This epic implements the forecasting engine that projects financial performance over the next 6 months. It generates two types of forecasts: Cash Flow forecasts (predicting liquidity and bank account balances month-by-month) and Profit & Loss forecasts (projecting revenue growth and expenses). Forecasts are driven by user-defined assumptions including growth rates, expense trends, and scenario parameters.

The forecasting system supports multiple scenarios (conservative, expected, optimistic) allowing bookkeepers to present clients with a range of potential outcomes.

## Success Criteria

- [ ] Generates accurate 6-month Cash Flow forecasts with monthly detail
- [ ] Generates 6-month P&L forecasts (revenue and expenses) with monthly detail
- [ ] Incorporates user-defined assumptions (growth rates, expense changes)
- [ ] Supports multiple named scenarios with independent parameters
- [ ] Validates forecasts for reasonability and provides warnings for concerning trends
- [ ] Handles seasonal patterns and trend analysis from historical data

---

## Sprint Breakdown

### Sprint 4.1: Cash Flow Forecasting Algorithm

**Status**: [ ] Not Started

**Description**:
Build a 6-month cash flow forecasting model that projects bank account balances (liquidity) month-by-month. Use historical cash flow patterns (operating, investing, financing activities) combined with user-defined assumptions about revenue growth, payment timing, and major cash events. Account for recurring cash inflows/outflows (payroll, rent, subscriptions) and seasonal patterns observed in historical data. Generate monthly detail showing projected beginning cash, cash in, cash out, and ending cash for each of the next 6 months. Include logic to detect and warn about projected negative cash balances.

**Acceptance Criteria**:
- Projects cash balance for 6 months forward with monthly detail breakdown
- Incorporates user-defined growth and assumption parameters from configuration
- Generates month-by-month cash flow detail (sources and uses)
- Warns when projected cash balance approaches or goes negative

**Estimated Complexity**: Complex

**Notes**: Consider identifying recurring cash flows automatically from historical patterns. Payment timing assumptions (e.g., "revenue collected 30 days after invoicing") significantly impact cash forecasts.

---

### Sprint 4.2: Profit & Loss Forecasting Algorithm

**Status**: [ ] Not Started

**Description**:
Implement Profit & Loss forecasting for revenue and expenses over the next 6 months. Use trend analysis from historical P&L data (growth rates, expense patterns) combined with user-defined assumptions for revenue growth and expense changes. Support both top-down forecasting (apply growth rate to total revenue) and bottom-up (forecast major revenue/expense categories independently). Calculate forecasted gross margin, operating expenses, EBITDA, and net income for each month. Handle expense categories differently: some grow with revenue (variable costs), others are fixed, others have custom growth rates.

**Acceptance Criteria**:
- Forecasts revenue for 6 months using user-defined growth rates or trend analysis
- Projects expenses with category-appropriate methods (variable vs fixed vs custom)
- Calculates forecasted margins (gross, EBITDA, net) and net income monthly
- Provides month-by-month P&L forecast detail

**Estimated Complexity**: Complex

**Notes**: Categorizing expenses as variable vs fixed may require user input or configuration. Consider asking user to tag expense categories or using heuristics (COGS = variable, rent = fixed).

---

### Sprint 4.3: Scenario-Based Forecasting

**Status**: [ ] Not Started

**Description**:
Extend the forecasting engine to support multiple scenarios with independent assumption sets. Allow users to define named scenarios (e.g., "Conservative", "Expected", "Optimistic") each with different growth rates, expense assumptions, and cash flow parameters. Generate separate Cash Flow and P&L forecasts for each scenario. Provide side-by-side scenario comparison views showing how different assumptions lead to different outcomes. Store scenario definitions in client configuration so they persist across report runs.

**Acceptance Criteria**:
- Supports multiple named scenarios with independent parameter sets
- Generates separate Cash Flow and P&L forecasts for each scenario
- Allows side-by-side scenario comparison in output
- Scenario definitions persist in client configuration

**Estimated Complexity**: Standard

**Notes**: Scenario naming and parameter sets should be fully user-configurable via Epic 5 forms. Consider providing scenario templates (e.g., "Conservative" defaults to 5% growth, "Optimistic" to 20%).

---

### Sprint 4.4: Forecast Validation & Reasonability Checks

**Status**: [ ] Not Started

**Description**:
Add a validation layer to forecasts that detects unreasonable projections and provides warnings. Implement checks for concerning trends including projected negative cash balances, cash runway less than 3 months, revenue growth rates exceeding industry norms (e.g., >200% YoY), expenses growing faster than revenue, and margins declining significantly. Provide confidence indicators for forecast quality based on factors like data availability (more historical data = higher confidence), consistency of historical trends, and volatility in historical performance. Generate warnings or alerts that appear in the report output.

**Acceptance Criteria**:
- Validates forecast outputs for reasonability (flags impossible projections)
- Warns on concerning trends (cash runway < 3 months, negative cash, margin decline)
- Provides confidence indicators based on historical data quality and consistency
- Validation messages appear clearly in report output

**Estimated Complexity**: Simple

**Notes**: Thresholds for warnings (e.g., "cash runway < 3 months") should be configurable. Confidence scoring is somewhat subjective - start simple and refine based on user feedback.

---

## Epic-Level Notes

*Track decisions about forecasting methodologies, scenario templates, validation thresholds, or specific client forecasting needs discovered during development.*
