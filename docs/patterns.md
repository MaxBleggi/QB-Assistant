# QB-Assistant Code Patterns

**Version**: 1.0
**Created**: 2026-01-25
**Codebase Reference**: ecc66e204d130337fc1f48c7a0ff8182fc5b37f3
**Audience**: FORGE explorer agent for architecture validation

---

## Overview

Catalogs 7 core code patterns consistently applied across QB-Assistant: Two-Pass Parser, Service Layer, GUI Form Navigation, Report Writer Composition, Pipeline Orchestration, Error Handling Hierarchy, Client Configuration Structure.

---

## 1. Two-Pass Parser Pattern

**Purpose**: Separate data extraction from hierarchy construction for QuickBooks CSV files with implicit hierarchy.

**Benefits**: Independent testing, clear separation of concerns, better error diagnostics.

**Structure**:
```python
class Parser:
    def __init__(self, file_loader: FileLoader)
    def parse(self, file_path) -> Model
    def _parse_raw_data(self, df) -> DataFrame    # First pass: extract metadata
    def _build_hierarchy(self, df) -> dict        # Second pass: construct tree
```

**Examples**:
- Balance Sheet: `/home/max/projects/QB-Assistant/src/parsers/balance_sheet_parser.py:24-119`
- P&L: `/home/max/projects/QB-Assistant/src/parsers/pl_parser.py:28-142`
- Cash Flow: `/home/max/projects/QB-Assistant/src/parsers/cash_flow_parser.py:31-142`

**Implementation**: First pass extracts account_name, raw_value, numeric_value, row_type ('section'|'parent'|'child'|'total'). Second pass constructs nested dict tree using row_type patterns.

**Use When**: Parsing QuickBooks CSV with hierarchical structure, hierarchy inferred from patterns.

---

## 2. Service Layer Pattern

**Purpose**: Decouple business logic from data models via lazy evaluation.

**Benefits**: Testability (mock models), deferred computation, clear data flow, reusability.

**Structure**:
```python
class Calculator:
    def __init__(self, *models)
    def calculate(self) -> ResultModel
```

**Examples**:
- Budget: `/home/max/projects/QB-Assistant/src/services/budget_calculator.py:18-77`
- Revenue: `/home/max/projects/QB-Assistant/src/metrics/revenue_calculator.py:14-78`
- KPI: `/home/max/projects/QB-Assistant/src/metrics/kpi_calculator.py:17-103`

**Implementation**: Accept models in `__init__`, expose `calculate()` method, return new model or dict. No side effects on input models.

**Use When**: Business logic transforming models, expensive calculations, separation of data and computation.

---

## 3. GUI Form Navigation Pattern

**Purpose**: Single-form navigation without form stacking or memory leaks.

**Benefits**: No memory leaks (destroy before create), simple navigation, clean state, independent forms.

**Structure**:
```python
class SomeForm(tk.Frame):
    def __init__(self, parent):  # parent is App instance
        super().__init__(parent)
        self.parent = parent
    def navigate(self):
        self.parent.show_form(NextFormClass)
```

**Examples**:
- Main Menu: `/home/max/projects/QB-Assistant/src/gui/forms/main_menu_form.py:18-145`
- Client Selection: `/home/max/projects/QB-Assistant/src/gui/forms/client_selection_form.py:23-178`
- App: `/home/max/projects/QB-Assistant/src/gui/app.py:58-74`

**Implementation**: Forms inherit `tk.Frame`, accept parent (App), navigate via `parent.show_form()`. App destroys current form before creating new.

**Use When**: Any GUI form, simple forward navigation.

---

## 4. Report Writer Composition Pattern

**Purpose**: Multi-sheet Excel reports with consistent formatting via shared workbook.

**Benefits**: Shared workbook instance, consistent formatting utilities, separation of concerns, code reuse.

**Structure**:
```python
class BaseExcelWriter:
    def __init__(self, file_path: str):
        self.workbook = Workbook()
    def apply_header_style(self, cell): ...
    def format_currency(self, cell, value): ...

class SpecificWriter(BaseExcelWriter):
    def __init__(self, base_writer: BaseExcelWriter):
        self.workbook = base_writer.workbook  # Share workbook
    def write(self, *models):
        sheet = self.workbook.create_sheet("Name")
```

**Examples**:
- Base: `/home/max/projects/QB-Assistant/src/exporters/base_writer.py:13-294`
- Executive Summary: `/home/max/projects/QB-Assistant/src/exporters/executive_summary_writer.py:16-164`
- KPI Dashboard: `/home/max/projects/QB-Assistant/src/exporters/kpi_dashboard_writer.py:12-152`

**Implementation**: BaseExcelWriter creates workbook. Child writers accept base_writer, set `self.workbook = base_writer.workbook`, implement `write()`.

**Use When**: Multi-sheet Excel reports, consistent formatting needed, independent sheets in one workbook.

---

## 5. Pipeline Orchestration Pattern

**Purpose**: Coordinate sequential processing stages integrating all Epics 1-6.

**Benefits**: Clear 8-stage structure, error isolation per stage, progress reporting, debuggability.

**Structure**:
```python
class PipelineOrchestrator:
    def __init__(self, project_root: str):
        self.config_manager = ConfigManager(project_root)
    def process_pipeline(...) -> Dict[str, Any]:
        # 8 stages: configs → parse → metrics → budget → scenarios → forecasts → report → save
        return {'status': '...', 'report_path': '...', 'errors': [...]}
```

**Example**: `/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py:32-366`

**Stages**:
1. Load configs (110-128)
2. Parse files (130-195)
3. Calculate metrics (197-216)
4. Budget defaults (218-238)
5. Load scenarios (240-254)
6. Run forecasts (256-294)
7. Generate report (296-336)
8. Save to client folder (338-360)

**Implementation**: Each stage in try/except, errors collected, status = 'success'|'partial'|'failed'.

**Use When**: Modifying Epic integration, adding pipeline stages, understanding system integration.

---

## 6. Error Handling Hierarchy

**Purpose**: Categorize errors by source (I/O vs. business logic) for targeted error handling.

**Benefits**: Targeted recovery (I/O → retry, logic → fix data), clear messages, type safety.

**Structure**:
```python
# I/O layer
class FileLoaderError(Exception): pass
class FileNotFoundError(FileLoaderError): pass
class InvalidFormatError(FileLoaderError): pass

# Business logic layer
class CalculationError(Exception): pass
class MissingDataError(CalculationError): pass
class InvalidInputError(CalculationError): pass
```

**Examples**:
- Loader: `/home/max/projects/QB-Assistant/src/loaders/exceptions.py:10-48`
- Metrics: `/home/max/projects/QB-Assistant/src/metrics/exceptions.py:11-66`

**Implementation**: Two hierarchies (FileLoaderError for I/O, CalculationError for logic). Specific exceptions inherit from appropriate base.

**Use When**: Raising errors in parsers (FileLoaderError), calculators (CalculationError), catching for targeted recovery.

---

## 7. Client Configuration Structure

**Purpose**: Manage per-client configuration with security validation and backward compatibility.

**Benefits**: Path traversal protection, backward compatibility via defaults, type safety (Pydantic), atomic writes.

**Structure**:
```python
class ConfigManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    def load_config(self, config_path: str, model_class):
        # Security validation → load JSON → validate Pydantic → return model
    def save_config(self, config_path: str, model: BaseModel):
        # Security validation → atomic write (temp + rename)
```

**Example**: `/home/max/projects/QB-Assistant/src/persistence/config_manager.py:19-205`

**Implementation**: Security validation (59-90), load (92-134), save (136-178). Pydantic defaults for backward compatibility.

**Use When**: Loading/saving any config, extending config schema, any persistence (never direct file I/O).

---

## Pattern Selection Guide

| Need | Pattern |
|------|---------|
| Parse QuickBooks CSV | Two-Pass Parser |
| Calculation/transformation | Service Layer |
| GUI screen | GUI Form Navigation |
| Excel report sheet | Report Writer Composition |
| Epic integration | Pipeline Orchestration |
| Errors | Error Handling Hierarchy |
| Configuration | Client Configuration |

---

## Pattern Relationships

- **Parser → Service**: Parsers create models → services consume models
- **Service → Writer**: Services produce calculated models → writers format to Excel
- **All → Pipeline**: PipelineOrchestrator integrates all patterns sequentially
- **Error Hierarchy**: Used throughout for consistent error handling
- **Config Manager**: Pipeline loads settings, GUI saves user input
