from sqlalchemy import inspect, text

from ssnit_engine.database.connection import (
    engine,
)


def main():

    inspector = inspect(engine)

    tables = inspector.get_table_names()


    if "users" not in tables:

        print(
            "users table does not exist."
        )

        return


    columns = {
        column["name"]
        for column
        in inspector.get_columns("users")
    }


    if "token_version" in columns:

        print(
            "token_version already exists."
        )

        return


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN token_version
                INTEGER NOT NULL DEFAULT 0
                """
            )
        )


    print(
        "token_version added successfully."
    )


if __name__ == "__main__":
    main()