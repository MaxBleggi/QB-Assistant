# Epic 8: Documentation & Maintenance

**Status**: In Progress
**Priority**: High
**Dependencies**: Epic 7 (complete project implementation)

---

## Purpose

This epic creates comprehensive documentation for QB-Assistant to support two distinct audiences:
1. **End users** (bookkeeper/accountant) and developers (installation/setup)
2. **Future FORGE instances** (maintenance, bug fixes, feature expansion)

The documentation enables smooth handoff to the client and ensures long-term maintainability through clear architectural documentation that FORGE can consume for future modifications.

## Success Criteria

- [x] README.md exists with installation guide and basic project info (concise, developer-facing)
- [x] usage_guide.md provides comprehensive guide for bookkeeper (non-technical, accountant audience)
- [x] Technical architecture documentation exists for FORGE consumption (architecture.md, patterns.md, maintenance_guide.md)
- [x] Documentation enables future FORGE instances to make bug fixes without reading entire codebase
- [x] Documentation enables future FORGE instances to add features efficiently

---

## Sprint Breakdown

### Sprint 8.1: User Documentation

**Status**: [x] Done

**Description**:
Create user-facing documentation for QB-Assistant: README.md for installation and quick start (developer audience), and comprehensive usage_guide.md for the bookkeeper/accountant end user. The README should be concise and follow standard README conventions (installation, features, usage, support). The usage guide should be written for a non-technical accountant audience with step-by-step workflows, screenshots/descriptions of UI flows, and troubleshooting for common issues.

**Acceptance Criteria**:
- README.md exists in project root with sections: Overview, Features, Installation, Quick Start, Requirements, Support/Contact
- README.md is concise (not overwhelming) and follows standard README best practices
- usage_guide.md exists in project root with comprehensive bookkeeper workflows
- usage_guide.md written for non-technical accountant audience (no programming jargon)
- usage_guide.md covers complete workflows: launching app, creating clients, selecting files, configuring parameters, processing data, interpreting reports
- usage_guide.md includes troubleshooting section for common errors

**Estimated Complexity**: Standard

**Notes**:
- README.md audience: Developers who need to install/run the application
- usage_guide.md audience: Bookkeeper/accountant end user (non-technical)
- Consider adding screenshots or detailed UI descriptions to usage guide for clarity
- Focus on workflows, not technical implementation details
- usage_guide.md should explain business value of each feature (why use forecast scenarios, what budget defaults mean, etc.)

---

### Sprint 8.2: Technical Documentation for FORGE

**Status**: [ ] Not Started

**Description**:
Create comprehensive technical documentation that enables future FORGE instances to understand the codebase architecture, patterns, and conventions without reading all source code. This documentation serves as high-level context for FORGE's architect and explorer agents when making modifications. Create three documents: architecture.md (system components, data flow, epic integration), patterns.md (code patterns, conventions, design decisions), and maintenance_guide.md (how to add features, fix bugs, extend functionality - FORGE-consumable format).

**Acceptance Criteria**:
- docs/architecture.md exists with system architecture overview, component diagram/description, data flow between epics, and epic integration points
- docs/patterns.md exists documenting code patterns discovered across Epics 1-7 (service layer pattern, parser pattern, GUI form pattern, etc.)
- docs/maintenance_guide.md exists with guidance for common modifications (adding new metric, adding new report sheet, adding new parser, etc.)
- Documentation enables FORGE architect to propose changes without full codebase exploration
- Documentation enables FORGE explorer to validate architecture quickly by referencing known patterns
- Each document includes file references (path:line) for key components

**Estimated Complexity**: Standard

**Notes**:
- This documentation is consumed by FORGE instances (architect, explorer agents)
- Focus on architectural patterns and component relationships, not implementation details
- Include Epic integration points (how Epics 1-6 connect in Epic 7 pipeline)
- Document key design decisions and their rationale (why ScenarioForecastOrchestrator pattern, why callback-based progress, etc.)
- Reference handoff files from Epic 7 sprints for architectural decisions
- maintenance_guide.md should have FORGE-friendly format (clear patterns, file locations, modification templates)

---

## Epic-Level Notes

**Audience Separation**:
- Sprint 8.1: Human end users (bookkeeper) + human developers (installation)
- Sprint 8.2: AI agents (future FORGE instances)

**Documentation Philosophy**:
- User docs: Workflow-focused, business value oriented, non-technical language
- Technical docs: Architecture-focused, pattern-oriented, FORGE-consumable format

**Key Design Decisions to Document** (Sprint 8.2):
- Service layer pattern (Epic 2-4 services follow consistent initialization/calculation pattern)
- Parser pattern (Epic 1 - FileLoader + Parser pattern with model returns)
- GUI form pattern (Epic 5 - show_form navigation, ConfigManager integration)
- Report writer composition (Epic 6 - BaseExcelWriter shared workbook pattern)
- Pipeline orchestration (Epic 7 - PipelineOrchestrator with progress callbacks)
- Error handling hierarchy (FileLoaderError, CalculationError custom exceptions with built-in messages)
- Client configuration structure (per-client YAML with budget params, forecast scenarios)

**Future Maintainability**:
- FORGE should be able to reference architecture.md when proposing new features
- FORGE should be able to reference patterns.md when implementing changes
- FORGE should be able to reference maintenance_guide.md for common modification templates

*Track decisions about documentation structure, content organization, or key architectural insights discovered during documentation creation.*
