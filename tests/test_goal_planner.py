from datetime import date
from decimal import Decimal


import pytest


from ssnit_engine.goal_planner import (
    GOAL_ACHIEVABLE,
    GOAL_ALREADY_ACHIEVABLE,
    GOAL_MONTHLY_PENSION_THRESHOLD_UNREACHABLE,
    GOAL_NOT_ACHIEVABLE_WITH_PROJECTED_SALARY,
    calculate_retirement_goal,
)


D = Decimal


# ============================================================
# ALREADY ACHIEVABLE
# ============================================================


def test_goal_already_achievable():

    result = calculate_retirement_goal(

        date_of_birth=(
            date(
                1972,
                8,
                20,
            )
        ),

        current_contribution_months=240,

        target_monthly_pension=(
            D("3000")
        ),

        projected_annual_salary=(
            D("90000")
        ),

        retirement_age=60,

        valuation_date=(
            date(
                2026,
                8,
                28,
            )
        ),
    )


    assert (
        result.goal_achievable
        is True
    )


    assert (
        result.goal_status
        ==
        GOAL_ALREADY_ACHIEVABLE
    )


    assert (
        result.current_projected_monthly_pension
        ==
        D("3234.38")
    )


    assert (
        result.required_contribution_months
        ==
        240
    )


    assert (
        result.additional_contribution_months_required
        ==
        0
    )


# ============================================================
# FIND MINIMUM REQUIRED CONTRIBUTION MONTHS
# ============================================================


def test_goal_finds_minimum_required_months():

    result = calculate_retirement_goal(

        date_of_birth=(
            date(
                1972,
                8,
                20,
            )
        ),

        current_contribution_months=240,

        target_monthly_pension=(
            D("3500")
        ),

        projected_annual_salary=(
            D("90000")
        ),

        retirement_age=60,

        valuation_date=(
            date(
                2026,
                8,
                28,
            )
        ),
    )


    assert (
        result.goal_status
        ==
        GOAL_ACHIEVABLE
    )


    assert (
        result.goal_achievable
        is True
    )


    assert (
        result.required_contribution_months
        ==
        278
    )


    assert (
        result.additional_contribution_months_required
        ==
        38
    )


    assert (
        result
        .estimated_monthly_pension_at_required_months
        ==
        D("3501.56")
    )


    assert (
        result
        .pension_right_at_required_months
        ==
        D("0.4668750")
    )


    assert (
        result.available_contribution_months
        ==
        71
    )


# ============================================================
# EARLY RETIREMENT FACTOR
# ============================================================


def test_goal_respects_age_57_reduction_factor():

    result = calculate_retirement_goal(

        date_of_birth=(
            date(
                1972,
                8,
                20,
            )
        ),

        current_contribution_months=180,

        target_monthly_pension=(
            D("3000")
        ),

        projected_annual_salary=(
            D("120000")
        ),

        retirement_age=57,

        valuation_date=(
            date(
                2026,
                8,
                28,
            )
        ),
    )


    assert (
        result.goal_status
        ==
        GOAL_ACHIEVABLE
    )


    assert (
        result.required_contribution_months
        ==
        207
    )


    assert (
        result.additional_contribution_months_required
        ==
        27
    )


    assert (
        result.retirement_age_factor
        ==
        D("0.750")
    )


    assert (
        result
        .estimated_monthly_pension_at_required_months
        ==
        D("3002.34")
    )


# ============================================================
# PROJECTED SALARY TOO LOW
# ============================================================


def test_goal_detects_when_projected_salary_is_too_low():

    result = calculate_retirement_goal(

        date_of_birth=(
            date(
                1990,
                4,
                16,
            )
        ),

        current_contribution_months=240,

        target_monthly_pension=(
            D("4000")
        ),

        projected_annual_salary=(
            D("60000")
        ),

        retirement_age=60,

        valuation_date=(
            date(
                2026,
                8,
                29,
            )
        ),
    )


    assert (
        result.goal_achievable
        is False
    )


    assert (
        result.goal_status
        ==
        GOAL_NOT_ACHIEVABLE_WITH_PROJECTED_SALARY
    )


    assert (
        result.available_contribution_months
        ==
        283
    )


    assert (
        result.maximum_attainable_contribution_months
        ==
        523
    )


    # Pension right is already capped at 60%
    # even though actual contribution history
    # can exceed 420 months.

    assert (
        result.maximum_attainable_pension_right
        ==
        D("0.60")
    )


    assert (
        result.maximum_attainable_monthly_pension
        ==
        D("3000.00")
    )


    assert (
        result.pension_gap_at_maximum
        ==
        D("1000.00")
    )


    assert (
        result
        .approximate_annual_salary_required_at_maximum_months
        ==
        D("80000.00")
    )


# ============================================================
# NOT ENOUGH TIME TO REACH 180 MONTHS
# ============================================================


def test_goal_detects_unreachable_monthly_pension_threshold():

    result = calculate_retirement_goal(

        date_of_birth=(
            date(
                1971,
                9,
                1,
            )
        ),

        current_contribution_months=170,

        target_monthly_pension=(
            D("1000")
        ),

        projected_annual_salary=(
            D("120000")
        ),

        retirement_age=55,

        valuation_date=(
            date(
                2026,
                8,
                29,
            )
        ),
    )


    assert (
        result.goal_achievable
        is False
    )


    assert (
        result.goal_status
        ==
        GOAL_MONTHLY_PENSION_THRESHOLD_UNREACHABLE
    )


    assert (
        result.available_contribution_months
        ==
        0
    )


    assert (
        result.maximum_attainable_contribution_months
        ==
        170
    )


    assert (
        result.required_contribution_months
        is None
    )


    assert (
        result.maximum_attainable_monthly_pension
        is None
    )


    assert (
        result
        .approximate_annual_salary_required_at_maximum_months
        is None
    )


# ============================================================
# INVALID TARGET
# ============================================================


def test_goal_rejects_zero_target():

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):

        calculate_retirement_goal(

            date_of_birth=(
                date(
                    1990,
                    4,
                    16,
                )
            ),

            current_contribution_months=240,

            target_monthly_pension=(
                D("0")
            ),

            projected_annual_salary=(
                D("90000")
            ),

            retirement_age=60,

            valuation_date=(
                date(
                    2026,
                    8,
                    29,
                )
            ),
        )


# ============================================================
# INVALID RETIREMENT AGE
# ============================================================


def test_goal_rejects_invalid_retirement_age():

    with pytest.raises(
        ValueError,
        match="between 55 and 60",
    ):

        calculate_retirement_goal(

            date_of_birth=(
                date(
                    1990,
                    4,
                    16,
                )
            ),

            current_contribution_months=240,

            target_monthly_pension=(
                D("4000")
            ),

            projected_annual_salary=(
                D("90000")
            ),

            retirement_age=61,

            valuation_date=(
                date(
                    2026,
                    8,
                    29,
                )
            ),
        )