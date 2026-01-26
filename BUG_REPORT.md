# QB-Assistant Bug Report
**Date**: 2026-01-25
**Tested Against**: Real QuickBooks data files in `data/` folder

## Executive Summary

Comprehensive testing reveals **1 CRITICAL bug** and **0 parser bugs**. All parsers work correctly with real data. The critical issue is in pipeline integration where budget variance calculation is incomplete.

---

## ✅ PARSERS: ALL PASSING

### Balance Sheet Parser
- **Status**: ✅ PASS
- **File**: `data/balance sheet.csv`
- **Result**: Correctly parsed 38 rows with proper hierarchy
- **Edge Cases Handled**:
  - 2-column format
  - Nested hierarchy (Assets → Current Assets → Bank Accounts → Checking)
  - Footer timestamp rows
  - Currency formatting ($1,201.00)

### Profit & Loss Parser
- **Status**: ✅ PASS
- **File**: `data/profit_loss.csv`
- **Result**: Correctly parsed 49 rows with 3-column format
- **Edge Cases Handled**:
  - Multi-column format with prior year (PY) column
  - Empty prior year data
  - Negative values (discounts, losses)
  - Nested parent accounts (Landscaping Services → Job Materials)
  - Calculated rows (Gross Profit, Net Income)

### Cash Flow Parser
- **Status**: ✅ PASS
- **File**: `data/cash_flows.csv`
- **Result**: Correctly parsed 19 rows
- **Edge Cases Handled**:
  - Different column name ("Full name" vs "Distribution account")
  - Empty sections (INVESTING ACTIVITIES has no children)
  - Section-level summaries
  - Mixed positive/negative cash flows

### Historical P&L Parser
- **Status**: ✅ PASS
- **File**: `data/historic_profit_loss.csv`
- **Result**: Correctly parsed 49 rows with 12 months of data
- **Edge Cases Handled**:
  - **Variable columns**: 13+ columns (account name + 12 months)
  - All 12 months preserved in values dict: `{'Nov 2024': 367.38, 'Dec 2024': 351.22, ...}`
  - Period header parsing
  - Monthly time series data

**Key Finding**: The historic data parser correctly handles variable columns by storing monthly data as a dictionary of `{period: value}` pairs, not as separate DataFrame columns.

---

## ❌ CRITICAL BUG: Budget Variance Pipeline Integration

### Location
`src/services/pipeline_orchestrator.py`, Stage 4-7 (lines 197-292)

### Description
The pipeline calls `BudgetDefaultsService.calculate_defaults()` which returns a **dict** of parameters, but then tries to pass this dict to `BudgetVarianceReportWriter.write()` which expects a **VarianceModel** object with a `.hierarchy` attribute.

### Root Cause
**Incomplete pipeline integration**. The AI created individual components (BudgetCalculator, BudgetVarianceCalculator, VarianceModel) but never integrated them into the pipeline properly.

### Current (Broken) Code
```python
# Stage 4 (line 201)
variance_model = BudgetDefaultsService.calculate_defaults(
    pl_model=pl_model,
    bs_model=None
)
# Returns: {'revenue_growth_rate': 0.05, 'expense_adjustment': 1.0, ...}

# Stage 7 (line 291)
budget_writer.write(variance_model)  # ❌ Crashes - dict has no .hierarchy
```

### Expected Flow
```python
# Stage 4a: Get defaults
defaults_dict = BudgetDefaultsService.calculate_defaults(pl_model=historical_pl)

# Stage 4b: Create parameter model
from src.models.parameters import ParameterModel
param_model = ParameterModel(defaults_dict)

# Stage 4c: Generate budget projections
from src.services.budget_calculator import BudgetCalculator
budget_calc = BudgetCalculator(historical_pl, param_model)
budget_model = budget_calc.calculate()  # Returns BudgetModel

# Stage 4d: Calculate variance
from src.services.budget_variance_calculator import BudgetVarianceCalculator
variance_calc = BudgetVarianceCalculator(budget_model, current_pl)
variance_model = variance_calc.calculate(threshold_pct=10.0, threshold_abs=1000.0)

# Stage 7: Write variance
budget_writer.write(variance_model)  # ✅ Works - VarianceModel has .hierarchy
```

### Error Message
```
Report generation failed: AttributeError: 'dict' object has no attribute 'hierarchy'
```

### Impact
- **Severity**: CRITICAL
- **Affected**: Budget vs Actual report sheet cannot be generated
- **Status**: All reports fail at Stage 7

### Files Involved
1. `src/services/pipeline_orchestrator.py` - Missing integration steps
2. `src/services/budget_defaults.py` - Works as designed, returns dict
3. `src/services/budget_calculator.py` - Exists but never called
4. `src/services/budget_variance_calculator.py` - Exists but never called
5. `src/exporters/budget_variance_writer.py` - Expects VarianceModel, receives dict

---

## Why This Bug Occurred

**Synthetic Data Testing**: The AI used its own generated test data instead of the real QuickBooks files in `data/`. This meant:

1. ✅ Individual components were tested in isolation with mock data
2. ❌ End-to-end pipeline was never tested with real data flow
3. ❌ Type mismatches between stages went undetected
4. ❌ Integration gaps were not discovered

The AI likely:
- Created `BudgetCalculator` and `BudgetVarianceCalculator` services
- Created models (`BudgetModel`, `VarianceModel`)
- Created the report writer expecting `VarianceModel`
- But when integrating into the pipeline, took a shortcut and called only `BudgetDefaultsService`
- Never ran end-to-end test to catch the type mismatch

---

## Recommended Fix

### Option 1: Complete the Integration (Recommended)

Modify `pipeline_orchestrator.py` Stage 4 to include full budget variance calculation:

```python
# === STAGE 4: Calculate Budget and Variance ===
self._notify_progress(progress_callback, "Calculating budget variance...")
print("\n=== Stage 4: Calculating budget and variance ===")
variance_model = None
try:
    # Step 1: Get intelligent defaults from historical data
    defaults_dict = BudgetDefaultsService.calculate_defaults(
        pl_model=historical_pl_model if historical_pl_model else None,
        bs_model=None
    )
    print(f"Budget defaults calculated: {defaults_dict}")

    # Step 2: Create parameter model
    from src.models.parameters import ParameterModel
    param_model = ParameterModel(defaults_dict)

    # Step 3: Generate budget projections from historical data
    if historical_pl_model:
        from src.services.budget_calculator import BudgetCalculator
        budget_calc = BudgetCalculator(historical_pl_model, param_model)
        budget_model = budget_calc.calculate()
        print("Budget model generated from historical data")

        # Step 4: Calculate variance (budget vs current actual)
        from src.services.budget_variance_calculator import BudgetVarianceCalculator
        variance_calc = BudgetVarianceCalculator(budget_model, pl_model)
        variance_model = variance_calc.calculate(
            threshold_pct=10.0,  # Flag variances > 10%
            threshold_abs=1000.0  # Flag variances > $1000
        )
        print("Variance model calculated successfully")
    else:
        print("Warning: No historical data - skipping variance calculation")
        variance_model = None

except Exception as e:
    error_msg = f"Budget variance calculation failed: {type(e).__name__}: {str(e)}"
    print(error_msg)
    errors.append(error_msg)
    result['status'] = 'partial'
    variance_model = None
```

### Option 2: Skip Budget Variance (Temporary Workaround)

If Option 1 is complex, temporarily disable the budget variance sheet:

```python
# Stage 7 - Comment out budget variance writer
# if variance_model:
#     budget_writer = BudgetVarianceReportWriter()
#     budget_writer.workbook = base_writer.workbook
#     budget_writer.write(variance_model)
#     print("Budget vs Actual sheet written")
```

This allows reports to generate without the Budget vs Actual sheet.

---

## Testing Recommendations

1. **Create Integration Tests**: Add `test_full_pipeline.py` to test suite (already created in testing)
2. **Use Real Data**: Always test with files in `data/` folder, not synthetic data
3. **Type Checking**: Consider adding type hints validation or runtime checks
4. **Pipeline Validation**: Add assertions between stages to verify data types

---

## Additional Observations

### Strengths
- **Two-pass parser pattern**: Well-designed and handles QuickBooks quirks elegantly
- **Service layer pattern**: Clean separation of concerns
- **Error handling**: Graceful degradation when data missing
- **Multi-period support**: Period-aware values dict handles variable columns correctly

### Potential Future Issues
Based on synthetic data testing patterns, watch for:
1. **Report writers**: May have similar type mismatch issues in forecast writers
2. **Forecast orchestrator**: Integration with scenarios may have gaps
3. **Config loading**: May assume ideal structure, not handle backward compatibility
4. **GUI forms**: May not validate user input edge cases

---

## Conclusion

**Parser Layer**: ✅ SOLID - All edge cases handled correctly
**Pipeline Integration**: ❌ BROKEN - Critical type mismatch in budget variance flow
**Root Cause**: Synthetic data testing missed end-to-end integration issues

**Priority**: Fix pipeline integration before client demo.
