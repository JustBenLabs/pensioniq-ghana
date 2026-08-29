from io import BytesIO
from pathlib import Path
from typing import Optional


from reportlab.lib import colors

from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
)

from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)

from reportlab.lib.units import mm

from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


from ssnit_engine.retirement_report import (
    RetirementReportData,
)


# ============================================================
# BRAND
# ============================================================


PAGE_WIDTH, PAGE_HEIGHT = A4


NAVY = colors.HexColor(
    "#102A43"
)

TEAL = colors.HexColor(
    "#0F766E"
)

LIGHT_TEAL = colors.HexColor(
    "#EAF7F5"
)

LIGHT_BLUE = colors.HexColor(
    "#F3F7FA"
)

LIGHT_GREY = colors.HexColor(
    "#F7F9FA"
)

MID_GREY = colors.HexColor(
    "#66788A"
)

BORDER_GREY = colors.HexColor(
    "#DCE3E8"
)

DARK_TEXT = colors.HexColor(
    "#243B53"
)

WARNING_BG = colors.HexColor(
    "#FFF7E8"
)

WARNING_BORDER = colors.HexColor(
    "#E6B85C"
)

WHITE = colors.white


LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 25 * mm
BOTTOM_MARGIN = 20 * mm


# ============================================================
# FORMATTERS
# ============================================================


def _safe(
    value,
    fallback: str = "Not available",
) -> str:

    if value is None:
        return fallback

    text = str(
        value
    ).strip()

    if not text:
        return fallback

    return text


def _currency(
    value,
) -> str:

    if value is None:
        return "Not available"

    try:

        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return _safe(
            value
        )

    return (
        "GH¢"
        +
        f"{number:,.2f}"
    )


def _percentage(
    value,
) -> str:

    if value is None:
        return "Not available"

    try:

        number = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return _safe(
            value
        )

    return (
        f"{number:.2f}%"
    )


def _months(
    value,
) -> str:

    if value is None:
        return "Not available"

    try:

        number = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return _safe(
            value
        )

    return (
        f"{number:,} months"
    )


def _yes_no(
    value,
) -> str:

    return (
        "Yes"
        if value
        else "No"
    )


# ============================================================
# STYLES
# ============================================================


def _build_styles():

    sample = (
        getSampleStyleSheet()
    )


    styles = {}


    styles[
        "title"
    ] = ParagraphStyle(

        "PensionIQTitle",

        parent=(
            sample[
                "Title"
            ]
        ),

        fontName=
            "Helvetica-Bold",

        fontSize=
            24,

        leading=
            29,

        textColor=
            NAVY,

        alignment=
            TA_LEFT,

        spaceAfter=
            4,
    )


    styles[
        "subtitle"
    ] = ParagraphStyle(

        "PensionIQSubtitle",

        parent=(
            sample[
                "Normal"
            ]
        ),

        fontName=
            "Helvetica",

        fontSize=
            10,

        leading=
            15,

        textColor=
            MID_GREY,

        spaceAfter=
            10,
    )


    styles[
        "section"
    ] = ParagraphStyle(

        "PensionIQSection",

        parent=(
            sample[
                "Heading2"
            ]
        ),

        fontName=
            "Helvetica-Bold",

        fontSize=
            15,

        leading=
            19,

        textColor=
            NAVY,

        spaceBefore=
            4,

        spaceAfter=
            9,
    )


    styles[
        "subsection"
    ] = ParagraphStyle(

        "PensionIQSubsection",

        parent=(
            sample[
                "Heading3"
            ]
        ),

        fontName=
            "Helvetica-Bold",

        fontSize=
            11,

        leading=
            14,

        textColor=
            TEAL,

        spaceBefore=
            4,

        spaceAfter=
            7,
    )


    styles[
        "body"
    ] = ParagraphStyle(

        "PensionIQBody",

        parent=(
            sample[
                "BodyText"
            ]
        ),

        fontName=
            "Helvetica",

        fontSize=
            9,

        leading=
            14,

        textColor=
            DARK_TEXT,

        spaceAfter=
            6,
    )


    styles[
        "small"
    ] = ParagraphStyle(

        "PensionIQSmall",

        parent=(
            styles[
                "body"
            ]
        ),

        fontSize=
            7.5,

        leading=
            11,

        textColor=
            MID_GREY,
    )


    styles[
        "label"
    ] = ParagraphStyle(

        "PensionIQLabel",

        parent=(
            styles[
                "body"
            ]
        ),

        fontName=
            "Helvetica-Bold",

        fontSize=
            7,

        leading=
            9,

        textColor=
            MID_GREY,
    )


    styles[
        "value"
    ] = ParagraphStyle(

        "PensionIQValue",

        parent=(
            styles[
                "body"
            ]
        ),

        fontName=
            "Helvetica-Bold",

        fontSize=
            10,

        leading=
            13,

        textColor=
            NAVY,
    )


    styles[
        "score"
    ] = ParagraphStyle(

        "PensionIQScore",

        parent=(
            styles[
                "body"
            ]
        ),

        fontName=
            "Helvetica-Bold",

        fontSize=
            21,

        leading=
            24,

        alignment=
            TA_CENTER,

        textColor=
            TEAL,
    )


    styles[
        "center_small"
    ] = ParagraphStyle(

        "PensionIQCenterSmall",

        parent=(
            styles[
                "small"
            ]
        ),

        alignment=
            TA_CENTER,
    )


    return styles


# ============================================================
# DOCUMENT
# ============================================================


class PensionIQReportDocument(
    BaseDocTemplate
):

    def __init__(
        self,
        buffer,
        *,
        report: RetirementReportData,
    ):

        super().__init__(

            buffer,

            pagesize=A4,

            leftMargin=
                LEFT_MARGIN,

            rightMargin=
                RIGHT_MARGIN,

            topMargin=
                TOP_MARGIN,

            bottomMargin=
                BOTTOM_MARGIN,

            title=
                (
                    "PensionIQ Personal "
                    "Retirement Report"
                ),

            author=
                "PensionIQ Ghana",
        )


        self.report = report


        frame = Frame(

            self.leftMargin,

            self.bottomMargin,

            self.width,

            self.height,

            id=
                "normal",
        )


        template = PageTemplate(

            id=
                "PensionIQ",

            frames=[
                frame
            ],

            onPage=
                self._draw_page,
        )


        self.addPageTemplates(
            [
                template
            ]
        )


    def _draw_page(
        self,
        canvas,
        document,
    ):

        canvas.saveState()


        # ----------------------------------------------------
        # TOP BRAND LINE
        # ----------------------------------------------------

        canvas.setFillColor(
            NAVY
        )

        canvas.rect(

            0,

            PAGE_HEIGHT
            -
            8 * mm,

            PAGE_WIDTH,

            8 * mm,

            stroke=0,

            fill=1,
        )


        canvas.setFillColor(
            WHITE
        )

        canvas.setFont(
            "Helvetica-Bold",
            10,
        )

        canvas.drawString(

            LEFT_MARGIN,

            PAGE_HEIGHT
            -
            5.2 * mm,

            "PensionIQ Ghana",
        )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        canvas.setStrokeColor(
            BORDER_GREY
        )

        canvas.setLineWidth(
            0.5
        )

        canvas.line(

            LEFT_MARGIN,

            13 * mm,

            PAGE_WIDTH
            -
            RIGHT_MARGIN,

            13 * mm,
        )


        canvas.setFillColor(
            MID_GREY
        )

        canvas.setFont(
            "Helvetica",
            7,
        )


        generated_date = (
            self.report
            .generated_at
            .date()
            .isoformat()
        )


        canvas.drawString(

            LEFT_MARGIN,

            8 * mm,

            (
                "PensionIQ Personal Retirement Report"
                f" | Generated {generated_date}"
            ),
        )


        page_number = (
            canvas.getPageNumber()
        )


        canvas.drawRightString(

            PAGE_WIDTH
            -
            RIGHT_MARGIN,

            8 * mm,

            f"Page {page_number}",
        )


        canvas.restoreState()


# ============================================================
# TABLE HELPERS
# ============================================================


def _metric_box(
    label: str,
    value: str,
    styles,
):

    data = [

        [
            Paragraph(
                label.upper(),
                styles[
                    "label"
                ],
            )
        ],

        [
            Paragraph(
                value,
                styles[
                    "value"
                ],
            )
        ],
    ]


    table = Table(

        data,

        colWidths=[
            53 * mm
        ],

        rowHeights=[
            8 * mm,
            10 * mm,
        ],
    )


    table.setStyle(

        TableStyle(
            [

                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    LIGHT_GREY,
                ),

                (
                    "BOX",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.6,
                    BORDER_GREY,
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    5,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    5,
                ),

            ]
        )
    )


    return table


def _key_value_table(
    rows,
    styles,
):

    formatted_rows = []


    for label, value in rows:

        formatted_rows.append(
            [

                Paragraph(
                    _safe(
                        label
                    ),
                    styles[
                        "body"
                    ],
                ),

                Paragraph(
                    _safe(
                        value
                    ),
                    styles[
                        "value"
                    ],
                ),

            ]
        )


    table = Table(

        formatted_rows,

        colWidths=[
            76 * mm,
            86 * mm,
        ],

        repeatRows=0,
    )


    table.setStyle(

        TableStyle(
            [

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),

                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        0,
                        -1,
                    ),
                    LIGHT_GREY,
                ),

                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    BORDER_GREY,
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    7,
                ),

            ]
        )
    )


    return table


# ============================================================
# REPORT CONTENT
# ============================================================


def _build_story(
    report: RetirementReportData,
):

    styles = (
        _build_styles()
    )


    story = []


    member = (
        report.member
    )

    contributions = (
        report.contribution_position
    )

    health = (
        report.contribution_health
    )

    pension = (
        report.pension_position
    )

    readiness = (
        report.retirement_readiness
    )

    planning = (
        report.planning_sections
    )


    # ========================================================
    # COVER / TITLE
    # ========================================================

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )


    story.append(
        Paragraph(
            "Personal Retirement Report",
            styles[
                "title"
            ],
        )
    )


    story.append(
        Paragraph(

            (
                "A PensionIQ Ghana retirement-planning "
                "summary based on the information currently "
                "stored in your PensionIQ profile."
            ),

            styles[
                "subtitle"
            ],
        )
    )


    report_meta = Table(

        [

            [
                Paragraph(
                    "MEMBER",
                    styles[
                        "label"
                    ],
                ),

                Paragraph(
                    _safe(
                        member.get(
                            "full_name"
                        )
                    ),
                    styles[
                        "value"
                    ],
                ),

                Paragraph(
                    "REPORT VERSION",
                    styles[
                        "label"
                    ],
                ),

                Paragraph(
                    _safe(
                        report
                        .report_version
                    ),
                    styles[
                        "value"
                    ],
                ),
            ],

            [
                Paragraph(
                    "GENERATED",
                    styles[
                        "label"
                    ],
                ),

                Paragraph(
                    (
                        report
                        .generated_at
                        .strftime(
                            "%d %b %Y %H:%M UTC"
                        )
                    ),
                    styles[
                        "value"
                    ],
                ),

                Paragraph(
                    "MEMBER ID",
                    styles[
                        "label"
                    ],
                ),

                Paragraph(
                    _safe(
                        member.get(
                            "member_id"
                        )
                    ),
                    styles[
                        "value"
                    ],
                ),
            ],

        ],

        colWidths=[
            30 * mm,
            52 * mm,
            30 * mm,
            50 * mm,
        ],
    )


    report_meta.setStyle(

        TableStyle(
            [

                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    LIGHT_BLUE,
                ),

                (
                    "BOX",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.6,
                    BORDER_GREY,
                ),

                (
                    "INNERGRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.3,
                    BORDER_GREY,
                ),

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "MIDDLE",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    7,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    7,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    7,
                ),

            ]
        )
    )


    story.append(
        report_meta
    )


    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )


    warning = Table(

        [

            [
                Paragraph(

                    (
                        "<b>Planning document - not an official "
                        "SSNIT benefit statement.</b><br/>"
                        "Use this report to understand your "
                        "PensionIQ retirement-planning position. "
                        "Official SSNIT records and determinations "
                        "govern actual benefits."
                    ),

                    styles[
                        "body"
                    ],
                )
            ]

        ],

        colWidths=[
            162 * mm
        ],
    )


    warning.setStyle(

        TableStyle(
            [

                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    WARNING_BG,
                ),

                (
                    "BOX",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.8,
                    WARNING_BORDER,
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    10,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    10,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    9,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    9,
                ),

            ]
        )
    )


    story.append(
        warning
    )


    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )


    # ========================================================
    # MEMBER SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "1. Member Summary",
            styles[
                "section"
            ],
        )
    )


    member_rows = [

        (
            "Full name",
            member.get(
                "full_name"
            ),
        ),

        (
            "Date of birth",
            member.get(
                "date_of_birth"
            ),
        ),

        (
            "Current age",
            (
                f"{member.get('current_age')} years"
                if (
                    member.get(
                        "current_age"
                    )
                    is not None
                )
                else
                "Not available"
            ),
        ),

        (
            "Sex",
            member.get(
                "sex"
            ),
        ),

        (
            "Best 3-year average annual salary",
            _currency(
                member.get(
                    "best_three_year_average_annual_salary"
                )
            ),
        ),

    ]


    story.append(
        _key_value_table(
            member_rows,
            styles,
        )
    )


    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )


    # ========================================================
    # CONTRIBUTION POSITION
    # ========================================================

    story.append(
        Paragraph(
            "2. Contribution Position",
            styles[
                "section"
            ],
        )
    )


    metric_row = Table(

        [

            [

                _metric_box(
                    "Contribution months",
                    _months(
                        contributions.get(
                            "stored_contribution_months"
                        )
                    ),
                    styles,
                ),

                _metric_box(
                    "Years contributed",
                    (
                        _safe(
                            contributions.get(
                                "contribution_years"
                            )
                        )
                        +
                        " years"
                    ),
                    styles,
                ),

                _metric_box(
                    "Months to maximum right",
                    _months(
                        contributions.get(
                            "months_to_maximum"
                        )
                    ),
                    styles,
                ),

            ]

        ],

        colWidths=[
            54 * mm,
            54 * mm,
            54 * mm,
        ],
    )


    metric_row.setStyle(

        TableStyle(
            [

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    1,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    1,
                ),

            ]
        )
    )


    story.append(
        metric_row
    )


    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )


    story.append(
        _key_value_table(

            [

                (
                    "Monthly pension contribution threshold met",
                    _yes_no(
                        contributions.get(
                            "monthly_pension_threshold_met"
                        )
                    ),
                ),

                (
                    "Months to 180-month threshold",
                    _months(
                        contributions.get(
                            "months_to_minimum"
                        )
                    ),
                ),

                (
                    "Detailed contribution records stored",
                    _months(
                        contributions.get(
                            "detailed_records_stored"
                        )
                    ),
                ),

                (
                    "Record alignment",
                    _safe(
                        contributions.get(
                            "record_alignment_status"
                        )
                    ),
                ),

            ],

            styles,
        )
    )


    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )


    # ========================================================
    # PENSION POSITION
    # ========================================================

    story.append(
        Paragraph(
            "3. Pension Position",
            styles[
                "section"
            ],
        )
    )


    baseline = (
        pension.get(
            "age_60_baseline"
        )
        or
        {}
    )


    story.append(
        _key_value_table(

            [

                (
                    "Current pension right",
                    _percentage(
                        pension.get(
                            "pension_right_percent"
                        )
                    ),
                ),

                (
                    "Annual salary basis",
                    _currency(
                        pension.get(
                            "salary_basis_annual"
                        )
                    ),
                ),

                (
                    "Monthly salary basis",
                    _currency(
                        pension.get(
                            "salary_basis_monthly"
                        )
                    ),
                ),

                (
                    "Age-60 baseline retirement date",
                    _safe(
                        baseline.get(
                            "retirement_date"
                        )
                    ),
                ),

                (
                    "Age-60 baseline estimated monthly pension",
                    _currency(
                        baseline.get(
                            "estimated_monthly_pension"
                        )
                    ),
                ),

                (
                    "Age-60 retirement factor",
                    _safe(
                        baseline.get(
                            "retirement_age_factor"
                        )
                    ),
                ),

            ],

            styles,
        )
    )


    baseline_note = (
        baseline.get(
            "note"
        )
    )


    if baseline_note:

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        story.append(
            Paragraph(
                baseline_note,
                styles[
                    "small"
                ],
            )
        )


    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )


    # ========================================================
    # READINESS
    # ========================================================

    story.append(
        Paragraph(
            "4. Retirement Readiness",
            styles[
                "section"
            ],
        )
    )


    score = (
        readiness.get(
            "score"
        )
    )


    rating = (
        readiness.get(
            "rating"
        )
    )


    if score is None:

        score_text = (
            "Incomplete"
        )

        score_subtitle = (
            "A complete score requires contribution "
            "history data that passes PensionIQ's "
            "data-quality safeguard."
        )

    else:

        score_text = (
            f"{score} / 100"
        )

        score_subtitle = (
            f"Rating: {_safe(rating)}"
        )


    score_table = Table(

        [

            [

                Paragraph(
                    score_text,
                    styles[
                        "score"
                    ],
                ),

                Paragraph(
                    (
                        "<b>"
                        +
                        _safe(
                            rating
                        )
                        +
                        "</b><br/>"
                        +
                        score_subtitle
                    ),
                    styles[
                        "body"
                    ],
                ),

            ]

        ],

        colWidths=[
            55 * mm,
            107 * mm,
        ],
    )


    score_table.setStyle(

        TableStyle(
            [

                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    LIGHT_TEAL,
                ),

                (
                    "BOX",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.7,
                    TEAL,
                ),

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "MIDDLE",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    10,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    10,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    12,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    12,
                ),

            ]
        )
    )


    story.append(
        score_table
    )


    components = (
        readiness.get(
            "components"
        )
        or
        {}
    )


    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )


    story.append(
        _key_value_table(

            [

                (
                    "Eligibility component",
                    (
                        _safe(
                            (
                                components
                                .get(
                                    "eligibility",
                                    {},
                                )
                                .get(
                                    "score"
                                )
                            )
                        )
                        +
                        " / 40"
                    ),
                ),

                (
                    "Pension-right component",
                    (
                        _safe(
                            (
                                components
                                .get(
                                    "pension_right",
                                    {},
                                )
                                .get(
                                    "score"
                                )
                            )
                        )
                        +
                        " / 35"
                    ),
                ),

                (
                    "Contribution consistency component",
                    (
                        _safe(
                            (
                                components
                                .get(
                                    "contribution_consistency",
                                    {},
                                )
                                .get(
                                    "score"
                                )
                            )
                        )
                        +
                        " / 25"
                    ),
                ),

                (
                    "Score provisional",
                    _yes_no(
                        readiness.get(
                            "provisional"
                        )
                    ),
                ),

            ],

            styles,
        )
    )


    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )


    # ========================================================
    # CONTRIBUTION HEALTH
    # ========================================================

    story.append(
        Paragraph(
            "5. Contribution Health",
            styles[
                "section"
            ],
        )
    )


    story.append(
        _key_value_table(

            [

                (
                    "Health status",
                    _safe(
                        health.get(
                            "status"
                        )
                    ),
                ),

                (
                    "Continuity ratio",
                    _percentage(
                        health.get(
                            "continuity_ratio_percent"
                        )
                    ),
                ),

                (
                    "Missing-month count",
                    _safe(
                        health.get(
                            "missing_month_count"
                        )
                    ),
                ),

                (
                    "Amount mismatch count",
                    _safe(
                        health.get(
                            "amount_mismatch_count"
                        )
                    ),
                ),

                (
                    "Record alignment",
                    _safe(
                        health.get(
                            "record_alignment_status"
                        )
                    ),
                ),

                (
                    "Total insurable earnings in stored records",
                    _currency(
                        health.get(
                            "total_insurable_earnings"
                        )
                    ),
                ),

                (
                    "Total recorded first-tier contributions",
                    _currency(
                        health.get(
                            "total_recorded_first_tier"
                        )
                    ),
                ),

            ],

            styles,
        )
    )


    health_note = (
        health.get(
            "diagnostic_note"
        )
    )


    if health_note:

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        story.append(
            Paragraph(
                health_note,
                styles[
                    "small"
                ],
            )
        )


    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )


    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    story.append(
        Paragraph(
            "6. PensionIQ Recommendations",
            styles[
                "section"
            ],
        )
    )


    if report.recommendations:

        for recommendation in (
            report.recommendations
        ):

            story.append(

                Paragraph(

                    (
                        "&#8226; "
                        +
                        _safe(
                            recommendation
                        )
                    ),

                    styles[
                        "body"
                    ],
                )

            )

    else:

        story.append(
            Paragraph(
                (
                    "No specific PensionIQ recommendations "
                    "are available for this report."
                ),
                styles[
                    "body"
                ],
            )
        )


    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )


    # ========================================================
    # PLANNING ANALYSES
    # ========================================================

    story.append(
        Paragraph(
            "7. Retirement Planning Analyses",
            styles[
                "section"
            ],
        )
    )


    what_if = (
        planning.get(
            "what_if_scenario",
            {},
        )
    )


    goal = (
        planning.get(
            "retirement_goal",
            {},
        )
    )


    if (
        what_if.get(
            "included"
        )
    ):

        story.append(
            Paragraph(
                "What-If Retirement Scenario",
                styles[
                    "subsection"
                ],
            )
        )

        story.append(
            Paragraph(
                (
                    "A What-If scenario was supplied "
                    "for this report."
                ),
                styles[
                    "body"
                ],
            )
        )

    else:

        story.append(
            Paragraph(
                (
                    "<b>What-If Retirement Scenario:</b> "
                    +
                    _safe(
                        what_if.get(
                            "note"
                        )
                    )
                ),
                styles[
                    "body"
                ],
            )
        )


    if (
        goal.get(
            "included"
        )
    ):

        story.append(
            Paragraph(
                "Retirement Goal Analysis",
                styles[
                    "subsection"
                ],
            )
        )

        story.append(
            Paragraph(
                (
                    "A retirement-goal analysis was "
                    "supplied for this report."
                ),
                styles[
                    "body"
                ],
            )
        )

    else:

        story.append(
            Paragraph(
                (
                    "<b>Retirement Goal Analysis:</b> "
                    +
                    _safe(
                        goal.get(
                            "note"
                        )
                    )
                ),
                styles[
                    "body"
                ],
            )
        )


    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )


    # ========================================================
    # ASSUMPTIONS
    # ========================================================

    story.append(
        Paragraph(
            "8. Important Assumptions",
            styles[
                "section"
            ],
        )
    )


    for assumption in (
        report.assumptions
    ):

        story.append(

            Paragraph(

                (
                    "&#8226; "
                    +
                    _safe(
                        assumption
                    )
                ),

                styles[
                    "body"
                ],
            )

        )


    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )


    # ========================================================
    # DISCLAIMER
    # ========================================================

    disclaimer_block = Table(

        [

            [
                Paragraph(
                    "<b>Important disclaimer</b>",
                    styles[
                        "subsection"
                    ],
                )
            ],

            [
                Paragraph(
                    report.disclaimer,
                    styles[
                        "small"
                    ],
                )
            ],

        ],

        colWidths=[
            162 * mm
        ],
    )


    disclaimer_block.setStyle(

        TableStyle(
            [

                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    LIGHT_GREY,
                ),

                (
                    "BOX",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.7,
                    BORDER_GREY,
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    10,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    10,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    8,
                ),

            ]
        )
    )


    story.append(
        KeepTogether(
            [
                disclaimer_block
            ]
        )
    )


    return story


# ============================================================
# PUBLIC API
# ============================================================


def generate_retirement_report_pdf(
    report: RetirementReportData,
) -> bytes:

    """
    Generate a branded PensionIQ Personal Retirement Report.

    Returns raw PDF bytes.
    """

    buffer = BytesIO()


    document = (
        PensionIQReportDocument(

            buffer,

            report=report,
        )
    )


    story = (
        _build_story(
            report
        )
    )


    document.build(
        story
    )


    pdf_bytes = (
        buffer.getvalue()
    )


    buffer.close()


    return pdf_bytes


def write_retirement_report_pdf(
    report: RetirementReportData,
    output_path,
) -> Path:

    """
    Convenience function for writing a report to disk.
    """

    output = Path(
        output_path
    )


    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    output.write_bytes(

        generate_retirement_report_pdf(
            report
        )

    )


    return output