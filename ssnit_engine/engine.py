
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

D = Decimal

def money(value: Decimal) -> Decimal:
    """Round Ghana cedi values to 2 decimal places."""
    return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)

def pct(value: str) -> Decimal:
    """Convert percentage text such as '5.5' into decimal 0.055."""
    return D(value) / D("100")


@dataclass(frozen=True)
class SSNITParameters:
    year: int
    minimum_insurable_earnings: Decimal
    maximum_insurable_earnings: Decimal

    employee_rate: Decimal
    employer_rate: Decimal
    first_tier_rate: Decimal
    second_tier_rate: Decimal
    nhia_rate: Decimal

    # Official published SSNIT First-Tier boundary amounts.
    minimum_first_tier_contribution: Decimal
    maximum_first_tier_contribution: Decimal


PARAMETERS_2026 = SSNITParameters(
    year=2026,
    minimum_insurable_earnings=D("587.80"),
    maximum_insurable_earnings=D("69000.00"),
    employee_rate=pct("5.5"),
    employer_rate=pct("13"),
    first_tier_rate=pct("13.5"),
    second_tier_rate=pct("5"),
    nhia_rate=pct("2.5"),
    minimum_first_tier_contribution=D("79.40"),
    maximum_first_tier_contribution=D("9315.00"),
)


def calculate_insurable_earnings(
    salary: Decimal,
    params: SSNITParameters = PARAMETERS_2026,
) -> Decimal:
    """
    Estimate insurable earnings by applying the year's minimum/maximum bounds.
    Official SSNIT insurable earnings, when available, should override this estimate.
    """
    if salary < 0:
        raise ValueError("Salary cannot be negative.")

    return min(
        params.maximum_insurable_earnings,
        max(salary, params.minimum_insurable_earnings),
    )


def calculate_contributions(
    salary: Decimal,
    params: SSNITParameters = PARAMETERS_2026,
) -> dict:
    """
    Calculate the statutory contribution breakdown for one month.
    """
    ie = calculate_insurable_earnings(salary, params)

    employee = money(ie * params.employee_rate)
    employer = money(ie * params.employer_rate)
    total = money(ie * (params.employee_rate + params.employer_rate))
    second_tier = money(ie * params.second_tier_rate)
    nhia = money(ie * params.nhia_rate)
    ssnit_retained = money(ie * (params.first_tier_rate - params.nhia_rate))

    # Respect SSNIT's officially published 2026 boundary amounts.
    if ie == params.minimum_insurable_earnings:
        first_tier = params.minimum_first_tier_contribution
    elif ie == params.maximum_insurable_earnings:
        first_tier = params.maximum_first_tier_contribution
    else:
        first_tier = money(ie * params.first_tier_rate)

    return {
        "salary_entered": money(salary),
        "insurable_earnings": money(ie),
        "employee_5_5_percent": employee,
        "employer_13_percent": employer,
        "total_18_5_percent": total,
        "first_tier_ssnit_13_5_percent": first_tier,
        "second_tier_5_percent": second_tier,
        "nhia_2_5_percent": nhia,
        "ssnit_retained_11_percent": ssnit_retained,
    }


def calculate_pension_right(contribution_months: int):
    """
    Act 766 / Act 883 old-age pension right.

    180 months -> 37.5%
    Each additional month -> 0.09375 percentage points
    420+ months -> capped at 60%
    """
    if contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    if contribution_months < 180:
        return None

    minimum_right = D("0.375")
    monthly_accrual = D("0.0009375")
    maximum_right = D("0.60")

    earned = minimum_right + monthly_accrual * D(contribution_months - 180)
    return min(earned, maximum_right)


def months_to_qualification(contribution_months: int) -> int:
    if contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")
    return max(0, 180 - contribution_months)


def months_to_maximum_right(contribution_months: int) -> int:
    if contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")
    return max(0, 420 - contribution_months)


def calculate_full_monthly_pension(
    best_three_year_average_annual_salary: Decimal,
    contribution_months: int,
) -> Decimal:
    """
    Full old-age pension estimate at age 60:
        monthly pension = (best-3-year annual average / 12) * pension right
    """
    if best_three_year_average_annual_salary < 0:
        raise ValueError("Salary average cannot be negative.")

    right = calculate_pension_right(contribution_months)

    if right is None:
        raise ValueError(
            "Member does not have the minimum 180 contribution months "
            "for an Act 766 monthly old-age pension."
        )

    monthly_salary_basis = best_three_year_average_annual_salary / D("12")
    return money(monthly_salary_basis * right)


# ============================================================
# v0.2 — Salary History / Best Three Years Engine
# ============================================================

from collections import defaultdict
from typing import Optional, Iterable


@dataclass(frozen=True)
class MonthlyEarningsRecord:
    year: int
    month: int
    basic_salary: Decimal
    contribution_valid: bool = True

    # If an official SSNIT-recognized insurable earnings figure is available,
    # store it here. It takes precedence over reconstructed earnings.
    official_insurable_earnings: Optional[Decimal] = None


@dataclass(frozen=True)
class SalaryHistoryResult:
    qualifying_years: tuple
    incomplete_years: tuple
    selected_best_three_years: tuple
    best_three_year_average_annual_salary: Decimal
    monthly_salary_basis: Decimal


def resolve_insurable_earnings(
    record: MonthlyEarningsRecord,
    parameter_registry: dict[int, SSNITParameters],
) -> Decimal:
    """
    Use official SSNIT-recognized insurable earnings whenever supplied.
    Otherwise reconstruct the amount using that year's statutory parameters.
    """
    if record.official_insurable_earnings is not None:
        if record.official_insurable_earnings < 0:
            raise ValueError("Official insurable earnings cannot be negative.")
        return record.official_insurable_earnings

    if record.year not in parameter_registry:
        raise ValueError(
            f"No statutory parameter set is available for {record.year}. "
            "Supply official_insurable_earnings or add that year's parameters."
        )

    return calculate_insurable_earnings(
        record.basic_salary,
        parameter_registry[record.year],
    )


def calculate_best_three_year_salary(
    records: Iterable[MonthlyEarningsRecord],
    parameter_registry: dict[int, SSNITParameters],
) -> SalaryHistoryResult:
    """
    v0.2 estimation rule:
      - use valid contribution months only;
      - require all 12 calendar months for a year to be treated as a complete year;
      - sum SSNIT-recognized/estimated insurable earnings for each complete year;
      - select the three highest complete annual totals;
      - flag incomplete years rather than annualising or imputing them.

    This deliberately avoids guessing the treatment of partial years.
    """
    by_year: dict[int, dict[int, Decimal]] = defaultdict(dict)

    for record in records:
        if not 1 <= record.month <= 12:
            raise ValueError(f"Invalid month: {record.month}")
        if record.basic_salary < 0:
            raise ValueError("Basic salary cannot be negative.")

        if not record.contribution_valid:
            # Keep the month absent from the qualifying salary set.
            continue

        if record.month in by_year[record.year]:
            raise ValueError(
                f"Duplicate qualifying salary record for "
                f"{record.year}-{record.month:02d}."
            )

        by_year[record.year][record.month] = resolve_insurable_earnings(
            record, parameter_registry
        )

    qualifying = {}
    incomplete = {}

    for year, monthly_values in sorted(by_year.items()):
        months_present = sorted(monthly_values)

        if months_present == list(range(1, 13)):
            qualifying[year] = sum(monthly_values.values(), D("0"))
        else:
            incomplete[year] = tuple(months_present)

    if len(qualifying) < 3:
        raise ValueError(
            "Insufficient complete qualifying salary history: "
            "at least three complete qualifying years are required "
            "by this v0.2 estimation engine."
        )

    ranked = sorted(
        qualifying.items(),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )

    best_three = ranked[:3]
    annual_average = sum((amount for _, amount in best_three), D("0")) / D("3")
    monthly_basis = annual_average / D("12")

    return SalaryHistoryResult(
        qualifying_years=tuple(
            (year, money(amount)) for year, amount in sorted(qualifying.items())
        ),
        incomplete_years=tuple(
            (year, months) for year, months in sorted(incomplete.items())
        ),
        selected_best_three_years=tuple(
            (year, money(amount)) for year, amount in best_three
        ),
        best_three_year_average_annual_salary=money(annual_average),
        monthly_salary_basis=money(monthly_basis),
    )


def calculate_full_pension_from_salary_history(
    records: Iterable[MonthlyEarningsRecord],
    contribution_months: int,
    parameter_registry: dict[int, SSNITParameters],
) -> dict:
    """
    Connect the salary-history engine directly to the pension-right engine.
    """
    salary_result = calculate_best_three_year_salary(records, parameter_registry)
    pension = calculate_full_monthly_pension(
        salary_result.best_three_year_average_annual_salary,
        contribution_months,
    )

    return {
        "salary_history": salary_result,
        "contribution_months": contribution_months,
        "pension_right": calculate_pension_right(contribution_months),
        "estimated_full_monthly_pension": pension,
    }


# ============================================================
# v0.3 — Contribution History / Gap Detection Engine
# ============================================================

from enum import Enum
from typing import Optional, Iterable


class ContributionStatus(str, Enum):
    MATCHED = "MATCHED"
    POSSIBLE_GAP = "POSSIBLE_GAP"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    CONTRIBUTION_ONLY = "CONTRIBUTION_ONLY"
    NO_DATA = "NO_DATA"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class ContributionHistoryRecord:
    year: int
    month: int

    # Employment/payslip side
    employed: bool
    basic_salary: Optional[Decimal] = None
    payslip_exists: bool = False

    # SSNIT side
    recorded_first_tier: Optional[Decimal] = None
    official_insurable_earnings: Optional[Decimal] = None

    employer_id: Optional[str] = None


@dataclass(frozen=True)
class ContributionMonthAssessment:
    year: int
    month: int
    employer_id: Optional[str]
    status: ContributionStatus

    expected_first_tier: Optional[Decimal]
    recorded_first_tier: Optional[Decimal]
    absolute_difference: Optional[Decimal]

    valid_contribution_month: bool


@dataclass(frozen=True)
class ContributionHistoryResult:
    assessments: tuple

    expected_employment_months: int
    valid_contribution_months: int
    possible_gap_months: int

    contribution_completeness_ratio: Optional[Decimal]
    months_to_qualification: int
    months_to_maximum_right: int

    pension_right: Optional[Decimal]


def _resolve_expected_first_tier(
    record: ContributionHistoryRecord,
    parameter_registry: dict[int, SSNITParameters],
) -> Optional[Decimal]:
    """
    Estimate expected First-Tier contribution where enough data exists.
    Prefer official insurable earnings when supplied.
    """
    if record.official_insurable_earnings is not None:
        if record.official_insurable_earnings < 0:
            raise ValueError("Official insurable earnings cannot be negative.")

        if record.year not in parameter_registry:
            # Rate is currently stable in our model, but we deliberately
            # require a year-specific statutory parameter set for auditability.
            raise ValueError(
                f"No statutory parameter set available for {record.year}."
            )

        params = parameter_registry[record.year]
        ie = record.official_insurable_earnings

        if ie == params.minimum_insurable_earnings:
            return params.minimum_first_tier_contribution

        if ie == params.maximum_insurable_earnings:
            return params.maximum_first_tier_contribution

        return money(ie * params.first_tier_rate)

    if record.basic_salary is None:
        return None

    if record.year not in parameter_registry:
        raise ValueError(
            f"No statutory parameter set available for {record.year}. "
            "Supply official_insurable_earnings or add that year's parameters."
        )

    params = parameter_registry[record.year]
    return calculate_contributions(record.basic_salary, params)[
        "first_tier_ssnit_13_5_percent"
    ]


def assess_contribution_month(
    record: ContributionHistoryRecord,
    parameter_registry: dict[int, SSNITParameters],
    tolerance: Decimal = D("0.01"),
) -> ContributionMonthAssessment:
    """
    Classify one month using employment/payslip evidence and SSNIT record.

    valid_contribution_month is True whenever a contribution record exists,
    even if the amount needs review. This avoids throwing away a recorded
    month merely because reconciliation is imperfect.
    """
    if not 1 <= record.month <= 12:
        raise ValueError(f"Invalid month: {record.month}")

    if record.basic_salary is not None and record.basic_salary < 0:
        raise ValueError("Basic salary cannot be negative.")

    if record.recorded_first_tier is not None and record.recorded_first_tier < 0:
        raise ValueError("Recorded First-Tier contribution cannot be negative.")

    expected = _resolve_expected_first_tier(record, parameter_registry)
    recorded = (
        money(record.recorded_first_tier)
        if record.recorded_first_tier is not None
        else None
    )

    evidence_of_employment = record.employed or record.payslip_exists
    contribution_exists = recorded is not None

    if evidence_of_employment and contribution_exists:
        if expected is None:
            status = ContributionStatus.INSUFFICIENT_DATA
            difference = None
        else:
            difference = money(abs(recorded - expected))
            if difference <= tolerance:
                status = ContributionStatus.MATCHED
            else:
                status = ContributionStatus.AMOUNT_MISMATCH

    elif evidence_of_employment and not contribution_exists:
        status = ContributionStatus.POSSIBLE_GAP
        difference = None

    elif not evidence_of_employment and contribution_exists:
        status = ContributionStatus.CONTRIBUTION_ONLY
        difference = None

    else:
        status = ContributionStatus.NO_DATA
        difference = None

    return ContributionMonthAssessment(
        year=record.year,
        month=record.month,
        employer_id=record.employer_id,
        status=status,
        expected_first_tier=expected,
        recorded_first_tier=recorded,
        absolute_difference=difference,
        valid_contribution_month=contribution_exists,
    )


def analyze_contribution_history(
    records: Iterable[ContributionHistoryRecord],
    parameter_registry: dict[int, SSNITParameters],
    tolerance: Decimal = D("0.01"),
) -> ContributionHistoryResult:
    """
    Analyse all monthly contribution records.

    expected_employment_months:
        months with employment/payslip evidence

    valid_contribution_months:
        months where a SSNIT contribution record exists

    possible_gap_months:
        employed/payslip months with no SSNIT contribution record

    contribution_completeness_ratio:
        our diagnostic metric, not an official SSNIT measure
    """
    assessments = []
    seen = set()

    for record in records:
        key = (record.year, record.month, record.employer_id)

        if key in seen:
            raise ValueError(
                f"Duplicate contribution record for {record.year}-"
                f"{record.month:02d}, employer={record.employer_id!r}."
            )
        seen.add(key)

        assessments.append(
            assess_contribution_month(record, parameter_registry, tolerance)
        )

    expected_months = sum(
        1
        for a, r in zip(
            assessments,
            records if isinstance(records, list) else []
        )
    )

    # Recompute directly from assessments + a materialized record list
    # to avoid depending on iterator reuse.
    # This block is overwritten below in the robust wrapper.
    raise RuntimeError("Use analyze_contribution_history_safe().")


def analyze_contribution_history_safe(
    records: Iterable[ContributionHistoryRecord],
    parameter_registry: dict[int, SSNITParameters],
    tolerance: Decimal = D("0.01"),
) -> ContributionHistoryResult:
    """
    Robust public wrapper that materializes the iterable once.
    """
    materialized = list(records)

    assessments = []
    seen = set()

    for record in materialized:
        key = (record.year, record.month, record.employer_id)

        if key in seen:
            raise ValueError(
                f"Duplicate contribution record for {record.year}-"
                f"{record.month:02d}, employer={record.employer_id!r}."
            )
        seen.add(key)

        assessments.append(
            assess_contribution_month(record, parameter_registry, tolerance)
        )

    expected_months = sum(
        1 for r in materialized if r.employed or r.payslip_exists
    )

    valid_month_keys = {
        (a.year, a.month)
        for a in assessments
        if a.valid_contribution_month
    }
    valid_months = len(valid_month_keys)

    gap_month_keys = {
        (a.year, a.month)
        for a in assessments
        if a.status == ContributionStatus.POSSIBLE_GAP
    }
    gap_months = len(gap_month_keys)

    if expected_months > 0:
        ccr = (
            D(valid_months) / D(expected_months) * D("100")
        ).quantize(D("0.01"), rounding=ROUND_HALF_UP)
    else:
        ccr = None

    return ContributionHistoryResult(
        assessments=tuple(assessments),
        expected_employment_months=expected_months,
        valid_contribution_months=valid_months,
        possible_gap_months=gap_months,
        contribution_completeness_ratio=ccr,
        months_to_qualification=months_to_qualification(valid_months),
        months_to_maximum_right=months_to_maximum_right(valid_months),
        pension_right=calculate_pension_right(valid_months),
    )


def estimate_gap_pension_impact(
    monthly_salary_basis: Decimal,
    valid_contribution_months: int,
    possible_gap_months: int,
) -> dict:
    """
    Illustrative pension impact of restoring possible missing contribution months.

    Applies only to the ordinary Act 766 accrual range.
    Caps pension right at 60%.

    This is a diagnostic estimate, not an official SSNIT determination.
    """
    if monthly_salary_basis < 0:
        raise ValueError("Monthly salary basis cannot be negative.")
    if valid_contribution_months < 0 or possible_gap_months < 0:
        raise ValueError("Month counts cannot be negative.")

    current_right = calculate_pension_right(valid_contribution_months)

    restored_months = valid_contribution_months + possible_gap_months
    restored_right = calculate_pension_right(restored_months)

    if current_right is None:
        current_pension = None
    else:
        current_pension = money(monthly_salary_basis * current_right)

    if restored_right is None:
        restored_pension = None
    else:
        restored_pension = money(monthly_salary_basis * restored_right)

    if current_pension is None or restored_pension is None:
        difference = None
    else:
        difference = money(restored_pension - current_pension)

    return {
        "current_contribution_months": valid_contribution_months,
        "possible_restored_months": restored_months,
        "current_pension_right": current_right,
        "restored_pension_right": restored_right,
        "current_monthly_pension_estimate": current_pension,
        "restored_monthly_pension_estimate": restored_pension,
        "illustrative_monthly_difference": difference,
    }


def calculate_full_pension_from_histories(
    salary_records: Iterable[MonthlyEarningsRecord],
    contribution_records: Iterable[ContributionHistoryRecord],
    parameter_registry: dict[int, SSNITParameters],
) -> dict:
    """
    Fully connect v0.2 salary history with v0.3 contribution history.
    No manual contribution-month count is required.
    """
    salary_result = calculate_best_three_year_salary(
        salary_records,
        parameter_registry,
    )

    contribution_result = analyze_contribution_history_safe(
        contribution_records,
        parameter_registry,
    )

    M = contribution_result.valid_contribution_months
    pension_right = calculate_pension_right(M)

    if pension_right is None:
        estimated_pension = None
    else:
        estimated_pension = money(
            salary_result.monthly_salary_basis * pension_right
        )

    gap_impact = estimate_gap_pension_impact(
        salary_result.monthly_salary_basis,
        M,
        contribution_result.possible_gap_months,
    )

    return {
        "salary_history": salary_result,
        "contribution_history": contribution_result,
        "estimated_full_monthly_pension": estimated_pension,
        "gap_impact": gap_impact,
    }


# Public name points to the robust implementation.
analyze_contribution_history = analyze_contribution_history_safe


# ============================================================
# v0.4 — Retirement Age & Benefit-Type Engine
# ============================================================

from datetime import date
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class OldAgeBenefitType(str, Enum):
    NOT_YET_ELIGIBLE = "NOT_YET_ELIGIBLE"
    REDUCED_PENSION = "REDUCED_PENSION"
    FULL_PENSION = "FULL_PENSION"
    HAZARDOUS_FULL_PENSION = "HAZARDOUS_FULL_PENSION"
    OLD_AGE_LUMP_SUM = "OLD_AGE_LUMP_SUM"
    OLD_AGE_LUMP_SUM_REVIEW = "OLD_AGE_LUMP_SUM_REVIEW"


@dataclass(frozen=True)
class RetirementAge:
    years: int
    months: int
    days: int

    @property
    def decimal_years_approx(self) -> Decimal:
        return (
            D(self.years)
            + D(self.months) / D("12")
            + D(self.days) / D("365.2425")
        )


@dataclass(frozen=True)
class RetirementEligibilityResult:
    benefit_type: OldAgeBenefitType
    eligible_for_monthly_pension: bool
    age: RetirementAge
    contribution_months: int
    reduction_factor: Optional[Decimal]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class RetirementBenefitResult:
    eligibility: RetirementEligibilityResult
    pension_right: Optional[Decimal]
    monthly_salary_basis: Optional[Decimal]
    estimated_monthly_pension: Optional[Decimal]
    calculation_status: str
    warnings: tuple[str, ...]


# Whole attained-age factors used in our v0.4 estimate.
# These are intentionally held in a separate data table so they can
# be replaced if SSNIT publishes a more granular age-month schedule.
REDUCED_PENSION_FACTORS = {
    55: D("0.600"),
    56: D("0.675"),
    57: D("0.750"),
    58: D("0.825"),
    59: D("0.900"),
}


def calculate_retirement_age(
    date_of_birth: date,
    retirement_date: date,
) -> RetirementAge:
    """
    Exact completed years/months/days between DOB and retirement date.
    """
    if retirement_date < date_of_birth:
        raise ValueError("Retirement date cannot be before date of birth.")

    years = retirement_date.year - date_of_birth.year
    months = retirement_date.month - date_of_birth.month
    days = retirement_date.day - date_of_birth.day

    if days < 0:
        # Borrow days from the previous calendar month.
        if retirement_date.month == 1:
            prev_month_year = retirement_date.year - 1
            prev_month = 12
        else:
            prev_month_year = retirement_date.year
            prev_month = retirement_date.month - 1

        # Find last day of previous month.
        if prev_month == 12:
            next_month = date(prev_month_year + 1, 1, 1)
        else:
            next_month = date(prev_month_year, prev_month + 1, 1)

        prev_month_start = date(prev_month_year, prev_month, 1)
        days_in_prev_month = (next_month - prev_month_start).days

        days += days_in_prev_month
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    return RetirementAge(years=years, months=months, days=days)


def get_reduced_pension_factor(age: RetirementAge) -> Decimal:
    """
    v0.4 uses the factor for the completed age 55-59.

    Example:
      57 years 8 months -> uses age-57 factor in this version.

    If SSNIT later provides an authoritative month-by-month factor table,
    replace this lookup without changing the rest of the engine.
    """
    if age.years not in REDUCED_PENSION_FACTORS:
        raise ValueError(
            "Reduced-pension factor is only defined for completed ages 55-59."
        )

    return REDUCED_PENSION_FACTORS[age.years]


def classify_old_age_benefit(
    date_of_birth: date,
    retirement_date: date,
    contribution_months: int,
    qualifying_hazardous_employment: bool = False,
) -> RetirementEligibilityResult:
    """
    Route a member into the appropriate OLD-AGE benefit path.

    v0.4 Act 766/883 logic:
      - under 55: not yet eligible for old-age benefit
      - age 55-59, 180+ months: reduced pension
      - age 60+, 180+ months: full pension
      - age 60+, under 180 months: old-age lump sum path
      - age 55-59, under 180 months: manual review path because
        current public SSNIT materials are not fully consistent
      - qualifying hazardous employment: full pension from age 55
        with 180+ months, subject to official occupational verification
    """
    if contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    age = calculate_retirement_age(date_of_birth, retirement_date)
    notes = []

    if age.years < 55:
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.NOT_YET_ELIGIBLE,
            eligible_for_monthly_pension=False,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=None,
            notes=("Minimum old-age retirement age not yet attained.",),
        )

    if (
        qualifying_hazardous_employment
        and age.years >= 55
        and contribution_months >= 180
    ):
        notes.append(
            "Hazardous-employment full-pension route selected; "
            "official occupational/service verification is required."
        )
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.HAZARDOUS_FULL_PENSION,
            eligible_for_monthly_pension=True,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=D("1.0"),
            notes=tuple(notes),
        )

    if contribution_months >= 180:
        if age.years >= 60:
            return RetirementEligibilityResult(
                benefit_type=OldAgeBenefitType.FULL_PENSION,
                eligible_for_monthly_pension=True,
                age=age,
                contribution_months=contribution_months,
                reduction_factor=D("1.0"),
                notes=(),
            )

        # 55 <= attained age < 60
        factor = get_reduced_pension_factor(age)
        notes.append(
            "v0.4 applies the reduction factor for completed age; "
            "month-level operational treatment should be verified before production."
        )
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.REDUCED_PENSION,
            eligible_for_monthly_pension=True,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=factor,
            notes=tuple(notes),
        )

    # Contribution months < 180.
    if age.years >= 60:
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.OLD_AGE_LUMP_SUM,
            eligible_for_monthly_pension=False,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=None,
            notes=(
                "Member is below the 180-month threshold for monthly old-age pension.",
                "Old-age lump-sum amount is not yet calculated by v0.4.",
            ),
        )

    # 55 <= age < 60 and M < 180
    return RetirementEligibilityResult(
        benefit_type=OldAgeBenefitType.OLD_AGE_LUMP_SUM_REVIEW,
        eligible_for_monthly_pension=False,
        age=age,
        contribution_months=contribution_months,
        reduction_factor=None,
        notes=(
            "Current public SSNIT materials are not fully consistent on this exact path.",
            "Manual SSNIT eligibility confirmation is required before quoting a lump-sum entitlement.",
        ),
    )


def calculate_retirement_benefit(
    date_of_birth: date,
    retirement_date: date,
    contribution_months: int,
    best_three_year_average_annual_salary: Optional[Decimal] = None,
    qualifying_hazardous_employment: bool = False,
) -> RetirementBenefitResult:
    """
    Calculate old-age monthly pension where the benefit path is pension-paying.

    Lump-sum routes are classified but intentionally not valued yet because
    the contribution accumulation/interest engine has not been implemented.
    """
    eligibility = classify_old_age_benefit(
        date_of_birth=date_of_birth,
        retirement_date=retirement_date,
        contribution_months=contribution_months,
        qualifying_hazardous_employment=qualifying_hazardous_employment,
    )

    warnings = list(eligibility.notes)

    if not eligibility.eligible_for_monthly_pension:
        return RetirementBenefitResult(
            eligibility=eligibility,
            pension_right=None,
            monthly_salary_basis=None,
            estimated_monthly_pension=None,
            calculation_status="CLASSIFIED_ONLY",
            warnings=tuple(warnings),
        )

    if best_three_year_average_annual_salary is None:
        return RetirementBenefitResult(
            eligibility=eligibility,
            pension_right=calculate_pension_right(contribution_months),
            monthly_salary_basis=None,
            estimated_monthly_pension=None,
            calculation_status="SALARY_HISTORY_REQUIRED",
            warnings=tuple(
                warnings + ["Best-three-year salary basis is required."]
            ),
        )

    if best_three_year_average_annual_salary < 0:
        raise ValueError("Best-three-year salary average cannot be negative.")

    right = calculate_pension_right(contribution_months)
    monthly_basis = best_three_year_average_annual_salary / D("12")

    pension = money(
        monthly_basis
        * right
        * eligibility.reduction_factor
    )

    return RetirementBenefitResult(
        eligibility=eligibility,
        pension_right=right,
        monthly_salary_basis=money(monthly_basis),
        estimated_monthly_pension=pension,
        calculation_status="ESTIMATED",
        warnings=tuple(warnings),
    )


# ============================================================
# v0.5 — Old-Age Lump Sum Engine
# ============================================================

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Iterable


class LumpSumCalculationStatus(str, Enum):
    RATE_BASIS_ONLY = "RATE_BASIS_ONLY"
    OFFICIAL_INTEREST_USED = "OFFICIAL_INTEREST_USED"
    ILLUSTRATIVE_ONLY = "ILLUSTRATIVE_ONLY"


@dataclass(frozen=True)
class ReturnableContributionRecord:
    """
    A contribution amount that SSNIT has confirmed is returnable for the
    old-age lump-sum calculation.

    We deliberately do NOT derive this from 5.5%, 11%, 13.5% or 18.5% here,
    because the exact returnable principal should come from the governing
    SSNIT record/rule rather than an assumption by our application.
    """
    year: int
    month: int
    returnable_amount: Decimal


@dataclass(frozen=True)
class OldAgeLumpSumResult:
    contribution_principal: Decimal
    treasury_bill_rate: Decimal
    statutory_interest_rate_basis: Decimal

    official_interest_amount: Optional[Decimal]
    estimated_lump_sum: Optional[Decimal]

    status: LumpSumCalculationStatus
    warnings: tuple[str, ...]


def sum_returnable_contributions(
    records: Iterable[ReturnableContributionRecord],
) -> Decimal:
    """
    Sum contribution amounts explicitly identified as returnable.
    """
    total = D("0")

    for record in records:
        if not 1 <= record.month <= 12:
            raise ValueError(f"Invalid month: {record.month}")
        if record.returnable_amount < 0:
            raise ValueError("Returnable contribution cannot be negative.")

        total += record.returnable_amount

    return money(total)


def old_age_lump_sum_interest_rate_basis(
    prevailing_91_day_tbill_rate: Decimal,
) -> Decimal:
    """
    Act 766 section 72:
        interest-rate basis = 75% of the prevailing Government Treasury-bill rate.

    Basic National Social Security Regulations, 2011, regulation 30(4):
        the referenced Treasury-bill rate is the prevailing 91-day rate
        (or another rate determined by SSNIT in consultation with NPRA).

    Example:
        20% T-bill rate -> statutory rate basis = 15%.
    """
    if prevailing_91_day_tbill_rate < 0:
        raise ValueError("Treasury-bill rate cannot be negative.")

    return prevailing_91_day_tbill_rate * D("0.75")


def calculate_old_age_lump_sum_basis(
    contribution_principal: Decimal,
    prevailing_91_day_tbill_rate: Decimal,
    official_interest_amount: Optional[Decimal] = None,
) -> OldAgeLumpSumResult:
    """
    Production-safe old-age lump-sum function.

    The law establishes:
      lump sum = returnable contribution principal + interest
      interest-rate basis = 75% of prevailing 91-day Treasury-bill rate.

    The public legal material reviewed does not fully specify the operational
    accumulation convention across contributions made at different dates.

    Therefore:
      - if official_interest_amount is supplied, a final lump sum is returned;
      - otherwise, the engine returns the statutory rate basis but does NOT
        invent an official interest amount.
    """
    if contribution_principal < 0:
        raise ValueError("Contribution principal cannot be negative.")

    if official_interest_amount is not None and official_interest_amount < 0:
        raise ValueError("Official interest amount cannot be negative.")

    principal = money(contribution_principal)
    rate_basis = old_age_lump_sum_interest_rate_basis(
        prevailing_91_day_tbill_rate
    )

    if official_interest_amount is None:
        return OldAgeLumpSumResult(
            contribution_principal=principal,
            treasury_bill_rate=prevailing_91_day_tbill_rate,
            statutory_interest_rate_basis=rate_basis,
            official_interest_amount=None,
            estimated_lump_sum=None,
            status=LumpSumCalculationStatus.RATE_BASIS_ONLY,
            warnings=(
                "Final SSNIT interest accumulation method has not been assumed.",
                "Supply SSNIT's official accumulated interest amount, or use the "
                "separate illustrative actuarial accumulator for scenario analysis.",
            ),
        )

    interest = money(official_interest_amount)

    return OldAgeLumpSumResult(
        contribution_principal=principal,
        treasury_bill_rate=prevailing_91_day_tbill_rate,
        statutory_interest_rate_basis=rate_basis,
        official_interest_amount=interest,
        estimated_lump_sum=money(principal + interest),
        status=LumpSumCalculationStatus.OFFICIAL_INTEREST_USED,
        warnings=(),
    )


def illustrative_lump_sum_accumulation(
    contribution_principal: Decimal,
    prevailing_91_day_tbill_rate: Decimal,
    years: Decimal,
    compound: bool = True,
) -> OldAgeLumpSumResult:
    """
    EDUCATIONAL / SCENARIO ANALYSIS ONLY.

    This is NOT asserted to be SSNIT's operational formula.

    It lets us study what the amount would be under either:
      compound: P(1+r)^n
      simple:   P(1+rn)

    where r = 75% of the supplied 91-day Treasury-bill rate.

    This is kept separate from calculate_old_age_lump_sum_basis() so that
    scenario mathematics cannot accidentally be presented as an official
    SSNIT benefit calculation.
    """
    if contribution_principal < 0:
        raise ValueError("Contribution principal cannot be negative.")
    if years < 0:
        raise ValueError("Years cannot be negative.")

    principal = contribution_principal
    r = old_age_lump_sum_interest_rate_basis(prevailing_91_day_tbill_rate)

    if compound:
        accumulated = principal * ((D("1") + r) ** years)
    else:
        accumulated = principal * (D("1") + r * years)

    accumulated = money(accumulated)
    illustrative_interest = money(accumulated - principal)

    method = "compound" if compound else "simple"

    return OldAgeLumpSumResult(
        contribution_principal=money(principal),
        treasury_bill_rate=prevailing_91_day_tbill_rate,
        statutory_interest_rate_basis=r,
        official_interest_amount=illustrative_interest,
        estimated_lump_sum=accumulated,
        status=LumpSumCalculationStatus.ILLUSTRATIVE_ONLY,
        warnings=(
            f"{method.title()} accumulation is illustrative only.",
            "Do not present this amount as the official SSNIT old-age lump sum.",
        ),
    )


def classify_old_age_benefit_v05(
    date_of_birth: date,
    retirement_date: date,
    contribution_months: int,
    qualifying_hazardous_employment: bool = False,
) -> RetirementEligibilityResult:
    """
    Corrected v0.5 routing based on Act 766 sections 70, 72, 75 and 76.

      under 55:
          not yet an old-age retirement benefit

      55-59 with 180+ months:
          reduced pension

      60+ with 180+ months:
          full pension

      55+ with fewer than 180 months and the member retires
      voluntarily or compulsorily:
          old-age lump-sum path

      qualifying hazardous employment, age 55+, 180+ months:
          full pension
    """
    if contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    age = calculate_retirement_age(date_of_birth, retirement_date)

    if age.years < 55:
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.NOT_YET_ELIGIBLE,
            eligible_for_monthly_pension=False,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=None,
            notes=("Minimum voluntary old-age retirement age not yet attained.",),
        )

    if (
        qualifying_hazardous_employment
        and contribution_months >= 180
    ):
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.HAZARDOUS_FULL_PENSION,
            eligible_for_monthly_pension=True,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=D("1.0"),
            notes=(
                "Official hazardous-employment/service verification is required.",
            ),
        )

    if contribution_months < 180:
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.OLD_AGE_LUMP_SUM,
            eligible_for_monthly_pension=False,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=None,
            notes=(
                "Old-age lump-sum path: fewer than 180 contribution months.",
            ),
        )

    if age.years >= 60:
        return RetirementEligibilityResult(
            benefit_type=OldAgeBenefitType.FULL_PENSION,
            eligible_for_monthly_pension=True,
            age=age,
            contribution_months=contribution_months,
            reduction_factor=D("1.0"),
            notes=(),
        )

    factor = get_reduced_pension_factor(age)

    return RetirementEligibilityResult(
        benefit_type=OldAgeBenefitType.REDUCED_PENSION,
        eligible_for_monthly_pension=True,
        age=age,
        contribution_months=contribution_months,
        reduction_factor=factor,
        notes=(
            "v0.5 currently uses the completed-age reduction factor; "
            "verify any finer age-month schedule before production.",
        ),
    )


# ============================================================
# v0.6 — Invalidity Pension Engine
# ============================================================

from dataclasses import dataclass
from enum import Enum
from datetime import date
from typing import Optional, Iterable


class InvalidityBenefitStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ENOUGH_RECENT_CONTRIBUTIONS = "NOT_ENOUGH_RECENT_CONTRIBUTIONS"
    MEDICAL_BOARD_CERTIFICATION_REQUIRED = "MEDICAL_BOARD_CERTIFICATION_REQUIRED"
    SALARY_HISTORY_REQUIRED = "SALARY_HISTORY_REQUIRED"


@dataclass(frozen=True)
class InvalidityEligibilityResult:
    status: InvalidityBenefitStatus
    eligible: bool
    reference_date: date
    recent_contribution_months: int
    required_recent_contribution_months: int
    total_contribution_months: int
    medical_board_certified: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class InvalidityPensionResult:
    eligibility: InvalidityEligibilityResult
    minimum_pension_right: Decimal
    earned_pension_right: Optional[Decimal]
    applied_pension_right: Optional[Decimal]
    monthly_salary_basis: Optional[Decimal]
    estimated_monthly_invalidity_pension: Optional[Decimal]
    warnings: tuple[str, ...]


def _month_index(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}")
    return year * 12 + (month - 1)


def count_recent_contribution_months(
    records: Iterable[ContributionHistoryRecord],
    reference_date: date,
    window_months: int = 36,
    include_reference_month: bool = True,
) -> int:
    """
    Count distinct calendar months containing a recorded SSNIT contribution
    within the configured rolling window.

    Default v0.6 interpretation:
      - 36 calendar months ending in the reference month.

    Because public wording uses phrases such as "within the last 36 months
    prior to the occurrence" and refers operationally to the termination/
    invalidity reference point, the inclusion convention is explicit and
    configurable rather than hidden in the code.
    """
    if window_months <= 0:
        raise ValueError("window_months must be positive.")

    ref_idx = _month_index(reference_date.year, reference_date.month)

    if include_reference_month:
        end_idx = ref_idx
    else:
        end_idx = ref_idx - 1

    start_idx = end_idx - (window_months - 1)

    qualifying_months = set()

    for record in records:
        idx = _month_index(record.year, record.month)

        if not (start_idx <= idx <= end_idx):
            continue

        if record.recorded_first_tier is not None:
            qualifying_months.add((record.year, record.month))

    return len(qualifying_months)


def calculate_invalidity_pension_right(
    total_contribution_months: int,
) -> tuple[Decimal, Optional[Decimal], Decimal]:
    """
    Section 79 logic:
      invalidity pension = higher of minimum pension or earned pension.

    Under Act 766 / Act 883:
      minimum pension right = 37.5%.

    If total contributions are below 180 months, ordinary old-age PR(M)
    is not available, so 37.5% applies.

    If M >= 180, compare 37.5% with the earned pension right.
    """
    if total_contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    minimum_right = D("0.375")
    earned_right = calculate_pension_right(total_contribution_months)

    if earned_right is None:
        applied_right = minimum_right
    else:
        applied_right = max(minimum_right, earned_right)

    return minimum_right, earned_right, applied_right


def assess_invalidity_eligibility(
    contribution_records: Iterable[ContributionHistoryRecord],
    reference_date: date,
    total_contribution_months: int,
    medical_board_certified: bool,
    include_reference_month: bool = True,
) -> InvalidityEligibilityResult:
    """
    Act 766 invalidity qualifying conditions:
      1) at least 12 contribution months within the last 36 months;
      2) permanent incapacity for normal gainful employment certified by
         the required Medical Board.

    This engine models the Medical Board condition as a verified boolean;
    it does not attempt to make a medical determination.
    """
    if total_contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    recent = count_recent_contribution_months(
        contribution_records,
        reference_date=reference_date,
        window_months=36,
        include_reference_month=include_reference_month,
    )

    if recent < 12:
        return InvalidityEligibilityResult(
            status=InvalidityBenefitStatus.NOT_ENOUGH_RECENT_CONTRIBUTIONS,
            eligible=False,
            reference_date=reference_date,
            recent_contribution_months=recent,
            required_recent_contribution_months=12,
            total_contribution_months=total_contribution_months,
            medical_board_certified=medical_board_certified,
            notes=(
                "Fewer than 12 recorded contribution months were found "
                "within the configured 36-month window.",
            ),
        )

    if not medical_board_certified:
        return InvalidityEligibilityResult(
            status=InvalidityBenefitStatus.MEDICAL_BOARD_CERTIFICATION_REQUIRED,
            eligible=False,
            reference_date=reference_date,
            recent_contribution_months=recent,
            required_recent_contribution_months=12,
            total_contribution_months=total_contribution_months,
            medical_board_certified=False,
            notes=(
                "Medical Board certification of permanent incapacity is required.",
            ),
        )

    return InvalidityEligibilityResult(
        status=InvalidityBenefitStatus.ELIGIBLE,
        eligible=True,
        reference_date=reference_date,
        recent_contribution_months=recent,
        required_recent_contribution_months=12,
        total_contribution_months=total_contribution_months,
        medical_board_certified=True,
        notes=(),
    )


def calculate_invalidity_pension(
    contribution_records: Iterable[ContributionHistoryRecord],
    reference_date: date,
    total_contribution_months: int,
    medical_board_certified: bool,
    best_three_year_average_annual_salary: Optional[Decimal],
    include_reference_month: bool = True,
) -> InvalidityPensionResult:
    """
    Calculate an estimated monthly invalidity pension.

    Formula:
        pension = monthly best-three-year salary basis
                  x max(37.5%, earned pension right)

    Eligibility must first satisfy the recent-contribution test and
    Medical Board certification.
    """
    records = list(contribution_records)

    eligibility = assess_invalidity_eligibility(
        contribution_records=records,
        reference_date=reference_date,
        total_contribution_months=total_contribution_months,
        medical_board_certified=medical_board_certified,
        include_reference_month=include_reference_month,
    )

    minimum_right, earned_right, applied_right = (
        calculate_invalidity_pension_right(total_contribution_months)
    )

    if not eligibility.eligible:
        return InvalidityPensionResult(
            eligibility=eligibility,
            minimum_pension_right=minimum_right,
            earned_pension_right=earned_right,
            applied_pension_right=None,
            monthly_salary_basis=None,
            estimated_monthly_invalidity_pension=None,
            warnings=eligibility.notes,
        )

    if best_three_year_average_annual_salary is None:
        return InvalidityPensionResult(
            eligibility=InvalidityEligibilityResult(
                status=InvalidityBenefitStatus.SALARY_HISTORY_REQUIRED,
                eligible=True,
                reference_date=eligibility.reference_date,
                recent_contribution_months=eligibility.recent_contribution_months,
                required_recent_contribution_months=12,
                total_contribution_months=eligibility.total_contribution_months,
                medical_board_certified=True,
                notes=("Best-three-year salary basis is required.",),
            ),
            minimum_pension_right=minimum_right,
            earned_pension_right=earned_right,
            applied_pension_right=applied_right,
            monthly_salary_basis=None,
            estimated_monthly_invalidity_pension=None,
            warnings=("Best-three-year salary basis is required.",),
        )

    if best_three_year_average_annual_salary < 0:
        raise ValueError("Best-three-year annual salary cannot be negative.")

    monthly_basis = best_three_year_average_annual_salary / D("12")
    pension = money(monthly_basis * applied_right)

    return InvalidityPensionResult(
        eligibility=eligibility,
        minimum_pension_right=minimum_right,
        earned_pension_right=earned_right,
        applied_pension_right=applied_right,
        monthly_salary_basis=money(monthly_basis),
        estimated_monthly_invalidity_pension=pension,
        warnings=(
            "Estimated benefit only; SSNIT Medical Board certification "
            "and official salary/contribution records govern entitlement.",
        ),
    )


def calculate_invalidity_pension_from_histories(
    salary_records: Iterable[MonthlyEarningsRecord],
    contribution_records: Iterable[ContributionHistoryRecord],
    reference_date: date,
    medical_board_certified: bool,
    parameter_registry: dict[int, SSNITParameters],
    include_reference_month: bool = True,
) -> InvalidityPensionResult:
    """
    Fully connect:
      salary history -> best-three-year basis
      contribution history -> total contribution months
      rolling 36-month test -> recent contribution months
      medical certification -> eligibility
      section 79 -> higher of minimum vs earned pension.
    """
    salary_records = list(salary_records)
    contribution_records = list(contribution_records)

    salary_result = calculate_best_three_year_salary(
        salary_records,
        parameter_registry,
    )

    contribution_result = analyze_contribution_history(
        contribution_records,
        parameter_registry,
    )

    return calculate_invalidity_pension(
        contribution_records=contribution_records,
        reference_date=reference_date,
        total_contribution_months=contribution_result.valid_contribution_months,
        medical_board_certified=medical_board_certified,
        best_three_year_average_annual_salary=(
            salary_result.best_three_year_average_annual_salary
        ),
        include_reference_month=include_reference_month,
    )


# ============================================================
# v0.7 — Survivor Benefit / Present Value Engine
# ============================================================

from dataclasses import dataclass
from enum import Enum
from datetime import date
from typing import Optional, Iterable
from decimal import localcontext


class SurvivorBenefitRoute(str, Enum):
    PRE_RETIREMENT_PRESENT_VALUE = "PRE_RETIREMENT_PRESENT_VALUE"
    PRE_RETIREMENT_RETURN_OF_CONTRIBUTIONS = "PRE_RETIREMENT_RETURN_OF_CONTRIBUTIONS"
    PENSIONER_UNEXPIRED_PRESENT_VALUE = "PENSIONER_UNEXPIRED_PRESENT_VALUE"
    NO_SURVIVOR_GUARANTEE_AFTER_75 = "NO_SURVIVOR_GUARANTEE_AFTER_75"
    OFFICIAL_VALUE_REQUIRED = "OFFICIAL_VALUE_REQUIRED"


class PaymentTiming(str, Enum):
    END_OF_MONTH = "END_OF_MONTH"      # annuity-immediate
    BEGINNING_OF_MONTH = "BEGINNING_OF_MONTH"  # annuity-due


@dataclass(frozen=True)
class SurvivorDiscountBasis:
    treasury_bill_rate: Decimal
    statutory_annual_discount_rate: Decimal
    monthly_effective_discount_rate: Decimal


@dataclass(frozen=True)
class SurvivorBenefitResult:
    route: SurvivorBenefitRoute
    recent_contribution_months: Optional[int]
    total_contribution_months: Optional[int]

    monthly_pension_basis: Optional[Decimal]
    guaranteed_months: Optional[int]

    annual_discount_rate: Optional[Decimal]
    monthly_discount_rate: Optional[Decimal]
    annuity_factor: Optional[Decimal]

    estimated_survivor_lump_sum: Optional[Decimal]

    calculation_status: str
    warnings: tuple[str, ...]


def survivor_discount_basis(
    prevailing_91_day_tbill_rate: Decimal,
) -> SurvivorDiscountBasis:
    """
    Act 766 section 78(1):
      discount at the prevailing Treasury-bill rate or 10%, whichever is lower.

    Basic National Social Security Regulations identify the referenced
    Treasury-bill rate as the prevailing 91-day rate (unless another rate
    is determined in consultation with NPRA).

    v0.7 actuarial convention:
      treat the selected annual rate as an annual effective rate and convert
      it to a monthly effective rate for monthly pension cashflows.

    The annual-to-monthly conversion convention is explicit because the
    public legal text does not spell out the operational compounding
    convention used by SSNIT.
    """
    if prevailing_91_day_tbill_rate < 0:
        raise ValueError("Treasury-bill rate cannot be negative.")

    annual = min(prevailing_91_day_tbill_rate, D("0.10"))

    with localcontext() as ctx:
        ctx.prec = 34
        monthly = (D("1") + annual) ** (D("1") / D("12")) - D("1")

    return SurvivorDiscountBasis(
        treasury_bill_rate=prevailing_91_day_tbill_rate,
        statutory_annual_discount_rate=annual,
        monthly_effective_discount_rate=monthly,
    )


def annuity_certain_factor(
    number_of_months: int,
    monthly_effective_rate: Decimal,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,
) -> Decimal:
    """
    Present value factor for level monthly pension payments.

    END_OF_MONTH:
        a-angle-n = [1 - (1+j)^(-n)] / j

    BEGINNING_OF_MONTH:
        a-double-dot-angle-n = (1+j) * a-angle-n

    If j = 0, the factor is simply n.
    """
    if number_of_months < 0:
        raise ValueError("Number of months cannot be negative.")
    if monthly_effective_rate < 0:
        raise ValueError("Monthly discount rate cannot be negative.")

    n = number_of_months

    if n == 0:
        return D("0")

    if monthly_effective_rate == 0:
        immediate = D(n)
    else:
        j = monthly_effective_rate
        immediate = (
            D("1") - (D("1") + j) ** D(-n)
        ) / j

    if payment_timing == PaymentTiming.BEGINNING_OF_MONTH:
        return immediate * (D("1") + monthly_effective_rate)

    return immediate


def present_value_of_monthly_pension(
    monthly_pension: Decimal,
    number_of_months: int,
    prevailing_91_day_tbill_rate: Decimal,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,
) -> dict:
    """
    Actuarial PV engine used by survivor calculations.
    """
    if monthly_pension < 0:
        raise ValueError("Monthly pension cannot be negative.")

    basis = survivor_discount_basis(prevailing_91_day_tbill_rate)
    factor = annuity_certain_factor(
        number_of_months,
        basis.monthly_effective_discount_rate,
        payment_timing,
    )

    pv = money(monthly_pension * factor)

    return {
        "discount_basis": basis,
        "annuity_factor": factor,
        "present_value": pv,
        "payment_timing": payment_timing,
    }


def estimate_months_to_age_75(
    date_of_birth: date,
    death_date: date,
) -> int:
    """
    Calendar-month estimator for the unexpired guarantee to age 75.

    Returns whole calendar months remaining to the 75th birthday, capped at 180.

    If the death occurs partway through a month, v0.7 counts a further month
    only when the day-of-month has not yet reached the 75th-birthday day.
    The operational SSNIT payment schedule should be used instead when known.
    """
    if death_date < date_of_birth:
        raise ValueError("Death date cannot be before date of birth.")

    seventy_fifth = date(
        date_of_birth.year + 75,
        date_of_birth.month,
        date_of_birth.day,
    )

    if death_date >= seventy_fifth:
        return 0

    months = (
        (seventy_fifth.year - death_date.year) * 12
        + (seventy_fifth.month - death_date.month)
    )

    if death_date.day < seventy_fifth.day:
        # There is a partial additional calendar month remaining.
        months += 1

    return max(0, min(180, months))


def survivor_pension_basis_from_earned_right(
    best_three_year_average_annual_salary: Decimal,
    total_contribution_months: int,
) -> Optional[Decimal]:
    """
    Estimate the deceased member's monthly earned pension only when the
    ordinary Act 766 earned pension right is defined (M >= 180).

    For M < 180 but with 12 contributions in the last 36 months, Act 766
    still routes the case to survivor PV, but the public materials reviewed
    do not sufficiently specify a production-safe pension-right basis.
    In that case this function returns None and the engine requires an
    official monthly pension basis.
    """
    if best_three_year_average_annual_salary < 0:
        raise ValueError("Salary basis cannot be negative.")
    if total_contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    right = calculate_pension_right(total_contribution_months)

    if right is None:
        return None

    monthly_basis = best_three_year_average_annual_salary / D("12")
    return money(monthly_basis * right)


def calculate_survivor_benefit_before_retirement(
    contribution_records: Iterable[ContributionHistoryRecord],
    death_date: date,
    total_contribution_months: int,
    prevailing_91_day_tbill_rate: Decimal,
    best_three_year_average_annual_salary: Optional[Decimal] = None,
    official_monthly_pension_basis: Optional[Decimal] = None,
    returnable_contribution_principal: Optional[Decimal] = None,
    official_return_interest_amount: Optional[Decimal] = None,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,
) -> SurvivorBenefitResult:
    """
    Death before retirement.

    Route A:
      >=12 contribution months in last 36 months:
      PV of 15 years (180 months) of the deceased member's pension.

    Route B:
      <12 contribution months in last 36 months:
      total returnable contributions + interest at 75% of Government
      Treasury-bill rate.

    Production safeguards:
      - for Route A with M < 180, require an official monthly pension basis
        rather than inventing a pension right;
      - for Route B, if official accumulated interest is unavailable, return
        the statutory rate basis only rather than inventing SSNIT's
        accumulation convention.
    """
    records = list(contribution_records)

    recent = count_recent_contribution_months(
        records,
        reference_date=death_date,
        window_months=36,
        include_reference_month=True,
    )

    if recent >= 12:
        if official_monthly_pension_basis is not None:
            if official_monthly_pension_basis < 0:
                raise ValueError("Official pension basis cannot be negative.")
            monthly_pension = money(official_monthly_pension_basis)
        elif best_three_year_average_annual_salary is not None:
            monthly_pension = survivor_pension_basis_from_earned_right(
                best_three_year_average_annual_salary,
                total_contribution_months,
            )
        else:
            monthly_pension = None

        if monthly_pension is None:
            return SurvivorBenefitResult(
                route=SurvivorBenefitRoute.OFFICIAL_VALUE_REQUIRED,
                recent_contribution_months=recent,
                total_contribution_months=total_contribution_months,
                monthly_pension_basis=None,
                guaranteed_months=180,
                annual_discount_rate=None,
                monthly_discount_rate=None,
                annuity_factor=None,
                estimated_survivor_lump_sum=None,
                calculation_status="OFFICIAL_PENSION_BASIS_REQUIRED",
                warnings=(
                    "The member qualifies for the 15-year survivor present-value route.",
                    "For contribution history below 180 months, v0.7 does not invent "
                    "the deceased member's pension basis. Supply SSNIT's official "
                    "monthly pension basis.",
                ),
            )

        pv = present_value_of_monthly_pension(
            monthly_pension=monthly_pension,
            number_of_months=180,
            prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
            payment_timing=payment_timing,
        )
        basis = pv["discount_basis"]

        return SurvivorBenefitResult(
            route=SurvivorBenefitRoute.PRE_RETIREMENT_PRESENT_VALUE,
            recent_contribution_months=recent,
            total_contribution_months=total_contribution_months,
            monthly_pension_basis=monthly_pension,
            guaranteed_months=180,
            annual_discount_rate=basis.statutory_annual_discount_rate,
            monthly_discount_rate=basis.monthly_effective_discount_rate,
            annuity_factor=pv["annuity_factor"],
            estimated_survivor_lump_sum=pv["present_value"],
            calculation_status="ACTUARIAL_ESTIMATE",
            warnings=(
                "Annual discount rate follows the statutory lower-of-T-bill-or-10% rule.",
                "Monthly conversion and payment timing are explicit actuarial modelling "
                "assumptions and should be replaced by SSNIT's operational convention "
                "when available.",
            ),
        )

    # Recent contribution test failed -> return-of-contributions route.
    if returnable_contribution_principal is None:
        return SurvivorBenefitResult(
            route=SurvivorBenefitRoute.PRE_RETIREMENT_RETURN_OF_CONTRIBUTIONS,
            recent_contribution_months=recent,
            total_contribution_months=total_contribution_months,
            monthly_pension_basis=None,
            guaranteed_months=None,
            annual_discount_rate=None,
            monthly_discount_rate=None,
            annuity_factor=None,
            estimated_survivor_lump_sum=None,
            calculation_status="RETURNABLE_PRINCIPAL_REQUIRED",
            warnings=(
                "Fewer than 12 contribution months were found in the last 36 months.",
                "Supply the verified returnable contribution principal.",
            ),
        )

    lump = calculate_old_age_lump_sum_basis(
        contribution_principal=returnable_contribution_principal,
        prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
        official_interest_amount=official_return_interest_amount,
    )

    return SurvivorBenefitResult(
        route=SurvivorBenefitRoute.PRE_RETIREMENT_RETURN_OF_CONTRIBUTIONS,
        recent_contribution_months=recent,
        total_contribution_months=total_contribution_months,
        monthly_pension_basis=None,
        guaranteed_months=None,
        annual_discount_rate=lump.statutory_interest_rate_basis,
        monthly_discount_rate=None,
        annuity_factor=None,
        estimated_survivor_lump_sum=lump.estimated_lump_sum,
        calculation_status=lump.status.value,
        warnings=lump.warnings,
    )


def calculate_survivor_benefit_for_pensioner(
    date_of_birth: date,
    death_date: date,
    monthly_pension_at_death: Decimal,
    prevailing_91_day_tbill_rate: Decimal,
    official_remaining_guaranteed_months: Optional[int] = None,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,
) -> SurvivorBenefitResult:
    """
    Death after retirement.

    Act 766 section 78(3):
      if a pensioner dies before age 75, pay the PV of the unexpired pension,
      not exceeding 15 years.

    v0.7 therefore uses:
      n = min(months remaining to age 75, 180)

    If SSNIT's actual remaining-payment count is known, supply it using
    official_remaining_guaranteed_months and it will override the estimator.
    """
    if monthly_pension_at_death < 0:
        raise ValueError("Monthly pension cannot be negative.")

    age = calculate_retirement_age(date_of_birth, death_date)

    if age.years >= 75:
        return SurvivorBenefitResult(
            route=SurvivorBenefitRoute.NO_SURVIVOR_GUARANTEE_AFTER_75,
            recent_contribution_months=None,
            total_contribution_months=None,
            monthly_pension_basis=money(monthly_pension_at_death),
            guaranteed_months=0,
            annual_discount_rate=None,
            monthly_discount_rate=None,
            annuity_factor=D("0"),
            estimated_survivor_lump_sum=D("0.00"),
            calculation_status="NO_UNEXPIRED_GUARANTEE",
            warnings=(
                "The Act 766 survivor guarantee for a pensioner does not extend "
                "beyond age 75.",
            ),
        )

    if official_remaining_guaranteed_months is not None:
        if official_remaining_guaranteed_months < 0:
            raise ValueError("Remaining guaranteed months cannot be negative.")
        n = min(180, official_remaining_guaranteed_months)
        month_warning = (
            "Official remaining guaranteed-payment count supplied.",
        )
    else:
        n = estimate_months_to_age_75(date_of_birth, death_date)
        month_warning = (
            "Remaining months are estimated from calendar age to 75; "
            "use SSNIT's actual payment schedule when available.",
        )

    pv = present_value_of_monthly_pension(
        monthly_pension=monthly_pension_at_death,
        number_of_months=n,
        prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
        payment_timing=payment_timing,
    )
    basis = pv["discount_basis"]

    return SurvivorBenefitResult(
        route=SurvivorBenefitRoute.PENSIONER_UNEXPIRED_PRESENT_VALUE,
        recent_contribution_months=None,
        total_contribution_months=None,
        monthly_pension_basis=money(monthly_pension_at_death),
        guaranteed_months=n,
        annual_discount_rate=basis.statutory_annual_discount_rate,
        monthly_discount_rate=basis.monthly_effective_discount_rate,
        annuity_factor=pv["annuity_factor"],
        estimated_survivor_lump_sum=pv["present_value"],
        calculation_status="ACTUARIAL_ESTIMATE",
        warnings=month_warning + (
            "Annual discount rate follows the statutory lower-of-T-bill-or-10% rule.",
            "Monthly rate conversion/payment timing remain explicit modelling assumptions.",
        ),
    )


# ============================================================
# v0.8 — Emigration Benefit Engine
# ============================================================

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EmigrationBenefitRoute(str, Enum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    PENSION_PRESENT_VALUE = "PENSION_PRESENT_VALUE"
    RETURN_OF_CONTRIBUTIONS = "RETURN_OF_CONTRIBUTIONS"
    OFFICIAL_DISCOUNT_RATE_REQUIRED = "OFFICIAL_DISCOUNT_RATE_REQUIRED"
    OFFICIAL_PENSION_BASIS_REQUIRED = "OFFICIAL_PENSION_BASIS_REQUIRED"
    RETURNABLE_PRINCIPAL_REQUIRED = "RETURNABLE_PRINCIPAL_REQUIRED"


@dataclass(frozen=True)
class EmigrationEligibilityResult:
    eligible: bool
    is_non_ghanaian: bool
    permanent_emigration_verified: bool
    contribution_months: int
    notes: tuple[str, ...]


@dataclass(frozen=True)
class EmigrationBenefitResult:
    eligibility: EmigrationEligibilityResult
    route: EmigrationBenefitRoute

    monthly_pension_basis: Optional[Decimal]
    guaranteed_months: Optional[int]

    annual_discount_rate: Optional[Decimal]
    monthly_discount_rate: Optional[Decimal]
    annuity_factor: Optional[Decimal]

    returnable_contribution_principal: Optional[Decimal]
    statutory_interest_rate_basis: Optional[Decimal]
    official_interest_amount: Optional[Decimal]

    estimated_emigration_lump_sum: Optional[Decimal]
    calculation_status: str
    warnings: tuple[str, ...]


def assess_emigration_eligibility(
    is_non_ghanaian: bool,
    permanent_emigration_verified: bool,
    contribution_months: int,
) -> EmigrationEligibilityResult:
    """
    Act 766 section 73A / Act 883:
      The emigration benefit applies to a non-Ghanaian member who satisfies
      the Trust that the member is emigrating or has emigrated permanently
      from Ghana.
    """
    if contribution_months < 0:
        raise ValueError("Contribution months cannot be negative.")

    notes = []

    if not is_non_ghanaian:
        notes.append(
            "The statutory emigration benefit is for a non-Ghanaian member."
        )

    if not permanent_emigration_verified:
        notes.append(
            "Permanent emigration must be accepted/verified by SSNIT."
        )

    return EmigrationEligibilityResult(
        eligible=is_non_ghanaian and permanent_emigration_verified,
        is_non_ghanaian=is_non_ghanaian,
        permanent_emigration_verified=permanent_emigration_verified,
        contribution_months=contribution_months,
        notes=tuple(notes),
    )


def emigration_pension_basis_from_history(
    best_three_year_average_annual_salary: Decimal,
    contribution_months: int,
) -> Optional[Decimal]:
    """
    For the 180+ month emigration branch, estimate the monthly pension basis
    from the ordinary Act 766 earned pension right.

    This is the pension amount that is then converted to a 15-year lump-sum
    present value.
    """
    if best_three_year_average_annual_salary < 0:
        raise ValueError("Best-three-year salary average cannot be negative.")

    right = calculate_pension_right(contribution_months)

    if right is None:
        return None

    monthly_salary_basis = best_three_year_average_annual_salary / D("12")
    return money(monthly_salary_basis * right)


def calculate_emigration_present_value(
    monthly_pension_basis: Decimal,
    official_annual_discount_rate: Decimal,
    guaranteed_months: int = 180,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,
) -> dict:
    """
    Actuarial present value for an emigration pension conversion.

    The NPRA expatriate guideline specifies a 15-year guaranteed period for
    the emigration present-value benefit where the member has 180+ months.

    IMPORTANT:
    Unlike the survivor-benefit provision, the public emigration provisions
    reviewed do not state a lower-of-T-bill-or-10% discount rule.

    Therefore the discount rate must be supplied from an official SSNIT/NPRA
    basis before this function is treated as production-grade.
    """
    if monthly_pension_basis < 0:
        raise ValueError("Monthly pension basis cannot be negative.")
    if official_annual_discount_rate < 0:
        raise ValueError("Discount rate cannot be negative.")
    if guaranteed_months < 0:
        raise ValueError("Guaranteed months cannot be negative.")

    with localcontext() as ctx:
        ctx.prec = 34
        monthly_rate = (
            (D("1") + official_annual_discount_rate)
            ** (D("1") / D("12"))
            - D("1")
        )

    factor = annuity_certain_factor(
        guaranteed_months,
        monthly_rate,
        payment_timing,
    )

    pv = money(monthly_pension_basis * factor)

    return {
        "annual_discount_rate": official_annual_discount_rate,
        "monthly_discount_rate": monthly_rate,
        "annuity_factor": factor,
        "present_value": pv,
    }


def calculate_emigration_benefit(
    is_non_ghanaian: bool,
    permanent_emigration_verified: bool,
    contribution_months: int,
    best_three_year_average_annual_salary: Optional[Decimal] = None,
    official_monthly_pension_basis: Optional[Decimal] = None,
    official_annual_discount_rate: Optional[Decimal] = None,
    official_present_value: Optional[Decimal] = None,
    prevailing_91_day_tbill_rate: Optional[Decimal] = None,
    returnable_contribution_principal: Optional[Decimal] = None,
    official_interest_amount: Optional[Decimal] = None,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,
) -> EmigrationBenefitResult:
    """
    Master First-Tier emigration benefit function.

    Route 1 — 180+ contribution months:
      Present value of the member's pension over a 15-year guaranteed period.

      Production safeguards:
        - an official present value can be supplied directly; OR
        - a pension basis + official annual discount rate can be supplied.
        - the survivor discount rule is NOT automatically reused.

    Route 2 — under 180 contribution months:
      return of contributions + interest at 75% of the 91-day Government
      Treasury-bill interest rate.

      Production safeguard:
        - final interest accumulation is not invented unless an official
          accumulated interest amount is supplied.
    """
    eligibility = assess_emigration_eligibility(
        is_non_ghanaian=is_non_ghanaian,
        permanent_emigration_verified=permanent_emigration_verified,
        contribution_months=contribution_months,
    )

    if not eligibility.eligible:
        return EmigrationBenefitResult(
            eligibility=eligibility,
            route=EmigrationBenefitRoute.NOT_ELIGIBLE,
            monthly_pension_basis=None,
            guaranteed_months=None,
            annual_discount_rate=None,
            monthly_discount_rate=None,
            annuity_factor=None,
            returnable_contribution_principal=None,
            statutory_interest_rate_basis=None,
            official_interest_amount=None,
            estimated_emigration_lump_sum=None,
            calculation_status="NOT_ELIGIBLE",
            warnings=eligibility.notes,
        )

    # --------------------------------------------------------
    # 180+ months: present value of 15 years of pension
    # --------------------------------------------------------
    if contribution_months >= 180:
        if official_present_value is not None:
            if official_present_value < 0:
                raise ValueError("Official present value cannot be negative.")

            return EmigrationBenefitResult(
                eligibility=eligibility,
                route=EmigrationBenefitRoute.PENSION_PRESENT_VALUE,
                monthly_pension_basis=(
                    money(official_monthly_pension_basis)
                    if official_monthly_pension_basis is not None
                    else None
                ),
                guaranteed_months=180,
                annual_discount_rate=official_annual_discount_rate,
                monthly_discount_rate=None,
                annuity_factor=None,
                returnable_contribution_principal=None,
                statutory_interest_rate_basis=None,
                official_interest_amount=None,
                estimated_emigration_lump_sum=money(official_present_value),
                calculation_status="OFFICIAL_PRESENT_VALUE_USED",
                warnings=(),
            )

        if official_monthly_pension_basis is not None:
            if official_monthly_pension_basis < 0:
                raise ValueError("Official pension basis cannot be negative.")
            monthly_pension = money(official_monthly_pension_basis)

        elif best_three_year_average_annual_salary is not None:
            monthly_pension = emigration_pension_basis_from_history(
                best_three_year_average_annual_salary,
                contribution_months,
            )
        else:
            monthly_pension = None

        if monthly_pension is None:
            return EmigrationBenefitResult(
                eligibility=eligibility,
                route=EmigrationBenefitRoute.OFFICIAL_PENSION_BASIS_REQUIRED,
                monthly_pension_basis=None,
                guaranteed_months=180,
                annual_discount_rate=None,
                monthly_discount_rate=None,
                annuity_factor=None,
                returnable_contribution_principal=None,
                statutory_interest_rate_basis=None,
                official_interest_amount=None,
                estimated_emigration_lump_sum=None,
                calculation_status="PENSION_BASIS_REQUIRED",
                warnings=(
                    "A monthly pension basis is required for the emigration "
                    "present-value calculation.",
                ),
            )

        if official_annual_discount_rate is None:
            return EmigrationBenefitResult(
                eligibility=eligibility,
                route=EmigrationBenefitRoute.OFFICIAL_DISCOUNT_RATE_REQUIRED,
                monthly_pension_basis=monthly_pension,
                guaranteed_months=180,
                annual_discount_rate=None,
                monthly_discount_rate=None,
                annuity_factor=None,
                returnable_contribution_principal=None,
                statutory_interest_rate_basis=None,
                official_interest_amount=None,
                estimated_emigration_lump_sum=None,
                calculation_status="OFFICIAL_DISCOUNT_RATE_REQUIRED",
                warnings=(
                    "The public emigration provisions reviewed specify present "
                    "value but not the survivor-benefit 10% discount cap.",
                    "Supply SSNIT/NPRA's official emigration discount basis "
                    "before quoting a final present-value estimate.",
                ),
            )

        pv = calculate_emigration_present_value(
            monthly_pension_basis=monthly_pension,
            official_annual_discount_rate=official_annual_discount_rate,
            guaranteed_months=180,
            payment_timing=payment_timing,
        )

        return EmigrationBenefitResult(
            eligibility=eligibility,
            route=EmigrationBenefitRoute.PENSION_PRESENT_VALUE,
            monthly_pension_basis=monthly_pension,
            guaranteed_months=180,
            annual_discount_rate=pv["annual_discount_rate"],
            monthly_discount_rate=pv["monthly_discount_rate"],
            annuity_factor=pv["annuity_factor"],
            returnable_contribution_principal=None,
            statutory_interest_rate_basis=None,
            official_interest_amount=None,
            estimated_emigration_lump_sum=pv["present_value"],
            calculation_status="ACTUARIAL_ESTIMATE_WITH_SUPPLIED_DISCOUNT_RATE",
            warnings=(
                "The 15-year period follows the NPRA expatriate guideline.",
                "The annual discount rate was supplied externally and should "
                "be verified as SSNIT/NPRA's operational emigration basis.",
            ),
        )

    # --------------------------------------------------------
    # Under 180 months: contribution return + interest
    # --------------------------------------------------------
    if returnable_contribution_principal is None:
        return EmigrationBenefitResult(
            eligibility=eligibility,
            route=EmigrationBenefitRoute.RETURNABLE_PRINCIPAL_REQUIRED,
            monthly_pension_basis=None,
            guaranteed_months=None,
            annual_discount_rate=None,
            monthly_discount_rate=None,
            annuity_factor=None,
            returnable_contribution_principal=None,
            statutory_interest_rate_basis=None,
            official_interest_amount=None,
            estimated_emigration_lump_sum=None,
            calculation_status="RETURNABLE_PRINCIPAL_REQUIRED",
            warnings=(
                "Verified returnable First-Tier contribution principal is required.",
            ),
        )

    if prevailing_91_day_tbill_rate is None:
        return EmigrationBenefitResult(
            eligibility=eligibility,
            route=EmigrationBenefitRoute.RETURN_OF_CONTRIBUTIONS,
            monthly_pension_basis=None,
            guaranteed_months=None,
            annual_discount_rate=None,
            monthly_discount_rate=None,
            annuity_factor=None,
            returnable_contribution_principal=money(
                returnable_contribution_principal
            ),
            statutory_interest_rate_basis=None,
            official_interest_amount=None,
            estimated_emigration_lump_sum=None,
            calculation_status="91_DAY_TBILL_RATE_REQUIRED",
            warnings=(
                "The applicable 91-day Government Treasury-bill rate is required.",
            ),
        )

    lump = calculate_old_age_lump_sum_basis(
        contribution_principal=returnable_contribution_principal,
        prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
        official_interest_amount=official_interest_amount,
    )

    return EmigrationBenefitResult(
        eligibility=eligibility,
        route=EmigrationBenefitRoute.RETURN_OF_CONTRIBUTIONS,
        monthly_pension_basis=None,
        guaranteed_months=None,
        annual_discount_rate=None,
        monthly_discount_rate=None,
        annuity_factor=None,
        returnable_contribution_principal=lump.contribution_principal,
        statutory_interest_rate_basis=lump.statutory_interest_rate_basis,
        official_interest_amount=lump.official_interest_amount,
        estimated_emigration_lump_sum=lump.estimated_lump_sum,
        calculation_status=lump.status.value,
        warnings=lump.warnings + (
            "NPRA's expatriate guideline describes compound interest for the "
            "less-than-15-year lump-sum route, but contribution-by-contribution "
            "timing/rate history should still come from official records.",
        ),
    )


# ============================================================
# v0.9 — Master Benefit Routing Engine
# ============================================================

from dataclasses import dataclass
from enum import Enum
from datetime import date
from typing import Optional, Iterable, Any


class BenefitEvent(str, Enum):
    RETIREMENT = "RETIREMENT"
    INVALIDITY = "INVALIDITY"
    DEATH_BEFORE_RETIREMENT = "DEATH_BEFORE_RETIREMENT"
    DEATH_AFTER_RETIREMENT = "DEATH_AFTER_RETIREMENT"
    EMIGRATION = "EMIGRATION"


@dataclass(frozen=True)
class MasterBenefitResult:
    event: BenefitEvent
    routed_benefit: str
    eligible: Optional[bool]

    monthly_benefit: Optional[Decimal]
    lump_sum_benefit: Optional[Decimal]

    calculation_status: str
    details: Any
    warnings: tuple[str, ...]


def _derive_total_contribution_months(
    explicit_contribution_months: Optional[int],
    contribution_records: Optional[Iterable[ContributionHistoryRecord]],
) -> int:
    """
    Prefer an explicit verified contribution-month count.
    Otherwise derive distinct months from contribution records containing
    a recorded First-Tier contribution.
    """
    if explicit_contribution_months is not None:
        if explicit_contribution_months < 0:
            raise ValueError("Contribution months cannot be negative.")
        return explicit_contribution_months

    if contribution_records is None:
        raise ValueError(
            "Either contribution_months or contribution_records is required."
        )

    distinct_months = {
        (r.year, r.month)
        for r in contribution_records
        if r.recorded_first_tier is not None
    }
    return len(distinct_months)


def calculate_master_benefit(
    event: BenefitEvent,

    # Core member/event data
    date_of_birth: Optional[date] = None,
    event_date: Optional[date] = None,
    contribution_months: Optional[int] = None,

    # Earnings/contribution evidence
    best_three_year_average_annual_salary: Optional[Decimal] = None,
    contribution_records: Optional[Iterable[ContributionHistoryRecord]] = None,

    # Retirement
    qualifying_hazardous_employment: bool = False,

    # Lump-sum / contribution-return inputs
    returnable_contribution_principal: Optional[Decimal] = None,
    prevailing_91_day_tbill_rate: Optional[Decimal] = None,
    official_interest_amount: Optional[Decimal] = None,

    # Invalidity
    medical_board_certified: bool = False,

    # Survivor
    monthly_pension_at_death: Optional[Decimal] = None,
    official_monthly_pension_basis: Optional[Decimal] = None,
    official_remaining_guaranteed_months: Optional[int] = None,
    payment_timing: PaymentTiming = PaymentTiming.END_OF_MONTH,

    # Emigration
    is_non_ghanaian: bool = False,
    permanent_emigration_verified: bool = False,
    official_annual_discount_rate: Optional[Decimal] = None,
    official_present_value: Optional[Decimal] = None,
) -> MasterBenefitResult:
    """
    Master Act 766 / Act 883 benefit router.

    The user supplies the life event once.
    This function determines the applicable benefit branch and calls the
    relevant actuarial module.

    Supported events:
      RETIREMENT
      INVALIDITY
      DEATH_BEFORE_RETIREMENT
      DEATH_AFTER_RETIREMENT
      EMIGRATION

    It intentionally does not mix PNDCL 247 calculations into this engine.
    """

    records = (
        list(contribution_records)
        if contribution_records is not None
        else None
    )

    M = _derive_total_contribution_months(
        contribution_months,
        records,
    )

    # --------------------------------------------------------
    # RETIREMENT
    # --------------------------------------------------------
    if event == BenefitEvent.RETIREMENT:
        if date_of_birth is None or event_date is None:
            raise ValueError(
                "date_of_birth and event_date are required for retirement."
            )

        eligibility = classify_old_age_benefit_v05(
            date_of_birth=date_of_birth,
            retirement_date=event_date,
            contribution_months=M,
            qualifying_hazardous_employment=qualifying_hazardous_employment,
        )

        # Monthly-pension routes
        if eligibility.eligible_for_monthly_pension:
            if best_three_year_average_annual_salary is None:
                return MasterBenefitResult(
                    event=event,
                    routed_benefit=eligibility.benefit_type.value,
                    eligible=True,
                    monthly_benefit=None,
                    lump_sum_benefit=None,
                    calculation_status="SALARY_HISTORY_REQUIRED",
                    details=eligibility,
                    warnings=(
                        "Best-three-year annual salary basis is required.",
                    ),
                )

            right = calculate_pension_right(M)
            monthly_basis = best_three_year_average_annual_salary / D("12")
            pension = money(
                monthly_basis
                * right
                * eligibility.reduction_factor
            )

            return MasterBenefitResult(
                event=event,
                routed_benefit=eligibility.benefit_type.value,
                eligible=True,
                monthly_benefit=pension,
                lump_sum_benefit=None,
                calculation_status="ESTIMATED",
                details={
                    "eligibility": eligibility,
                    "pension_right": right,
                    "monthly_salary_basis": money(monthly_basis),
                    "reduction_factor": eligibility.reduction_factor,
                },
                warnings=eligibility.notes,
            )

        # Old-age lump-sum route
        if eligibility.benefit_type == OldAgeBenefitType.OLD_AGE_LUMP_SUM:
            if returnable_contribution_principal is None:
                return MasterBenefitResult(
                    event=event,
                    routed_benefit=eligibility.benefit_type.value,
                    eligible=True,
                    monthly_benefit=None,
                    lump_sum_benefit=None,
                    calculation_status="RETURNABLE_PRINCIPAL_REQUIRED",
                    details=eligibility,
                    warnings=(
                        "Verified returnable contribution principal is required.",
                    ),
                )

            if prevailing_91_day_tbill_rate is None:
                return MasterBenefitResult(
                    event=event,
                    routed_benefit=eligibility.benefit_type.value,
                    eligible=True,
                    monthly_benefit=None,
                    lump_sum_benefit=None,
                    calculation_status="91_DAY_TBILL_RATE_REQUIRED",
                    details=eligibility,
                    warnings=(
                        "Applicable 91-day Government Treasury-bill rate is required.",
                    ),
                )

            lump = calculate_old_age_lump_sum_basis(
                contribution_principal=returnable_contribution_principal,
                prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
                official_interest_amount=official_interest_amount,
            )

            return MasterBenefitResult(
                event=event,
                routed_benefit=eligibility.benefit_type.value,
                eligible=True,
                monthly_benefit=None,
                lump_sum_benefit=lump.estimated_lump_sum,
                calculation_status=lump.status.value,
                details={
                    "eligibility": eligibility,
                    "lump_sum": lump,
                },
                warnings=lump.warnings,
            )

        return MasterBenefitResult(
            event=event,
            routed_benefit=eligibility.benefit_type.value,
            eligible=False,
            monthly_benefit=None,
            lump_sum_benefit=None,
            calculation_status="NOT_YET_ELIGIBLE",
            details=eligibility,
            warnings=eligibility.notes,
        )

    # --------------------------------------------------------
    # INVALIDITY
    # --------------------------------------------------------
    if event == BenefitEvent.INVALIDITY:
        if event_date is None:
            raise ValueError("event_date is required for invalidity.")
        if records is None:
            raise ValueError(
                "contribution_records are required for the rolling "
                "36-month invalidity test."
            )

        result = calculate_invalidity_pension(
            contribution_records=records,
            reference_date=event_date,
            total_contribution_months=M,
            medical_board_certified=medical_board_certified,
            best_three_year_average_annual_salary=(
                best_three_year_average_annual_salary
            ),
        )

        return MasterBenefitResult(
            event=event,
            routed_benefit="INVALIDITY_PENSION",
            eligible=result.eligibility.eligible,
            monthly_benefit=result.estimated_monthly_invalidity_pension,
            lump_sum_benefit=None,
            calculation_status=result.eligibility.status.value,
            details=result,
            warnings=result.warnings,
        )

    # --------------------------------------------------------
    # DEATH BEFORE RETIREMENT
    # --------------------------------------------------------
    if event == BenefitEvent.DEATH_BEFORE_RETIREMENT:
        if event_date is None:
            raise ValueError("event_date/death_date is required.")
        if records is None:
            raise ValueError(
                "contribution_records are required for the survivor "
                "36-month contribution test."
            )
        if prevailing_91_day_tbill_rate is None:
            raise ValueError(
                "The applicable 91-day Treasury-bill rate is required "
                "for survivor calculations."
            )

        result = calculate_survivor_benefit_before_retirement(
            contribution_records=records,
            death_date=event_date,
            total_contribution_months=M,
            prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
            best_three_year_average_annual_salary=(
                best_three_year_average_annual_salary
            ),
            official_monthly_pension_basis=official_monthly_pension_basis,
            returnable_contribution_principal=(
                returnable_contribution_principal
            ),
            official_return_interest_amount=official_interest_amount,
            payment_timing=payment_timing,
        )

        return MasterBenefitResult(
            event=event,
            routed_benefit=result.route.value,
            eligible=True,
            monthly_benefit=None,
            lump_sum_benefit=result.estimated_survivor_lump_sum,
            calculation_status=result.calculation_status,
            details=result,
            warnings=result.warnings,
        )

    # --------------------------------------------------------
    # DEATH AFTER RETIREMENT
    # --------------------------------------------------------
    if event == BenefitEvent.DEATH_AFTER_RETIREMENT:
        if date_of_birth is None or event_date is None:
            raise ValueError(
                "date_of_birth and event_date/death_date are required."
            )
        if monthly_pension_at_death is None:
            raise ValueError(
                "monthly_pension_at_death is required for a pensioner death."
            )
        if prevailing_91_day_tbill_rate is None:
            raise ValueError(
                "The applicable 91-day Treasury-bill rate is required."
            )

        result = calculate_survivor_benefit_for_pensioner(
            date_of_birth=date_of_birth,
            death_date=event_date,
            monthly_pension_at_death=monthly_pension_at_death,
            prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
            official_remaining_guaranteed_months=(
                official_remaining_guaranteed_months
            ),
            payment_timing=payment_timing,
        )

        return MasterBenefitResult(
            event=event,
            routed_benefit=result.route.value,
            eligible=(
                result.route
                != SurvivorBenefitRoute.NO_SURVIVOR_GUARANTEE_AFTER_75
            ),
            monthly_benefit=None,
            lump_sum_benefit=result.estimated_survivor_lump_sum,
            calculation_status=result.calculation_status,
            details=result,
            warnings=result.warnings,
        )

    # --------------------------------------------------------
    # EMIGRATION
    # --------------------------------------------------------
    if event == BenefitEvent.EMIGRATION:
        result = calculate_emigration_benefit(
            is_non_ghanaian=is_non_ghanaian,
            permanent_emigration_verified=permanent_emigration_verified,
            contribution_months=M,
            best_three_year_average_annual_salary=(
                best_three_year_average_annual_salary
            ),
            official_monthly_pension_basis=official_monthly_pension_basis,
            official_annual_discount_rate=official_annual_discount_rate,
            official_present_value=official_present_value,
            prevailing_91_day_tbill_rate=prevailing_91_day_tbill_rate,
            returnable_contribution_principal=(
                returnable_contribution_principal
            ),
            official_interest_amount=official_interest_amount,
            payment_timing=payment_timing,
        )

        return MasterBenefitResult(
            event=event,
            routed_benefit=result.route.value,
            eligible=result.eligibility.eligible,
            monthly_benefit=None,
            lump_sum_benefit=result.estimated_emigration_lump_sum,
            calculation_status=result.calculation_status,
            details=result,
            warnings=result.warnings,
        )

    raise ValueError(f"Unsupported benefit event: {event}")


def master_result_summary(result: MasterBenefitResult) -> dict:
    """
    Small UI/API-friendly summary.
    """
    return {
        "event": result.event.value,
        "routed_benefit": result.routed_benefit,
        "eligible": result.eligible,
        "monthly_benefit": result.monthly_benefit,
        "lump_sum_benefit": result.lump_sum_benefit,
        "calculation_status": result.calculation_status,
        "warnings": result.warnings,
    }
