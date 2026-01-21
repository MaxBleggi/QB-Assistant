# Epic 2: Core Metrics Calculation

**Status**: DONE
**Priority**: High
**Dependencies**: Epic 1 (requires parsed financial data)

---

## Purpose

This epic implements the calculation engine for executive summary metrics and key performance indicators (KPIs). Using the parsed financial data from Epic 1, this system computes revenue metrics with growth analysis (month-over-month and year-over-year), margin calculations (gross, EBITDA, net), cash flow metrics, and financial health indicators.

These calculations form the core analytical value of QB-Assistant, providing bookkeepers with the key insights they need to present to clients in monthly reports.

## Success Criteria

- [x] Accurately calculates revenue, margins (gross, EBITDA, net), and growth rates (MoM, YoY)
- [x] Computes cash flow metrics and liquidity indicators
- [x] Generates comprehensive KPI set including current ratio, burn rate, and cash runway
- [x] All calculations validated with unit tests against known financial scenarios
- [x] Handles edge cases (missing data, zero denominators) gracefully

---

## Sprint Breakdown

### Sprint 2.1: Revenue & Margin Calculations

**Status**: [x] Done

**Description**:
Implement the calculation engine for revenue metrics and margin analysis. Calculate total revenue for the current period, compute month-over-month growth (comparing to previous month), and year-over-year growth (comparing to same month previous year). Implement margin calculations including gross margin (revenue minus COGS / revenue), EBITDA margin, and net profit margin. Include percentage change calculations with proper handling of zero/negative base values. Create comprehensive unit tests to verify all formulas.

**Acceptance Criteria**:
- Calculates total revenue with month-over-month and year-over-year growth rates
- Computes gross margin, EBITDA margin, and net margin correctly
- Unit tests verify percentage calculations and edge cases (zero revenue, negative values)

**Estimated Complexity**: Standard

**Notes**: EBITDA calculation may require identifying depreciation/amortization in P&L - handle cases where these aren't broken out separately

---

### Sprint 2.2: Cash Flow & Liquidity Metrics

**Status**: [x] Done

**Description**:
Build calculation functions for cash flow and liquidity analysis. Extract operating cash flow from the parsed Cash Flow statement, track cash balance changes month-over-month, and compute free cash flow when capital expenditure data is available (operating cash flow minus capex). Calculate working capital from Balance Sheet (current assets minus current liabilities). Include trend analysis for cash position over time.

**Acceptance Criteria**:
- Calculates operating cash flow from Cash Flow statement
- Tracks cash balance changes month-over-month with trend indicators
- Computes free cash flow when capital expenditure data is available

**Estimated Complexity**: Simple

**Notes**: Free cash flow may not always be calculable if capex isn't broken out - make this optional

---

### Sprint 2.3: Key Performance Indicators (KPIs)

**Status**: [x] Done

**Description**:
Implement a comprehensive KPI calculation engine for financial health indicators. Calculate current ratio (current assets / current liabilities) from Balance Sheet, compute normalized monthly burn rate (average monthly cash decrease), and calculate cash runway in months (current cash / monthly burn). Make the KPI set configurable to allow future expansion with additional metrics. Include validation to ensure ratios handle zero denominators appropriately and provide meaningful defaults or warnings.

**Acceptance Criteria**:
- Calculates current ratio from Balance Sheet data
- Computes normalized monthly burn rate and cash runway in months
- Unit tests verify KPI formulas and edge case handling (zero denominators)

**Estimated Complexity**: Standard

**Notes**: Monthly burn calculation should use a rolling average to smooth out seasonal variations. Consider making the averaging period configurable (e.g., 3-month vs 6-month average).

---

## Epic-Level Notes

*Track decisions about KPI formulas, handling of edge cases, or requests for additional metrics that emerge during development.*
