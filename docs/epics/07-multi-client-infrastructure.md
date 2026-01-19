# Epic 7: Multi-client Infrastructure

**Status**: NOT STARTED
**Priority**: Low
**Dependencies**: Epic 5 (configuration system), Epic 6 (report output system)

---

## Purpose

This epic implements the multi-client infrastructure that allows the bookkeeper to manage separate folders and configurations for each client. It ties together all previous epics into a cohesive end-to-end workflow: select client, load their configuration, select input files, process data through all calculation engines, and generate the final report.

This is the final integration epic that makes QB-Assistant a complete, production-ready tool for managing multiple bookkeeping clients.

## Success Criteria

- [ ] Automatic client discovery from folder structure
- [ ] Per-client configuration storage and retrieval
- [ ] Client selection interface in GUI
- [ ] Complete end-to-end workflow from input selection to report generation
- [ ] Progress indicators show current processing step
- [ ] Comprehensive error handling with actionable error messages
- [ ] Main application entry point (script or command) to launch QB-Assistant

---

## Sprint Breakdown

### Sprint 7.1: Client Folder Management System

**Status**: [ ] Not Started

**Description**:
Implement the client folder structure convention (e.g., `clients/[client-name]/` containing input files and configuration) with automatic client discovery by scanning the clients directory. Create per-client configuration storage that saves budget parameters, forecast assumptions, and scenarios to a client-specific config file (e.g., `clients/[client-name]/config.yaml`). Build client selection interface in the GUI (dropdown or list) that displays discovered clients and allows the user to select which client to process. When a client is selected, automatically load their configuration and populate the parameter forms. Support creating new clients by creating a new folder and initializing default configuration.

**Acceptance Criteria**:
- Discovers clients from folder structure automatically (scans `clients/` directory)
- Loads and saves per-client configuration files (preserves parameters across runs)
- GUI provides client selection interface (dropdown or list view)
- Supports creating new clients with default configuration
- Selected client's configuration populates parameter forms automatically

**Estimated Complexity**: Standard

**Notes**: Folder structure should be documented for users. Consider adding a "New Client" wizard that prompts for client name and sets up the folder structure. Configuration files should be versioned (include a schema version) for future compatibility.

---

### Sprint 7.2: End-to-End Workflow Integration

**Status**: [ ] Not Started

**Description**:
Integrate all components (Epic 1-6) into a complete workflow orchestrated from the GUI. Workflow steps: user selects client → loads configuration → selects input files (Balance Sheet, P&L, Cash Flow, Historical Data) via file picker dialogs → validates all files are present → processes data through all engines (parsing → metrics → budget → forecasting → report generation) → saves output report to client folder. Add progress indicators showing current processing step (e.g., progress bar or status text: "Parsing P&L...", "Calculating metrics...", "Generating report..."). Implement comprehensive error handling with user-friendly error messages that explain what went wrong and suggest corrective actions. Create main application entry point (Python script) that launches the GUI. Handle edge cases like missing input files, malformed data, and processing errors gracefully.

**Acceptance Criteria**:
- Complete workflow runs from GUI start to report output in client folder
- Progress indicators show current processing step with status updates
- Errors display clearly with actionable messages (not just stack traces)
- Main entry point script launches the application
- Generated report saves to client folder with timestamped filename

**Estimated Complexity**: Standard

**Notes**: Consider adding a "workflow log" that records processing steps and any warnings for debugging. Timestamped output filenames prevent overwriting (e.g., `ClientName_Report_2026-01-19.xlsx`). Entry point could be `qb_assistant.py` or similar.

---

## Epic-Level Notes

*Track decisions about folder structure conventions, workflow orchestration details, error handling strategies, or user experience improvements discovered during integration.*
