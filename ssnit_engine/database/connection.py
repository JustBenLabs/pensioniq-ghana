import os

from pathlib import Path

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)


DATA_DIRECTORY = (
    PROJECT_ROOT
    /
    "data"
)


DATA_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


SQLITE_DATABASE_PATH = (
    DATA_DIRECTORY
    /
    "pensioniq.db"
)


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


# ------------------------------------------------------------
# LOCAL DEVELOPMENT
# ------------------------------------------------------------

if not DATABASE_URL:

    DATABASE_URL = (
        f"sqlite:///"
        f"{SQLITE_DATABASE_PATH.as_posix()}"
    )


# ------------------------------------------------------------
# POSTGRESQL NORMALIZATION
# ------------------------------------------------------------
# Render may provide a URL beginning with:
#
# postgresql://
# or
# postgres://
#
# We explicitly use Psycopg 3 with SQLAlchemy.
# ------------------------------------------------------------

elif DATABASE_URL.startswith(
    "postgres://"
):

    DATABASE_URL = (
        DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    )


elif DATABASE_URL.startswith(
    "postgresql://"
):

    DATABASE_URL = (
        DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )
    )


# ============================================================
# ENGINE OPTIONS
# ============================================================

engine_options = {

    "pool_pre_ping":
        True,
}


if DATABASE_URL.startswith(
    "sqlite"
):

    engine_options[
        "connect_args"
    ] = {

        "check_same_thread":
            False
    }


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


# ============================================================
# SESSION FACTORY
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


# ============================================================
# BASE MODEL
# ============================================================

class Base(
    DeclarativeBase
):

    pass


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()