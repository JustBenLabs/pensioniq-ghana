from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Optional


from ssnit_engine.contribution_health import (
    analyse_contribution_history,
)

from ssnit_engine.engine import (
    BenefitEvent,
    calculate_master_benefit,
    calculate_pension_right,
)

from ssnit_engine.readiness import (
    calculate_retirement_readiness,
)

from ssnit_engine.scenario import (
    retirement_date_for_age,
)


D = Decimal


# ============================================================
# REPORT CONSTANTS
# ============================================================


REPORT_VERSION = "1.0"

MINIMUM_PENSION_MONTHS = 180
MAXIMUM_PENSION_RIGHT_MONTHS = 420


REPORT_DISCLAIMER = (
    "This PensionIQ Personal Retirement Report is a "
    "retirement-planning document generated from information "
    "stored in PensionIQ and assumptions configured in the "
    "PensionIQ actuarial engine. It is not an official SSNIT "
    "statement, entitlement decision, benefit quotation or "
    "guarantee of future pension benefits. Official SSNIT "
    "records and determinations govern actual benefits."
)


# ============================================================
# DATA MODEL
# ============================================================


@dataclass(frozen=True)
class RetirementReportData:

    report_version: str

    generated_at: datetime

    member: dict[str, Any]

    contribution_position: dict[str, Any]

    contribution_health: dict[str, Any]

    pension_position: dict[str, Any]

    retirement_readiness: dict[str, Any]

    planning_sections: dict[str, Any]

    recommendations: tuple[str, ...]

    assumptions: tuple[str, ...]

    disclaimer: str


# ============================================================
# HELPERS
# ============================================================


def _decimal(
    value,
) -> Decimal:

    return D(
        str(value)
    )


def _round_two(
    value: Decimal,
) -> Decimal:

    return value.quantize(
        D("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _decimal_string(
    value,
) -> Optional[str]:

    if value is None:
        return None

    return str(
        _round_two(
            _decimal(value)
        )
    )


def _percentage_string(
    value,
) -> Optional[str]:

    if value is None:
        return None

    percentage = (
        _decimal(value)
        *
        D("100")
    )

    return str(
        _round_two(
            percentage
        )
    )


def _calculate_age(
    date_of_birth: date,
    valuation_date: date,
) -> int:

    age = (
        valuation_date.year
        -
        date_of_birth.year
    )

    birthday_has_not_occurred = (
        (
            valuation_date.month,
            valuation_date.day,
        )
        <
        (
            date_of_birth.month,
            date_of_birth.day,
        )
    )

    if birthday_has_not_occurred:
        age -= 1

    return age


def _record_alignment_status(
    *,
    stored_contribution_months: int,
    detailed_record_count: int,
) -> str:

    if detailed_record_count == 0:

        return (
            "NO_DETAILED_HISTORY"
        )

    if (
        detailed_record_count
        ==
        stored_contribution_months
    ):

        return "ALIGNED"

    return (
        "TOTAL_AND_HISTORY_DIFFER"
    )


# ============================================================
# AGE-60 BASELINE
# ============================================================


def _calculate_age_60_baseline(
    *,
    date_of_birth: date,
    contribution_months: int,
    annual_salary: Decimal,
    valuation_date: date,
) -> dict[str, Any]:

    """
    Estimate the member's age-60 pension using the contribution
    months and salary currently stored in PensionIQ.

    This is deliberately labelled as a baseline assumption.
    It does not project additional future contributions or
    future salary growth.
    """

    retirement_date = (
        retirement_date_for_age(
            date_of_birth,
            60,
        )
    )


    if retirement_date < valuation_date:

        return {

            "available":
                False,

            "reason":
                (
                    "The member's age-60 anniversary "
                    "has already passed."
                ),

            "retirement_age":
                60,

            "retirement_date":
                retirement_date.isoformat(),

            "estimated_monthly_pension":
                None,

            "retirement_age_factor":
                None,
        }


    benefit = (
        calculate_master_benefit(

            event=BenefitEvent.RETIREMENT,

            date_of_birth=(
                date_of_birth
            ),

            event_date=(
                retirement_date
            ),

            contribution_months=(
                contribution_months
            ),

            best_three_year_average_annual_salary=(
                annual_salary
            ),
        )
    )


    reduction_factor = None


    if isinstance(
        benefit.details,
        dict,
    ):

        reduction_factor = (
            benefit
            .details
            .get(
                "reduction_factor"
            )
        )


    return {

        "available":
            True,

        "retirement_age":
            60,

        "retirement_date":
            retirement_date.isoformat(),

        "estimated_monthly_pension":
            _decimal_string(
                benefit.monthly_benefit
            ),

        "retirement_age_factor":
            _decimal_string(
                reduction_factor
            ),

        "calculation_status":
            benefit.calculation_status,

        "note":
            (
                "Age-60 baseline using the member's "
                "currently stored contribution-month total "
                "and currently stored best-three-year "
                "average annual salary. No future salary "
                "growth or additional contributions are "
                "projected in this baseline."
            ),
    }


# ============================================================
# BUILD REPORT DATA
# ============================================================


def build_retirement_report_data(
    *,
    member,
    contribution_records: Iterable,
    generated_at: Optional[datetime] = None,
    valuation_date: Optional[date] = None,
    what_if_scenario: Optional[dict[str, Any]] = None,
    retirement_goal: Optional[dict[str, Any]] = None,
) -> RetirementReportData:

    """
    Assemble the PensionIQ Personal Retirement Report dataset.

    The function does not generate a PDF.

    It creates a stable report-data structure that the later
    PDF renderer can consume.

    What-If and Retirement Goal sections are optional because
    those analyses are currently calculated on demand and are
    not automatically persisted in the member database.
    """


    # ========================================================
    # DATES
    # ========================================================

    if generated_at is None:

        generated_at = (
            datetime.now(
                timezone.utc
            )
        )


    if valuation_date is None:

        valuation_date = (
            generated_at.date()
        )


    # ========================================================
    # MEMBER DATA
    # ========================================================

    date_of_birth = (
        member.date_of_birth
    )


    contribution_months = int(
        member.contribution_months
    )


    annual_salary = _decimal(
        member
        .best_three_year_average_annual_salary
    )


    current_age = (
        _calculate_age(
            date_of_birth,
            valuation_date,
        )
    )


    member_data = {

        "member_id":
            member.id,

        "first_name":
            member.first_name,

        "last_name":
            member.last_name,

        "full_name":
            (
                f"{member.first_name} "
                f"{member.last_name}"
            ),

        "date_of_birth":
            date_of_birth.isoformat(),

        "current_age":
            current_age,

        "sex":
            member.sex,

        "best_three_year_average_annual_salary":
            _decimal_string(
                annual_salary
            ),
    }


    # ========================================================
    # CONTRIBUTION HISTORY
    # ========================================================

    records = list(
        contribution_records
    )


    health = (
        analyse_contribution_history(
            records
        )
    )


    detailed_record_count = (
        len(records)
    )


    alignment_status = (
        _record_alignment_status(

            stored_contribution_months=(
                contribution_months
            ),

            detailed_record_count=(
                detailed_record_count
            ),
        )
    )


    continuity_ratio_percent = (
        health.get(
            "continuity_ratio_percent"
        )
    )


    continuity_ratio = None
    continuity_used_in_readiness = False


    if (
        alignment_status
        ==
        "ALIGNED"
        and
        continuity_ratio_percent
        is not None
    ):

        continuity_ratio = (
            _decimal(
                continuity_ratio_percent
            )
            /
            D("100")
        )

        continuity_used_in_readiness = True


    # ========================================================
    # CONTRIBUTION POSITION
    # ========================================================

    contribution_years = (
        D(
            contribution_months
        )
        /
        D("12")
    )


    months_to_minimum = max(
        0,
        (
            MINIMUM_PENSION_MONTHS
            -
            contribution_months
        ),
    )


    months_to_maximum = max(
        0,
        (
            MAXIMUM_PENSION_RIGHT_MONTHS
            -
            contribution_months
        ),
    )


    contribution_position = {

        "stored_contribution_months":
            contribution_months,

        "contribution_years":
            _decimal_string(
                contribution_years
            ),

        "detailed_records_stored":
            detailed_record_count,

        "record_alignment_status":
            alignment_status,

        "minimum_monthly_pension_threshold":
            MINIMUM_PENSION_MONTHS,

        "maximum_pension_right_months":
            MAXIMUM_PENSION_RIGHT_MONTHS,

        "months_to_minimum":
            months_to_minimum,

        "months_to_maximum":
            months_to_maximum,

        "monthly_pension_threshold_met":
            (
                contribution_months
                >=
                MINIMUM_PENSION_MONTHS
            ),
    }


    # ========================================================
    # PENSION RIGHT
    # ========================================================

    if (
        contribution_months
        >=
        MINIMUM_PENSION_MONTHS
    ):

        pension_right = (
            calculate_pension_right(
                contribution_months
            )
        )

    else:

        pension_right = None


    age_60_baseline = (
        _calculate_age_60_baseline(

            date_of_birth=(
                date_of_birth
            ),

            contribution_months=(
                contribution_months
            ),

            annual_salary=(
                annual_salary
            ),

            valuation_date=(
                valuation_date
            ),
        )
    )


    pension_position = {

        "pension_right":
            (
                str(
                    pension_right
                )
                if pension_right
                is not None
                else None
            ),

        "pension_right_percent":
            _percentage_string(
                pension_right
            ),

        "salary_basis_annual":
            _decimal_string(
                annual_salary
            ),

        "salary_basis_monthly":
            _decimal_string(
                annual_salary
                /
                D("12")
            ),

        "age_60_baseline":
            age_60_baseline,
    }


    # ========================================================
    # READINESS
    # ========================================================

    readiness = (
        calculate_retirement_readiness(

            contribution_months=(
                contribution_months
            ),

            continuity_ratio=(
                continuity_ratio
            ),
        )
    )


    retirement_readiness = {

        "indicator_name":
            (
                "PensionIQ Retirement "
                "Readiness Indicator"
            ),

        "score":
            _decimal_string(
                readiness.total_score
            ),

        "maximum_score":
            "100.00",

        "rating":
            readiness.rating,

        "provisional":
            readiness.provisional,

        "components": {

            "eligibility": {

                "score":
                    _decimal_string(
                        readiness
                        .eligibility_score
                    ),

                "maximum":
                    "40.00",
            },

            "pension_right": {

                "score":
                    _decimal_string(
                        readiness
                        .pension_right_score
                    ),

                "maximum":
                    "35.00",
            },

            "contribution_consistency": {

                "score":
                    _decimal_string(
                        readiness
                        .consistency_score
                    ),

                "maximum":
                    "25.00",
            },
        },

        "data_quality": {

            "record_alignment_status":
                alignment_status,

            "continuity_ratio_percent":
                continuity_ratio_percent,

            "continuity_used_in_score":
                continuity_used_in_readiness,
        },
    }


    # ========================================================
    # CONTRIBUTION HEALTH
    # ========================================================

    contribution_health = {

        "status":
            health.get(
                "status"
            ),

        "continuity_ratio_percent":
            continuity_ratio_percent,

        "missing_month_count":
            health.get(
                "missing_month_count"
            ),

        "amount_mismatch_count":
            health.get(
                "amount_mismatch_count"
            ),

        "total_insurable_earnings":
            health.get(
                "total_insurable_earnings"
            ),

        "total_recorded_first_tier":
            health.get(
                "total_recorded_first_tier"
            ),

        "record_alignment_status":
            alignment_status,

        "diagnostic_note":
            (
                "Contribution-health findings refer to "
                "records currently stored in PensionIQ. "
                "Missing months or differences do not by "
                "themselves prove that SSNIT failed to "
                "receive a contribution."
            ),
    }


    # ========================================================
    # OPTIONAL PLANNING SECTIONS
    # ========================================================

    planning_sections = {

        "what_if_scenario": {

            "included":
                (
                    what_if_scenario
                    is not None
                ),

            "data":
                what_if_scenario,

            "note":
                (
                    None
                    if what_if_scenario
                    is not None
                    else
                    (
                        "No saved What-If retirement "
                        "scenario was supplied for this "
                        "report."
                    )
                ),
        },

        "retirement_goal": {

            "included":
                (
                    retirement_goal
                    is not None
                ),

            "data":
                retirement_goal,

            "note":
                (
                    None
                    if retirement_goal
                    is not None
                    else
                    (
                        "No saved retirement-goal "
                        "analysis was supplied for this "
                        "report."
                    )
                ),
        },
    }


    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    recommendations = tuple(
        readiness.recommendations
    )


    # ========================================================
    # ASSUMPTIONS
    # ========================================================

    assumptions = (

        (
            "Pension-right calculations use the rules "
            "configured in the PensionIQ actuarial engine."
        ),

        (
            "The age-60 baseline uses the currently stored "
            "contribution-month total without assuming "
            "additional future contribution months."
        ),

        (
            "The age-60 baseline uses the currently stored "
            "best-three-year average annual salary without "
            "projecting future salary growth."
        ),

        (
            "Contribution continuity is included in the "
            "Retirement Readiness Indicator only when the "
            "detailed contribution-record count aligns with "
            "the stored contribution-month total."
        ),

        (
            "Contribution-health diagnostics describe the "
            "records stored in PensionIQ and are not an "
            "official SSNIT contribution statement."
        ),
    )


    # ========================================================
    # RESULT
    # ========================================================

    return RetirementReportData(

        report_version=(
            REPORT_VERSION
        ),

        generated_at=(
            generated_at
        ),

        member=(
            member_data
        ),

        contribution_position=(
            contribution_position
        ),

        contribution_health=(
            contribution_health
        ),

        pension_position=(
            pension_position
        ),

        retirement_readiness=(
            retirement_readiness
        ),

        planning_sections=(
            planning_sections
        ),

        recommendations=(
            recommendations
        ),

        assumptions=(
            assumptions
        ),

        disclaimer=(
            REPORT_DISCLAIMER
        ),
    )