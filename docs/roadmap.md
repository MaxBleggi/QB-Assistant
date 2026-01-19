# QB-Assistant Development Roadmap

**Vision**: Local financial reporting tool for bookkeeping companies processing QuickBooks Online exports

**Created**: 2026-01-19
**Status**: In Progress

---

## Overview

QB-Assistant is a privacy-first financial reporting tool designed for bookkeeping professionals who need to generate comprehensive financial reports from QuickBooks Online exports. The tool processes Balance Sheets, Profit & Loss statements, and Cash Flow statements entirely locally (no cloud/AI services) to protect sensitive client financial data.

The system generates executive summaries with current month metrics, calculates Budget vs Actual comparisons using historical data and user-tunable parameters, and produces 6-month forecasts for both Cash Flow (liquidity prediction) and P&L (growth/expenses). A simple GUI allows users to configure budget and forecast assumptions, and the tool supports multi-client workflows with separate folder management per client.

Output is provided as Excel-compatible spreadsheet reports that can be directly imported into Excel for client delivery. Built in Python, QB-Assistant is designed for monthly report generation across multiple bookkeeping clients.

---

## Epics Breakdown

### Epic 1: Data Ingestion & Parsing [STARTED]
**Purpose**: Parse QuickBooks CSV/Excel exports and extract structured financial data from Balance Sheet, P&L, Cash Flow, and historical data files
**Priority**: High
**Estimated Sprints**: 5

- [x] Sprint 1.1: File Loader & Validation Framework
- [x] Sprint 1.2: Balance Sheet Parser
- [ ] Sprint 1.3: Profit & Loss Parser with Historical Data
- [ ] Sprint 1.4: Cash Flow Statement Parser
- [ ] Sprint 1.5: Historical Data File Parser

### Epic 2: Core Metrics Calculation [NOT STARTED]
**Purpose**: Calculate executive summary metrics (revenue, margins, cash flow) and KPIs with month-over-month and year-over-year comparisons
**Priority**: High
**Estimated Sprints**: 3

- [ ] Sprint 2.1: Revenue & Margin Calculations
- [ ] Sprint 2.2: Cash Flow & Liquidity Metrics
- [ ] Sprint 2.3: Key Performance Indicators (KPIs)

### Epic 3: Budget System [NOT STARTED]
**Purpose**: Calculate budgets from historical data plus user-tunable parameters, then generate Budget vs Actual YTD comparisons
**Priority**: High
**Estimated Sprints**: 3

- [ ] Sprint 3.1: Budget Calculation Engine
- [ ] Sprint 3.2: Budget vs Actual Comparison
- [ ] Sprint 3.3: Year-to-Date Aggregation

### Epic 4: Forecasting Engine [NOT STARTED]
**Purpose**: Generate 6-month forecasts for both Cash Flow (liquidity) and P&L (growth/expenses) with monthly detail, driven by user-defined assumptions
**Priority**: High
**Estimated Sprints**: 4

- [ ] Sprint 4.1: Cash Flow Forecasting Algorithm
- [ ] Sprint 4.2: Profit & Loss Forecasting Algorithm
- [ ] Sprint 4.3: Scenario-Based Forecasting
- [ ] Sprint 4.4: Forecast Validation & Reasonability Checks

### Epic 5: Parameter Configuration Interface [NOT STARTED]
**Purpose**: Build simple GUI/form for users to set budget and forecast parameters, with configuration persistence per client
**Priority**: Medium
**Estimated Sprints**: 3

- [ ] Sprint 5.1: GUI Framework & Basic Parameter Input
- [ ] Sprint 5.2: Budget Parameter Forms
- [ ] Sprint 5.3: Forecast Assumption Forms

### Epic 6: Report Generation & Output [NOT STARTED]
**Purpose**: Format all calculated outputs into professional Excel-compatible spreadsheet reports
**Priority**: Medium
**Estimated Sprints**: 3

- [ ] Sprint 6.1: Excel Output Framework
- [ ] Sprint 6.2: Executive Summary & KPI Sheets
- [ ] Sprint 6.3: Budget & Forecast Report Sections

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
- **Epic 5 Sprint 5.1** (basic parameter input) should be completed before Epic 3 & 4 are fully functional
- **Epic 2, 3, 4** can proceed in parallel after their dependencies are met
- **Epic 6** requires Epic 2, 3, and 4 to be complete (needs all calculations)
- **Epic 7** ties everything together (requires Epic 5 and 6 complete)

**Recommended Execution Sequence**:
1. Complete Epic 1 (all 5 sprints)
2. Complete Epic 5 Sprint 5.1 (basic parameter infrastructure)
3. Complete Epic 2, Epic 3, Epic 4 (can work sequentially or in parallel)
4. Complete remaining Epic 5 sprints (5.2, 5.3)
5. Complete Epic 6 (all 3 sprints)
6. Complete Epic 7 (final integration)

---

## Notes

*This section can be used to track insights, blockers, or strategic pivots discovered during development.*
