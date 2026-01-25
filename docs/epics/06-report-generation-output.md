# Epic 6: Report Generation & Output

**Status**: STARTED
**Priority**: Medium
**Dependencies**: Epic 2 (metrics), Epic 3 (budget), Epic 4 (forecasts) - requires all calculations to be complete

---

## Purpose

This epic builds the report generation system that formats all calculated outputs into professional, Excel-compatible spreadsheet reports. The reports include Executive Summary (current month metrics), KPI sheets, Budget vs Actual comparisons with variance highlighting, and Forecast sheets showing 6-month projections for Cash Flow and P&L.

The output must be polished and professional since bookkeepers will deliver these reports directly to their clients. Formatting, clarity, and visual hierarchy are critical.

## Success Criteria

- [ ] Generates Excel workbooks (.xlsx format) compatible with Excel on macOS/Windows
- [ ] Reports include all required sections (Executive Summary, KPIs, Budget vs Actual, Forecasts)
- [ ] Professional formatting with clear headers, appropriate number formats, and visual hierarchy
- [ ] Variance highlighting draws attention to significant deviations
- [ ] Multi-scenario forecasts display side-by-side for comparison
- [ ] Output files are ready for client delivery without manual reformatting

---

## Sprint Breakdown

### Sprint 6.1: Excel Output Framework

**Status**: [x] Done

**Description**:
Create the Excel workbook generation framework using openpyxl or xlsxwriter library. Implement template structure with multiple sheets including Executive Summary, KPI Dashboard, Budget vs Actual, Cash Flow Forecast, and P&L Forecast. Build formatting utilities for professional appearance including header styles, currency formatting ($ with thousand separators), percentage formatting, borders, font sizing, and column width auto-adjustment. Implement helper functions for common operations like writing tables, creating headers, and applying conditional formatting. Verify workbooks open correctly in Excel on macOS.

**Acceptance Criteria**:
- Generates Excel workbook (.xlsx) with multiple named sheets
- Applies professional formatting (fonts, borders, number formats for currency/percentages)
- Workbook opens correctly and displays properly in Excel on macOS
- Formatting utilities are reusable across different report sections

**Estimated Complexity**: Standard

**Notes**: openpyxl is pure Python and well-documented. xlsxwriter is faster but write-only. Consider openpyxl for better compatibility. Test with both Excel and LibreOffice/Google Sheets for compatibility.

---

### Sprint 6.2: Executive Summary & KPI Sheets

**Status**: [x] Done

**Description**:
Build report generators for Executive Summary and KPI Dashboard sheets. Executive Summary should display current month metrics including revenue (with MoM/YoY growth and trend indicators ▲/▼), gross margin, operating cash flow, and net income with margin percentage. Format with clear sections and visual hierarchy (bold headers, aligned columns, highlighted key figures). KPI Dashboard should display all calculated KPIs from Epic 2 including growth metrics, profitability ratios, and liquidity indicators with context (e.g., "Current Ratio: 1.9x" with interpretation). Use conditional formatting for trend indicators and threshold warnings (e.g., cash runway < 6 months highlighted in yellow).

**Acceptance Criteria**:
- Executive Summary sheet contains all current month metrics with MoM/YoY comparisons
- KPI Dashboard displays calculated KPIs with clear context and units
- Trend indicators (▲/▼) show growth/decline clearly with color coding
- Professional layout with visual hierarchy and appropriate formatting

**Estimated Complexity**: Standard

**Notes**: Consider adding mini charts/sparklines for KPI trends if openpyxl supports it. Color coding should be subtle (green for positive, red for negative, yellow for warnings).

---

### Sprint 6.3: Budget & Forecast Report Sections

**Status**: [x] Done

**Description**:
Implement Budget vs Actual and Forecast report generators. Budget vs Actual table should show line items from P&L with columns for Budget, Actual, Variance ($), and Variance (%), using conditional formatting to highlight significant variances (red for unfavorable >10%, yellow for moderate 5-10%). Include subtotals for revenue, expenses, and net income. Forecast sheets (separate sheets for Cash Flow and P&L) should display variable-horizon projections (6-month OR 12-month based on Epic 5 Sprint 5.7 setting) with monthly columns showing month-by-month detail. Display confidence intervals as three rows per metric: Lower Bound (10th percentile), Projected (median), Upper Bound (90th percentile). If multiple scenarios exist, display them side-by-side for comparison with clear scenario labels (all using same horizon per uniform policy). Include summary rows for totals and key metrics (ending cash, net income, margins).

**Acceptance Criteria**:
- Budget vs Actual table shows all line items with variance highlighting
- Forecast sheets display 6-month OR 12-month projections (dynamic column count based on Epic 5 Sprint 5.7 horizon setting)
- Confidence intervals displayed as three rows per metric (Lower Bound / Projected / Upper Bound)
- Multiple scenarios display side-by-side when present with clear labels
- All scenarios use same horizon (uniform policy - no mixing 6 and 12 month)
- Conditional formatting highlights significant variances and concerning trends
- Summary rows provide totals and key calculated metrics

**Estimated Complexity**: Complex

**Notes**: Variance highlighting thresholds (10%, 5%) should match those from Epic 3 Sprint 3.2. Three-row confidence interval display (Option A from sprint_changes.md) is clearest for non-technical business owners. Complexity increased to Complex due to variable column count and confidence interval formatting.

---

### Sprint 6.4: Report Metadata & Explanatory Documentation

**Status**: [ ] Not Started

**Description**:
Add report cover page and methodology documentation to help business owners understand how forecasts were calculated. Include report metadata (generation date, horizon selected, scenarios included), methodology summary (Simple Growth Rate Projection, historical percentiles confidence intervals), complete assumptions documentation (growth rates applied, collection periods, major events), excluded periods with reasons (anomalies annotated in Epic 5 Sprint 5.5), and confidence interval interpretation guide. Provide context and transparency so clients can trust and explain the forecast numbers.

**Acceptance Criteria**:
- Cover page sheet with report metadata (date generated, horizon, client name, scenarios included)
- Methodology summary explaining Simple Growth Rate Projection and confidence interval calculation method
- Assumptions section listing all parameters applied (growth rates, timing adjustments, major events, external events)
- Excluded periods section showing anomaly annotations with reasons (from Epic 5 Sprint 5.5)
- Confidence interval interpretation guide ("80% confidence means we expect actual values to fall between Lower and Upper bounds 80% of the time")
- Footnotes explaining key concepts for non-technical business owners
- Professional formatting consistent with other report sheets

**Estimated Complexity**: Simple

**Notes**: This addresses the client workflow where business owners ask "How did you calculate this?" Transparency builds trust and helps bookkeepers explain forecasts to their clients.

---

## Epic-Level Notes

*Track decisions about report layout, formatting conventions, conditional formatting rules, or client-specific reporting requests discovered during development.*
