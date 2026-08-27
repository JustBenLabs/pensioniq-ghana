import os

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path

import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from jwt.exceptions import (
    InvalidTokenError,
)

from pwdlib import PasswordHash

from sqlalchemy.orm import Session

from ssnit_engine.database.connection import (
    get_db,
)

from ssnit_engine.database.models import (
    User,
)


def load_dotenv(path: Path) -> None:
    """Load environment values from a simple .env file if it exists."""
    if not path.is_file():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        os.environ.setdefault(key, value)


# ============================================================
# ENVIRONMENT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


load_dotenv(
    PROJECT_ROOT / ".env"
)


JWT_SECRET = os.getenv(
    "PENSIONIQ_JWT_SECRET"
)


if not JWT_SECRET:

    raise RuntimeError(
        "PENSIONIQ_JWT_SECRET environment "
        "variable is not configured."
    )


JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

JWT_ISSUER = "pensioniq-ghana-api"

JWT_AUDIENCE = "pensioniq-ghana-web"


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = (
    PasswordHash.recommended()
)


DUMMY_HASH = password_hash.hash(
    "pensioniq-dummy-password"
)


def hash_password(
    password: str,
) -> str:

    return password_hash.hash(
        password
    )


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:

    return password_hash.verify(
        password,
        hashed_password,
    )


# ============================================================
# JWT
# ============================================================

def create_access_token(
    user_id: int,
    token_version: int,
) -> str:

    now = datetime.now(
        timezone.utc
    )


    expires_at = (
        now
        +
        timedelta(
            minutes=(
                ACCESS_TOKEN_EXPIRE_MINUTES
            )
        )
    )


    payload = {

    "sub":
        str(user_id),

    "type":
        "access",

    "iat":
        now,

    "exp":
        expires_at,

    "ver":
        token_version,

    "iss":
        JWT_ISSUER,

    "aud":
        JWT_AUDIENCE,

}


    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


# ============================================================
# BEARER AUTHENTICATION
# ============================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


def get_current_user(

    credentials:
        HTTPAuthorizationCredentials
        | None
        =
        Depends(
            bearer_scheme
        ),

    db: Session = Depends(
        get_db
    ),

) -> User:

    if (
        credentials is None
        or
        credentials.scheme.lower()
        !=
        "bearer"
    ):

        raise HTTPException(

            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),

            detail=(
                "Authentication required."
            ),

            headers={
                "WWW-Authenticate":
                    "Bearer"
            },
        )


    token = credentials.credentials


    try:

        payload = jwt.decode(

    token,

    JWT_SECRET,

    algorithms=[
        JWT_ALGORITHM
    ],

    issuer=
        JWT_ISSUER,

    audience=
        JWT_AUDIENCE,

    options={
        "require": [
            "sub",
            "type",
            "iat",
            "exp",
            "ver",
            "iss",
            "aud",
        ]
    },
)


        if (
            payload.get("type")
            !=
            "access"
        ):

            raise HTTPException(

                status_code=(
                    status
                    .HTTP_401_UNAUTHORIZED
                ),

                detail=(
                    "Invalid authentication token."
                ),

                headers={
                    "WWW-Authenticate":
                        "Bearer"
                },
            )


        user_id_raw = (
            payload.get("sub")
        )


        if user_id_raw is None:

            raise HTTPException(

                status_code=(
                    status
                    .HTTP_401_UNAUTHORIZED
                ),

                detail=(
                    "Invalid authentication token."
                ),

                headers={
                    "WWW-Authenticate":
                        "Bearer"
                },
            )


        user_id = int(
            user_id_raw
        )


    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):

        raise HTTPException(

            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),

            detail=(
                "Invalid or expired "
                "authentication token."
            ),

            headers={
                "WWW-Authenticate":
                    "Bearer"
            },
        )


    user = db.get(
        User,
        user_id,
    )


    if (
        user is None
        or
        not user.is_active
    ):

        raise HTTPException(

            status_code=(
                status
                .HTTP_401_UNAUTHORIZED
            ),

            detail=(
                "Invalid authentication token."
            ),

            headers={
                "WWW-Authenticate":
                    "Bearer"
            },
        )
    token_version = payload.get(
        "ver"
    )


    if (
        token_version is None
        or
        token_version
        !=
        user.token_version
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Authentication token is no longer valid."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


    return user