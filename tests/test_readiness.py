from decimal import Decimal

import pytest

from ssnit_engine.readiness import (
    RetirementReadinessResult,
    _readiness_rating,
    calculate_retirement_readiness,
)


# ============================================================
# BASIC READINESS CALCULATIONS
# ============================================================


def test_zero_contribution_months():

    result = calculate_retirement_readiness(
        contribution_months=0,
        continuity_ratio=Decimal("0"),
    )

    assert isinstance(
        result,
        RetirementReadinessResult,
    )

    assert result.contribution_months == 0

    assert result.pension_right is None

    assert (
        result.eligibility_score
        ==
        Decimal("0.00")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("0.00")
    )

    assert (
        result.consistency_score
        ==
        Decimal("0.00")
    )

    assert (
        result.total_score
        ==
        Decimal("0.00")
    )

    assert (
        result.rating
        ==
        "Needs Attention"
    )

    assert result.provisional is False

    assert result.months_to_minimum == 180

    assert result.months_to_maximum == 420


def test_179_contribution_months():

    result = calculate_retirement_readiness(
        contribution_months=179,
        continuity_ratio=Decimal("1"),
    )

    assert result.pension_right is None

    assert (
        result.eligibility_score
        ==
        Decimal("39.78")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("0.00")
    )

    assert (
        result.consistency_score
        ==
        Decimal("25.00")
    )

    assert (
        result.total_score
        ==
        Decimal("64.78")
    )

    assert result.rating == "Building"

    assert result.months_to_minimum == 1

    assert result.months_to_maximum == 241


def test_180_contribution_months():

    result = calculate_retirement_readiness(
        contribution_months=180,
        continuity_ratio=Decimal("1"),
    )

    assert (
        result.pension_right
        ==
        Decimal("0.375")
    )

    assert (
        result.eligibility_score
        ==
        Decimal("40.00")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("0.00")
    )

    assert (
        result.consistency_score
        ==
        Decimal("25.00")
    )

    assert (
        result.total_score
        ==
        Decimal("65.00")
    )

    assert result.rating == "Fair"

    assert result.months_to_minimum == 0

    assert result.months_to_maximum == 240


def test_240_contribution_months():

    result = calculate_retirement_readiness(
        contribution_months=240,
        continuity_ratio=Decimal("0.92"),
    )

    assert (
        result.pension_right
        ==
        Decimal("0.4312500")
    )

    assert (
        result.eligibility_score
        ==
        Decimal("40.00")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("8.75")
    )

    assert (
        result.consistency_score
        ==
        Decimal("23.00")
    )

    assert (
        result.total_score
        ==
        Decimal("71.75")
    )

    assert result.rating == "Fair"

    assert result.provisional is False

    assert result.months_to_minimum == 0

    assert result.months_to_maximum == 180


def test_420_contribution_months():

    result = calculate_retirement_readiness(
        contribution_months=420,
        continuity_ratio=Decimal("1"),
    )

    assert (
        result.pension_right
        ==
        Decimal("0.60")
    )

    assert (
        result.eligibility_score
        ==
        Decimal("40.00")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("35.00")
    )

    assert (
        result.consistency_score
        ==
        Decimal("25.00")
    )

    assert (
        result.total_score
        ==
        Decimal("100.00")
    )

    assert result.rating == "Strong"

    assert result.months_to_minimum == 0

    assert result.months_to_maximum == 0


def test_more_than_420_contribution_months():

    result = calculate_retirement_readiness(
        contribution_months=500,
        continuity_ratio=Decimal("1"),
    )

    assert (
        result.pension_right
        ==
        Decimal("0.60")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("35.00")
    )

    assert (
        result.total_score
        ==
        Decimal("100.00")
    )

    assert result.rating == "Strong"

    assert result.months_to_maximum == 0


# ============================================================
# CONTRIBUTION CONSISTENCY
# ============================================================


def test_zero_percent_continuity():

    result = calculate_retirement_readiness(
        contribution_months=240,
        continuity_ratio=Decimal("0"),
    )

    assert (
        result.consistency_score
        ==
        Decimal("0.00")
    )

    assert (
        result.total_score
        ==
        Decimal("48.75")
    )

    assert result.rating == "Building"


def test_full_continuity():

    result = calculate_retirement_readiness(
        contribution_months=240,
        continuity_ratio=Decimal("1"),
    )

    assert (
        result.consistency_score
        ==
        Decimal("25.00")
    )

    assert (
        result.total_score
        ==
        Decimal("73.75")
    )

    assert result.rating == "Fair"


# ============================================================
# MISSING CONTRIBUTION HISTORY
# ============================================================


def test_missing_contribution_history_is_provisional():

    result = calculate_retirement_readiness(
        contribution_months=240,
        continuity_ratio=None,
    )

    assert (
        result.eligibility_score
        ==
        Decimal("40.00")
    )

    assert (
        result.pension_right_score
        ==
        Decimal("8.75")
    )

    assert result.consistency_score is None

    assert result.total_score is None

    assert result.rating == "Incomplete"

    assert result.provisional is True

    assert any(
        "contribution history"
        in recommendation.lower()
        for recommendation
        in result.recommendations
    )


# ============================================================
# VALIDATION
# ============================================================


def test_negative_contribution_months_rejected():

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):

        calculate_retirement_readiness(
            contribution_months=-1,
            continuity_ratio=Decimal("1"),
        )


def test_negative_continuity_ratio_rejected():

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):

        calculate_retirement_readiness(
            contribution_months=240,
            continuity_ratio=Decimal("-0.01"),
        )


def test_continuity_ratio_above_one_rejected():

    with pytest.raises(
        ValueError,
        match="between 0 and 1",
    ):

        calculate_retirement_readiness(
            contribution_months=240,
            continuity_ratio=Decimal("1.01"),
        )


# ============================================================
# SCORE RATING BOUNDARIES
# ============================================================


@pytest.mark.parametrize(
    (
        "score",
        "expected_rating",
    ),
    [
        (
            Decimal("0"),
            "Needs Attention",
        ),
        (
            Decimal("39.99"),
            "Needs Attention",
        ),
        (
            Decimal("40"),
            "Building",
        ),
        (
            Decimal("59.99"),
            "Building",
        ),
        (
            Decimal("60"),
            "Fair",
        ),
        (
            Decimal("74.99"),
            "Fair",
        ),
        (
            Decimal("75"),
            "Good",
        ),
        (
            Decimal("89.99"),
            "Good",
        ),
        (
            Decimal("90"),
            "Strong",
        ),
        (
            Decimal("100"),
            "Strong",
        ),
    ],
)
def test_readiness_rating_boundaries(
    score,
    expected_rating,
):

    assert (
        _readiness_rating(score)
        ==
        expected_rating
    )


def test_missing_score_rating():

    assert (
        _readiness_rating(None)
        ==
        "Incomplete"
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================


def test_below_minimum_recommendation():

    result = calculate_retirement_readiness(
        contribution_months=156,
        continuity_ratio=Decimal("0.90"),
    )

    assert result.months_to_minimum == 24

    assert any(
        "24 additional"
        in recommendation
        for recommendation
        in result.recommendations
    )


def test_maximum_pension_right_recommendation():

    result = calculate_retirement_readiness(
        contribution_months=420,
        continuity_ratio=Decimal("1"),
    )

    assert any(
        "420-month"
        in recommendation
        and
        "60%"
        in recommendation
        for recommendation
        in result.recommendations
    )


def test_low_continuity_recommendation():

    result = calculate_retirement_readiness(
        contribution_months=240,
        continuity_ratio=Decimal("0.60"),
    )

    assert any(
        "significant gaps"
        in recommendation.lower()
        for recommendation
        in result.recommendations
    )


def test_strong_continuity_recommendation():

    result = calculate_retirement_readiness(
        contribution_months=240,
        continuity_ratio=Decimal("0.98"),
    )

    assert any(
        "strong consistency"
        in recommendation.lower()
        for recommendation
        in result.recommendations
    )

def test_readiness_rating_capped_before_eligibility():

    result = calculate_retirement_readiness(
        contribution_months=179,
        continuity_ratio=Decimal("1"),
    )

    assert (
        result.total_score
        ==
        Decimal("64.78")
    )

    assert result.rating == "Building"


def test_readiness_rating_cap_removed_at_180_months():

    result = calculate_retirement_readiness(
        contribution_months=180,
        continuity_ratio=Decimal("1"),
    )

    assert (
        result.total_score
        ==
        Decimal("65.00")
    )

    assert result.rating == "Fair"    