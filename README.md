# QB-Assistant

A specialized financial analysis tool for bookkeepers managing multiple small business clients. Automates QuickBooks data processing to generate comprehensive forecasts, budgets, and KPI reports.

## Features

- **Multi-Client Management**: Organize and switch between multiple client workspaces
- **Automated Forecasting**: Generate 6-month or 12-month cash flow and P&L forecasts
- **Budget Analysis**: Compare actuals to budgets with variance reporting
- **KPI Dashboard**: Track key metrics including revenue growth, margins, and cash flow
- **Scenario Planning**: Model multiple forecast scenarios (optimistic, realistic, pessimistic)
- **Historical Anomaly Detection**: Identify and annotate unusual patterns in historical data
- **Excel Report Generation**: Comprehensive multi-sheet reports with visualizations

## Requirements

- Python 3.x (3.7 or higher recommended)
- Dependencies listed in `requirements.txt`

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

Launch the application:

```bash
python qb_assistant.py
```

The application will:
1. Create necessary directories (`clients/`, `config/`) on first run
2. Open the client selection screen
3. Prompt you to create a client or select an existing one
4. Navigate to the main menu for parameter configuration and data processing

## Project Structure

```
QB-Assistant/
├── qb_assistant.py          # Main application entry point
├── src/                     # Source code (parsers, calculators, GUI)
├── clients/                 # Client folders with reports (created on first run)
├── config/                  # Configuration files (created on first run)
├── qb_assistant.log         # Application log file
├── requirements.txt         # Python dependencies
└── usage_guide.md          # Comprehensive user guide for bookkeepers
```

## Input Files

QB-Assistant processes 4 QuickBooks export files:
- Balance Sheet (Excel `.xlsx`)
- Profit & Loss Statement (Excel `.xlsx`)
- Cash Flow Statement (Excel `.xlsx`)
- Historical Data (CSV `.csv`)

## Output

Reports are saved to: `clients/[ClientName]/[ClientName]_Report_[Date].xlsx`

Each report contains 7 sheets:
- Executive Summary
- KPI Dashboard
- Budget vs Actual Analysis
- Cash Flow Forecast
- P&L Forecast
- Assumptions & Parameters
- Metadata Documentation

## Support

For detailed usage instructions, see `usage_guide.md`.

For technical issues, check the `qb_assistant.log` file for error details.

## License

Proprietary - Internal use only
