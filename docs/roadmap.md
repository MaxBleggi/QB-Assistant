# QB-Assistant Development Roadmap

**Vision**: Local financial reporting tool for bookkeeping companies processing QuickBooks Online exports

**Created**: 2026-01-19
**Status**: In Progress

---

## Overview

QB-Assistant is a privacy-first financial reporting tool designed for bookkeeping professionals who need to generate comprehensive financial reports from QuickBooks Online exports. The tool processes Balance Sheets, Profit & Loss statements, and Cash Flow statements entirely locally (no cloud/AI services) to protect sensitive client financial data.

The system generates executive summaries with current month metrics, calculates Budget vs Actual comparisons using historical data and user-tunable parameters, and produces variable-horizon forecasts (6-month or 12-month) for both Cash Flow (liquidity prediction) and P&L (growth/expenses) with statistical confidence intervals. A simple GUI allows users to configure budget and forecast assumptions, annotate anomalous periods, and the tool supports multi-client workflows with separate folder management per client.

Output is provided as Excel-compatible spreadsheet reports that can be directly imported into Excel for client delivery. Built in Python, QB-Assistant is designed for monthly report generation across multiple bookkeeping clients.

---

## Epics Breakdown

### Epic 1: Data Ingestion & Parsing [IN PROGRESS]
**Purpose**: Parse QuickBooks CSV/Excel exports and extract structured financial data from Balance Sheet, P&L, Cash Flow, and historical data files. Includes visualization and anomaly detection for identifying irregular historical patterns.
**Priority**: High
**Estimated Sprints**: 6

- [x] Sprint 1.1: File Loader & Validation Framework
- [x] Sprint 1.2: Balance Sheet Parser
- [x] Sprint 1.3: Profit & Loss Parser with Historical Data
- [x] Sprint 1.4: Cash Flow Statement Parser
- [x] Sprint 1.5: Historical Data File Parser
- [ ] Sprint 1.6: Historical Data Visualization & Anomaly Detection

### Epic 2: Core Metrics Calculation [DONE]
**Purpose**: Calculate executive summary metrics (revenue, margins, cash flow) and KPIs with month-over-month and year-over-year comparisons
**Priority**: High
**Estimated Sprints**: 3

- [x] Sprint 2.1: Revenue & Margin Calculations
- [x] Sprint 2.2: Cash Flow & Liquidity Metrics
- [x] Sprint 2.3: Key Performance Indicators (KPIs)

### Epic 3: Budget System [DONE]
**Purpose**: Calculate budgets from historical data plus user-tunable parameters, then generate Budget vs Actual YTD comparisons
**Priority**: High
**Estimated Sprints**: 3

- [x] Sprint 3.1: Budget Calculation Engine
- [x] Sprint 3.2: Budget vs Actual Comparison
- [x] Sprint 3.3: Year-to-Date Aggregation

### Epic 4: Forecasting Engine [NOT STARTED]
**Purpose**: Generate variable-horizon forecasts (6-month or 12-month) for both Cash Flow and P&L with statistical confidence intervals, anomaly-aware baseline calculation, and scenario comparison for professional services bookkeeping clients
**Priority**: High
**Estimated Sprints**: 7

- [ ] Sprint 4.1: Cash Flow Forecasting with Variable Horizon & Confidence Intervals
- [ ] Sprint 4.2: Profit & Loss Forecasting with Variable Horizon & Confidence Intervals
- [ ] Sprint 4.3: Scenario-Based Forecasting with Confidence Bands
- [ ] Sprint 4.4: Forecast Validation & Reasonability Checks
- [ ] Sprint 4.5: Statistical Volatility Analysis & Percentile Calculation
- [ ] Sprint 4.6: Anomaly Exclusion Logic & Median-Based Statistics
- [ ] Sprint 4.7: Budget vs Forecast Variance Analysis

### Epic 5: Parameter Configuration Interface [IN PROGRESS]
**Purpose**: Build simple GUI/form for users to set budget and forecast parameters, annotate historical anomalies, configure variable forecast horizons, and define external economic events, with configuration persistence per client
**Priority**: Medium
**Estimated Sprints**: 7

- [x] Sprint 5.1: GUI Framework & Basic Parameter Input
- [x] Sprint 5.2: Budget Parameter Forms
- [x] Sprint 5.3: Forecast Assumption Forms
- [x] Sprint 5.4 (unplanned): Integrated previous sprints into one UI
- [ ] Sprint 5.5: Historical Data Anomaly Annotation UI
- [ ] Sprint 5.6: External Economic Event Parameters
- [ ] Sprint 5.7: Variable Forecast Horizon Selector

### Epic 6: Report Generation & Output [NOT STARTED]
**Purpose**: Format all calculated outputs into professional Excel-compatible spreadsheet reports with variable-horizon forecasts, confidence intervals, and explanatory documentation
**Priority**: Medium
**Estimated Sprints**: 4

- [ ] Sprint 6.1: Excel Output Framework
- [ ] Sprint 6.2: Executive Summary & KPI Sheets
- [ ] Sprint 6.3: Budget & Forecast Report Sections
- [ ] Sprint 6.4: Report Metadata & Explanatory Documentation

### Epic 7: Multi-client Infrastructure [NOT STARTED]
**Purpose**: Handle client folder management, per-client configurations, and workflow for processing multiple clients
**Priority**: Low
**Estimated Sprints**: 2

- [ ] Sprint 7.1: Client Folder Management System
- [ ] Sprint 7.2: End-to-End Workflow Integration

---

## How to Use This Roadmap

1. **Start with Epic 1, Sprint 1.1**
2. **Run FORGE for each sprint**:
   ```bash
   /orchestrate-sprint --project-root /home/max/projects/QB-Assistant/ "<sprint description from epic file>"
   ```
3. **Check off completed sprints** in this file and the epic file (change `[ ]` to `[x]`)
4. **Proceed to next sprint** when ready

---

## Dependencies Between Epics

**Critical Path**:
- **Epic 1** is the foundation - must be completed first (all other epics depend on parsed data)
- **Epic 1 Sprint 1.6** is required before Epic 5 Sprint 5.5 (anomaly detection feeds annotation UI)
- **Epic 5 Sprint 5.1** (basic parameter input) should be completed before Epic 3 & 4 are fully functional
- **Epic 4** requires Epic 1 Sprint 1.6, Epic 5 Sprint 5.5 (Anomaly Annotation UI), and Epic 5 Sprint 5.7 (Variable Horizon Selector) before implementation can begin
- **Epic 2, 3, 4** can proceed in parallel after their dependencies are met
- **Epic 6** requires Epic 2, 3, and 4 to be complete (needs all calculations)
- **Epic 6 Sprint 6.3** requires Epic 5 Sprint 5.7 (needs horizon setting for variable column count)
- **Epic 7** ties everything together (requires Epic 5 and 6 complete)

**Recommended Execution Sequence** (Updated 2026-01-23):
1. Complete Epic 1 Sprint 1.6 (anomaly detection prerequisite)
2. Complete Epic 5 Sprint 5.5 (anomaly annotation UI)
3. Complete Epic 5 Sprint 5.7 (variable horizon selector)
4. Complete Epic 5 Sprint 5.6 (external events - optional, can be deferred)
5. Begin Epic 4 (all 7 sprints - dependencies now satisfied)
6. Complete Epic 6 Sprint 6.1, 6.2 (report framework)
7. Complete Epic 6 Sprint 6.3, 6.4 (forecast reports with confidence intervals)
8. Complete Epic 7 (final integration)

---

## Notes

### 2026-01-23: Roadmap Update - Epic 4 Scope Expansion

Epic 4 regenerated based on client clarification session during Sprint 4.1 checkpoint. Key changes:

**Epic 4 Changes**:
- Added variable forecast horizon (6-month or 12-month user-selectable)
- Added statistical confidence intervals using historical percentiles method
- Added anomaly-aware baseline calculation using median-based statistics
- Expanded from 4 to 7 sprints to accommodate new capabilities

**Epic 1 Extension**:
- Added Sprint 1.6: Historical Data Visualization & Anomaly Detection
- Provides automated anomaly flagging (>2σ) and visual review UI
- Status changed from DONE to IN PROGRESS

**Epic 5 Extensions**:
- Added Sprint 5.5: Historical Data Anomaly Annotation UI (manual annotation with exclusion rules)
- Added Sprint 5.6: External Economic Event Parameters (planned future external events)
- Added Sprint 5.7: Variable Forecast Horizon Selector (6-month vs 12-month)
- Estimated sprints increased from 4 to 7
- Status changed from DONE to IN PROGRESS

**Epic 6 Updates**:
- Sprint 6.3 updated: Variable horizon support, confidence interval display (three-row format)
- Added Sprint 6.4: Report Metadata & Explanatory Documentation
- Estimated sprints increased from 3 to 4

**Dependencies**:
- Epic 4 cannot start until Epic 1 Sprint 1.6, Epic 5 Sprints 5.5 and 5.7 are complete
- See updated "Recommended Execution Sequence" above

**Documentation**:
- See `docs/sprint_changes.md` for detailed gap analysis and architectural decisions
- See `docs/epics/04-forecasting-engine.md` for complete Epic 4 sprint details
