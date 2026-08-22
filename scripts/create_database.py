import sys
from pathlib import Path


sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

# The project root is added above so this script also works when run directly.
from ssnit_engine.database.connection import (  # pyright: ignore[reportMissingImports]
    Base,
    engine,
)

from ssnit_engine.database import models  # pyright: ignore[reportMissingImports]


def main():

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "PensionIQ database created successfully."
    )


if __name__ == "__main__":
    main()