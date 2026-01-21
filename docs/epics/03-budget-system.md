# Epic 3: Budget System

**Status**: STARTED
**Priority**: High
**Dependencies**: Epic 1 (requires historical data parsing), Epic 5 Sprint 5.1 (requires parameter input infrastructure)

---

## Purpose

This epic builds the budget calculation and comparison system. Using historical financial data from the previous year combined with user-tunable parameters (growth rates, expense adjustments), the system generates line-item budgets for revenue and expenses. It then compares actual year-to-date performance against these budgets, calculates variances, and identifies significant deviations.

Budget vs Actual analysis is a core deliverable for bookkeeping clients, helping them understand where their business is tracking ahead or behind expectations.

## Success Criteria

- [ ] Generates accurate line-item budgets from historical data and user parameters
- [ ] Correctly matches budget line items to actual P&L line items
- [ ] Calculates variances in both absolute (dollar) and percentage terms
- [ ] Aggregates monthly data to year-to-date correctly
- [ ] Handles partial-year scenarios (clients mid-fiscal-year)
- [ ] Flags significant variances for attention

---

## Sprint Breakdown

### Sprint 3.1: Budget Calculation Engine

**Status**: [x] Done

**Description**:
Build the budget calculator that takes historical financial data (from previous year) and applies user-tunable parameters to generate current year budgets. Support both revenue and expense budget categories. Implement parameter types including percentage-based growth rates (e.g., "increase revenue by 15%"), absolute adjustments (e.g., "add $5,000 to marketing budget"), and account-level overrides. Handle different budget methodologies: simple growth from prior year, average of historical periods, or zero-based for new accounts. Create data structures to store budget line items that mirror P&L structure.

**Acceptance Criteria**:
- Applies user-defined parameters (growth rates, adjustments) to historical data
- Generates line-item budgets for both revenue and expense categories
- Handles both percentage-based and absolute dollar adjustments
- Supports account-level overrides for specific line items

**Estimated Complexity**: Complex

**Notes**: Consider supporting multiple budget methodologies per line item (some accounts use growth %, others use historical average). User parameters come from Epic 5 Sprint 5.1.

---

### Sprint 3.2: Budget vs Actual Comparison

**Status**: [x] Done

**Description**:
Create the comparison engine that matches actual P&L line items to budgeted line items, handling potential naming variations between budget and actual. Calculate variances in both absolute terms (actual minus budget) and percentage terms ((actual - budget) / budget). Implement logic to flag significant deviations based on configurable thresholds (e.g., variances greater than 10% or $10,000). Handle favorable vs unfavorable variance direction (for revenue, actual > budget is favorable; for expenses, actual < budget is favorable). Include handling for budget line items without actuals and vice versa.

**Acceptance Criteria**:
- Matches budget to actual line items correctly, handling naming variations
- Calculates variance in both dollar and percentage terms
- Identifies significant variances based on configurable thresholds
- Distinguishes favorable vs unfavorable variance by account type (revenue vs expense)

**Estimated Complexity**: Standard

**Notes**: Account matching may require fuzzy matching if historical account names differ from current. Consider using account numbers if available for more reliable matching.

---

### Sprint 3.3: Year-to-Date Aggregation

**Status**: [ ] Not Started

**Description**:
Implement year-to-date (YTD) aggregation logic for both budget and actual data. Accumulate monthly budget and actual amounts from fiscal year start through current month, calculate cumulative variances, and compute YTD percentage of budget. Support partial-year analysis for clients who start using QB-Assistant mid-fiscal-year (pro-rate annual budgets or use remaining months only). Handle fiscal years that don't align with calendar years. Provide month-by-month accumulation detail in addition to total YTD figures.

**Acceptance Criteria**:
- Aggregates monthly budget and actual data to YTD correctly
- Calculates YTD variances (cumulative actual vs cumulative budget)
- Handles partial-year scenarios (mid-year starts, non-calendar fiscal years)
- Provides month-by-month accumulation detail

**Estimated Complexity**: Standard

**Notes**: Need to determine fiscal year start date - either from configuration, user input, or inferred from data. Consider adding fiscal year settings to client configuration.

---

## Epic-Level Notes

*Track decisions about budget methodologies, variance thresholds, account matching algorithms, or client-specific budgeting needs discovered during development.*
