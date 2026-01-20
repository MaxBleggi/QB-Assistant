# Epic 5: Parameter Configuration Interface

**Status**: NOT STARTED
**Priority**: Medium
**Dependencies**: None (can develop independently, but Epic 3 & 4 need Sprint 5.1 to be functional)

---

## Purpose

This epic builds the user interface for configuring budget and forecast parameters. A simple GUI (form-based interface) allows the bookkeeper to set growth rates, expense adjustments, forecast assumptions, and scenario definitions before generating reports. The interface provides input validation, helpful defaults derived from historical data, and clear labeling to make parameter configuration intuitive.

Configuration is saved per client, allowing different parameter sets for different bookkeeping clients. This epic is critical for making QB-Assistant user-friendly and flexible enough to handle diverse client needs.

## Success Criteria

- [ ] GUI launches and runs reliably on macOS
- [ ] Forms capture all parameters needed for budget calculation (Epic 3)
- [ ] Forms capture all parameters needed for forecasting (Epic 4)
- [ ] Supports multiple scenario creation and editing
- [ ] Configuration saves to and loads from per-client files
- [ ] Input validation prevents invalid parameter values
- [ ] Interface is intuitive with clear labels and helpful defaults

---

## Sprint Breakdown

### Sprint 5.1: GUI Framework & Basic Parameter Input

**Status**: [x] Done

**Description**:
Set up the Python GUI framework using tkinter (built into Python, works well on macOS) or an alternative like PyQt if richer UI is needed. Create the basic window management, layout structure, and navigation between different parameter forms. Implement the parameter data model - a structured representation of all budget and forecast parameters that can be saved to and loaded from configuration files (JSON or YAML format). Build save/load functionality with file I/O, error handling, and validation. Create a basic form with a few sample parameters to validate the framework works end-to-end.

**Acceptance Criteria**:
- GUI launches and displays correctly on macOS
- Basic form fields for parameter input work (text entry, dropdowns, checkboxes)
- Parameters save to and load from configuration file (JSON/YAML)
- Error handling for file I/O issues

**Estimated Complexity**: Standard

**Notes**: tkinter is simplest (built-in to Python), but PyQt/PySide offers more polished UI if needed. Configuration file format should be human-readable for debugging. This sprint is a dependency for Epic 3 & 4.

---

### Sprint 5.2: Budget Parameter Forms

**Status**: [x] Done

**Description**:
Build comprehensive GUI forms for budget parameters. Include input fields for revenue growth rates (overall and per-category), expense adjustment factors (percentage or absolute), account-level overrides for specific line items, and budget methodology selection (growth from prior year vs historical average vs zero-based). Provide input validation to prevent invalid values (e.g., negative growth rates where inappropriate, non-numeric input). Pre-populate forms with reasonable defaults calculated from historical data (e.g., default revenue growth = average of last 3 months growth). Include help text and tooltips explaining what each parameter controls.

**Acceptance Criteria**:
- Forms capture all budget parameters needed by Epic 3 (growth rates, adjustments, overrides)
- Input validation prevents invalid values (with clear error messages)
- Forms pre-populate with reasonable defaults derived from historical data
- Help text and labels make parameters understandable

**Estimated Complexity**: Standard

**Notes**: Consider organizing parameters hierarchically (revenue section, expense section, account overrides section). Defaults calculation requires access to parsed historical data from Epic 1.

---

### Sprint 5.3: Forecast Assumption Forms

**Status**: [ ] Not Started

**Description**:
Create GUI forms for forecast assumptions including revenue growth rates (monthly or averaged), expense trend adjustments (by category), cash flow timing parameters (payment collection periods, payment terms), and major cash events (planned capital expenditures, debt payments). Implement scenario management UI allowing users to create, name, edit, and delete multiple forecast scenarios. Each scenario should have an independent set of forecast parameters. Provide scenario templates (e.g., "Conservative", "Expected", "Optimistic") with pre-set parameter values that users can customize. Include clear labeling to distinguish between scenario name, parameter categories, and individual parameters.

**Acceptance Criteria**:
- Forms capture Cash Flow and P&L forecast parameters needed by Epic 4
- Supports creating and editing multiple named scenarios
- Clear labeling and help text for all forecast assumptions
- Scenario templates available for quick setup

**Estimated Complexity**: Standard

**Notes**: Scenario management UI is the most complex part - consider a list view of scenarios with add/edit/delete buttons and a detail form for the selected scenario. Templates should be suggestive but fully editable.

---

## Epic-Level Notes

*Track UI/UX decisions, parameter naming conventions, default calculation logic, or user feedback about parameter organization and clarity.*
