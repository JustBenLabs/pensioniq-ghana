# Architecture

## Layers

1. **Actuarial Engine (`ssnit_engine/engine.py`)**
   - Holds benefit rules, formulas, eligibility logic, present-value calculations,
     and statutory parameter logic.
   - Contains no web UI code.

2. **API Layer (`ssnit_engine/api.py`)**
   - Converts HTTP requests into validated inputs.
   - Calls the actuarial engine.
   - Returns API-friendly results.

3. **Tests (`tests/`)**
   - Boundary and regression tests for pension rights and benefit routing.

4. **Future Database Layer**
   - Member profiles
   - Monthly contribution records
   - Salary / insurable earnings history
   - Annual statutory parameters
   - Calculation audit logs

## Recommended production rule

Store statutory parameters by effective year/date. Never hard-code future SSNIT
thresholds or rates inside the UI.

## Auditability

Each production calculation should eventually record:
- calculation timestamp
- law regime
- statutory parameter version
- input source (user-entered vs official)
- warnings
- formula route used
- result
