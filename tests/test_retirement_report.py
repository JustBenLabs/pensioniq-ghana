from datetime import (
    date,
    datetime,
    timezone,
)

from decimal import Decimal

from types import SimpleNamespace


from ssnit_engine.retirement_report import (
    REPORT_VERSION,
    build_retirement_report_data,
)


D = Decimal


# ============================================================
# TEST HELPERS
# ============================================================


def make_member(
    *,
    member_id=1,
    contribution_months=240,
    annual_salary="72000.00",
):

    return SimpleNamespace(

        id=member_id,

        first_name="Ama",

        last_name="Mensah",

        date_of_birth=(
            date(
                1990,
                4,
                16,
            )
        ),

        sex="Female",

        contribution_months=(
            contribution_months
        ),

        best_three_year_average_annual_salary=(
            D(
                annual_salary
            )
        ),
    )


def make_record(
    *,
    year,
    month,
    earnings="5000.00",
):

    earnings_value = D(
        earnings
    )


    return SimpleNamespace(

        year=year,

        month=month,

        insurable_earnings=(
            earnings_value
        ),

        recorded_first_tier_contribution=(
            earnings_value
            *
            D("0.135")
        ),
    )


FIXED_GENERATED_AT = (
    datetime(
        2026,
        8,
        29,
        6,
        0,
        tzinfo=timezone.utc,
    )
)


# ============================================================
# BASE REPORT
# ============================================================


def test_report_builds_member_and_pension_position():

    member = make_member()


    report = build_retirement_report_data(

        member=member,

        contribution_records=[],

        generated_at=(
            FIXED_GENERATED_AT
        ),
    )


    assert (
        report.report_version
        ==
        REPORT_VERSION
    )


    assert (
        report.member[
            "member_id"
        ]
        ==
        1
    )


    assert (
        report.member[
            "full_name"
        ]
        ==
        "Ama Mensah"
    )


    assert (
        report.member[
            "current_age"
        ]
        ==
        36
    )


    assert (
        report.contribution_position[
            "stored_contribution_months"
        ]
        ==
        240
    )


    assert (
        report.contribution_position[
            "monthly_pension_threshold_met"
        ]
        is True
    )


    assert (
        report.pension_position[
            "pension_right_percent"
        ]
        ==
        "43.13"
    )


    assert (
        report.pension_position[
            "salary_basis_monthly"
        ]
        ==
        "6000.00"
    )


# ============================================================
# AGE-60 BASELINE
# ============================================================


def test_report_age_60_baseline_uses_current_stored_position():

    member = make_member(

        contribution_months=240,

        annual_salary="72000.00",
    )


    report = build_retirement_report_data(

        member=member,

        contribution_records=[],

        generated_at=(
            FIXED_GENERATED_AT
        ),
    )


    baseline = (
        report
        .pension_position[
            "age_60_baseline"
        ]
    )


    assert (
        baseline[
            "available"
        ]
        is True
    )


    assert (
        baseline[
            "retirement_age"
        ]
        ==
        60
    )


    assert (
        baseline[
            "retirement_date"
        ]
        ==
        "2050-04-16"
    )


    assert (
        baseline[
            "retirement_age_factor"
        ]
        ==
        "1.00"
    )


    assert (
        baseline[
            "estimated_monthly_pension"
        ]
        ==
        "2587.50"
    )


# ============================================================
# NO DETAILED HISTORY
# ============================================================


def test_report_marks_no_detailed_history_as_incomplete_readiness():

    member = make_member(
        contribution_months=240
    )


    report = build_retirement_report_data(

        member=member,

        contribution_records=[],

        generated_at=(
            FIXED_GENERATED_AT
        ),
    )


    quality = (
        report
        .retirement_readiness[
            "data_quality"
        ]
    )


    assert (
        quality[
            "record_alignment_status"
        ]
        ==
        "NO_DETAILED_HISTORY"
    )


    assert (
        quality[
            "continuity_used_in_score"
        ]
        is False
    )


    assert (
        report
        .retirement_readiness[
            "score"
        ]
        is None
    )


    assert (
        report
        .retirement_readiness[
            "rating"
        ]
        ==
        "Incomplete"
    )


# ============================================================
# PARTIAL HISTORY MUST NOT ENTER READINESS
# ============================================================


def test_report_does_not_use_partial_history_continuity():

    member = make_member(
        contribution_months=240
    )


    records = [

        make_record(
            year=2026,
            month=1,
        ),

    ]


    report = build_retirement_report_data(

        member=member,

        contribution_records=records,

        generated_at=(
            FIXED_GENERATED_AT
        ),
    )


    quality = (
        report
        .retirement_readiness[
            "data_quality"
        ]
    )


    assert (
        quality[
            "record_alignment_status"
        ]
        ==
        "TOTAL_AND_HISTORY_DIFFER"
    )


    assert (
        quality[
            "continuity_used_in_score"
        ]
        is False
    )


    assert (
        report
        .retirement_readiness[
            "score"
        ]
        is None
    )


# ============================================================
# ALIGNED HISTORY
# ============================================================


def test_report_uses_continuity_when_history_is_aligned():

    member = make_member(
        contribution_months=3
    )


    records = [

        make_record(
            year=2026,
            month=1,
        ),

        make_record(
            year=2026,
            month=2,
        ),

        make_record(
            year=2026,
            month=3,
        ),

    ]


    report = build_retirement_report_data(

        member=member,

        contribution_records=records,

        generated_at=(
            FIXED_GENERATED_AT
        ),
    )


    quality = (
        report
        .retirement_readiness[
            "data_quality"
        ]
    )


    assert (
        quality[
            "record_alignment_status"
        ]
        ==
        "ALIGNED"
    )


    assert (
        quality[
            "continuity_used_in_score"
        ]
        is True
    )


    assert (
        quality[
            "continuity_ratio_percent"
        ]
        ==
        "100.00"
    )


    assert (
        report
        .retirement_readiness[
            "score"
        ]
        ==
        "25.67"
    )


    assert (
        report
        .retirement_readiness[
            "rating"
        ]
        ==
        "Needs Attention"
    )


# ============================================================
# OPTIONAL PLANNING SECTIONS
# ============================================================


def test_report_omits_unsaved_planning_sections():

    member = make_member()


    report = build_retirement_report_data(

        member=member,

        contribution_records=[],

        generated_at=(
            FIXED_GENERATED_AT
        ),
    )


    assert (
        report
        .planning_sections[
            "what_if_scenario"
        ][
            "included"
        ]
        is False
    )


    assert (
        report
        .planning_sections[
            "retirement_goal"
        ][
            "included"
        ]
        is False
    )


def test_report_can_include_supplied_planning_sections():

    member = make_member()


    scenario = {

        "scenario":
            "example",

    }


    goal = {

        "goal":
            "example",

    }


    report = build_retirement_report_data(

        member=member,

        contribution_records=[],

        generated_at=(
            FIXED_GENERATED_AT
        ),

        what_if_scenario=(
            scenario
        ),

        retirement_goal=(
            goal
        ),
    )


    assert (
        report
        .planning_sections[
            "what_if_scenario"
        ][
            "included"
        ]
        is True
    )


    assert (
        report
        .planning_sections[
            "what_if_scenario"
        ][
            "data"
        ]
        ==
        scenario
    )


    assert (
        report
        .planning_sections[
            "retirement_goal"
        ][
            "included"
        ]
        is True
    )


    assert (
        report
        .planning_sections[
            "retirement_goal"
        ][
            "data"
        ]
        ==
        goal
    )