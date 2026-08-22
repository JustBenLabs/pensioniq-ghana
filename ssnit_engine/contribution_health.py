from calendar import month_name
from decimal import Decimal


FIRST_TIER_RATE_2026 = Decimal("0.135")

CONTRIBUTION_TOLERANCE = Decimal("0.50")


def month_key(
    year: int,
    month: int,
) -> tuple[int, int]:

    return year, month


def next_month(
    year: int,
    month: int,
) -> tuple[int, int]:

    if month == 12:
        return year + 1, 1

    return year, month + 1


def expected_months_between(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> list[tuple[int, int]]:

    months = []

    year = start_year
    month = start_month

    while (year, month) <= (
        end_year,
        end_month,
    ):

        months.append(
            (year, month)
        )

        year, month = next_month(
            year,
            month,
        )

    return months


def expected_first_tier_contribution(
    *,
    year: int,
    insurable_earnings: Decimal,
) -> Decimal | None:
    """
    Current diagnostic supports the known 2026
    First-Tier contribution rate.

    Older/future years should be added through
    a formal rate table instead of guessed.
    """

    if year != 2026:
        return None

    return (
        insurable_earnings
        *
        FIRST_TIER_RATE_2026
    ).quantize(
        Decimal("0.01")
    )


def analyse_contribution_history(
    records,
) -> dict:

    if not records:

        return {
            "status": "NO_DATA",
            "recorded_months": 0,
            "first_record": None,
            "last_record": None,
            "months_in_observed_period": 0,
            "missing_month_count": 0,
            "missing_months": [],
            "continuity_ratio_percent": None,
            "total_insurable_earnings": "0.00",
            "total_recorded_first_tier": "0.00",
            "amount_mismatch_count": 0,
            "amount_checks": [],
        }


    ordered_records = sorted(
        records,
        key=lambda record: (
            record.year,
            record.month,
        ),
    )


    first = ordered_records[0]

    last = ordered_records[-1]


    expected_months = (
        expected_months_between(
            first.year,
            first.month,
            last.year,
            last.month,
        )
    )


    recorded_months = {
        month_key(
            record.year,
            record.month,
        )
        for record in ordered_records
    }


    missing_months = [
        {
            "year": year,
            "month": month,
            "month_name": month_name[month],
        }
        for year, month
        in expected_months
        if (
            year,
            month,
        )
        not in recorded_months
    ]


    total_insurable_earnings = sum(
        (
            Decimal(
                str(
                    record.insurable_earnings
                )
            )
            for record
            in ordered_records
        ),
        Decimal("0"),
    )


    total_recorded_first_tier = sum(
        (
            Decimal(
                str(
                    record
                    .recorded_first_tier_contribution
                )
            )
            for record
            in ordered_records
            if (
                record
                .recorded_first_tier_contribution
                is not None
            )
        ),
        Decimal("0"),
    )


    amount_checks = []

    mismatch_count = 0


    for record in ordered_records:

        earnings = Decimal(
            str(
                record.insurable_earnings
            )
        )


        recorded_amount = (
            Decimal(
                str(
                    record
                    .recorded_first_tier_contribution
                )
            )
            if (
                record
                .recorded_first_tier_contribution
                is not None
            )
            else None
        )


        expected_amount = (
            expected_first_tier_contribution(
                year=record.year,
                insurable_earnings=earnings,
            )
        )


        if expected_amount is None:

            amount_status = (
                "RATE_NOT_CONFIGURED"
            )

            difference = None


        elif recorded_amount is None:

            amount_status = (
                "NO_RECORDED_AMOUNT"
            )

            difference = None


        else:

            difference = (
                recorded_amount
                -
                expected_amount
            ).quantize(
                Decimal("0.01")
            )


            if (
                abs(difference)
                <=
                CONTRIBUTION_TOLERANCE
            ):

                amount_status = "MATCHED"

            else:

                amount_status = (
                    "AMOUNT_MISMATCH"
                )

                mismatch_count += 1


        amount_checks.append(
            {
                "year": record.year,

                "month": record.month,

                "month_name":
                    month_name[
                        record.month
                    ],

                "insurable_earnings":
                    str(
                        earnings.quantize(
                            Decimal("0.01")
                        )
                    ),

                "recorded_first_tier":
                    (
                        str(recorded_amount)
                        if recorded_amount
                        is not None
                        else None
                    ),

                "expected_first_tier":
                    (
                        str(expected_amount)
                        if expected_amount
                        is not None
                        else None
                    ),

                "difference":
                    (
                        str(difference)
                        if difference
                        is not None
                        else None
                    ),

                "status":
                    amount_status,
            }
        )


    observed_month_count = len(
        expected_months
    )


    continuity_ratio = (
        Decimal(
            len(recorded_months)
        )
        /
        Decimal(
            observed_month_count
        )
        *
        Decimal("100")
    )


    if missing_months:

        overall_status = (
            "INCOMPLETE_RECORDED_HISTORY"
        )

    elif mismatch_count > 0:

        overall_status = (
            "AMOUNT_REVIEW_NEEDED"
        )

    else:

        overall_status = (
            "RECORDED_HISTORY_COMPLETE"
        )


    return {

        "status":
            overall_status,

        "recorded_months":
            len(recorded_months),

        "first_record": {
            "year":
                first.year,

            "month":
                first.month,

            "month_name":
                month_name[
                    first.month
                ],
        },

        "last_record": {
            "year":
                last.year,

            "month":
                last.month,

            "month_name":
                month_name[
                    last.month
                ],
        },

        "months_in_observed_period":
            observed_month_count,

        "missing_month_count":
            len(
                missing_months
            ),

        "missing_months":
            missing_months,

        "continuity_ratio_percent":
            str(
                continuity_ratio.quantize(
                    Decimal("0.01")
                )
            ),

        "total_insurable_earnings":
            str(
                total_insurable_earnings
                .quantize(
                    Decimal("0.01")
                )
            ),

        "total_recorded_first_tier":
            str(
                total_recorded_first_tier
                .quantize(
                    Decimal("0.01")
                )
            ),

        "amount_mismatch_count":
            mismatch_count,

        "amount_checks":
            amount_checks,
    }