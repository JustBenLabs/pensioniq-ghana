from dataclasses import dataclass
from datetime import date
from decimal import (
    Decimal,
    ROUND_CEILING,
    ROUND_HALF_UP,
)
from typing import Optional


from ssnit_engine.engine import (
    BenefitEvent,
    calculate_master_benefit,
    calculate_pension_right,
)

from ssnit_engine.scenario import (
    full_months_between,
    retirement_date_for_age,
)


D = Decimal


# ============================================================
# GOAL STATUS
# ============================================================


GOAL_ALREADY_ACHIEVABLE = (
    "ALREADY_ACHIEVABLE"
)

GOAL_ACHIEVABLE = (
    "ACHIEVABLE"
)

GOAL_NOT_ACHIEVABLE_WITH_PROJECTED_SALARY = (
    "NOT_ACHIEVABLE_WITH_PROJECTED_SALARY"
)

GOAL_MONTHLY_PENSION_THRESHOLD_UNREACHABLE = (
    "MONTHLY_PENSION_THRESHOLD_UNREACHABLE"
)


# ============================================================
# RESULT MODEL
# ============================================================


@dataclass(frozen=True)
class RetirementGoalResult:

    target_monthly_pension: Decimal

    projected_annual_salary: Decimal

    retirement_age: int

    retirement_date: date

    current_contribution_months: int

    available_contribution_months: int

    maximum_attainable_contribution_months: int

    current_projected_monthly_pension: Optional[Decimal]

    required_contribution_months: Optional[int]

    additional_contribution_months_required: Optional[int]

    estimated_monthly_pension_at_required_months: Optional[Decimal]

    pension_right_at_required_months: Optional[Decimal]

    maximum_attainable_monthly_pension: Optional[Decimal]

    maximum_attainable_pension_right: Optional[Decimal]

    retirement_age_factor: Optional[Decimal]

    pension_gap_at_maximum: Decimal

    approximate_annual_salary_required_at_maximum_months: Optional[Decimal]

    goal_achievable: bool

    goal_status: str


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
# ENGINE CALL
# ============================================================


def _calculate_retirement_result(
    *,
    date_of_birth: date,
    retirement_date: date,
    contribution_months: int,
    annual_salary: Decimal,
):

    """
    Ask the existing PensionIQ master benefit engine
    to calculate the retirement result.

    No pension formula is duplicated here.
    """

    return calculate_master_benefit(

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


# ============================================================
# RETIREMENT FACTOR
# ============================================================


def _extract_retirement_factor(
    benefit_result,
) -> Optional[Decimal]:

    if not isinstance(
        benefit_result.details,
        dict,
    ):

        return None


    return (
        benefit_result
        .details
        .get(
            "reduction_factor"
        )
    )


# ============================================================
# MINIMUM CONTRIBUTION MONTH SEARCH
# ============================================================


def _find_required_contribution_months(
    *,
    date_of_birth: date,
    retirement_date: date,
    current_contribution_months: int,
    maximum_contribution_months: int,
    annual_salary: Decimal,
    target_monthly_pension: Decimal,
) -> Optional[int]:

    """
    Find the smallest contribution-month total
    at or above the member's current total that
    satisfies the requested pension target.

    The existing retirement engine is called
    for every candidate month.
    """

    starting_month = max(
        current_contribution_months,
        180,
    )


    for contribution_months in range(
        starting_month,
        maximum_contribution_months + 1,
    ):

        benefit_result = (
            _calculate_retirement_result(

                date_of_birth=(
                    date_of_birth
                ),

                retirement_date=(
                    retirement_date
                ),

                contribution_months=(
                    contribution_months
                ),

                annual_salary=(
                    annual_salary
                ),
            )
        )


        monthly_pension = (
            benefit_result
            .monthly_benefit
        )


        if (
            monthly_pension
            is not None
            and
            monthly_pension
            >=
            target_monthly_pension
        ):

            return contribution_months


    return None


# ============================================================
# APPROXIMATE SALARY SEARCH
# ============================================================


def _find_approximate_required_annual_salary(
    *,
    date_of_birth: date,
    retirement_date: date,
    contribution_months: int,
    target_monthly_pension: Decimal,
    starting_annual_salary: Decimal,
) -> Optional[Decimal]:

    """
    Find an approximate whole-Ghana-cedi annual salary
    basis that would produce the target monthly pension
    at the supplied contribution-month total.

    This is intentionally found by repeatedly calling
    the existing pension engine rather than solving a
    second copy of the pension formula algebraically.
    """


    if contribution_months < 180:

        return None


    # --------------------------------------------------------
    # INITIAL UPPER BOUND
    # --------------------------------------------------------

    high = max(
        1,
        int(
            starting_annual_salary
            .to_integral_value(
                rounding=ROUND_CEILING
            )
        ),
    )


    # --------------------------------------------------------
    # EXPAND UPPER BOUND
    # --------------------------------------------------------

    while True:

        result = (
            _calculate_retirement_result(

                date_of_birth=(
                    date_of_birth
                ),

                retirement_date=(
                    retirement_date
                ),

                contribution_months=(
                    contribution_months
                ),

                annual_salary=(
                    D(high)
                ),
            )
        )


        monthly_pension = (
            result.monthly_benefit
        )


        if (
            monthly_pension
            is not None
            and
            monthly_pension
            >=
            target_monthly_pension
        ):

            break


        high *= 2


        if high > 10_000_000_000:

            raise RuntimeError(
                "Unable to determine a reasonable "
                "salary search range for this goal."
            )


    # --------------------------------------------------------
    # BINARY SEARCH
    # --------------------------------------------------------

    low = 0


    while low < high:

        midpoint = (
            low
            +
            high
        ) // 2


        result = (
            _calculate_retirement_result(

                date_of_birth=(
                    date_of_birth
                ),

                retirement_date=(
                    retirement_date
                ),

                contribution_months=(
                    contribution_months
                ),

                annual_salary=(
                    D(midpoint)
                ),
            )
        )


        monthly_pension = (
            result.monthly_benefit
        )


        if (
            monthly_pension
            is not None
            and
            monthly_pension
            >=
            target_monthly_pension
        ):

            high = midpoint

        else:

            low = midpoint + 1


    return (
        D(low)
        .quantize(
            D("0.01")
        )
    )


# ============================================================
# RETIREMENT GOAL PLANNER
# ============================================================


def calculate_retirement_goal(
    *,
    date_of_birth: date,
    current_contribution_months: int,
    target_monthly_pension: Decimal,
    projected_annual_salary: Decimal,
    retirement_age: int,
    valuation_date: Optional[date] = None,
) -> RetirementGoalResult:

    """
    PensionIQ Retirement Goal Planner.

    Determines whether a requested monthly pension
    target can be reached by the selected retirement
    age using the supplied projected annual salary.

    Where achievable, the function finds the smallest
    contribution-month total required.

    Where the target cannot be achieved with the
    supplied salary, PensionIQ estimates the annual
    salary basis that would be required at the maximum
    attainable contribution-month total.

    This is a planning simulation and not an official
    SSNIT entitlement or benefit determination.
    """


    # ========================================================
    # NORMALISE DECIMALS
    # ========================================================

    target_monthly_pension = D(
        str(
            target_monthly_pension
        )
    )


    projected_annual_salary = D(
        str(
            projected_annual_salary
        )
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    if current_contribution_months < 0:

        raise ValueError(
            "Current contribution months "
            "cannot be negative."
        )


    if target_monthly_pension <= 0:

        raise ValueError(
            "Target monthly pension "
            "must be greater than zero."
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


    if retirement_date < valuation_date:

        raise ValueError(
            "The selected retirement age "
            "has already passed."
        )


    # ========================================================
    # CONTRIBUTION CAPACITY
    # ========================================================

    available_contribution_months = (
        full_months_between(
            valuation_date,
            retirement_date,
        )
    )


    # PensionIQ currently models contributions
    # from age 15 onward.

    maximum_possible_history = (
        retirement_age
        -
        15
    ) * 12


    if (
        current_contribution_months
        >
        maximum_possible_history
    ):

        raise ValueError(
            "Current contribution months exceed "
            "the maximum plausible contribution "
            "history for the selected retirement age."
        )


    maximum_attainable_contribution_months = (
        min(
            (
                current_contribution_months
                +
                available_contribution_months
            ),
            maximum_possible_history,
        )
    )


    # ========================================================
    # CURRENT CONTRIBUTION POSITION AT SELECTED RETIREMENT AGE
    # ========================================================

    current_result = (
        _calculate_retirement_result(

            date_of_birth=(
                date_of_birth
            ),

            retirement_date=(
                retirement_date
            ),

            contribution_months=(
                current_contribution_months
            ),

            annual_salary=(
                projected_annual_salary
            ),
        )
    )


    current_projected_monthly_pension = (
        current_result
        .monthly_benefit
    )


    # ========================================================
    # MAXIMUM ATTAINABLE POSITION
    # ========================================================

    maximum_result = (
        _calculate_retirement_result(

            date_of_birth=(
                date_of_birth
            ),

            retirement_date=(
                retirement_date
            ),

            contribution_months=(
                maximum_attainable_contribution_months
            ),

            annual_salary=(
                projected_annual_salary
            ),
        )
    )


    maximum_attainable_monthly_pension = (
        maximum_result
        .monthly_benefit
    )


    maximum_attainable_pension_right = (
        calculate_pension_right(
            maximum_attainable_contribution_months
        )
    )


    retirement_age_factor = (
        _extract_retirement_factor(
            maximum_result
        )
    )


    # ========================================================
    # IS GOAL ALREADY ACHIEVABLE?
    # ========================================================

    if (
        current_projected_monthly_pension
        is not None
        and
        current_projected_monthly_pension
        >=
        target_monthly_pension
    ):

        required_contribution_months = (
            current_contribution_months
        )


        additional_contribution_months_required = 0


        estimated_monthly_pension_at_required_months = (
            current_projected_monthly_pension
        )


        pension_right_at_required_months = (
            calculate_pension_right(
                current_contribution_months
            )
        )


        return RetirementGoalResult(

            target_monthly_pension=(
                _round_two(
                    target_monthly_pension
                )
            ),

            projected_annual_salary=(
                _round_two(
                    projected_annual_salary
                )
            ),

            retirement_age=(
                retirement_age
            ),

            retirement_date=(
                retirement_date
            ),

            current_contribution_months=(
                current_contribution_months
            ),

            available_contribution_months=(
                available_contribution_months
            ),

            maximum_attainable_contribution_months=(
                maximum_attainable_contribution_months
            ),

            current_projected_monthly_pension=(
                current_projected_monthly_pension
            ),

            required_contribution_months=(
                required_contribution_months
            ),

            additional_contribution_months_required=(
                additional_contribution_months_required
            ),

            estimated_monthly_pension_at_required_months=(
                estimated_monthly_pension_at_required_months
            ),

            pension_right_at_required_months=(
                pension_right_at_required_months
            ),

            maximum_attainable_monthly_pension=(
                maximum_attainable_monthly_pension
            ),

            maximum_attainable_pension_right=(
                maximum_attainable_pension_right
            ),

            retirement_age_factor=(
                retirement_age_factor
            ),

            pension_gap_at_maximum=(
                D("0.00")
            ),

            approximate_annual_salary_required_at_maximum_months=(
                None
            ),

            goal_achievable=True,

            goal_status=(
                GOAL_ALREADY_ACHIEVABLE
            ),
        )


    # ========================================================
    # FIND REQUIRED CONTRIBUTION MONTHS
    # ========================================================

    required_contribution_months = (
        _find_required_contribution_months(

            date_of_birth=(
                date_of_birth
            ),

            retirement_date=(
                retirement_date
            ),

            current_contribution_months=(
                current_contribution_months
            ),

            maximum_contribution_months=(
                maximum_attainable_contribution_months
            ),

            annual_salary=(
                projected_annual_salary
            ),

            target_monthly_pension=(
                target_monthly_pension
            ),
        )
    )


    # ========================================================
    # GOAL IS ACHIEVABLE
    # ========================================================

    if required_contribution_months is not None:

        required_result = (
            _calculate_retirement_result(

                date_of_birth=(
                    date_of_birth
                ),

                retirement_date=(
                    retirement_date
                ),

                contribution_months=(
                    required_contribution_months
                ),

                annual_salary=(
                    projected_annual_salary
                ),
            )
        )


        return RetirementGoalResult(

            target_monthly_pension=(
                _round_two(
                    target_monthly_pension
                )
            ),

            projected_annual_salary=(
                _round_two(
                    projected_annual_salary
                )
            ),

            retirement_age=(
                retirement_age
            ),

            retirement_date=(
                retirement_date
            ),

            current_contribution_months=(
                current_contribution_months
            ),

            available_contribution_months=(
                available_contribution_months
            ),

            maximum_attainable_contribution_months=(
                maximum_attainable_contribution_months
            ),

            current_projected_monthly_pension=(
                current_projected_monthly_pension
            ),

            required_contribution_months=(
                required_contribution_months
            ),

            additional_contribution_months_required=(
                required_contribution_months
                -
                current_contribution_months
            ),

            estimated_monthly_pension_at_required_months=(
                required_result
                .monthly_benefit
            ),

            pension_right_at_required_months=(
                calculate_pension_right(
                    required_contribution_months
                )
            ),

            maximum_attainable_monthly_pension=(
                maximum_attainable_monthly_pension
            ),

            maximum_attainable_pension_right=(
                maximum_attainable_pension_right
            ),

            retirement_age_factor=(
                _extract_retirement_factor(
                    required_result
                )
            ),

            pension_gap_at_maximum=(
                D("0.00")
            ),

            approximate_annual_salary_required_at_maximum_months=(
                None
            ),

            goal_achievable=True,

            goal_status=(
                GOAL_ACHIEVABLE
            ),
        )


    # ========================================================
    # MONTHLY-PENSION THRESHOLD CANNOT BE REACHED
    # ========================================================

    if (
        maximum_attainable_contribution_months
        <
        180
    ):

        return RetirementGoalResult(

            target_monthly_pension=(
                _round_two(
                    target_monthly_pension
                )
            ),

            projected_annual_salary=(
                _round_two(
                    projected_annual_salary
                )
            ),

            retirement_age=(
                retirement_age
            ),

            retirement_date=(
                retirement_date
            ),

            current_contribution_months=(
                current_contribution_months
            ),

            available_contribution_months=(
                available_contribution_months
            ),

            maximum_attainable_contribution_months=(
                maximum_attainable_contribution_months
            ),

            current_projected_monthly_pension=(
                current_projected_monthly_pension
            ),

            required_contribution_months=None,

            additional_contribution_months_required=None,

            estimated_monthly_pension_at_required_months=None,

            pension_right_at_required_months=None,

            maximum_attainable_monthly_pension=None,

            maximum_attainable_pension_right=None,

            retirement_age_factor=None,

            pension_gap_at_maximum=(
                _round_two(
                    target_monthly_pension
                )
            ),

            approximate_annual_salary_required_at_maximum_months=None,

            goal_achievable=False,

            goal_status=(
                GOAL_MONTHLY_PENSION_THRESHOLD_UNREACHABLE
            ),
        )


    # ========================================================
    # TARGET CANNOT BE MET WITH PROJECTED SALARY
    # ========================================================

    if maximum_attainable_monthly_pension is None:

        pension_gap_at_maximum = (
            target_monthly_pension
        )

    else:

        pension_gap_at_maximum = max(
            D("0"),
            (
                target_monthly_pension
                -
                maximum_attainable_monthly_pension
            ),
        )


    approximate_required_salary = (
        _find_approximate_required_annual_salary(

            date_of_birth=(
                date_of_birth
            ),

            retirement_date=(
                retirement_date
            ),

            contribution_months=(
                maximum_attainable_contribution_months
            ),

            target_monthly_pension=(
                target_monthly_pension
            ),

            starting_annual_salary=(
                projected_annual_salary
            ),
        )
    )


    return RetirementGoalResult(

        target_monthly_pension=(
            _round_two(
                target_monthly_pension
            )
        ),

        projected_annual_salary=(
            _round_two(
                projected_annual_salary
            )
        ),

        retirement_age=(
            retirement_age
        ),

        retirement_date=(
            retirement_date
        ),

        current_contribution_months=(
            current_contribution_months
        ),

        available_contribution_months=(
            available_contribution_months
        ),

        maximum_attainable_contribution_months=(
            maximum_attainable_contribution_months
        ),

        current_projected_monthly_pension=(
            current_projected_monthly_pension
        ),

        required_contribution_months=None,

        additional_contribution_months_required=None,

        estimated_monthly_pension_at_required_months=None,

        pension_right_at_required_months=None,

        maximum_attainable_monthly_pension=(
            maximum_attainable_monthly_pension
        ),

        maximum_attainable_pension_right=(
            maximum_attainable_pension_right
        ),

        retirement_age_factor=(
            retirement_age_factor
        ),

        pension_gap_at_maximum=(
            _round_two(
                pension_gap_at_maximum
            )
        ),

        approximate_annual_salary_required_at_maximum_months=(
            approximate_required_salary
        ),

        goal_achievable=False,

        goal_status=(
            GOAL_NOT_ACHIEVABLE_WITH_PROJECTED_SALARY
        ),
    )