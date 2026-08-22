import argparse
import csv
from decimal import Decimal
from pathlib import Path

from ssnit_engine.mortality import mx_to_qx


SOURCE_NAME = "UN World Population Prospects 2024"

VALID_SEXES = {
    "Male",
    "Female",
}


def import_wpp_mortality(
    input_path: Path,
    output_path: Path,
    target_year: int | None = None,
) -> None:

    records = []

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "IndicatorId",
            "IndicatorName",
            "Source",
            "SourceYear",
            "Location",
            "Iso3",
            "Time",
            "Variant",
            "Sex",
            "AgeStart",
            "AgeEnd",
            "Age",
            "EstimateType",
            "EstimateMethod",
            "Value",
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
                "Missing required WPP columns: "
                + ", ".join(
                    sorted(missing_columns)
                )
            )

        available_years = set()

        for row in reader:

            # -------------------------
            # Confirm correct indicator
            # -------------------------

            if row["IndicatorId"] != "80":
                continue

            # -------------------------
            # Ghana only
            # -------------------------

            if row["Iso3"] != "GHA":
                continue

            if row["Location"] != "Ghana":
                continue

            # -------------------------
            # Median projection only
            # -------------------------

            if row["Variant"] != "Median":
                continue

            # -------------------------
            # Male / Female separately
            # -------------------------

            sex = row["Sex"]

            if sex not in VALID_SEXES:
                continue

            # -------------------------
            # Calendar year
            # -------------------------

            year = int(row["Time"])

            available_years.add(year)

            if (
                target_year is not None
                and year != target_year
            ):
                continue

            # -------------------------
            # Single-age records only
            # -----------------

            age_start_text = row["AgeStart"].strip()
            age_end_text = row["AgeEnd"].strip()

            invalid_age_values = {
                "",
                "null",
                "none",
                "na",
                "n/a",
            }

            if (
                age_start_text.lower()
                in invalid_age_values
                or
                age_end_text.lower()
                in invalid_age_values
            ):
                continue

            try:
                age_start = int(age_start_text)
                age_end = int(age_end_text)
            except ValueError:
                continue

            # We only want true single-age records.
            if age_start != age_end:
                continue

            age = age_start

            # PensionIQ retirement-age range
            if age < 55 or age > 100:
                continue

            # -------------------------
            # Mortality rate mx
            # -------------------------

            mx = Decimal(
                row["Value"]
            )

            if mx < 0:
                raise ValueError(
                    f"Negative mx found for "
                    f"{sex}, age {age}."
                )

            qx = mx_to_qx(mx)

            records.append(
                {
                    "year": year,
                    "sex": sex,
                    "age": age,
                    "mx": str(mx),
                    "qx": str(qx),
                    "source": SOURCE_NAME,
                    "source_year": row[
                        "SourceYear"
                    ],
                    "estimate_type": row[
                        "EstimateType"
                    ],
                    "estimate_method": row[
                        "EstimateMethod"
                    ],
                }
            )

    if not records:

        if target_year is not None:

            years_text = ", ".join(
                str(year)
                for year in sorted(
                    available_years
                )
            )

            raise ValueError(
                f"No usable Ghana mortality records "
                f"found for {target_year}. "
                f"Available years in the file: "
                f"{years_text or 'none'}."
            )

        raise ValueError(
            "No usable Ghana mortality records found."
        )

    # Male first, then Female, ordered by age
    sex_order = {
        "Male": 0,
        "Female": 1,
    }

    records.sort(
        key=lambda record: (
            sex_order[
                record["sex"]
            ],
            record["age"],
        )
    )

    # -------------------------
    # Validation
    # -------------------------

    validate_records(records)

    # -------------------------
    # Save cleaned data
    # -------------------------

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "year",
        "sex",
        "age",
        "mx",
        "qx",
        "source",
        "source_year",
        "estimate_type",
        "estimate_method",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(records)

    years = sorted(
        {
            record["year"]
            for record in records
        }
    )

    print(
        "WPP mortality import successful."
    )

    print(
        f"Input:  {input_path}"
    )

    print(
        f"Output: {output_path}"
    )

    print(
        f"Years:  {years}"
    )

    print(
        f"Rows:   {len(records)}"
    )

    for sex in VALID_SEXES:

        sex_records = [
            record
            for record in records
            if record["sex"] == sex
        ]

        if sex_records:

            ages = [
                record["age"]
                for record in sex_records
            ]

            print(
                f"{sex}: "
                f"{len(sex_records)} records, "
                f"ages {min(ages)}-{max(ages)}"
            )


def validate_records(
    records: list[dict],
) -> None:

    for record in records:

        qx = Decimal(
            record["qx"]
        )

        if qx < 0 or qx > 1:
            raise ValueError(
                "Converted qx must be "
                "between 0 and 1."
            )

    years = {
        record["year"]
        for record in records
    }

    for year in years:

        for sex in VALID_SEXES:

            ages = {
                record["age"]
                for record in records
                if (
                    record["year"]
                    == year
                    and
                    record["sex"]
                    == sex
                )
            }

            # We need at least 55-99 for
            # projections through age 100.
            required_ages = set(
                range(55, 100)
            )

            missing = (
                required_ages
                -
                ages
            )

            if missing:

                raise ValueError(
                    f"{sex} {year} mortality "
                    f"table is incomplete. "
                    f"Missing ages: "
                    f"{sorted(missing)}"
                )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Convert raw UN WPP Ghana "
            "age-specific mortality data "
            "into PensionIQ format."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Raw WPP CSV file.",
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Clean PensionIQ CSV.",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=(
            "Optional calendar year "
            "to import."
        ),
    )

    args = parser.parse_args()

    import_wpp_mortality(
        input_path=args.input,
        output_path=args.output,
        target_year=args.year,
    )


if __name__ == "__main__":
    main()