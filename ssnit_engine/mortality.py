import csv
import math

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass(frozen=True)
class MortalityRate:
    """
    Represents a one-year probability of death qx
    at a particular age.
    """

    age: int
    qx: Decimal


@dataclass(frozen=True)
class MortalityCentralRate:
    """
    Represents a central mortality rate mx
    at a particular age.
    """

    age: int
    mx: Decimal


@dataclass(frozen=True)
class MortalityBasis:
    """
    Metadata describing the source and basis
    of a mortality table.
    """

    source: str
    reference_year: int
    sex: str
    population: str = "Ghana"
    model_type: str = "population"

    def __post_init__(self):

        valid_sexes = {
            "Male",
            "Female",
            "Both",
        }

        if self.sex not in valid_sexes:
            raise ValueError(
                "sex must be Male, Female, or Both."
            )

        if self.reference_year < 1900:
            raise ValueError(
                "Invalid mortality reference year."
            )

        if not self.source.strip():
            raise ValueError(
                "Mortality source must be identified."
            )

        if not self.population.strip():
            raise ValueError(
                "Population must be identified."
            )


# ============================================================
# MORTALITY RATE CONVERSION
# ============================================================


def mx_to_qx(
    mx: Decimal,
) -> Decimal:
    """
    Convert a central mortality rate mx into
    a one-year death probability qx.

    Under the constant-force-of-mortality
    assumption:

        qx = 1 - exp(-mx)

    This is a modelling conversion and does not
    alter the original source mx value.
    """

    if mx < 0:
        raise ValueError(
            "mx cannot be negative."
        )

    qx = (
        1
        -
        math.exp(
            -float(mx)
        )
    )

    return Decimal(
        str(qx)
    )


# ============================================================
# MORTALITY TABLE
# ============================================================


class MortalityTable:
    """
    Generic actuarial mortality table.

    The table stores qx values by integer age
    together with metadata describing the
    mortality basis.

    It does not assume that the table is an
    official SSNIT mortality table.
    """

    def __init__(
        self,
        rates: Iterable[MortalityRate],
        basis: MortalityBasis,
    ):

        self.basis = basis

        self._rates = {
            rate.age: Decimal(rate.qx)
            for rate in rates
        }

        self._validate()


    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def _validate(self):

        if not self._rates:
            raise ValueError(
                "Mortality table cannot be empty."
            )

        for age, qx in self._rates.items():

            if age < 0:
                raise ValueError(
                    f"Invalid age: {age}"
                )

            if qx < 0 or qx > 1:
                raise ValueError(
                    f"qx must lie between 0 and 1 "
                    f"at age {age}."
                )


    # --------------------------------------------------------
    # qx
    # --------------------------------------------------------

    def qx(
        self,
        age: int,
    ) -> Decimal:
        """
        Probability that a life aged x dies
        before reaching age x + 1.
        """

        try:

            return self._rates[age]

        except KeyError:

            raise ValueError(
                f"No mortality rate available "
                f"for age {age}."
            )


    # --------------------------------------------------------
    # px
    # --------------------------------------------------------

    def px(
        self,
        age: int,
    ) -> Decimal:
        """
        One-year survival probability.

            px = 1 - qx
        """

        return (
            Decimal("1")
            -
            self.qx(age)
        )


    # --------------------------------------------------------
    # Monthly survival
    # --------------------------------------------------------

    def monthly_survival_probability(
        self,
        age: int,
    ) -> Decimal:
        """
        Equivalent one-month survival probability.

        We assume a constant force of mortality
        within each year of age.

            monthly_px = px^(1/12)
        """

        annual_survival = float(
            self.px(age)
        )

        monthly_survival = (
            annual_survival
            ** (1 / 12)
        )

        return Decimal(
            str(monthly_survival)
        )


    # --------------------------------------------------------
    # Survival for several months
    # --------------------------------------------------------

    def survival_probability_months(
        self,
        start_age: int,
        months: int,
    ) -> Decimal:
        """
        Probability that a person aged start_age
        survives for a specified number of months.

        Example:

            survival_probability_months(
                start_age=55,
                months=60
            )

        gives the probability of surviving
        approximately from age 55 to age 60.
        """

        if months < 0:
            raise ValueError(
                "Months cannot be negative."
            )

        if months == 0:
            return Decimal("1")

        survival = Decimal("1")

        for month in range(months):

            attained_age = (
                start_age
                +
                month // 12
            )

            monthly_px = (
                self
                .monthly_survival_probability(
                    attained_age
                )
            )

            survival *= monthly_px

        return survival


# ============================================================
# BUILD TABLE FROM mx VALUES
# ============================================================


def mortality_table_from_mx(
    rates: Iterable[MortalityCentralRate],
    basis: MortalityBasis,
) -> MortalityTable:
    """
    Construct a MortalityTable from mx values.

    Each source mx is converted to qx using:

        qx = 1 - exp(-mx)
    """

    qx_rates = [
        MortalityRate(
            age=rate.age,
            qx=mx_to_qx(
                rate.mx
            ),
        )
        for rate in rates
    ]

    return MortalityTable(
        rates=qx_rates,
        basis=basis,
    )


# ============================================================
# GENERIC qx CSV LOADER
# ============================================================


def load_mortality_table_csv(
    file_path: str | Path,
    *,
    basis: MortalityBasis,
) -> MortalityTable:
    """
    Load a simple CSV containing:

        age,qx

    This loader is useful for generic mortality
    tables that have already been converted to qx.
    """

    rates = []

    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        required_columns = {
            "age",
            "qx",
        }

        actual_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            required_columns
            -
            actual_columns
        )

        if missing_columns:

            raise ValueError(
                "Mortality CSV must contain "
                "age and qx columns."
            )

        for row in reader:

            age_text = (
                row["age"]
                .strip()
            )

            qx_text = (
                row["qx"]
                .strip()
            )

            if not age_text or not qx_text:
                continue

            rates.append(
                MortalityRate(
                    age=int(
                        age_text
                    ),
                    qx=Decimal(
                        qx_text
                    ),
                )
            )

    return MortalityTable(
        rates=rates,
        basis=basis,
    )


# ============================================================
# PENSIONIQ CLEAN MORTALITY CSV LOADER
# ============================================================


def load_pensioniq_mortality_csv(
    file_path: str | Path,
    *,
    year: int,
    sex: str,
) -> MortalityTable:
    """
    Load mortality data produced by the
    PensionIQ WPP importer.

    Expected columns include:

        year
        sex
        age
        mx
        qx
        source
        source_year
        estimate_type
        estimate_method
    """

    valid_sexes = {
        "Male",
        "Female",
    }

    if sex not in valid_sexes:
        raise ValueError(
            "sex must be Male or Female."
        )

    rates = []

    source = None
    model_type = None

    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        required_columns = {
            "year",
            "sex",
            "age",
            "qx",
            "source",
            "estimate_type",
            "estimate_method",
        }

        actual_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            required_columns
            -
            actual_columns
        )

        if missing_columns:

            raise ValueError(
                "Mortality file is missing columns: "
                +
                ", ".join(
                    sorted(
                        missing_columns
                    )
                )
            )

        for row in reader:

            year_text = (
                row["year"]
                .strip()
            )

            sex_text = (
                row["sex"]
                .strip()
            )

            age_text = (
                row["age"]
                .strip()
            )

            qx_text = (
                row["qx"]
                .strip()
            )

            if (
                not year_text
                or
                not sex_text
                or
                not age_text
                or
                not qx_text
            ):
                continue


            if int(year_text) != year:
                continue


            if sex_text != sex:
                continue


            age = int(
                age_text
            )

            qx = Decimal(
                qx_text
            )


            rates.append(
                MortalityRate(
                    age=age,
                    qx=qx,
                )
            )


            if source is None:

                source = (
                    row["source"]
                    .strip()
                )


            if model_type is None:

                estimate_type = (
                    row[
                        "estimate_type"
                    ]
                    .strip()
                )

                estimate_method = (
                    row[
                        "estimate_method"
                    ]
                    .strip()
                )

                model_type = (
                    f"{estimate_type} / "
                    f"{estimate_method}"
                )


    if not rates:

        raise ValueError(
            f"No mortality data found "
            f"for {sex}, {year}."
        )


    # --------------------------------------------------------
    # Make sure ages are unique
    # --------------------------------------------------------

    ages = [
        rate.age
        for rate in rates
    ]

    if len(ages) != len(set(ages)):

        raise ValueError(
            f"Duplicate mortality ages found "
            f"for {sex}, {year}."
        )


    # --------------------------------------------------------
    # Build mortality basis metadata
    # --------------------------------------------------------

    basis = MortalityBasis(

        source=(
            source
            or
            "Unknown mortality source"
        ),

        reference_year=year,

        sex=sex,

        population="Ghana",

        model_type=(
            model_type
            or
            "population mortality"
        ),
    )


    return MortalityTable(
        rates=rates,
        basis=basis,
    )


# ============================================================
# PENSION EXPECTED PRESENT VALUE
# ============================================================


def pension_expected_present_value(
    *,
    valuation_age: int,
    retirement_age: int,
    monthly_pension: Decimal,
    annual_discount_rate: Decimal,
    projection_age: int,
    mortality_table: MortalityTable,
) -> Decimal:
    """
    Calculate the mortality-adjusted Expected
    Present Value of a monthly pension.

    The model is:

        EPV =
            sum(
                monthly pension
                × survival probability
                × discount factor
            )

    Payments are assumed to occur monthly
    in arrears.

    Mortality:
        Survival is calculated from valuation_age.

    Discounting:
        annual effective rate is converted to an
        equivalent monthly effective rate.

    The current model does NOT include:

        - pension indexation
        - inflation-linked pension increases
        - spouse/survivor benefits
        - stochastic interest rates
        - SSNIT-specific pensioner mortality
    """

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if valuation_age < 0:
        raise ValueError(
            "Valuation age cannot be negative."
        )

    if retirement_age < valuation_age:
        raise ValueError(
            "Retirement age cannot be below "
            "valuation age."
        )

    if projection_age <= retirement_age:
        raise ValueError(
            "Projection age must exceed "
            "retirement age."
        )

    if monthly_pension < 0:
        raise ValueError(
            "Monthly pension cannot be negative."
        )

    if annual_discount_rate < 0:
        raise ValueError(
            "Discount rate cannot be negative."
        )


    if monthly_pension == 0:
        return Decimal("0")


    # --------------------------------------------------------
    # Convert annual effective discount rate
    # into monthly effective rate
    #
    # (1 + j)^12 = (1 + i)
    # --------------------------------------------------------

    monthly_discount_rate = Decimal(
        str(
            (
                1
                +
                float(
                    annual_discount_rate
                )
            )
            ** (1 / 12)
            -
            1
        )
    )


    # --------------------------------------------------------
    # First pension payment
    #
    # +1 means payments occur at the end
    # of the first pension month.
    # --------------------------------------------------------

    first_payment_month = (
        (
            retirement_age
            -
            valuation_age
        )
        *
        12
        +
        1
    )


    # --------------------------------------------------------
    # Final projection month
    # --------------------------------------------------------

    final_payment_month = (
        (
            projection_age
            -
            valuation_age
        )
        *
        12
    )


    epv = Decimal("0")


    # --------------------------------------------------------
    # Monthly EPV calculation
    # --------------------------------------------------------

    for month in range(
        first_payment_month,
        final_payment_month + 1,
    ):

        survival_probability = (
            mortality_table
            .survival_probability_months(
                start_age=valuation_age,
                months=month,
            )
        )


        discount_factor = (
            Decimal("1")
            +
            monthly_discount_rate
        ) ** month


        present_value_payment = (
            monthly_pension
            *
            survival_probability
            /
            discount_factor
        )


        epv += (
            present_value_payment
        )


    return epv