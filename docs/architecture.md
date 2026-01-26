# QB-Assistant Architecture

**Version**: 1.0
**Created**: 2026-01-25
**Codebase Reference**: ecc66e204d130337fc1f48c7a0ff8182fc5b37f3
**Audience**: FORGE architect and explorer agents

---

## System Overview

QB-Assistant is a privacy-first local financial reporting tool for bookkeeping professionals. It processes QuickBooks Online CSV exports (Balance Sheet, P&L, Cash Flow, Historical Data) into comprehensive Excel reports with metrics, budgets, and multi-scenario forecasts with confidence intervals.

**Core Workflow**: File Input → Parsing → Metrics Calculation → Budget Defaults → Forecasting → Excel Report Generation → Client Folder Output

**Architecture**: 7-epic structure with Epic 7 pipeline orchestrator integrating Epics 1-6 in sequential stages.

**Entry Point**: `/home/max/projects/QB-Assistant/qb_assistant.py:67-100` (main function auto-detects project root, initializes GUI)

---

## Epic Structure

### Epic 1: Data Ingestion & Parsing
**Purpose**: Parse 4 QuickBooks CSV files into structured Python models
**Components**: FileLoader, 4 parsers (BalanceSheet, P&L, CashFlow, HistoricalData)
**Pattern**: Two-pass parsing (metadata extraction → hierarchy construction)
**Location**: `/home/max/projects/QB-Assistant/src/parsers/` and `/home/max/projects/QB-Assistant/src/loaders/`

### Epic 2: Core Metrics Calculation
**Purpose**: Calculate executive summary metrics and KPIs with MoM/YoY comparisons
**Components**: RevenueCalculator, CashFlowCalculator, KPICalculator
**Pattern**: Service layer pattern (accept models in __init__, expose calculate() method)
**Location**: `/home/max/projects/QB-Assistant/src/metrics/`

### Epic 3: Budget System
**Purpose**: Calculate budgets from historical data + user parameters, generate Budget vs Actual
**Components**: BudgetCalculator, BudgetDefaultsService
**Pattern**: Service layer with lazy evaluation
**Location**: `/home/max/projects/QB-Assistant/src/services/budget_calculator.py:18-77`

### Epic 4: Forecasting Engine
**Purpose**: Generate 6-month or 12-month forecasts with confidence intervals and scenario comparison
**Components**: CashFlowForecaster, PLForecaster, ScenarioForecastOrchestrator
**Pattern**: Statistical forecasting with anomaly-aware baseline using median-based statistics
**Location**: `/home/max/projects/QB-Assistant/src/forecasting/`

### Epic 5: Parameter Configuration Interface
**Purpose**: GUI for budget/forecast parameters, anomaly annotation, horizon selection
**Components**: Tkinter forms (MainMenuForm, BudgetParamForm, ForecastParamForm, etc.)
**Pattern**: tk.Frame inheritance with parent.show_form() navigation
**Location**: `/home/max/projects/QB-Assistant/src/gui/forms/`

### Epic 6: Report Generation & Output
**Purpose**: Format all calculations into professional Excel reports
**Components**: 6 specialized writers (ExecutiveSummary, KPIDashboard, BudgetVariance, CashFlowForecast, PLForecast, MetadataDocumentation)
**Pattern**: BaseExcelWriter composition with shared workbook
**Location**: `/home/max/projects/QB-Assistant/src/exporters/`

### Epic 7: Multi-client Infrastructure
**Purpose**: Client folder management, per-client configurations, complete pipeline orchestration
**Components**: PipelineOrchestrator, ConfigManager, client selection workflow
**Pattern**: Sequential pipeline stages 1-8 integrating all epics
**Location**: `/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py:32-366`

---

## Component Hierarchy

```
Application Layer
├── qb_assistant.py                    # Entry point (main function)
└── src/gui/app.py:15-74               # GUI application controller

Epic Integration Layer
└── PipelineOrchestrator               # Coordinates Epics 1-6

Data Layer (Epic 1)
├── FileLoader                         # CSV/Excel file loading
└── Parsers (4)                        # QuickBooks format parsers

Business Logic Layer (Epics 2-4)
├── Metrics (Epic 2)                   # KPI calculations
├── Services (Epic 3)                  # Budget calculations
└── Forecasting (Epic 4)               # Statistical forecasts

Presentation Layer (Epics 5-6)
├── GUI Forms (Epic 5)                 # Parameter configuration
└── Excel Writers (Epic 6)             # Report generation

Persistence Layer (Epic 7)
└── ConfigManager                      # Client configuration management
```

---

## Data Flow

**Stage 1: Input**
- User selects 4 QuickBooks CSV files via GUI (ClientSelectionForm)
- Files: Balance Sheet, P&L, Cash Flow, Historical Data (optional)

**Stage 2: Parsing (Epic 1)**
- FileLoader validates file existence and format
- 4 parsers convert CSV → Python models (BalanceSheetModel, PLModel, etc.)
- Two-pass parsing: metadata extraction → hierarchy construction

**Stage 3: Metrics Calculation (Epic 2)**
- KPICalculator accepts parsed models
- Calculates: revenue, margins, cash flow metrics, MoM/YoY comparisons
- Output: KPIModel (metrics dictionary)

**Stage 4: Budget Calculation (Epic 3)**
- BudgetDefaultsService applies historical data + user parameters
- BudgetCalculator generates Budget vs Actual YTD comparisons
- Output: BudgetModel

**Stage 5: Forecasting (Epic 4)**
- ScenarioForecastOrchestrator loads scenarios from client config
- Runs CashFlowForecaster + PLForecaster for each scenario
- Calculates confidence intervals using historical percentiles
- Output: ForecastResultsModel (multiple scenarios with confidence bands)

**Stage 6: Report Generation (Epic 6)**
- BaseExcelWriter creates workbook
- 6 specialized writers share workbook, each writes one sheet
- Writers traverse hierarchies and format data with consistent styling
- Output: Multi-sheet Excel file

**Stage 7: Output**
- Report saved to client folder with timestamp
- Path: `clients/{client_name}/reports/{client_name}_report_{timestamp}.xlsx`

---

## Epic 7 Pipeline Integration

**PipelineOrchestrator** (`/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py:32-366`) ties Epics 1-6 together in 8 sequential stages:

**Stage 1** (lines 110-128): Load global + client configurations (ConfigManager)
**Stage 2** (lines 130-195): Parse 4 input files using Epic 1 parsers
**Stage 3** (lines 197-216): Calculate metrics using Epic 2 KPICalculator
**Stage 4** (lines 218-238): Apply budget defaults using Epic 3 BudgetDefaultsService
**Stage 5** (lines 240-254): Load forecast scenarios from client config
**Stage 6** (lines 256-294): Run multi-scenario forecasts using Epic 4 orchestrator
**Stage 7** (lines 296-336): Generate Excel report with Epic 6 writers (6 sheets)
**Stage 8** (lines 338-360): Save report to client folder with timestamped filename

**Error Handling**: Each stage wrapped in try/except, partial completion supported
**Progress Reporting**: Optional progress_callback for GUI status updates
**Return Value**: Dict with status ('success'/'partial'/'failed'), report_path, errors array

---

## Key Design Decisions

### 1. Two-Pass Parsing Pattern
**Decision**: Separate metadata extraction from hierarchy construction
**Rationale**: QuickBooks CSV has no visual indentation - hierarchy inferred from patterns (sections, parents, totals). Two-pass approach enables independent testing of extraction vs. construction logic.
**Implementation**: All 3 statement parsers (BS, P&L, CF) follow identical pattern
**Reference**: `/home/max/projects/QB-Assistant/src/parsers/balance_sheet_parser.py:108-118`

### 2. Lazy Evaluation via Service Layer
**Decision**: Services accept models in constructor, expose calculate() method
**Rationale**: Defers computation until needed, enables testing with mock data, clear data flow
**Implementation**: BudgetCalculator, RevenueCalculator, KPICalculator all follow this pattern
**Reference**: `/home/max/projects/QB-Assistant/src/services/budget_calculator.py:18-37`

### 3. Shared Excel Workbook via Composition
**Decision**: BaseExcelWriter creates workbook, child writers share it via composition
**Rationale**: Enables multi-sheet reports without passing workbook through pipeline, consistent formatting across sheets
**Implementation**: All 6 report writers inherit BaseExcelWriter, set self.workbook = base_writer.workbook
**Reference**: `/home/max/projects/QB-Assistant/src/exporters/executive_summary_writer.py:27-35`

### 4. Single-Form GUI Navigation
**Decision**: App.show_form() destroys current form before creating new one
**Rationale**: Prevents form stacking and memory leaks, simpler than managing form stack
**Implementation**: All forms accept parent (App instance), call parent.show_form(NextFormClass)
**Reference**: `/home/max/projects/QB-Assistant/src/gui/app.py:58-74`

### 5. Sequential Pipeline Orchestration
**Decision**: Linear 8-stage pipeline (not graph-based workflow engine)
**Rationale**: Financial processing is inherently sequential - each stage depends on previous. Simple, predictable, easy to debug.
**Implementation**: PipelineOrchestrator.process_pipeline() executes stages 1-8 with error handling
**Reference**: `/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py:67-103`

### 6. Anomaly-Aware Forecasting
**Decision**: Use median-based statistics instead of mean, allow user to exclude anomalous periods
**Rationale**: Bookkeeping clients have irregular patterns (one-time events). Median is robust to outliers.
**Implementation**: Forecasters calculate percentiles from historical data, user can annotate exclusions
**Reference**: Epic 4 forecasting logic with Epic 5 Sprint 5.5 anomaly annotation UI

### 7. Two-Tier Error Hierarchy
**Decision**: FileLoaderError for I/O issues, CalculationError for business logic issues
**Rationale**: Enables targeted error handling (I/O errors → retry, calculation errors → fix data)
**Implementation**: loaders/exceptions.py and metrics/exceptions.py define hierarchies
**Reference**: `/home/max/projects/QB-Assistant/src/loaders/exceptions.py:10-48`

---

## Integration Points for Future Modifications

**Add New Parser** (Epic 1 extension):
- Follow two-pass pattern (see patterns.md)
- Integrate in PipelineOrchestrator Stage 2
- Update relevant models

**Add New Metric** (Epic 2 extension):
- Follow service layer pattern (see patterns.md)
- Integrate in KPICalculator
- Add to KPIDashboardWriter for report output

**Add New Report Sheet** (Epic 6 extension):
- Inherit from BaseExcelWriter
- Implement write() method
- Add to PipelineOrchestrator Stage 7 writer instantiation

**Extend Client Configuration** (Epic 7 extension):
- Update ClientConfigModel in models/client_config.py
- ConfigManager handles backward compatibility automatically
- Update relevant GUI forms for new parameters

---

## References

**Roadmap**: `/home/max/projects/QB-Assistant/docs/roadmap.md:20-143` (epic breakdown and dependencies)
**Main Entry**: `/home/max/projects/QB-Assistant/qb_assistant.py:67-100`
**Pipeline Orchestrator**: `/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py:32-366`
**GUI Application**: `/home/max/projects/QB-Assistant/src/gui/app.py:15-74`
**Pattern Details**: See patterns.md for implementation details of 7 core patterns
**Modification Templates**: See maintenance_guide.md for FORGE-consumable modification guidance
