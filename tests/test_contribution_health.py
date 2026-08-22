from decimal import Decimal
from types import SimpleNamespace

from ssnit_engine.contribution_health import (
    analyse_contribution_history,
    expected_first_tier_contribution,
)


def make_record(
    year,
    month,
    earnings,
    contribution=None,
):
    return SimpleNamespace(
        year=year,
        month=month,
        insurable_earnings=Decimal(str(earnings)),
        recorded_first_tier_contribution=(
            Decimal(str(contribution))
            if contribution is not None
            else None
        ),
    )


def test_no_contribution_data():

    result = analyse_contribution_history([])

    assert result["status"] == "NO_DATA"

    assert result["recorded_months"] == 0

    assert result["missing_month_count"] == 0

    assert result["continuity_ratio_percent"] is None


def test_complete_contribution_history():

    records = [
        make_record(
            2026,
            7,
            6000,
            810,
        ),
        make_record(
            2026,
            8,
            6200,
            837,
        ),
    ]

    result = analyse_contribution_history(
        records
    )

    assert (
        result["status"]
        ==
        "RECORDED_HISTORY_COMPLETE"
    )

    assert result["recorded_months"] == 2

    assert (
        result["months_in_observed_period"]
        ==
        2
    )

    assert (
        result["missing_month_count"]
        ==
        0
    )

    assert (
        result["continuity_ratio_percent"]
        ==
        "100.00"
    )

    assert (
        result["amount_mismatch_count"]
        ==
        0
    )


def test_missing_month_detection():

    records = [
        make_record(
            2026,
            7,
            6000,
            810,
        ),
        make_record(
            2026,
            8,
            6200,
            837,
        ),
        make_record(
            2026,
            10,
            6500,
            877.50,
        ),
    ]

    result = analyse_contribution_history(
        records
    )

    assert (
        result["status"]
        ==
        "INCOMPLETE_RECORDED_HISTORY"
    )

    assert (
        result["recorded_months"]
        ==
        3
    )

    assert (
        result["months_in_observed_period"]
        ==
        4
    )

    assert (
        result["missing_month_count"]
        ==
        1
    )

    assert (
        result["continuity_ratio_percent"]
        ==
        "75.00"
    )

    missing_month = (
        result["missing_months"][0]
    )

    assert missing_month["year"] == 2026

    assert missing_month["month"] == 9

    assert (
        missing_month["month_name"]
        ==
        "September"
    )


def test_contribution_amount_mismatch():

    records = [
        make_record(
            2026,
            7,
            6000,
            700,
        ),
    ]

    result = analyse_contribution_history(
        records
    )

    assert (
        result["status"]
        ==
        "AMOUNT_REVIEW_NEEDED"
    )

    assert (
        result["amount_mismatch_count"]
        ==
        1
    )

    check = result["amount_checks"][0]

    assert (
        check["expected_first_tier"]
        ==
        "810.00"
    )

    assert (
        check["recorded_first_tier"]
        ==
        "700"
    )

    assert (
        check["difference"]
        ==
        "-110.00"
    )

    assert (
        check["status"]
        ==
        "AMOUNT_MISMATCH"
    )


def test_correct_2026_first_tier_calculation():

    expected = (
        expected_first_tier_contribution(
            year=2026,
            insurable_earnings=Decimal(
                "6000"
            ),
        )
    )

    assert expected == Decimal(
        "810.00"
    )


def test_unconfigured_year_does_not_guess_rate():

    expected = (
        expected_first_tier_contribution(
            year=2025,
            insurable_earnings=Decimal(
                "6000"
            ),
        )
    )

    assert expected is None


def test_unconfigured_year_is_flagged():

    records = [
        make_record(
            2025,
            12,
            6000,
            810,
        ),
    ]

    result = analyse_contribution_history(
        records
    )

    check = result["amount_checks"][0]

    assert (
        check["status"]
        ==
        "RATE_NOT_CONFIGURED"
    )

    assert (
        check["expected_first_tier"]
        is None
    )