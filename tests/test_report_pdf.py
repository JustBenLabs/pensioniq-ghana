from datetime import (
    date,
    datetime,
    timezone,
)

from decimal import Decimal

from types import SimpleNamespace


from ssnit_engine.report_pdf import (
    generate_retirement_report_pdf,
    write_retirement_report_pdf,
)

from ssnit_engine.retirement_report import (
    build_retirement_report_data,
)


D = Decimal


# ============================================================
# HELPERS
# ============================================================


def make_member():

    return SimpleNamespace(

        id=1,

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

        contribution_months=240,

        best_three_year_average_annual_salary=(
            D("72000.00")
        ),
    )


GENERATED_AT = (
    datetime(
        2026,
        8,
        29,
        6,
        0,
        tzinfo=timezone.utc,
    )
)


def make_report():

    return (
        build_retirement_report_data(

            member=(
                make_member()
            ),

            contribution_records=[],

            generated_at=(
                GENERATED_AT
            ),
        )
    )


# ============================================================
# VALID PDF BYTES
# ============================================================


def test_generate_retirement_report_pdf_returns_pdf_bytes():

    report = make_report()


    pdf_bytes = (
        generate_retirement_report_pdf(
            report
        )
    )


    assert isinstance(
        pdf_bytes,
        bytes,
    )


    assert pdf_bytes.startswith(
        b"%PDF-"
    )


    assert len(
        pdf_bytes
    ) > 3000


    assert pdf_bytes.rstrip().endswith(
        b"%%EOF"
    )


# ============================================================
# WRITE PDF TO DISK
# ============================================================


def test_write_retirement_report_pdf(
    tmp_path,
):

    report = make_report()


    output_path = (
        tmp_path
        /
        "pensioniq-retirement-report.pdf"
    )


    result = (
        write_retirement_report_pdf(

            report,

            output_path,
        )
    )


    assert result == output_path


    assert output_path.exists()


    pdf_bytes = (
        output_path.read_bytes()
    )


    assert pdf_bytes.startswith(
        b"%PDF-"
    )


    assert len(
        pdf_bytes
    ) > 3000