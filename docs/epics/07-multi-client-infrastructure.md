# Epic 7: Multi-client Infrastructure

**Status**: IN PROGRESS
**Priority**: Low
**Dependencies**: Epic 5 (configuration system), Epic 6 (report output system)

---

## Purpose

This epic implements the multi-client infrastructure that allows the bookkeeper to manage separate folders and configurations for each client. It ties together all previous epics into a cohesive end-to-end workflow: select client, load their configuration, select input files, process data through all calculation engines, and generate the final report.

This is the final integration epic that makes QB-Assistant a complete, production-ready tool for managing multiple bookkeeping clients.

## Success Criteria

- [x] Automatic client discovery from folder structure
- [x] Per-client configuration storage and retrieval
- [x] Client selection interface in GUI
- [ ] Complete end-to-end workflow from input selection to report generation
- [ ] Progress indicators show current processing step
- [ ] Comprehensive error handling with actionable error messages
- [ ] Main application entry point (script or command) to launch QB-Assistant

---

## Sprint Breakdown

### Sprint 7.1: Client Folder Management System

**Status**: [x] Done

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

### Sprint 7.2: File Selection & Validation Workflow

**Status**: [x] Done

**Description**:
Implement file selection workflow for the 4 required QuickBooks input files (Balance Sheet, Profit & Loss, Cash Flow Statement, Historical Data CSV). Add file picker dialogs to the GUI that allow the user to browse and select each file type. Validate that all 4 required files are selected before allowing the user to proceed. Store the selected file paths in application state for use by the processing pipeline. Display the selected filenames in the GUI so the user can verify their selections. Implement "Clear Selections" functionality to reset the file pickers. Follow existing GUI patterns from ClientSelectionForm for consistency.

**Acceptance Criteria**:
- GUI provides file picker dialogs for all 4 required input types
- Selected file paths are validated (files exist and are readable)
- All 4 files must be selected before proceeding to processing
- Selected filenames are displayed clearly in the GUI
- File selections persist during the session but are cleared when a different client is selected

**Estimated Complexity**: Simple

**Notes**: File pickers should use tkinter.filedialog (askopenfilename) with appropriate file type filters (e.g., .xlsx for QB exports, .csv for historical data). Store file paths in App state similar to selected_client pattern from Sprint 7.1.

---

### Sprint 7.3: Core Pipeline Integration & Orchestration

**Status**: [x] Done

**Description**:
Integrate all service components from Epics 1-6 into a complete processing pipeline orchestrated from the GUI. Implement "Process Data" button that triggers the full workflow: load selected input files → parse financial data (Epic 1 ParserService) → calculate metrics (Epic 2 MetricsCalculatorService) → apply budget defaults (Epic 3 BudgetDefaultsService) → run forecasting scenarios (Epic 4 ForecastingEngine) → generate Excel report (Epic 6 ReportGeneratorService) → save report to client folder with timestamped filename (e.g., `clients/ClientName/ClientName_Report_2026-01-25.xlsx`). Load the selected client's configuration from Sprint 7.1 and pass parameters to each service. Implement basic error catching to prevent application crashes (log errors to console for debugging). This sprint focuses on getting the technical integration working end-to-end without UX polish.

**Acceptance Criteria**:
- "Process Data" button triggers complete pipeline from file selection to report generation
- All 6 epic services are integrated in correct sequence (parse → metrics → budget → forecast → report)
- Client configuration from Sprint 7.1 is loaded and applied to services
- Generated report saves to `clients/[client-name]/[ClientName]_Report_[timestamp].xlsx`
- Pipeline completes successfully for valid input data (basic error catching prevents crashes)

**Estimated Complexity**: Complex

**Notes**: This is the highest-risk sprint due to 6-epic integration. Focus on getting the technical orchestration correct. Progress indicators and user-friendly error messages will be added in Sprint 7.4. Use try/except blocks to catch errors and print to console for now. Test with known-good input files to validate the integration.

---

### Sprint 7.4: Progress Indicators & Error Handling

**Status**: [ ] Not Started

**Description**:
Enhance the processing pipeline from Sprint 7.3 with detailed progress indicators and user-friendly error handling. Add status label or progress text that updates during pipeline execution with detailed substeps (e.g., "Parsing Balance Sheet...", "Parsing P&L...", "Parsing Cash Flow...", "Calculating financial metrics...", "Applying budget defaults...", "Running forecast scenarios...", "Generating Excel report...", "Saving report..."). Implement comprehensive error handling that catches specific error types (file not found, parse errors, calculation errors) and displays user-friendly error dialogs with actionable messages explaining what went wrong and suggesting corrective actions (e.g., "Could not parse Balance Sheet: Invalid date format in cell B5. Please ensure dates are in MM/DD/YYYY format."). Errors should halt the workflow immediately with a dialog (fail-fast approach). Handle edge cases like missing input files, malformed data, and service processing errors gracefully.

**Acceptance Criteria**:
- Progress indicators show detailed substeps during pipeline execution (not just "Processing...")
- Error dialogs display user-friendly messages with specific issues and corrective actions
- Errors halt workflow immediately and display dialog (fail-fast)
- Edge cases handled: missing files, malformed Excel data, invalid CSV format, calculation errors
- Progress indicator updates for each major pipeline step (8+ distinct status messages)

**Estimated Complexity**: Standard

**Notes**: Use tkinter.Label for status text updates (update text property during processing). Use tkinter.messagebox.showerror for error dialogs. Consider using threading or after() calls if GUI freezes during processing. Map technical exceptions to user-friendly messages (e.g., KeyError during parsing → "Missing required column in Balance Sheet").

---

### Sprint 7.5: Main Application Entry Point

**Status**: [ ] Not Started

**Description**:
Create main application entry point script (`qb_assistant.py` or `main.py`) that serves as the launcher for the QB-Assistant application. The script should initialize the application, set up the project root path, create the main App instance, and launch the GUI. This is a simple launcher suitable for a non-technical bookkeeper user - no command-line arguments or complex configuration needed. The user will double-click this script (or run it via `python qb_assistant.py`) to start the application. Ensure proper application initialization sequence (create necessary directories like `clients/` and `config/` if they don't exist, initialize services, load any startup configuration). Add minimal logging setup for debugging if needed. Verify the complete end-to-end workflow works from fresh launch.

**Acceptance Criteria**:
- Main entry point script exists (`qb_assistant.py` or `main.py`) in project root
- Script launches GUI when executed (no command-line arguments required)
- Application initializes properly (creates necessary directories, initializes services)
- Complete workflow runs successfully from fresh application launch: launch → select client → select files → process → report generated
- Entry point is simple and suitable for non-technical user (bookkeeper)

**Estimated Complexity**: Simple

**Notes**: Entry point should be in project root for easy access. Use `if __name__ == "__main__":` pattern. Consider adding simple try/except around main() to catch catastrophic errors at startup. Test by running the script fresh in a new terminal/process to verify initialization works.

---

## Epic-Level Notes

**Sprint Decomposition Rationale** (2026-01-25):
Original Sprint 7.2 was overly ambitious (9+ integration touchpoints across 6 epics). Decomposed into 4 focused sprints to manage integration risk:
- Sprint 7.2: File selection foundation (low risk)
- Sprint 7.3: Technical pipeline integration (high risk, isolated from UX)
- Sprint 7.4: UX enhancement (progress + errors)
- Sprint 7.5: Entry point (final validation)

This separation allows architectural issues in pipeline integration (7.3) to be discovered and resolved before adding UX complexity.

*Track decisions about folder structure conventions, workflow orchestration details, error handling strategies, or user experience improvements discovered during integration.*
