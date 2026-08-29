# ============================================================
# CREATE RETIREMENT PLANS TABLE
# ============================================================


from sqlalchemy import inspect


from ssnit_engine.database.connection import (
    engine,
)

from ssnit_engine.database.models import (
    RetirementPlan,
)


def main():

    inspector = inspect(
        engine
    )


    # --------------------------------------------------------
    # ALREADY EXISTS
    # --------------------------------------------------------

    if inspector.has_table(
        RetirementPlan.__tablename__
    ):

        print(
            "retirement_plans table already exists."
        )

        return


    # --------------------------------------------------------
    # CREATE TABLE
    # --------------------------------------------------------

    RetirementPlan.__table__.create(
        bind=engine,
        checkfirst=True,
    )


    print(
        "retirement_plans table created successfully."
    )


if __name__ == "__main__":

    main()