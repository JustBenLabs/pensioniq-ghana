from dataclasses import dataclass
from datetime import date
from decimal import (
    Decimal,
    ROUND_HALF_UP,
)
from typing import Optional


from ssnit_engine.engine import (
    BenefitEvent,
    calculate_master_benefit,
    calculate_pension_right,
)

from ssnit_engine.readiness import (
    calculate_retirement_readiness,
)


D = Decimal


# ============================================================
# RESULT MODELS
# ============================================================


@dataclass(frozen=True)
class RetirementScenarioPosition:

    contribution_months: int

    annual_salary: Decimal

    retirement_age: int

    retirement_date: date

    pension_right: Optional[Decimal]

    retirement_age_factor: Optional[Decimal]

    monthly_pension: Optional[Decimal]

    readiness_score: Optional[Decimal]

    readiness_rating: str

    readiness_provisional: bool


@dataclass(frozen=True)
class RetirementScenarioResult:

    baseline: RetirementScenarioPosition

    scenario: RetirementScenarioPosition

    additional_contribution_months: int

    available_contribution_months: int

    pension_right_change_percentage_points: Optional[Decimal]

    monthly_pension_change: Optional[Decimal]

    monthly_pension_change_percent: Optional[Decimal]

    readiness_score_change: Optional[Decimal]

    became_monthly_pension_eligible: bool

    continuity_assumption: str


# ============================================================
# ROUNDING
# ============================================================


def _round_two(
    value: Decimal,
) -> Decimal:

    return value.quantize(
        D("0.01"),
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# RETIREMENT DATE
# ============================================================


def retirement_date_for_age(
    date_of_birth: date,
    retirement_age: int,
) -> date:

    """
    Convert a selected retirement age into
    the member's retirement anniversary date.

    For a 29 February birthday in a non-leap
    retirement year, 28 February is used as
    the planner anniversary convention.
    """

    target_year = (
        date_of_birth.year
        +
        retirement_age
    )

    try:

        return date(
            target_year,
            date_of_birth.month,
            date_of_birth.day,
        )

    except ValueError:

        # 29 February DOB in a non-leap year.

        return date(
            target_year,
            2,
            28,
        )


# ============================================================
# MONTHS AVAILABLE UNTIL RETIREMENT
# ============================================================


def full_months_between(
    start_date: date,
    end_date: date,
) -> int:

    """
    Number of completed calendar months between
    two dates.
    """

    if end_date < start_date:

        return 0


    months = (
        (
            end_date.year
            -
            start_date.year
        )
        *
        12
        +
        (
            end_date.month
            -
            start_date.month
        )
    )


    if (
        end_date.day
        <
        start_date.day
    ):

        months -= 1


    return max(
        0,
        months,
    )


# ============================================================
# POSITION BUILDER
# ============================================================


def _build_position(
    *,
    date_of_birth: date,
    retirement_date: date,
    retirement_age: int,
    contribution_months: int,
    annual_salary: Decimal,
    continuity_ratio: Optional[Decimal],
) -> RetirementScenarioPosition:

    benefit_result = (
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


    pension_right = (
        calculate_pension_right(
            contribution_months
        )
    )


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


    # --------------------------------------------------------
    # Retirement-age factor
    # --------------------------------------------------------

    retirement_age_factor = None


    if isinstance(
        benefit_result.details,
        dict,
    ):

        retirement_age_factor = (
            benefit_result.details.get(
                "reduction_factor"
            )
        )


    return RetirementScenarioPosition(

        contribution_months=(
            contribution_months
        ),

        annual_salary=(
            annual_salary
        ),

        retirement_age=(
            retirement_age
        ),

        retirement_date=(
            retirement_date
        ),

        pension_right=(
            pension_right
        ),

        retirement_age_factor=(
            retirement_age_factor
        ),

        monthly_pension=(
            benefit_result.monthly_benefit
        ),

        readiness_score=(
            readiness.total_score
        ),

        readiness_rating=(
            readiness.rating
        ),

        readiness_provisional=(
            readiness.provisional
        ),
    )


# ============================================================
# RETIREMENT WHAT-IF SCENARIO
# ============================================================


def calculate_retirement_scenario(
    *,
    date_of_birth: date,
    current_contribution_months: int,
    current_annual_salary: Decimal,
    additional_contribution_months: int,
    projected_annual_salary: Decimal,
    retirement_age: int,
    continuity_ratio: Optional[Decimal] = None,
    valuation_date: Optional[date] = None,
) -> RetirementScenarioResult:

    """
    PensionIQ What-If Retirement Planner.

    Baseline:
        Uses the member's current contribution
        months and current salary at the selected
        retirement age.

    Scenario:
        Uses current contribution months plus
        simulated additional contribution months
        and the projected salary at the same
        retirement age.

    The calculation does not modify the member's
    profile or contribution records.

    Where a trusted continuity ratio is supplied,
    PensionIQ holds that ratio constant for the
    scenario. Future simulated contribution
    consistency is therefore an assumption rather
    than recorded history.

    This is a retirement-planning simulation and
    not an official SSNIT determination.
    """


    # ========================================================
    # VALIDATION
    # ========================================================

    if current_contribution_months < 0:

        raise ValueError(
            "Current contribution months "
            "cannot be negative."
        )


    if additional_contribution_months < 0:

        raise ValueError(
            "Additional contribution months "
            "cannot be negative."
        )


    if current_annual_salary < 0:

        raise ValueError(
            "Current annual salary "
            "cannot be negative."
        )


    if projected_annual_salary < 0:

        raise ValueError(
            "Projected annual salary "
            "cannot be negative."
        )


    if not (
        55
        <=
        retirement_age
        <=
        60
    ):

        raise ValueError(
            "Retirement age must be "
            "between 55 and 60."
        )


    if continuity_ratio is not None:

        continuity_ratio = D(
            str(
                continuity_ratio
            )
        )

        if not (
            D("0")
            <=
            continuity_ratio
            <=
            D("1")
        ):

            raise ValueError(
                "Continuity ratio must be "
                "between 0 and 1."
            )


    if valuation_date is None:

        valuation_date = (
            date.today()
        )


    if valuation_date < date_of_birth:

        raise ValueError(
            "Valuation date cannot be "
            "before date of birth."
        )


    retirement_date = (
        retirement_date_for_age(
            date_of_birth,
            retirement_age,
        )
    )


    if (
        retirement_date
        <
        valuation_date
    ):

        raise ValueError(
            "The selected retirement age "
            "has already passed."
        )


    # ========================================================
    # AVAILABLE FUTURE CONTRIBUTION MONTHS
    # ========================================================

    available_contribution_months = (
        full_months_between(
            valuation_date,
            retirement_date,
        )
    )


    if (
        additional_contribution_months
        >
        available_contribution_months
    ):

        raise ValueError(
            (
                "Additional contribution months "
                "cannot exceed the number of full "
                "months available before the "
                "selected retirement date "
                f"({available_contribution_months})."
            )
        )


    scenario_contribution_months = (
        current_contribution_months
        +
        additional_contribution_months
    )


    # Contributions are modelled from age 15 onward.

    maximum_possible_months = (
        retirement_age
        -
        15
    ) * 12


    if (
        scenario_contribution_months
        >
        maximum_possible_months
    ):

        raise ValueError(
            (
                "Scenario contribution months "
                "exceed the maximum plausible "
                "contribution history for the "
                "selected retirement age."
            )
        )


    # ========================================================
    # BASELINE
    # ========================================================

    baseline = (
        _build_position(
            date_of_birth=(
                date_of_birth
            ),

            retirement_date=(
                retirement_date
            ),

            retirement_age=(
                retirement_age
            ),

            contribution_months=(
                current_contribution_months
            ),

            annual_salary=(
                current_annual_salary
            ),

            continuity_ratio=(
                continuity_ratio
            ),
        )
    )


    # ========================================================
    # SCENARIO
    # ========================================================

    scenario = (
        _build_position(
            date_of_birth=(
                date_of_birth
            ),

            retirement_date=(
                retirement_date
            ),

            retirement_age=(
                retirement_age
            ),

            contribution_months=(
                scenario_contribution_months
            ),

            annual_salary=(
                projected_annual_salary
            ),

            continuity_ratio=(
                continuity_ratio
            ),
        )
    )


    # ========================================================
    # PENSION-RIGHT CHANGE
    # ========================================================

    if (
        baseline.pension_right
        is not None
        and
        scenario.pension_right
        is not None
    ):

        pension_right_change = (
            _round_two(
                (
                    scenario.pension_right
                    -
                    baseline.pension_right
                )
                *
                D("100")
            )
        )

    else:

        pension_right_change = None


    # ========================================================
    # MONTHLY PENSION CHANGE
    # ========================================================

    if (
        baseline.monthly_pension
        is not None
        and
        scenario.monthly_pension
        is not None
    ):

        monthly_pension_change = (
            _round_two(
                scenario.monthly_pension
                -
                baseline.monthly_pension
            )
        )

    else:

        monthly_pension_change = None


    # ========================================================
    # MONTHLY PENSION % CHANGE
    # ========================================================

    if (
        monthly_pension_change
        is not None
        and
        baseline.monthly_pension
        is not None
        and
        baseline.monthly_pension
        >
        0
    ):

        monthly_pension_change_percent = (
            _round_two(
                (
                    monthly_pension_change
                    /
                    baseline.monthly_pension
                )
                *
                D("100")
            )
        )

    else:

        monthly_pension_change_percent = None


    # ========================================================
    # READINESS CHANGE
    # ========================================================

    if (
        baseline.readiness_score
        is not None
        and
        scenario.readiness_score
        is not None
    ):

        readiness_score_change = (
            _round_two(
                scenario.readiness_score
                -
                baseline.readiness_score
            )
        )

    else:

        readiness_score_change = None


    # ========================================================
    # ELIGIBILITY TRANSITION
    # ========================================================

    became_monthly_pension_eligible = (
        baseline.monthly_pension
        is None
        and
        scenario.monthly_pension
        is not None
    )


    # ========================================================
    # CONTINUITY ASSUMPTION
    # ========================================================

    if continuity_ratio is None:

        continuity_assumption = (
            "NOT_ASSESSED"
        )

    else:

        continuity_assumption = (
            "CURRENT_ASSESSED_CONTINUITY_HELD_CONSTANT"
        )


    return RetirementScenarioResult(

        baseline=baseline,

        scenario=scenario,

        additional_contribution_months=(
            additional_contribution_months
        ),

        available_contribution_months=(
            available_contribution_months
        ),

        pension_right_change_percentage_points=(
            pension_right_change
        ),

        monthly_pension_change=(
            monthly_pension_change
        ),

        monthly_pension_change_percent=(
            monthly_pension_change_percent
        ),

        readiness_score_change=(
            readiness_score_change
        ),

        became_monthly_pension_eligible=(
            became_monthly_pension_eligible
        ),

        continuity_assumption=(
            continuity_assumption
        ),
    )