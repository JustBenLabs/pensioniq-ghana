from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from ssnit_engine.engine import calculate_pension_right


D = Decimal


MINIMUM_PENSION_MONTHS = 180
MAXIMUM_PENSION_RIGHT_MONTHS = 420

ELIGIBILITY_WEIGHT = D("40")
PENSION_RIGHT_WEIGHT = D("35")
CONSISTENCY_WEIGHT = D("25")

MINIMUM_PENSION_RIGHT = D("0.375")
MAXIMUM_PENSION_RIGHT = D("0.60")


@dataclass(frozen=True)
class RetirementReadinessResult:
    contribution_months: int

    pension_right: Optional[Decimal]

    eligibility_score: Decimal
    pension_right_score: Decimal
    consistency_score: Optional[Decimal]

    total_score: Optional[Decimal]
    rating: str
    provisional: bool

    months_to_minimum: int
    months_to_maximum: int

    recommendations: tuple[str, ...]


def _round_score(value: Decimal) -> Decimal:
    return value.quantize(
        D("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _readiness_rating(
    score: Optional[Decimal],
) -> str:

    if score is None:
        return "Incomplete"

    if score < D("40"):
        return "Needs Attention"

    if score < D("60"):
        return "Building"

    if score < D("75"):
        return "Fair"

    if score < D("90"):
        return "Good"

    return "Strong"

def _apply_eligibility_rating_cap(
    rating: str,
    contribution_months: int,
) -> str:
    """
    Prevent a member who has not yet reached the
    minimum 180-month contribution threshold from
    receiving a readiness rating above Building.

    The numerical readiness score is preserved.
    """

    if (
        contribution_months
        <
        MINIMUM_PENSION_MONTHS
        and
        rating in {
            "Fair",
            "Good",
            "Strong",
        }
    ):
        return "Building"

    return rating

def _build_recommendations(
    contribution_months: int,
    continuity_ratio: Optional[Decimal],
) -> tuple[str, ...]:

    recommendations: list[str] = []

    # ---------------------------------------------------------
    # Minimum pension contribution threshold
    # ---------------------------------------------------------

    if contribution_months < MINIMUM_PENSION_MONTHS:

        remaining = (
            MINIMUM_PENSION_MONTHS
            - contribution_months
        )

        recommendations.append(
            (
                f"You need {remaining} additional "
                "qualifying contribution months to reach "
                "the 180-month minimum contribution "
                "threshold used by the PensionIQ "
                "old-age pension model."
            )
        )

    else:

        recommendations.append(
            (
                "You have reached the minimum "
                "180-month contribution threshold "
                "used for an ordinary monthly "
                "old-age pension estimate."
            )
        )

    # ---------------------------------------------------------
    # Maximum pension-right progress
    # ---------------------------------------------------------

    if (
        contribution_months
        >=
        MAXIMUM_PENSION_RIGHT_MONTHS
    ):

        recommendations.append(
            (
                "You have reached the 420-month level "
                "at which PensionIQ's configured "
                "pension-right formula reaches the "
                "60% maximum."
            )
        )

    elif contribution_months >= MINIMUM_PENSION_MONTHS:

        remaining = (
            MAXIMUM_PENSION_RIGHT_MONTHS
            - contribution_months
        )

        recommendations.append(
            (
                f"You are {remaining} contribution "
                "months away from the 420-month "
                "maximum pension-right level. "
                "Additional qualifying contributions "
                "can continue increasing your pension "
                "right until the maximum is reached."
            )
        )

    # ---------------------------------------------------------
    # Contribution consistency
    # ---------------------------------------------------------

    if continuity_ratio is None:

        recommendations.append(
            (
                "Add or import your detailed "
                "contribution history so PensionIQ "
                "can assess contribution consistency "
                "and complete your readiness score."
            )
        )

    elif continuity_ratio < D("0.80"):

        recommendations.append(
            (
                "Your contribution history indicates "
                "significant gaps. Review missing or "
                "irregular contribution periods and "
                "verify them against your official "
                "SSNIT records."
            )
        )

    elif continuity_ratio < D("0.95"):

        recommendations.append(
            (
                "Your contribution consistency is "
                "generally healthy, but some gaps may "
                "still exist. Maintaining regular "
                "contributions can strengthen your "
                "retirement position."
            )
        )

    else:

        recommendations.append(
            (
                "Your recorded contribution history "
                "shows strong consistency. Continue "
                "maintaining regular contributions."
            )
        )

    return tuple(recommendations)


def calculate_retirement_readiness(
    contribution_months: int,
    continuity_ratio: Optional[Decimal] = None,
) -> RetirementReadinessResult:
    """
    Calculate the PensionIQ Retirement Readiness Indicator.

    This is a PensionIQ retirement-planning diagnostic.
    It is not an official SSNIT score or determination.

    Score components:

        Contribution eligibility progress: 40 points
        Pension-right progress:            35 points
        Contribution consistency:          25 points

        Maximum:                           100 points

    If contribution consistency cannot be assessed because
    detailed contribution history is unavailable, the final
    score is intentionally left incomplete rather than
    treating missing data as poor contribution behaviour.
    """

    if contribution_months < 0:
        raise ValueError(
            "Contribution months cannot be negative."
        )

    if continuity_ratio is not None:

        continuity_ratio = D(
            str(continuity_ratio)
        )

        if not (
            D("0")
            <= continuity_ratio
            <= D("1")
        ):
            raise ValueError(
                "Continuity ratio must be between 0 and 1."
            )

    # =========================================================
    # 1. CONTRIBUTION ELIGIBILITY SCORE
    # =========================================================

    eligibility_progress = min(
        D(contribution_months)
        /
        D(MINIMUM_PENSION_MONTHS),
        D("1"),
    )

    eligibility_score = _round_score(
        eligibility_progress
        *
        ELIGIBILITY_WEIGHT
    )

    # =========================================================
    # 2. PENSION-RIGHT SCORE
    # =========================================================

    pension_right = calculate_pension_right(
        contribution_months
    )

    if pension_right is None:

        pension_right_score = D("0.00")

    else:

        pension_progress = (
            pension_right
            -
            MINIMUM_PENSION_RIGHT
        ) / (
            MAXIMUM_PENSION_RIGHT
            -
            MINIMUM_PENSION_RIGHT
        )

        pension_progress = max(
            D("0"),
            min(
                pension_progress,
                D("1"),
            ),
        )

        pension_right_score = _round_score(
            pension_progress
            *
            PENSION_RIGHT_WEIGHT
        )

    # =========================================================
    # 3. CONTRIBUTION CONSISTENCY SCORE
    # =========================================================

    if continuity_ratio is None:

        consistency_score = None
        total_score = None
        provisional = True

    else:

        consistency_score = _round_score(
            continuity_ratio
            *
            CONSISTENCY_WEIGHT
        )

        total_score = _round_score(
            eligibility_score
            +
            pension_right_score
            +
            consistency_score
        )

        provisional = False

    # =========================================================
    # STATUS
    # =========================================================

    rating = _readiness_rating(
        total_score
    )

    rating = _apply_eligibility_rating_cap(
        rating,
        contribution_months,
    )

    months_to_minimum = max(
        0,
        MINIMUM_PENSION_MONTHS
        -
        contribution_months,
    )

    months_to_maximum = max(
        0,
        MAXIMUM_PENSION_RIGHT_MONTHS
        -
        contribution_months,
    )

    recommendations = _build_recommendations(
        contribution_months,
        continuity_ratio,
    )

    return RetirementReadinessResult(
        contribution_months=contribution_months,
        pension_right=pension_right,
        eligibility_score=eligibility_score,
        pension_right_score=pension_right_score,
        consistency_score=consistency_score,
        total_score=total_score,
        rating=rating,
        provisional=provisional,
        months_to_minimum=months_to_minimum,
        months_to_maximum=months_to_maximum,
        recommendations=recommendations,
    )