# QB-Assistant Maintenance Guide

**Version**: 1.0
**Created**: 2026-01-25
**Codebase Reference**: ecc66e204d130337fc1f48c7a0ff8182fc5b37f3
**Audience**: FORGE architect agent for modification planning

---

## Overview

This guide provides FORGE-consumable templates for 5 common QB-Assistant modifications. Each template includes pattern reference, modification steps, integration points, and files to modify.

**Templates**:
1. Adding a New Metric
2. Adding a New Report Sheet
3. Adding a New Parser
4. Adding a New GUI Form
5. Extending Client Configuration

---

## Template 1: Adding a New Metric

### Pattern Reference
**Service Layer Pattern**: `/home/max/projects/QB-Assistant/src/metrics/revenue_calculator.py:14-78`

### Purpose
Add a new financial metric calculation (e.g., gross profit margin, debt-to-equity ratio, working capital).

### Files to Modify
1. **Create**: `/home/max/projects/QB-Assistant/src/metrics/{metric_name}_calculator.py`
2. **Modify**: `/home/max/projects/QB-Assistant/src/metrics/kpi_calculator.py`
3. **Modify**: `/home/max/projects/QB-Assistant/src/exporters/kpi_dashboard_writer.py`

### Steps
1. **Create Calculator Class**:
   - Follow service layer pattern: accept models in `__init__`, expose `calculate_*()` method
   - Return Dict[str, float] or specific result type
   - Use existing models (PLModel, BalanceSheetModel, etc.) as input

2. **Integrate in KPICalculator**:
   - Import new calculator in `src/metrics/kpi_calculator.py`
   - Instantiate in `calculate()` method
   - Add results to returned KPIModel

3. **Add to Dashboard Writer**:
   - Import KPIModel updates in `src/exporters/kpi_dashboard_writer.py`
   - Add new metric to appropriate sheet section
   - Use inherited formatting methods (format_currency, apply_header_style)

### Integration Points
- **Pipeline Stage 3**: KPICalculator.calculate() called in PipelineOrchestrator (lines 197-216)
- **Pipeline Stage 7**: KPIDashboardWriter.write() called in PipelineOrchestrator (lines 296-336)

---

## Template 2: Adding a New Report Sheet

### Pattern Reference
**Report Writer Composition Pattern**: `/home/max/projects/QB-Assistant/src/exporters/executive_summary_writer.py:16-164`

### Purpose
Add a new Excel sheet to the generated report (e.g., trend analysis, ratio analysis, custom client view).

### Files to Modify
1. **Create**: `/home/max/projects/QB-Assistant/src/exporters/{sheet_name}_writer.py`
2. **Modify**: `/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py`

### Steps
1. **Create Writer Class**:
   - Inherit from BaseExcelWriter
   - Accept `base_writer: BaseExcelWriter` in `__init__`, set `self.workbook = base_writer.workbook`
   - Implement `write(*models)` method to create sheet
   - Use `self.workbook.create_sheet("Sheet Name")`
   - Use inherited formatting: `apply_header_style()`, `format_currency()`, `traverse_hierarchy()`

2. **Integrate in Pipeline**:
   - Import new writer in `src/services/pipeline_orchestrator.py`
   - Add instantiation in Stage 7 (lines 296-336)
   - Call `writer.write(models)` with required models
   - Workbook shared automatically via composition pattern

### Integration Points
- **Pipeline Stage 7**: All writers instantiated and called sequentially
- **BaseExcelWriter**: Shared workbook ensures all sheets in one file
- **Save**: BaseExcelWriter.save() called once after all writers complete (line 334)

---

## Template 3: Adding a New Parser

### Pattern Reference
**Two-Pass Parser Pattern**: `/home/max/projects/QB-Assistant/src/parsers/balance_sheet_parser.py:24-356`

### Purpose
Add support for a new QuickBooks CSV export type (e.g., Accounts Receivable Aging, Trial Balance).

### Files to Modify
1. **Create**: `/home/max/projects/QB-Assistant/src/parsers/{statement_type}_parser.py`
2. **Create**: `/home/max/projects/QB-Assistant/src/models/{statement_type}.py`
3. **Modify**: `/home/max/projects/QB-Assistant/src/services/pipeline_orchestrator.py`

### Steps
1. **Create Model**:
   - Define Pydantic model in `src/models/{statement_type}.py`
   - Include `df: pd.DataFrame` and `hierarchy: dict` fields
   - Add any statement-specific fields

2. **Create Parser**:
   - Follow two-pass pattern:
     - `__init__(self, file_loader: FileLoader)` - dependency injection
     - `parse(self, file_path) -> Model` - main entry point
     - `_parse_raw_data(self, df) -> DataFrame` - first pass (metadata extraction)
     - `_build_hierarchy(self, df) -> dict` - second pass (tree construction)
   - Handle QuickBooks CSV format quirks (metadata rows, footer detection)
   - Validate required sections exist

3. **Integrate in Pipeline**:
   - Import parser and model in `src/services/pipeline_orchestrator.py`
   - Add file path parameter to `process_pipeline()` method
   - Add parsing logic in Stage 2 (lines 130-195)
   - Pass parsed model to downstream stages as needed

### Integration Points
- **Pipeline Stage 2**: File parsing happens here, models passed to subsequent stages
- **FileLoader**: Used by all parsers for consistent file loading (lines 133-146)
- **Error Handling**: Catch FileLoaderError for I/O issues

---

## Template 4: Adding a New GUI Form

### Pattern Reference
**GUI Form Navigation Pattern**: `/home/max/projects/QB-Assistant/src/gui/forms/main_menu_form.py:18-145`

### Purpose
Add a new GUI screen for user input or configuration (e.g., new parameter form, data review screen).

### Files to Modify
1. **Create**: `/home/max/projects/QB-Assistant/src/gui/forms/{form_name}_form.py`
2. **Modify**: Calling form (e.g., `main_menu_form.py` or another form)

### Steps
1. **Create Form Class**:
   - Inherit from `tk.Frame`
   - Accept `parent` in `__init__(self, parent)`, call `super().__init__(parent)`
   - Store `self.parent = parent` (parent is App instance)
   - Build UI using tkinter widgets (labels, entries, buttons, etc.)
   - Add navigation: `self.parent.show_form(TargetFormClass)` for forward navigation

2. **Add Navigation from Calling Form**:
   - Import new form class in calling form
   - Add button or menu item
   - Button command: `lambda: self.parent.show_form(NewFormClass)`

### Integration Points
- **App.show_form()**: Handles form lifecycle (destroy old, create new, pack)
  - Reference: `/home/max/projects/QB-Assistant/src/gui/app.py:58-74`
- **Form State**: Store state in App instance (`self.parent.client_name`, etc.) for cross-form access
- **ConfigManager**: Load/save configuration via `self.parent` or pass ConfigManager to form

---

## Template 5: Extending Client Configuration

### Pattern Reference
**Client Configuration Structure**: `/home/max/projects/QB-Assistant/src/persistence/config_manager.py:19-205`

### Purpose
Add new configuration fields (e.g., new budget parameter, new forecast scenario field, new report option).

### Files to Modify
1. **Modify**: `/home/max/projects/QB-Assistant/src/models/client_config.py` (or `global_config.py`)
2. **Modify**: Relevant GUI form (e.g., `budget_param_form.py`, `forecast_param_form.py`)
3. **Modify**: Service/calculator that uses the new config

### Steps
1. **Update Configuration Model**:
   - Add new field to Pydantic model (ClientConfigModel or GlobalConfigModel)
   - Provide default value for backward compatibility: `new_field: float = 0.0`
   - ConfigManager handles old config files without new field automatically

2. **Update GUI Form**:
   - Add tkinter widgets for new field (Label, Entry, Checkbutton, etc.)
   - Load value from config in form initialization
   - Save value to config when user submits form
   - Use ConfigManager.load_config() and ConfigManager.save_config()

3. **Use in Service/Calculator**:
   - Access config value in relevant calculator (e.g., BudgetCalculator, Forecaster)
   - Config passed from PipelineOrchestrator Stage 1 (lines 110-128)
   - Use config field in calculation logic

### Integration Points
- **Pipeline Stage 1**: Configs loaded here, passed to downstream stages
  - Global config: `/home/max/projects/QB-Assistant/config/global_settings.json`
  - Client config: `/home/max/projects/QB-Assistant/clients/{client_name}/config.json`
- **ConfigManager**: Handles all load/save operations with security validation
- **Backward Compatibility**: Pydantic defaults ensure old configs work with new code

---

## Modification Guidelines

### General Principles
1. **Follow Existing Patterns**: Use patterns documented in patterns.md
2. **File:Line References**: Check referenced files for implementation examples
3. **Integration Points**: Update PipelineOrchestrator when adding new epic components
4. **Error Handling**: Use Error Handling Hierarchy (FileLoaderError for I/O, CalculationError for logic)
5. **Testing**: Add tests for new calculators, parsers, and writers (follow existing test structure)

### Pipeline Integration Checklist
- [ ] Does new component fit into existing pipeline stage (1-8)?
- [ ] If yes, modify that stage in PipelineOrchestrator
- [ ] If no, consider if new stage is needed (rare - most modifications fit existing stages)
- [ ] Update error handling in pipeline stage to catch new exception types
- [ ] Add progress callback message for new step (if user-facing)

### Common Pitfalls
- **Don't bypass ConfigManager**: Always use ConfigManager for config I/O (security validation required)
- **Don't create new patterns**: Reuse existing 7 patterns unless absolutely necessary
- **Don't modify BaseExcelWriter lightly**: Shared by all writers, changes affect all reports
- **Don't break backward compatibility**: Always provide defaults for new config fields
- **Don't skip two-pass pattern**: All QuickBooks parsers must use two-pass for consistency

---

## Quick Reference

| Modification Type | Primary Pattern | Pipeline Stage | Key Files |
|-------------------|----------------|----------------|-----------|
| New Metric | Service Layer | Stage 3 | kpi_calculator.py, kpi_dashboard_writer.py |
| New Report Sheet | Report Writer Composition | Stage 7 | New writer class, pipeline_orchestrator.py |
| New Parser | Two-Pass Parser | Stage 2 | New parser class, new model, pipeline_orchestrator.py |
| New GUI Form | GUI Form Navigation | N/A (UI layer) | New form class, calling form |
| New Config Field | Client Configuration | Stage 1 | client_config.py, relevant form, relevant service |

---

## Additional Resources
- **Architecture Overview**: See architecture.md for system structure and epic relationships
- **Pattern Details**: See patterns.md for detailed pattern descriptions with code examples
- **Roadmap**: `/home/max/projects/QB-Assistant/docs/roadmap.md` for epic breakdown and dependencies
