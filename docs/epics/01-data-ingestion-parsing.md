# Epic 1: Data Ingestion & Parsing

**Status**: STARTED
**Priority**: High
**Dependencies**: None (foundation epic)

---

## Purpose

This epic establishes the foundation of QB-Assistant by building robust parsers for QuickBooks Online export files. The goal is to extract structured financial data from Balance Sheets, Profit & Loss statements, Cash Flow statements, and historical data files (CSV or Excel format). These parsers must handle variations in QuickBooks export formats, validate data integrity, and provide clear error messages when files are malformed.

All subsequent epics depend on this data ingestion layer, making it critical to build a flexible, well-tested parsing system that can accommodate QuickBooks format variations while maintaining data accuracy.

## Success Criteria

- [ ] Successfully parses all four QuickBooks document types (Balance Sheet, P&L, Cash Flow, Historical Data)
- [ ] Handles both CSV and Excel file formats reliably
- [ ] Extracts hierarchical account structures and historical comparison data
- [ ] Validates data integrity and provides actionable error messages for malformed files
- [ ] Unit tests cover common QuickBooks format variations and error cases

---

## Sprint Breakdown

### Sprint 1.1: File Loader & Validation Framework

**Status**: [x] Done

**Description**:
Create a file loading system that accepts both CSV and Excel files, automatically detects file type, validates basic structure, and provides comprehensive error handling for malformed files. Build a validation framework that checks for required columns, data types, and structural consistency. Include unit tests covering various file formats and common error scenarios (missing columns, incorrect data types, empty files).

**Acceptance Criteria**:
- Loads both CSV and Excel files successfully with automatic format detection
- Validates file structure and provides clear, actionable error messages for malformed files
- Unit tests cover common error cases (missing columns, type mismatches, empty files)

**Estimated Complexity**: Standard

**Notes**: Use pandas for CSV/Excel reading, consider using openpyxl or xlrd for Excel-specific features

---

### Sprint 1.2: Balance Sheet Parser

**Status**: [x] Done

**Description**:
Implement a parser to extract Balance Sheet data including assets, liabilities, and equity from QuickBooks export format. Handle common variations in QuickBooks export structures, including hierarchical account structures (parent/child accounts) and subtotals. Create a data model for Balance Sheet representation that preserves account hierarchy and categorization. Include comprehensive unit tests with sample Balance Sheet data.

**Acceptance Criteria**:
- Extracts assets, liabilities, and equity line items with correct categorization
- Handles hierarchical account structures (parent accounts with children/subtotals)
- Unit tests validate parsing with sample Balance Sheet data from QuickBooks

**Estimated Complexity**: Standard

**Notes**: Pay attention to account hierarchy - QuickBooks uses indentation or prefixes to indicate parent-child relationships

---

### Sprint 1.3: Profit & Loss Parser with Historical Data

**Status**: [ ] Not Started

**Description**:
Build a Profit & Loss parser that extracts revenue, cost of goods sold, expenses, and net income data from QuickBooks exports. Critically, this parser must handle embedded historical data for month-over-month and year-over-year comparisons, as P&L exports can include multiple time period columns (current month, previous month, previous year, YTD). Support both monthly and year-to-date column formats. Create a data model that preserves time-series comparison data.

**Acceptance Criteria**:
- Extracts current period and historical period data (previous month, previous year)
- Correctly identifies and categorizes revenue vs expense line items
- Handles both monthly and YTD column formats in QuickBooks exports
- Preserves time-series data for MoM and YoY comparisons

**Estimated Complexity**: Complex

**Notes**: This is the most complex parser - QuickBooks P&L can have many column variations. Consider making column mapping configurable.

---

### Sprint 1.4: Cash Flow Statement Parser

**Status**: [ ] Not Started

**Description**:
Implement a Cash Flow statement parser that extracts cash flow from operating activities, investing activities, and financing activities. Extract beginning and ending cash balances as well as line-item detail within each cash flow category. Build a data model that represents the three-category cash flow structure while preserving individual line items for detailed analysis.

**Acceptance Criteria**:
- Extracts all three cash flow categories (operating, investing, financing) with line-item detail
- Captures beginning and ending cash positions from the statement
- Unit tests validate cash flow calculations (sum of categories equals change in cash)

**Estimated Complexity**: Standard

**Notes**: Cash flow statements have a standardized structure, making this simpler than P&L parsing

---

### Sprint 1.5: Historical Data File Parser

**Status**: [ ] Not Started

**Description**:
Create a parser for the historical data file containing previous year's financial data needed for budget calculations. Design a flexible schema to handle year-over-year data structures, allowing for monthly or annual historical data. Implement account mapping logic to match historical accounts to current period accounts (account names/numbers may vary slightly year-over-year). Validate data completeness to ensure sufficient historical data exists for budget calculations.

**Acceptance Criteria**:
- Loads historical year data for budget calculations (previous year monthly or annual data)
- Maps historical accounts to current accounts, handling minor naming variations
- Validates data completeness and provides warnings if insufficient historical data exists

**Estimated Complexity**: Simple

**Notes**: Format of historical file may be user-defined - consider documenting expected structure or making it configurable

---

## Epic-Level Notes

*Use this section to track patterns discovered during parser development, QuickBooks format quirks, or decisions about handling edge cases.*
