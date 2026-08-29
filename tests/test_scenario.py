from datetime import date
from decimal import Decimal


import pytest


from ssnit_engine.scenario import (
    calculate_retirement_scenario,
    full_months_between,
    retirement_date_for_age,
)


D = Decimal


# ============================================================
# DATE HELPERS
# ============================================================


def test_retirement_date_for_age():

    result = retirement_date_for_age(
        date(1972, 8, 20),
        60,
    )

    assert result == date(
        2032,
        8,
        20,
    )


def test_full_months_between():

    result = full_months_between(
        date(2026, 8, 28),
        date(2032, 8, 20),
    )

    assert result == 71


# ============================================================
# BASIC AGE-60 SCENARIO
# ============================================================


def test_retirement_scenario_age_60():

    result = (
        calculate_retirement_scenario(

            date_of_birth=(
                date(
                    1972,
                    8,
                    20,
                )
            ),

            current_contribution_months=240,

            current_annual_salary=(
                D("72000")
            ),

            additional_contribution_months=60,

            projected_annual_salary=(
                D("90000")
            ),

            retirement_age=60,

            continuity_ratio=(
                D("0.92")
            ),

            valuation_date=(
                date(
                    2026,
                    8,
                    28,
                )
            ),
        )
    )


    assert (
        result.baseline
        .contribution_months
        ==
        240
    )


    assert (
        result.scenario
        .contribution_months
        ==
        300
    )


    assert (
        result.baseline
        .pension_right
        ==
        D("0.4312500")
    )


    assert (
        result.scenario
        .pension_right
        ==
        D("0.4875000")
    )


    assert (
        result.baseline
        .monthly_pension
        ==
        D("2587.50")
    )


    assert (
        result.scenario
        .monthly_pension
        ==
        D("3656.25")
    )


    assert (
        result
        .monthly_pension_change
        ==
        D("1068.75")
    )


    assert (
        result
        .monthly_pension_change_percent
        ==
        D("41.30")
    )


    assert (
        result
        .pension_right_change_percentage_points
        ==
        D("5.63")
    )


    assert (
        result.baseline
        .readiness_score
        ==
        D("71.75")
    )


    assert (
        result.scenario
        .readiness_score
        ==
        D("80.50")
    )


    assert (
        result
        .readiness_score_change
        ==
        D("8.75")
    )


    assert (
        result.scenario
        .readiness_rating
        ==
        "Good"
    )


    assert (
        result
        .continuity_assumption
        ==
        "CURRENT_ASSESSED_CONTINUITY_HELD_CONSTANT"
    )


# ============================================================
# EARLY RETIREMENT
# ============================================================


def test_retirement_scenario_age_57_uses_reduction():

    result = (
        calculate_retirement_scenario(

            date_of_birth=(
                date(
                    1972,
                    8,
                    20,
                )
            ),

            current_contribution_months=240,

            current_annual_salary=(
                D("72000")
            ),

            additional_contribution_months=12,

            projected_annual_salary=(
                D("72000")
            ),

            retirement_age=57,

            continuity_ratio=(
                D("1")
            ),

            valuation_date=(
                date(
                    2026,
                    8,
                    28,
                )
            ),
        )
    )


    assert (
        result.baseline
        .retirement_age_factor
        ==
        D("0.750")
    )


    assert (
        result.baseline
        .monthly_pension
        ==
        D("1940.63")
    )


    assert (
        result.scenario
        .monthly_pension
        ==
        D("1991.25")
    )


# ============================================================
# DATA-LIMIT VALIDATION
# ============================================================


def test_scenario_rejects_too_many_future_months():

    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):

        calculate_retirement_scenario(

            date_of_birth=(
                date(
                    1972,
                    8,
                    20,
                )
            ),

            current_contribution_months=240,

            current_annual_salary=(
                D("72000")
            ),

            additional_contribution_months=36,

            projected_annual_salary=(
                D("80000")
            ),

            retirement_age=57,

            continuity_ratio=(
                D("1")
            ),

            valuation_date=(
                date(
                    2026,
                    8,
                    28,
                )
            ),
        )


# ============================================================
# PROVISIONAL READINESS
# ============================================================


def test_scenario_readiness_incomplete_without_continuity():

    result = (
        calculate_retirement_scenario(

            date_of_birth=(
                date(
                    1972,
                    8,
                    20,
                )
            ),

            current_contribution_months=240,

            current_annual_salary=(
                D("72000")
            ),

            additional_contribution_months=24,

            projected_annual_salary=(
                D("80000")
            ),

            retirement_age=60,

            continuity_ratio=None,

            valuation_date=(
                date(
                    2026,
                    8,
                    28,
                )
            ),
        )
    )


    assert (
        result.baseline
        .readiness_score
        is None
    )


    assert (
        result.scenario
        .readiness_score
        is None
    )


    assert (
        result.baseline
        .readiness_rating
        ==
        "Incomplete"
    )


    assert (
        result.scenario
        .readiness_rating
        ==
        "Incomplete"
    )


    assert (
        result
        .readiness_score_change
        is None
    )


    assert (
        result
        .continuity_assumption
        ==
        "NOT_ASSESSED"
    )


# ============================================================
# ELIGIBILITY TRANSITION
# ============================================================


def test_scenario_can_cross_180_month_threshold():

    result = (
        calculate_retirement_scenario(

            date_of_birth=(
                date(
                    1972,
                    8,
                    20,
                )
            ),

            current_contribution_months=170,

            current_annual_salary=(
                D("72000")
            ),

            additional_contribution_months=12,

            projected_annual_salary=(
                D("72000")
            ),

            retirement_age=60,

            continuity_ratio=(
                D("1")
            ),

            valuation_date=(
                date(
                    2026,
                    8,
                    28,
                )
            ),
        )
    )


    assert (
        result.baseline
        .monthly_pension
        is None
    )


    assert (
        result.scenario
        .contribution_months
        ==
        182
    )


    assert (
        result.scenario
        .pension_right
        ==
        D("0.3768750")
    )


    assert (
        result.scenario
        .monthly_pension
        ==
        D("2261.25")
    )


    assert (
        result
        .became_monthly_pension_eligible
        is True
    )