from datetime import date
from decimal import Decimal as D

from ssnit_engine.engine import (
    BenefitEvent,
    calculate_master_benefit,
    calculate_pension_right,
    calculate_retirement_age,
)


def test_pension_right_below_threshold():
    assert calculate_pension_right(179) is None


def test_pension_right_at_threshold():
    assert calculate_pension_right(180) == D("0.3750000")


def test_pension_right_one_month_above_threshold():
    assert calculate_pension_right(181) == D("0.3759375")


def test_pension_right_20_years():
    assert calculate_pension_right(240) == D("0.4312500")


def test_pension_right_caps_at_60_percent():
    assert calculate_pension_right(420) == D("0.6000000")
    assert calculate_pension_right(480) == D("0.60")


def test_exact_retirement_age():
    age = calculate_retirement_age(date(1966, 8, 20), date(2026, 8, 20))
    assert (age.years, age.months, age.days) == (60, 0, 0)


def test_full_retirement_master_route():
    result = calculate_master_benefit(
        event=BenefitEvent.RETIREMENT,
        date_of_birth=date(1966, 8, 20),
        event_date=date(2026, 8, 20),
        contribution_months=240,
        best_three_year_average_annual_salary=D("72000"),
    )
    assert result.routed_benefit == "FULL_PENSION"
    assert result.monthly_benefit == D("2587.50")


def test_reduced_retirement_age_57():
    result = calculate_master_benefit(
        event=BenefitEvent.RETIREMENT,
        date_of_birth=date(1969, 8, 20),
        event_date=date(2026, 8, 20),
        contribution_months=240,
        best_three_year_average_annual_salary=D("72000"),
    )
    assert result.routed_benefit == "REDUCED_PENSION"
    assert result.monthly_benefit == D("1940.63")


def test_old_age_lump_sum_route():
    result = calculate_master_benefit(
        event=BenefitEvent.RETIREMENT,
        date_of_birth=date(1969, 8, 20),
        event_date=date(2026, 8, 20),
        contribution_months=179,
        returnable_contribution_principal=D("10000"),
        prevailing_91_day_tbill_rate=D("0.20"),
        official_interest_amount=D("3500"),
    )
    assert result.routed_benefit == "OLD_AGE_LUMP_SUM"
    assert result.lump_sum_benefit == D("13500.00")


def test_not_yet_old_age_eligible_under_55():
    result = calculate_master_benefit(
        event=BenefitEvent.RETIREMENT,
        date_of_birth=date(1972, 8, 21),
        event_date=date(2026, 8, 20),
        contribution_months=240,
        best_three_year_average_annual_salary=D("72000"),
    )
    assert result.eligible is False
    assert result.routed_benefit == "NOT_YET_ELIGIBLE"
def test_health_endpoint_has_security_headers(
    client,
):
    response = client.get("/health")

    assert response.status_code == 200

    assert (
        response.headers[
            "x-content-type-options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "x-frame-options"
        ]
        == "DENY"
    )

    assert (
        response.headers[
            "referrer-policy"
        ]
        == "no-referrer"
    )

    assert (
        response.headers[
            "permissions-policy"
        ]
        ==
        "camera=(), microphone=(), geolocation=()"
    )
def test_retirement_api_exposes_full_pension_calculation_details(
    client,
):
    response = client.post(
        "/benefits/retirement",
        json={
            "date_of_birth": "1966-08-20",
            "retirement_date": "2026-08-20",
            "contribution_months": 240,
            "best_three_year_average_annual_salary": "72000",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        D(data["monthly_salary_basis"])
        ==
        D("6000.00")
    )

    assert (
        D(data["retirement_age_factor"])
        ==
        D("1")
    )


def test_retirement_api_exposes_reduced_pension_factor(
    client,
):
    response = client.post(
        "/benefits/retirement",
        json={
            "date_of_birth": "1969-08-20",
            "retirement_date": "2026-08-20",
            "contribution_months": 240,
            "best_three_year_average_annual_salary": "72000",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        D(data["monthly_salary_basis"])
        ==
        D("6000.00")
    )

    assert (
        D(data["retirement_age_factor"])
        ==
        D("0.75")
    )
