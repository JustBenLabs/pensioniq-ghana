from decimal import Decimal

import pytest

from ssnit_engine.mortality import (
    MortalityBasis,
    MortalityCentralRate,
    MortalityRate,
    MortalityTable,
    mortality_table_from_mx,
    mx_to_qx,
)


# ============================================================
# TEST MORTALITY BASIS
# ============================================================

TEST_BASIS = MortalityBasis(
    source="Software Test Mortality Table",
    reference_year=2026,
    sex="Male",
    population="Test Population",
    model_type="software test",
)


# ============================================================
# BASIC qx / px TESTS
# ============================================================


def test_px_equals_one_minus_qx():

    table = MortalityTable(
        rates=[
            MortalityRate(
                age=55,
                qx=Decimal("0.01"),
            )
        ],
        basis=TEST_BASIS,
    )

    assert table.px(55) == Decimal("0.99")


def test_invalid_qx_above_one():

    with pytest.raises(ValueError):

        MortalityTable(
            rates=[
                MortalityRate(
                    age=55,
                    qx=Decimal("1.20"),
                )
            ],
            basis=TEST_BASIS,
        )


def test_invalid_negative_qx():

    with pytest.raises(ValueError):

        MortalityTable(
            rates=[
                MortalityRate(
                    age=55,
                    qx=Decimal("-0.01"),
                )
            ],
            basis=TEST_BASIS,
        )


def test_missing_age():

    table = MortalityTable(
        rates=[
            MortalityRate(
                age=55,
                qx=Decimal("0.01"),
            )
        ],
        basis=TEST_BASIS,
    )

    with pytest.raises(ValueError):

        table.qx(56)


# ============================================================
# mx -> qx CONVERSION TESTS
# ============================================================


def test_mx_zero_gives_qx_zero():

    result = mx_to_qx(
        Decimal("0")
    )

    assert result == Decimal("0")


def test_mx_conversion():

    result = mx_to_qx(
        Decimal("0.01")
    )

    expected = Decimal(
        "0.009950166250831893"
    )

    tolerance = Decimal(
        "0.000000000001"
    )

    assert abs(
        result - expected
    ) < tolerance


# ============================================================
# BUILD MORTALITY TABLE FROM mx
# ============================================================


def test_mortality_table_from_mx():

    basis = MortalityBasis(
        source="Software Test",
        reference_year=2026,
        sex="Male",
        population="Test Population",
        model_type="software test",
    )

    table = mortality_table_from_mx(
        rates=[
            MortalityCentralRate(
                age=55,
                mx=Decimal("0.01"),
            ),
        ],
        basis=basis,
    )

    assert table.qx(55) > Decimal("0")

    assert table.qx(55) < Decimal("1")

    assert table.basis.source == "Software Test"

    assert table.basis.reference_year == 2026

    assert table.basis.sex == "Male"