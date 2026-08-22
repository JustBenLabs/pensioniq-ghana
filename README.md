# SSNIT Actuarial Engine v1.0

A Python actuarial calculation engine for selected Ghana SSNIT Act 766 / Act 883
benefit pathways.

## Implemented modules

- Contribution and pension-right calculations
- Best-three-year salary logic
- Contribution-gap analysis
- Full and reduced old-age pension routing
- Old-age lump-sum routing
- Invalidity pension
- Survivor present-value calculations
- Emigration benefit
- Master benefit router

## Important

This project is an **educational and estimation tool**, not an official SSNIT
calculator. Official SSNIT records, regulations, administrative conventions,
and benefit determinations govern actual entitlement and payment.

## Run tests

```bash
pip install -r requirements.txt
pytest
```

## Run the API

```bash
uvicorn ssnit_engine.api:app --reload
```

Then open:

- `/health`
- `/docs`
- `/pension-right`
- `/benefits/retirement`

## Example Python usage

```python
from datetime import date
from decimal import Decimal
from ssnit_engine import BenefitEvent, calculate_master_benefit

result = calculate_master_benefit(
    event=BenefitEvent.RETIREMENT,
    date_of_birth=date(1966, 8, 20),
    event_date=date(2026, 8, 20),
    contribution_months=240,
    best_three_year_average_annual_salary=Decimal("72000"),
)

print(result.monthly_benefit)
# 2587.50
```
