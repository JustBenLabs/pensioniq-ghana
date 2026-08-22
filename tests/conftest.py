import os

import pytest

from fastapi.testclient import (
    TestClient,
)

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    sessionmaker,
)

from sqlalchemy.pool import (
    StaticPool,
)


# ============================================================
# TEST JWT SECRET
# ============================================================

os.environ.setdefault(
    "PENSIONIQ_JWT_SECRET",
    (
        "pensioniq-test-secret-"
        "do-not-use-in-production-"
        "123456789"
    ),
)


# Import application only AFTER
# the test JWT secret is configured.
os.environ[
    "PENSIONIQ_DEV_MODE"
] = "true"
from ssnit_engine.api import app

from ssnit_engine.database.connection import (
    Base,
    get_db,
)

# Import models so SQLAlchemy knows
# about all tables before create_all().

from ssnit_engine.database import models  # noqa: F401


# ============================================================
# TEST DATABASE
# ============================================================

TEST_DATABASE_URL = "sqlite://"


test_engine = create_engine(

    TEST_DATABASE_URL,

    connect_args={
        "check_same_thread":
            False
    },

    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(

    bind=test_engine,

    autoflush=False,

    expire_on_commit=False,
)


# ============================================================
# DATABASE FIXTURE
# ============================================================

@pytest.fixture()
def test_database():

    Base.metadata.create_all(
        bind=test_engine
    )


    yield


    Base.metadata.drop_all(
        bind=test_engine
    )


# ============================================================
# CLIENT FIXTURE
# ============================================================

@pytest.fixture()
def client(
    test_database,
):

    def override_get_db():

        db = TestingSessionLocal()

        try:

            yield db

        finally:

            db.close()


    app.dependency_overrides[
        get_db
    ] = override_get_db


    with TestClient(
        app
    ) as test_client:

        yield test_client


    app.dependency_overrides.clear()


# ============================================================
# DIRECT DATABASE SESSION
# ============================================================

@pytest.fixture()
def db_session(
    test_database,
):

    db = TestingSessionLocal()

    try:

        yield db

    finally:

        db.close()