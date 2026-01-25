# QB-Assistant Usage Guide

A comprehensive guide for bookkeepers and accountants using QB-Assistant to generate financial forecasts and analysis reports for small business clients.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Client Management](#client-management)
4. [Selecting Input Files](#selecting-input-files)
5. [Configuring Parameters](#configuring-parameters)
6. [Processing Data](#processing-data)
7. [Understanding Your Reports](#understanding-your-reports)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is QB-Assistant?

QB-Assistant is a financial analysis tool designed specifically for bookkeepers who manage multiple small business clients. It automates the time-consuming process of creating financial forecasts and budget analyses from QuickBooks data.

### What Does It Do?

QB-Assistant takes your QuickBooks export files and automatically:
- Calculates key performance indicators (KPIs) like revenue growth and profit margins
- Generates 6-month or 12-month cash flow forecasts
- Creates profit and loss (P&L) forecasts
- Compares actual performance to budgets
- Identifies unusual patterns in historical data
- Produces professional Excel reports with visualizations

### Business Value

Instead of spending hours manually building forecast models in Excel, you can:
- Process multiple clients quickly with consistent methodology
- Generate professional reports for client meetings
- Model different scenarios (optimistic, realistic, pessimistic) to support planning discussions
- Identify cash flow issues before they become problems
- Provide data-driven recommendations to business owners

---

## Getting Started

### Launching the Application

1. Open a command prompt or terminal window
2. Navigate to the QB-Assistant folder
3. Run the command: `python qb_assistant.py`

The application window will open showing the Client Selection screen.

### First-Time Setup

When you launch QB-Assistant for the first time, it automatically creates two folders in your QB-Assistant directory:
- **clients/** - This is where all your client data and reports are stored
- **config/** - This stores configuration settings

You don't need to create these folders manually.

---

## Client Management

### Creating Your First Client

Before you can process any data, you need to create a client workspace.

1. On the **Client Selection** screen, click the **"Create Client"** button
2. Enter the client name when prompted (example: "Acme-Plumbing")
   - Use only letters, numbers, hyphens, and underscores
   - No spaces or special characters
   - The system will create a folder with this name
3. Click **OK**

You'll see a confirmation message that the client was created successfully.

### Selecting an Existing Client

To work with a client you've already created:

1. On the **Client Selection** screen, find your client in the list
2. Click on the client name to highlight it
3. Click the **"Select Client"** button

The application will take you to the Main Menu for that client.

### Switching Between Clients

If you need to switch to a different client while working:

1. From the Main Menu, click the **"Change Client"** button in the client information section at the top
2. You'll return to the Client Selection screen
3. Select the new client and click **"Select Client"**

All your configuration settings are saved separately for each client, so switching clients won't affect your work.

### Deleting a Client

If you need to remove a client from the system:

1. On the **Client Selection** screen, click on the client name to highlight it
2. Click the **"Delete Client"** button
3. Confirm the deletion when prompted

**Warning**: This permanently deletes the client folder and all reports. Make sure you've backed up any reports you need before deleting.

---

## Selecting Input Files

### Required Files from QuickBooks

QB-Assistant needs 4 files exported from QuickBooks:

1. **Balance Sheet** (Excel `.xlsx` format)
   - Shows assets, liabilities, and equity
   - Export from QuickBooks: Reports → Company & Financial → Balance Sheet Summary

2. **Profit & Loss Statement** (Excel `.xlsx` format)
   - Shows revenue and expenses
   - Export from QuickBooks: Reports → Company & Financial → Profit & Loss Standard

3. **Cash Flow Statement** (Excel `.xlsx` format)
   - Shows operating, investing, and financing cash flows
   - Export from QuickBooks: Reports → Company & Financial → Statement of Cash Flows

4. **Historical Data** (CSV `.csv` format)
   - Time-series data for trend analysis and anomaly detection
   - Export from QuickBooks: Reports → Custom Reports → Export to CSV

### Selecting Files in QB-Assistant

1. From the Main Menu, click **"Select Input Files"**
2. The File Selection screen shows 4 file selection rows
3. Click the **"Browse..."** button next to each file type:
   - A file browser window will open
   - Navigate to where you saved your QuickBooks exports
   - Select the appropriate file
   - Click **Open**
4. The filename will appear next to the Browse button
5. Repeat for all 4 file types

Once all 4 files are selected, the **"Proceed"** button becomes active (changes from gray to blue).

### Verifying Your Selections

Before proceeding, double-check that:
- Each filename shows the correct client's data
- The file dates match the period you want to analyze
- All 4 files are from the same accounting period

If you need to change a selection, click **"Browse..."** again for that file type.

### Clearing Selections

If you need to start over:
1. Click the **"Clear Selections"** button
2. All file selections will be reset
3. You can now select new files

---

## Configuring Parameters

After selecting your client and input files, you need to configure parameters that control how forecasts are generated.

### Forecast Horizon Setting

Before configuring detailed parameters, choose your forecast time period:

1. On the Main Menu, look for the **"Forecast Settings"** section
2. You'll see two options:
   - **6 months**: Best for near-term liquidity planning and short-term cash flow management
   - **12 months**: Best for strategic planning and expansion decisions
3. Click the radio button for your preferred horizon
4. The setting is saved automatically

The forecast horizon affects how far into the future your cash flow and P&L forecasts extend.

### Sample Parameters

Sample parameters control how historical data is used for forecasting trends.

1. From the Main Menu, click **"Sample Parameters"**
2. The Sample Parameters screen shows editable fields:
   - **Lookback Window**: How many months of historical data to analyze (default: 12 months)
   - **Sample Size**: Minimum number of data points required for valid trends (default: 6 points)
3. Modify values if needed (most users can keep the defaults)
4. Click **"Save"** to store your settings
5. Click **"Back to Main Menu"** to return

**When to adjust**: Only change these if you have limited historical data (less than 12 months) or want to emphasize more recent trends.

### Budget Parameters

Budget parameters define expected performance targets for variance reporting.

1. From the Main Menu, click **"Budget Parameters"**
2. Enter budget values for key metrics:
   - **Target Revenue**: Expected monthly revenue
   - **Target Gross Margin**: Expected gross profit percentage (e.g., 45 for 45%)
   - **Operating Expense Budget**: Expected monthly operating expenses
   - **Capital Expenditure Budget**: Planned equipment or asset purchases
3. If you have a formal budget from the client, enter those values
4. If not, the system will use historical averages as defaults
5. Click **"Save"** to store your budget parameters
6. Click **"Back to Main Menu"** to return

**Tip**: You can leave fields blank, and the system will calculate reasonable defaults based on historical patterns.

### Forecast Scenarios

Forecast scenarios let you model different possible futures (optimistic, realistic, pessimistic).

1. From the Main Menu, click **"Forecast Scenarios"**
2. The Scenario List screen shows any existing scenarios
3. To create a new scenario, click **"Create Scenario"**
4. Fill in the scenario details:
   - **Scenario Name**: Descriptive name (e.g., "Optimistic Growth")
   - **Revenue Growth Rate**: Expected revenue change percentage (e.g., 10 for 10% growth)
   - **Expense Growth Rate**: Expected expense change percentage (e.g., 5 for 5% increase)
   - **Description**: Notes about assumptions (optional)
5. Click **"Save"**
6. Repeat to create multiple scenarios

**Recommended**: Create 3 scenarios:
- **Optimistic**: Higher revenue growth, controlled expenses
- **Realistic**: Moderate growth based on trends
- **Pessimistic**: Lower revenue growth, higher expenses

All scenarios you create will be included in the final report for comparison.

### Historical Data Anomaly Review

This tool helps you identify and explain unusual spikes or dips in historical data.

1. From the Main Menu, click **"Historical Data Anomaly Review"**
2. The system displays a chart showing historical trends with flagged anomalies
3. For each flagged point:
   - Review the date and value
   - Click the anomaly point to add a note
   - Enter an explanation (e.g., "One-time equipment purchase" or "Seasonal holiday spike")
4. Annotated anomalies are excluded from trend calculations, improving forecast accuracy
5. Click **"Save Annotations"** when done
6. Click **"Back to Main Menu"** to return

**Why this matters**: Anomalies like one-time expenses or unusual sales spikes can distort forecasts. Annotating them ensures more accurate projections.

---

## Processing Data

Once you've selected files and configured parameters, you're ready to generate the report.

### Running the Processing Pipeline

1. From the Main Menu, verify the "Current Client" shows the correct client name
2. Verify your forecast horizon setting (6 or 12 months)
3. Click **"Process Data"**

### What Happens During Processing

The system executes 8 stages (this takes 10-30 seconds depending on data size):

1. **Loading Files**: Reads your 4 QuickBooks export files
2. **Parsing Balance Sheet**: Extracts assets, liabilities, and equity data
3. **Parsing Profit & Loss**: Extracts revenue and expense data
4. **Parsing Cash Flow**: Extracts cash flow activity data
5. **Calculating KPIs**: Computes metrics like revenue growth and margins
6. **Applying Budget Defaults**: Fills in any missing budget parameters
7. **Running Forecasts**: Generates projections for all scenarios
8. **Generating Report**: Creates the Excel workbook with all sheets

You'll see progress messages at the bottom of the screen showing which stage is running.

### Success Confirmation

When processing completes successfully, you'll see:
- A green status message: **"Processing complete!"**
- A popup dialog showing where the report was saved

Example: `Report saved to: clients/Acme-Plumbing/Acme-Plumbing_Report_2026-01-25.xlsx`

Click **OK** to close the dialog.

### Partial Success

If some stages encounter issues but a report is still generated, you'll see:
- A warning dialog: **"Processing Completed with Warnings"**
- A description of which stages had issues
- The report path

The report is still usable, but some sections may be incomplete. Check the warning details to understand what's missing.

### Processing Failure

If processing fails completely (no report generated), you'll see:
- An error dialog: **"Processing Failed"**
- A description of what went wrong
- Suggestions for how to fix the issue

See the [Troubleshooting](#troubleshooting) section for common issues and solutions.

---

## Understanding Your Reports

### Where to Find Your Reports

Reports are saved in: `clients/[ClientName]/[ClientName]_Report_[Date].xlsx`

Example: If you processed data for client "Acme-Plumbing" on January 25, 2026, the report is at:
```
clients/Acme-Plumbing/Acme-Plumbing_Report_2026-01-25.xlsx
```

Each time you process data, a new report is created with the current date, so you can track changes over time.

### Report Structure

Every report contains 7 sheets (tabs in Excel):

#### 1. Executive Summary
High-level overview of current financial performance:
- **Current Period Revenue**: Most recent month's revenue
- **Revenue Growth**: Month-over-month (MoM) and year-over-year (YoY) growth rates
- **Profitability**: Gross margin and net income percentages
- **Cash Flow**: Operating cash flow for the period

**Who uses this**: Business owners and managers who want a quick snapshot without digging into details.

#### 2. KPI Dashboard
Detailed key performance indicators with trend arrows:
- Revenue metrics (total, growth rates)
- Margin metrics (gross margin, operating margin, net margin)
- Cash flow metrics (operating, investing, financing activities)
- Efficiency ratios

**Who uses this**: You (the bookkeeper) to track performance over time and identify trends.

#### 3. Budget vs Actual Analysis
Compares actual performance to budget targets:
- Revenue actual vs. budget with variance
- Expense actual vs. budget with variance
- Variance explanations (over/under budget)

**Who uses this**: Business owners to understand if they're meeting financial targets.

**Tip**: Large variances (>10%) may warrant investigation. Prepare to explain unusual variances in client meetings.

#### 4. Cash Flow Forecast
Projects cash inflows and outflows for the next 6 or 12 months:
- Operating cash flow forecast by month
- Investing cash flow (equipment purchases, etc.)
- Financing cash flow (loans, owner draws)
- Net cash flow and cumulative cash position

**Who uses this**: Business owners planning for cash needs (can they afford a new hire? Do they need a line of credit?).

**Critical insight**: If cumulative cash position goes negative in any month, the business may need financing or expense cuts.

#### 5. P&L Forecast
Projects revenue and expenses for the next 6 or 12 months:
- Revenue forecast by month
- Expense forecast by category
- Projected net income by month

Shows all scenarios you created (optimistic, realistic, pessimistic) for comparison.

**Who uses this**: Business owners planning expansion, hiring, or pricing changes.

#### 6. Assumptions & Parameters
Documents all the settings you configured:
- Sample parameters (lookback window, sample size)
- Budget parameters (target revenue, margins, expenses)
- Forecast scenarios (growth rates, assumptions)
- Anomaly annotations

**Why this matters**: This sheet ensures transparency. Clients can see exactly what assumptions drove the forecasts.

#### 7. Metadata Documentation
Technical details about the report:
- Client name
- Report generation date and time
- Input file names and paths
- Forecast horizon (6 or 12 months)
- Software version

**Who uses this**: You (for recordkeeping) and auditors (if financial statements are reviewed).

---

## Troubleshooting

### Common Error: "File Not Found"

**What it means**: The application can't find one of the files you selected.

**How to fix**:
1. Make sure the file still exists at the location where you saved it
2. Don't move or rename QuickBooks export files after selecting them
3. Use the **"Select Input Files"** screen to choose the file again
4. Verify the file path is correct (no typos in folder names)

### Common Error: "Data Format Error"

**What it means**: One of your QuickBooks export files has data in an unexpected format.

**How to fix**:
1. Re-export the file from QuickBooks using the standard report template
2. Check that date formats are consistent (MM/DD/YYYY)
3. Verify that currency amounts don't contain letters or special characters
4. Make sure the file has all required columns
5. If the file looks corrupted, export fresh data from QuickBooks

**Tip**: QB-Assistant expects standard QuickBooks report formats. Custom report layouts may cause errors.

### Common Error: "Missing Required Data"

**What it means**: A required section is missing from one of your input files.

**What's required**:
- Balance Sheet must have: Assets, Liabilities, Equity sections
- P&L must have: Revenue, Expenses, Net Income
- Cash Flow must have: Operating, Investing, Financing activities

**How to fix**:
1. Use QuickBooks standard report templates (not custom layouts)
2. Export the full report (don't filter out sections)
3. Verify the QuickBooks date range includes actual transactions (empty periods cause issues)

### Common Error: "Calculation Error"

**What it means**: The system encountered invalid data during calculations (like division by zero).

**Common causes**:
- Zero revenue in a period (can't calculate margin percentages)
- Missing cost of goods sold (COGS) data
- Incomplete historical data (too few data points)

**How to fix**:
1. Check that the QuickBooks date range includes actual business activity
2. For new businesses with limited history, use shorter lookback windows in Sample Parameters
3. Verify all financial statement sections have data (not blank rows)

### Common Error: Processing Hangs or Takes Too Long

**What it means**: The system is struggling to process very large files or complex data.

**How to fix**:
1. Wait 2-3 minutes (large files can take time)
2. If still hung, close the application and restart
3. Try exporting QuickBooks data for a shorter date range (e.g., 12 months instead of 5 years)
4. Check the `qb_assistant.log` file for detailed error messages

### Application Won't Launch

**Symptoms**: Double-clicking `qb_assistant.py` does nothing, or you see a command window that immediately closes.

**How to fix**:
1. Verify Python is installed: Open command prompt and type `python --version`
   - You should see "Python 3.x.x"
   - If not, install Python 3.x from python.org
2. Verify dependencies are installed: Run `pip install -r requirements.txt`
3. Run from command prompt: `python qb_assistant.py` to see error messages
4. Check `qb_assistant.log` file for startup errors

### Can't See My Client in the List

**Symptoms**: You created a client, but it doesn't appear in the Client Selection list.

**How to fix**:
1. Click the **"Create Client"** screen again to refresh the list
2. Check the `clients/` folder to verify the client folder exists
3. If the folder exists but doesn't appear, the folder name may contain invalid characters
4. Manually rename the folder to remove spaces or special characters, then refresh

### Budget Parameters Not Saving

**Symptoms**: You enter budget values, click Save, but they don't appear next time you open Budget Parameters.

**How to fix**:
1. Verify you clicked **"Save"** before clicking **"Back to Main Menu"**
2. Check that you have write permissions to the `config/` folder
3. Look for a file named `config/[ClientName]_budget_params.json`
   - If it exists, your saves are working
   - If not, there may be a permissions issue with the config folder

### Reports Are Incomplete

**Symptoms**: The report generates, but some sheets are empty or missing data.

**Common causes**:
- Missing data in QuickBooks exports (empty sections)
- No historical data (can't generate trends)
- No scenarios created (P&L Forecast sheet may be limited)

**How to fix**:
1. Verify all 4 input files have actual data (not just headers)
2. Create at least one forecast scenario using **"Forecast Scenarios"**
3. For historical trend issues, provide at least 6 months of historical data
4. Check the warning message to see which stage failed

### Getting Help

If you encounter an error not covered here:

1. **Check the log file**: Open `qb_assistant.log` in a text editor
   - Look for ERROR or EXCEPTION messages near the end of the file
   - These contain technical details about what went wrong

2. **Take a screenshot**: Capture the error dialog and any status messages

3. **Note your steps**: Write down exactly what you did before the error occurred

4. **Contact support**: Provide the log file, screenshot, and step description

---

## Best Practices

### For Accurate Forecasts
- Use at least 12 months of historical data when possible
- Create multiple scenarios (optimistic, realistic, pessimistic) for comparison
- Annotate any known anomalies (one-time events, seasonal spikes)
- Update budget parameters quarterly based on actual performance

### For Efficient Workflow
- Create all your clients at once, then switch between them as needed
- Save QuickBooks exports in a consistent folder structure (e.g., `QB-Exports/[ClientName]/[Date]/`)
- Generate reports monthly for consistent tracking
- Keep old reports (they're automatically dated) to track how forecasts evolved

### For Client Presentations
- Review the Executive Summary first to understand the story
- Prepare explanations for large budget variances (>10%)
- Use scenario comparison to show "what if" planning options
- Point clients to the Cash Flow Forecast to plan for upcoming cash needs

---

**Need more help?** See the README.md file for technical support information, or check qb_assistant.log for detailed error messages.
