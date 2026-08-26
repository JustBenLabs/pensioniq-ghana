import hashlib
import os
import secrets
from ssnit_engine.email_service import (
    send_password_reset_email,
)
from datetime import (
    UTC,
    date,
    datetime,
    timedelta,
)
from decimal import Decimal
from enum import Enum
from pathlib import Path

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from pydantic import (
    BaseModel,
    EmailStr,
)

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ssnit_engine.auth import (
    DUMMY_HASH,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

from ssnit_engine.contribution_health import (
    analyse_contribution_history,
)

from ssnit_engine.database.connection import (
    get_db,
)

from ssnit_engine.database.models import (
    ContributionRecord,
    Member,
    PasswordResetToken,
    User,
)

from ssnit_engine.engine import (
    BenefitEvent,
    calculate_master_benefit,
    calculate_pension_right,
    master_result_summary,
)

from ssnit_engine.mortality import (
    load_pensioniq_mortality_csv,
    pension_expected_present_value,
)
from ssnit_engine.rate_limit import (
    forgot_password_rate_limit,
    login_rate_limit,
    register_rate_limit,
    reset_password_rate_limit,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="PensionIQ Ghana API",
    version="1.0.0",
    description=(
        "Retirement planning, contribution analysis "
        "and actuarial estimation API for PensionIQ Ghana. "
        "Official SSNIT records and determinations govern "
        "actual pension benefits."
    ),
)


# ============================================================
# CORS
# ============================================================

# ==========================================================
# CORS CONFIGURATION
# ==========================================================

FRONTEND_BASE_URL = os.getenv(
    "PENSIONIQ_FRONTEND_BASE_URL",
    "http://127.0.0.1:5500",
).rstrip("/")

allowed_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://pensioniq-ghana.web.app",
    "https://pensioniq-ghana.firebaseapp.com",
]

if FRONTEND_BASE_URL not in allowed_origins:
    allowed_origins.append(
        FRONTEND_BASE_URL
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def add_security_headers(
    request,
    call_next,
):
    response = await call_next(request)

    # Prevent browsers from guessing MIME/content types.
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    # Prevent this API from being embedded in frames.
    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    # Avoid leaking URL/referrer information.
    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    # PensionIQ does not need access to these browser features.
    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=()"
    )

    # Tell browsers to use HTTPS for the public Render service.
    forwarded_proto = request.headers.get(
        "x-forwarded-proto",
        request.url.scheme,
    )

    if forwarded_proto == "https":
        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )

    return response

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


MORTALITY_DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "ghana_mortality_2025.csv"
)


MORTALITY_YEAR = 2025


# ============================================================
# REQUEST MODELS
# ============================================================


class PensionRightRequest(BaseModel):

    contribution_months: int


class RetirementRequest(BaseModel):

    date_of_birth: date

    retirement_date: date

    contribution_months: int

    best_three_year_average_annual_salary: Decimal

    qualifying_hazardous_employment: bool = False

    returnable_contribution_principal: Decimal | None = None

    prevailing_91_day_tbill_rate: Decimal | None = None

    official_interest_amount: Decimal | None = None


class RetirementComparisonRequest(BaseModel):

    date_of_birth: date

    contribution_months_at_55: int

    best_three_year_average_annual_salary: Decimal

    qualifying_hazardous_employment: bool = False


class RetirementEPVRequest(BaseModel):

    date_of_birth: date

    retirement_age: int

    contribution_months_at_55: int

    best_three_year_average_annual_salary: Decimal

    sex: str

    annual_discount_rate_percent: Decimal = Decimal("8")

    projection_age: int = 80

    qualifying_hazardous_employment: bool = False


class RetirementEPVComparisonRequest(BaseModel):

    date_of_birth: date

    contribution_months_at_55: int

    best_three_year_average_annual_salary: Decimal

    sex: str

    annual_discount_rate_percent: Decimal = Decimal("8")

    projection_age: int = 80

    qualifying_hazardous_employment: bool = False


class MemberUpdateRequest(BaseModel):

    first_name: str | None = None

    last_name: str | None = None

    date_of_birth: date | None = None

    sex: str | None = None

    contribution_months: int | None = None

    best_three_year_average_annual_salary: Decimal | None = None


class ContributionCreateRequest(BaseModel):

    year: int

    month: int

    insurable_earnings: Decimal

    recorded_first_tier_contribution: Decimal | None = None


class ContributionUpdateRequest(BaseModel):

    year: int | None = None

    month: int | None = None

    insurable_earnings: Decimal | None = None

    recorded_first_tier_contribution: Decimal | None = None


class RegisterRequest(BaseModel):

    email: EmailStr

    password: str

    first_name: str

    last_name: str

    date_of_birth: date

    sex: str

    contribution_months: int = 0

    best_three_year_average_annual_salary: Decimal = Decimal("0")


class LoginRequest(BaseModel):

    email: EmailStr

    password: str
class ChangePasswordRequest(BaseModel):

    current_password: str

    new_password: str
class ForgotPasswordRequest(BaseModel):

    email: EmailStr


class ResetPasswordRequest(BaseModel):

    token: str

    new_password: str
# ============================================================
# GENERAL HELPERS
# ============================================================


def serialize_value(
    value,
):

    if isinstance(
        value,
        Decimal,
    ):
        return str(value)

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    return value


def birthday_at_age(
    date_of_birth: date,
    age: int,
) -> date:

    target_year = (
        date_of_birth.year
        +
        age
    )

    try:

        return date_of_birth.replace(
            year=target_year
        )

    except ValueError:

        return date(
            target_year,
            2,
            28,
        )


def calculate_current_age(
    date_of_birth: date,
) -> int:

    today = date.today()

    age = (
        today.year
        -
        date_of_birth.year
    )

    if (
        today.month,
        today.day,
    ) < (
        date_of_birth.month,
        date_of_birth.day,
    ):

        age -= 1

    return age
def validate_member_date_of_birth(
    date_of_birth: date,
) -> None:
    """
    Validate a member's date of birth for
    PensionIQ profile/account data.

    These are application-level plausibility
    checks, not official SSNIT eligibility rules.
    """

    if date_of_birth > date.today():
        raise HTTPException(
            status_code=400,
            detail=(
                "Date of birth cannot be "
                "in the future."
            ),
        )

    age = calculate_current_age(
        date_of_birth
    )

    if age < 15:
        raise HTTPException(
            status_code=400,
            detail=(
                "Member must be at least "
                "15 years old."
            ),
        )

    if age > 120:
        raise HTTPException(
            status_code=400,
            detail=(
                "Date of birth produces an "
                "implausible member age."
            ),
        )

def extract_pension_right(
    result,
) -> str | None:

    if not isinstance(
        result.details,
        dict,
    ):
        return None

    right = (
        result.details.get(
            "pension_right"
        )
    )

    if right is None:
        return None

    return str(right)


def validate_sex(
    sex: str,
):

    if sex not in {
        "Male",
        "Female",
    }:

        raise ValueError(
            "Sex must be Male or Female."
        )


def validate_projection_age(
    projection_age: int,
    retirement_age: int | None = None,
):

    if retirement_age is not None:

        if (
            projection_age
            <=
            retirement_age
        ):

            raise ValueError(
                "Projection age must exceed "
                "retirement age."
            )

    else:

        if projection_age <= 60:

            raise ValueError(
                "Projection age must be "
                "greater than 60."
            )


    if projection_age > 100:

        raise ValueError(
            "Projection age cannot exceed 100 "
            "with the current mortality table."
        )


def load_current_mortality_table(
    sex: str,
):

    validate_sex(
        sex
    )


    if not MORTALITY_DATA_FILE.exists():

        raise ValueError(
            "Mortality data file was not found: "
            f"{MORTALITY_DATA_FILE}"
        )


    return (
        load_pensioniq_mortality_csv(
            MORTALITY_DATA_FILE,
            year=MORTALITY_YEAR,
            sex=sex,
        )
    )
def hash_password_reset_token(
    token: str,
) -> str:

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
def validate_contribution_months_for_age(
    date_of_birth: date,
    contribution_months: int,
) -> None:
    """
    Check whether contribution months are
    plausible for the member's age.

    This is a PensionIQ data-quality check,
    not an official SSNIT determination.
    """

    if contribution_months < 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Contribution months "
                "cannot be negative."
            ),
        )

    age = calculate_current_age(
        date_of_birth
    )

    # Allow one full extra year as a generous
    # calendar-month buffer.
    maximum_plausible_months = max(
        0,
        (age - 15 + 1) * 12,
    )

    if (
        contribution_months
        >
        maximum_plausible_months
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Contribution months are not "
                "plausible for the member's age."
            ),
        )
# ============================================================
# AUTHORIZATION
# ============================================================


def require_member_ownership(
    member_id: int,
    current_user: User,
):

    if (
        current_user.member_id
        !=
        member_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You are not authorized to access "
                "this member's information."
            ),
        )


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
def health():

    return {
        "status": "ok",
        "engine": "pensioniq-ghana",
        "version": "1.0.0",
        "mortality_year": MORTALITY_YEAR,
    }


# ============================================================
# AUTHENTICATION — REGISTER
# ============================================================


@app.post(
    "/auth/register",
    dependencies=[
        Depends(register_rate_limit)
    ],
)
def register(
    request: RegisterRequest,
    db: Session = Depends(
        get_db
    ),
):

    email = (
        str(
            request.email
        )
        .strip()
        .lower()
    )


    first_name = (
        request.first_name
        .strip()
    )


    last_name = (
        request.last_name
        .strip()
    )


    if not first_name:

        raise HTTPException(
            status_code=400,
            detail="First name is required.",
        )


    if not last_name:

        raise HTTPException(
            status_code=400,
            detail="Last name is required.",
        )


    validate_member_date_of_birth(
    request.date_of_birth
)
    validate_contribution_months_for_age(
    request.date_of_birth,
    request.contribution_months,
)


    if request.sex not in {
        "Male",
        "Female",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "Sex must be Male or Female."
            ),
        )


    if (
        request.contribution_months
        <
        0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Contribution months "
                "cannot be negative."
            ),
        )


    if (
        request
        .best_three_year_average_annual_salary
        <
        0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Salary cannot be negative."
            ),
        )


    if (
        len(request.password) < 8
        or
        len(request.password) > 128
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain between "
                "8 and 128 characters."
            ),
        )


    existing_user = db.scalar(
        select(
            User
        )
        .where(
            User.email
            ==
            email
        )
    )


    if existing_user is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "An account already exists "
                "for this email address."
            ),
        )


    try:

        member = Member(

            first_name=first_name,

            last_name=last_name,

            date_of_birth=(
                request.date_of_birth
            ),

            sex=request.sex,

            contribution_months=(
                request.contribution_months
            ),

            best_three_year_average_annual_salary=(
                request
                .best_three_year_average_annual_salary
            ),
        )


        db.add(
            member
        )


        db.flush()


        user = User(

            email=email,

            password_hash=(
                hash_password(
                    request.password
                )
            ),

            member_id=(
                member.id
            ),

            is_active=True,
        )


        db.add(
            user
        )


        db.commit()


        db.refresh(
            user
        )


        return {

            "message":
                "Account created successfully.",

            "user": {

                "id":
                    user.id,

                "email":
                    user.email,

                "member_id":
                    user.member_id,
            },
        }


    except IntegrityError:

        db.rollback()


        raise HTTPException(
            status_code=409,
            detail=(
                "Unable to create account because "
                "one of the account details "
                "already exists."
            ),
        )


# ============================================================
# AUTHENTICATION — LOGIN
# ============================================================


@app.post(
    "/auth/login",
    dependencies=[
        Depends(login_rate_limit)
    ],
)
def login(
    request: LoginRequest,
    db: Session = Depends(
        get_db
    ),
):

    email = (
        str(
            request.email
        )
        .strip()
        .lower()
    )


    user = db.scalar(
        select(
            User
        )
        .where(
            User.email
            ==
            email
        )
    )


    if user is None:

        verify_password(
            request.password,
            DUMMY_HASH,
        )


        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password."
            ),
        )


    if not user.is_active:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password."
            ),
        )


    if not verify_password(
        request.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid email or password."
            ),
        )


    access_token = create_access_token(
    user.id,
    user.token_version,
)


    return {

        "access_token":
            access_token,

        "token_type":
            "bearer",

        "expires_in_seconds":
            3600,
    }


# ============================================================
# AUTHENTICATION — CURRENT USER
# ============================================================


@app.get("/auth/me")
def auth_me(
    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    member = db.get(
        Member,
        current_user.member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Member profile not found."
            ),
        )


    return {

        "user": {

            "id":
                current_user.id,

            "email":
                current_user.email,

            "is_active":
                current_user.is_active,
        },


        "member": {

            "id":
                member.id,

            "first_name":
                member.first_name,

            "last_name":
                member.last_name,

            "date_of_birth":
                member.date_of_birth,

            "sex":
                member.sex,

            "contribution_months":
                member.contribution_months,

            "best_three_year_average_annual_salary":
                str(
                    member
                    .best_three_year_average_annual_salary
                ),
        },
    }

# ============================================================
# AUTHENTICATION — CHANGE PASSWORD
# ============================================================


@app.post("/auth/change-password")
def change_password(
    request: ChangePasswordRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        request.current_password,
        current_user.password_hash,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Current password is incorrect."
            ),
        )


    # --------------------------------------------------------
    # Validate new password
    # --------------------------------------------------------

    if (
        len(request.new_password) < 8
        or
        len(request.new_password) > 128
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must contain between "
                "8 and 128 characters."
            ),
        )


    if (
        request.new_password
        ==
        request.current_password
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must be different "
                "from your current password."
            ),
        )


    # --------------------------------------------------------
    # Update password
    # --------------------------------------------------------

    current_user.password_hash = (
        hash_password(
            request.new_password
        )
    )
    current_user.token_version += 1


    db.commit()


    return {
        "message":
            "Password changed successfully."
    }

# ============================================================
# AUTHENTICATION — FORGOT PASSWORD
# ============================================================


# ============================================================
# AUTHENTICATION — FORGOT PASSWORD
# ============================================================


@app.post(
    "/auth/forgot-password",
    dependencies=[
        Depends(
            forgot_password_rate_limit
        )
    ],
)
def forgot_password(
    request: ForgotPasswordRequest,

    db: Session = Depends(
        get_db
    ),
):

    email = (
        str(request.email)
        .strip()
        .lower()
    )


    # --------------------------------------------------------
    # Generic public response
    # --------------------------------------------------------
    # We deliberately return the same response whether or not
    # the email exists. This prevents account enumeration.
    # --------------------------------------------------------

    public_response = {
        "message": (
            "If an account exists for this email address, "
            "password reset instructions have been generated."
        )
    }


    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = db.scalar(
        select(User)
        .where(
            User.email == email
        )
    )


    # Unknown or inactive account.
    # Return the same generic response.

    if (
        user is None
        or
        not user.is_active
    ):

        return public_response


    now = datetime.now(UTC)


    # --------------------------------------------------------
    # Invalidate previous unused reset tokens
    # --------------------------------------------------------

    previous_tokens = db.scalars(
        select(
            PasswordResetToken
        )
        .where(
            PasswordResetToken.user_id
            ==
            user.id,

            PasswordResetToken.used_at
            .is_(None),
        )
    ).all()


    for previous_token in previous_tokens:

        previous_token.used_at = now


    # --------------------------------------------------------
    # Generate new secure reset token
    # --------------------------------------------------------

    raw_token = secrets.token_urlsafe(
        32
    )


    token_hash = (
        hash_password_reset_token(
            raw_token
        )
    )


    reset_token = PasswordResetToken(

        user_id=user.id,

        token_hash=token_hash,

        expires_at=(
            now
            +
            timedelta(
                minutes=15
            )
        ),

        used_at=None,
    )


    db.add(
        reset_token
    )


    # --------------------------------------------------------
    # Build frontend reset URL
    # --------------------------------------------------------

    reset_url = (
        f"{FRONTEND_BASE_URL}/"
        f"reset-password.html"
        f"?token={raw_token}"
    )

    # --------------------------------------------------------
    # Development / production delivery
    # --------------------------------------------------------

    development_mode = (
        os.getenv(
            "PENSIONIQ_DEV_MODE",
            "false",
        )
        .strip()
        .lower()
        ==
        "true"
    )


    try:

        if development_mode:

            print()

            print(
                "========================================"
            )

            print(
                "PENSIONIQ DEVELOPMENT PASSWORD RESET"
            )

            print(
                f"Email: {email}"
            )

            print(
                f"Reset link: {reset_url}"
            )

            print(
                "Expires in: 15 minutes"
            )

            print(
                "========================================"
            )

            print()

        else:

            send_password_reset_email(
                recipient_email=email,
                reset_url=reset_url,
            )


        db.commit()


    except Exception as exc:

        db.rollback()


        # Do not expose delivery failure
        # to the person making the request.

        print(
        f"Password reset email delivery failed: "
        f"{type(exc).__name__}: {exc}"
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # This return must be OUTSIDE the try/except.
    # --------------------------------------------------------

    return public_response
# ============================================================
# AUTHENTICATION — RESET PASSWORD
# ============================================================


@app.post(
    "/auth/reset-password",
    dependencies=[
        Depends(
            reset_password_rate_limit
        )
    ],
)
def reset_password(
    request: ResetPasswordRequest,

    db: Session = Depends(
        get_db
    ),
):

    raw_token = (
        request.token.strip()
    )


    if not raw_token:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or expired "
                "password reset token."
            ),
        )


    if (
        len(request.new_password) < 8
        or
        len(request.new_password) > 128
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must contain between "
                "8 and 128 characters."
            ),
        )


    token_hash = (
        hash_password_reset_token(
            raw_token
        )
    )


    now = datetime.now(UTC)


    reset_record = db.scalar(
        select(
            PasswordResetToken
        )
        .where(
            PasswordResetToken.token_hash
            ==
            token_hash,

            PasswordResetToken.used_at
            .is_(None),

            PasswordResetToken.expires_at
            >
            now,
        )
    )


    if reset_record is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or expired "
                "password reset token."
            ),
        )


    user = db.get(
        User,
        reset_record.user_id,
    )


    if (
        user is None
        or
        not user.is_active
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or expired "
                "password reset token."
            ),
        )


    # --------------------------------------------------------
    # Change password
    # --------------------------------------------------------

    user.password_hash = (
        hash_password(
            request.new_password
        )
    )


    # Invalidate every existing JWT.

    user.token_version += 1


    # Mark this token as consumed.

    reset_record.used_at = now


    # --------------------------------------------------------
    # Invalidate any other outstanding reset tokens
    # --------------------------------------------------------

    remaining_tokens = db.scalars(
        select(
            PasswordResetToken
        )
        .where(
            PasswordResetToken.user_id
            ==
            user.id,

            PasswordResetToken.used_at
            .is_(None),
        )
    ).all()


    for token_record in remaining_tokens:

        token_record.used_at = now


    db.commit()


    return {
        "message": (
            "Password reset successfully. "
            "Please sign in with your new password."
        )
    }
# ============================================================
# PENSION RIGHT
# ============================================================


@app.post("/pension-right")
def pension_right(
    request: PensionRightRequest,
):

    try:

        if (
            request.contribution_months
            <
            0
        ):

            raise ValueError(
                "Contribution months "
                "cannot be negative."
            )


        result = (
            calculate_pension_right(
                request.contribution_months
            )
            if (
                request.contribution_months
                >=
                180
            )
            else None
        )


        return {

            "contribution_months":
                request.contribution_months,

            "pension_right":
                (
                    str(result)
                    if result
                    is not None
                    else None
                ),

            "eligible_for_monthly_old_age_pension":
                (
                    request.contribution_months
                    >=
                    180
                ),
        }


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# RETIREMENT BENEFIT
# ============================================================


@app.post("/benefits/retirement")
def retirement(
    request: RetirementRequest,
):

    try:

        if (
            request.contribution_months
            <
            0
        ):

            raise ValueError(
                "Contribution months "
                "cannot be negative."
            )


        if (
            request
            .best_three_year_average_annual_salary
            <
            0
        ):

            raise ValueError(
                "Salary cannot be negative."
            )


        result = (
            calculate_master_benefit(

                event=BenefitEvent.RETIREMENT,

                date_of_birth=(
                    request.date_of_birth
                ),

                event_date=(
                    request.retirement_date
                ),

                contribution_months=(
                    request.contribution_months
                ),

                best_three_year_average_annual_salary=(
                    request
                    .best_three_year_average_annual_salary
                ),

                qualifying_hazardous_employment=(
                    request
                    .qualifying_hazardous_employment
                ),

                returnable_contribution_principal=(
                    request
                    .returnable_contribution_principal
                ),

                prevailing_91_day_tbill_rate=(
                    request
                    .prevailing_91_day_tbill_rate
                ),

                official_interest_amount=(
                    request
                    .official_interest_amount
                ),
            )
        )


        summary = (
            master_result_summary(
                result
            )
        )


        response_data = {

            key:
                serialize_value(
                    value
                )

            for key, value
            in summary.items()
        }


        response_data[
            "pension_right"
        ] = extract_pension_right(
            result
        )


        response_data[
            "contribution_months"
        ] = request.contribution_months


        return response_data


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# RETIREMENT COMPARISON
# ============================================================


@app.post(
    "/benefits/retirement-comparison"
)
def retirement_comparison(
    request: RetirementComparisonRequest,
):

    try:

        if (
            request.contribution_months_at_55
            <
            0
        ):

            raise ValueError(
                "Contribution months "
                "cannot be negative."
            )


        if (
            request
            .best_three_year_average_annual_salary
            <
            0
        ):

            raise ValueError(
                "Salary cannot be negative."
            )


        scenarios = []


        for retirement_age in range(
            55,
            61,
        ):

            retirement_date = (
                birthday_at_age(
                    request.date_of_birth,
                    retirement_age,
                )
            )


            contribution_months = (
                request
                .contribution_months_at_55
                +
                (
                    retirement_age
                    -
                    55
                )
                *
                12
            )


            result = (
                calculate_master_benefit(

                    event=(
                        BenefitEvent
                        .RETIREMENT
                    ),

                    date_of_birth=(
                        request.date_of_birth
                    ),

                    event_date=(
                        retirement_date
                    ),

                    contribution_months=(
                        contribution_months
                    ),

                    best_three_year_average_annual_salary=(
                        request
                        .best_three_year_average_annual_salary
                    ),

                    qualifying_hazardous_employment=(
                        request
                        .qualifying_hazardous_employment
                    ),
                )
            )


            scenarios.append(
                {

                    "retirement_age":
                        retirement_age,

                    "retirement_date":
                        retirement_date
                        .isoformat(),

                    "contribution_months":
                        contribution_months,

                    "pension_right":
                        extract_pension_right(
                            result
                        ),

                    "benefit_type":
                        serialize_value(
                            result.routed_benefit
                        ),

                    "eligible":
                        result.eligible,

                    "monthly_benefit":
                        (
                            str(
                                result.monthly_benefit
                            )
                            if (
                                result.monthly_benefit
                                is not None
                            )
                            else None
                        ),

                    "calculation_status":
                        serialize_value(
                            result.calculation_status
                        ),
                }
            )


        return {

            "assumptions": {

                "salary_basis_constant":
                    True,

                "continuous_future_contributions":
                    True,

                "additional_months_per_year":
                    12,
            },

            "scenarios":
                scenarios,
        }


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# SINGLE RETIREMENT EPV
# ============================================================


@app.post(
    "/benefits/retirement-epv"
)
def retirement_epv(
    request: RetirementEPVRequest,
):

    try:

        if (
            request.retirement_age < 55
            or
            request.retirement_age > 60
        ):

            raise ValueError(
                "Retirement age must be "
                "between 55 and 60."
            )


        validate_sex(
            request.sex
        )


        if (
            request.contribution_months_at_55
            <
            0
        ):

            raise ValueError(
                "Contribution months "
                "cannot be negative."
            )


        if (
            request
            .best_three_year_average_annual_salary
            <
            0
        ):

            raise ValueError(
                "Salary cannot be negative."
            )


        validate_projection_age(
            request.projection_age,
            request.retirement_age,
        )


        if (
            request
            .annual_discount_rate_percent
            <
            0
        ):

            raise ValueError(
                "Discount rate "
                "cannot be negative."
            )


        retirement_date = (
            birthday_at_age(
                request.date_of_birth,
                request.retirement_age,
            )
        )


        contribution_months = (
            request.contribution_months_at_55
            +
            (
                request.retirement_age
                -
                55
            )
            *
            12
        )


        result = (
            calculate_master_benefit(

                event=BenefitEvent.RETIREMENT,

                date_of_birth=(
                    request.date_of_birth
                ),

                event_date=(
                    retirement_date
                ),

                contribution_months=(
                    contribution_months
                ),

                best_three_year_average_annual_salary=(
                    request
                    .best_three_year_average_annual_salary
                ),

                qualifying_hazardous_employment=(
                    request
                    .qualifying_hazardous_employment
                ),
            )
        )


        if (
            result.monthly_benefit
            is None
        ):

            return {

                "eligible":
                    result.eligible,

                "retirement_age":
                    request.retirement_age,

                "retirement_date":
                    retirement_date
                    .isoformat(),

                "contribution_months":
                    contribution_months,

                "monthly_pension":
                    None,

                "pension_right":
                    extract_pension_right(
                        result
                    ),

                "expected_present_value":
                    None,

                "message":
                    (
                        "No monthly pension is "
                        "available for this scenario."
                    ),
            }


        mortality_table = (
            load_current_mortality_table(
                request.sex
            )
        )


        annual_discount_rate = (
            request
            .annual_discount_rate_percent
            /
            Decimal("100")
        )


        epv = (
            pension_expected_present_value(

                valuation_age=55,

                retirement_age=(
                    request.retirement_age
                ),

                monthly_pension=(
                    result.monthly_benefit
                ),

                annual_discount_rate=(
                    annual_discount_rate
                ),

                projection_age=(
                    request.projection_age
                ),

                mortality_table=(
                    mortality_table
                ),
            )
        )


        return {

            "eligible":
                result.eligible,

            "retirement_age":
                request.retirement_age,

            "retirement_date":
                retirement_date
                .isoformat(),

            "contribution_months":
                contribution_months,

            "monthly_pension":
                str(
                    result.monthly_benefit
                ),

            "pension_right":
                extract_pension_right(
                    result
                ),

            "sex":
                request.sex,

            "discount_rate_percent":
                str(
                    request
                    .annual_discount_rate_percent
                ),

            "projection_age":
                request.projection_age,

            "valuation_age":
                55,

            "expected_present_value":
                str(
                    epv.quantize(
                        Decimal("0.01")
                    )
                ),

            "mortality_basis": {

                "source":
                    mortality_table
                    .basis
                    .source,

                "population":
                    mortality_table
                    .basis
                    .population,

                "sex":
                    mortality_table
                    .basis
                    .sex,

                "reference_year":
                    mortality_table
                    .basis
                    .reference_year,

                "model_type":
                    mortality_table
                    .basis
                    .model_type,
            },

            "calculation_status":
                "ACTUARIAL_ESTIMATE",

            "important_note":
                (
                    "Mortality is based on Ghana "
                    "population mortality and is not "
                    "an official SSNIT pensioner "
                    "mortality table."
                ),
        }


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# RETIREMENT EPV COMPARISON
# ============================================================


@app.post(
    "/benefits/retirement-epv-comparison"
)
def retirement_epv_comparison(
    request: RetirementEPVComparisonRequest,
):

    try:

        validate_sex(
            request.sex
        )


        if (
            request.contribution_months_at_55
            <
            0
        ):

            raise ValueError(
                "Contribution months "
                "cannot be negative."
            )


        if (
            request
            .best_three_year_average_annual_salary
            <
            0
        ):

            raise ValueError(
                "Salary cannot be negative."
            )


        validate_projection_age(
            request.projection_age
        )


        if (
            request
            .annual_discount_rate_percent
            <
            0
        ):

            raise ValueError(
                "Discount rate "
                "cannot be negative."
            )


        mortality_table = (
            load_current_mortality_table(
                request.sex
            )
        )


        annual_discount_rate = (
            request
            .annual_discount_rate_percent
            /
            Decimal("100")
        )


        scenarios = []


        for retirement_age in range(
            55,
            61,
        ):

            retirement_date = (
                birthday_at_age(
                    request.date_of_birth,
                    retirement_age,
                )
            )


            contribution_months = (
                request
                .contribution_months_at_55
                +
                (
                    retirement_age
                    -
                    55
                )
                *
                12
            )


            result = (
                calculate_master_benefit(

                    event=(
                        BenefitEvent
                        .RETIREMENT
                    ),

                    date_of_birth=(
                        request.date_of_birth
                    ),

                    event_date=(
                        retirement_date
                    ),

                    contribution_months=(
                        contribution_months
                    ),

                    best_three_year_average_annual_salary=(
                        request
                        .best_three_year_average_annual_salary
                    ),

                    qualifying_hazardous_employment=(
                        request
                        .qualifying_hazardous_employment
                    ),
                )
            )


            if (
                result.monthly_benefit
                is None
            ):

                scenarios.append(
                    {

                        "retirement_age":
                            retirement_age,

                        "retirement_date":
                            retirement_date
                            .isoformat(),

                        "contribution_months":
                            contribution_months,

                        "eligible":
                            result.eligible,

                        "monthly_pension":
                            None,

                        "pension_right":
                            extract_pension_right(
                                result
                            ),

                        "expected_present_value":
                            None,

                        "benefit_type":
                            serialize_value(
                                result.routed_benefit
                            ),

                        "calculation_status":
                            serialize_value(
                                result.calculation_status
                            ),
                    }
                )

                continue


            epv = (
                pension_expected_present_value(

                    valuation_age=55,

                    retirement_age=(
                        retirement_age
                    ),

                    monthly_pension=(
                        result.monthly_benefit
                    ),

                    annual_discount_rate=(
                        annual_discount_rate
                    ),

                    projection_age=(
                        request.projection_age
                    ),

                    mortality_table=(
                        mortality_table
                    ),
                )
            )


            scenarios.append(
                {

                    "retirement_age":
                        retirement_age,

                    "retirement_date":
                        retirement_date
                        .isoformat(),

                    "contribution_months":
                        contribution_months,

                    "eligible":
                        result.eligible,

                    "monthly_pension":
                        str(
                            result.monthly_benefit
                        ),

                    "pension_right":
                        extract_pension_right(
                            result
                        ),

                    "expected_present_value":
                        str(
                            epv.quantize(
                                Decimal("0.01")
                            )
                        ),

                    "benefit_type":
                        serialize_value(
                            result.routed_benefit
                        ),

                    "calculation_status":
                        serialize_value(
                            result.calculation_status
                        ),
                }
            )


        return {

            "sex":
                request.sex,

            "discount_rate_percent":
                str(
                    request
                    .annual_discount_rate_percent
                ),

            "projection_age":
                request.projection_age,

            "valuation_age":
                55,

            "mortality_basis": {

                "source":
                    mortality_table
                    .basis
                    .source,

                "population":
                    mortality_table
                    .basis
                    .population,

                "sex":
                    mortality_table
                    .basis
                    .sex,

                "reference_year":
                    mortality_table
                    .basis
                    .reference_year,

                "model_type":
                    mortality_table
                    .basis
                    .model_type,
            },

            "assumptions": {

                "salary_basis_constant":
                    True,

                "continuous_future_contributions":
                    True,

                "additional_contribution_months_per_year":
                    12,

                "mortality_adjusted":
                    True,

                "pension_indexation_included":
                    False,

                "valuation_age":
                    55,
            },

            "scenarios":
                scenarios,

            "important_note":
                (
                    "Mortality is based on Ghana "
                    "population mortality and is not "
                    "an official SSNIT pensioner "
                    "mortality table."
                ),
        }


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# MEMBER — GET PROFILE
# ============================================================


@app.get(
    "/members/{member_id}"
)
def get_member(
    member_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    return {

        "id":
            member.id,

        "first_name":
            member.first_name,

        "last_name":
            member.last_name,

        "date_of_birth":
            member.date_of_birth,

        "sex":
            member.sex,

        "contribution_months":
            member.contribution_months,

        "best_three_year_average_annual_salary":
            str(
                member
                .best_three_year_average_annual_salary
            ),

        "created_at":
            member.created_at,
    }


# ============================================================
# MEMBER — UPDATE PROFILE
# ============================================================


@app.put(
    "/members/{member_id}"
)
def update_member(
    member_id: int,

    request: MemberUpdateRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    updates = (
        request.model_dump(
            exclude_unset=True
        )
    )


    if (
        "first_name" in updates
        and
        (
            updates["first_name"]
            is None
            or
            not updates[
                "first_name"
            ].strip()
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "First name cannot be empty."
            ),
        )


    if (
        "last_name" in updates
        and
        (
            updates["last_name"]
            is None
            or
            not updates[
                "last_name"
            ].strip()
        )
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Last name cannot be empty."
            ),
        )


    if "date_of_birth" in updates:
        date_of_birth = updates[
            "date_of_birth"
        ]

        if date_of_birth is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Date of birth cannot "
                    "be empty."
                ),
            )

        validate_member_date_of_birth(
            date_of_birth
        )

    if (
        "sex" in updates
        and
        updates["sex"]
        not in {
            "Male",
            "Female",
        }
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Sex must be Male or Female."
            ),
        )


    if (
        "contribution_months"
        in updates
        and
        updates[
            "contribution_months"
        ]
        is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Contribution months "
                "cannot be empty."
            ),
        )
    final_date_of_birth = updates.get(
        "date_of_birth",
        member.date_of_birth,
    )

    final_contribution_months = updates.get(
        "contribution_months",
        member.contribution_months,
    )

    validate_contribution_months_for_age(
        final_date_of_birth,
        final_contribution_months,
    )


    if (
        "best_three_year_average_annual_salary"
        in updates
    ):

        salary = updates[
            "best_three_year_average_annual_salary"
        ]


        if (
            salary is None
            or
            salary < 0
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Salary cannot be negative."
                ),
            )


    for field, value in updates.items():

        if (
            field
            in {
                "first_name",
                "last_name",
            }
        ):

            value = value.strip()


        setattr(
            member,
            field,
            value,
        )


    db.commit()

    db.refresh(
        member
    )


    return {

        "id":
            member.id,

        "first_name":
            member.first_name,

        "last_name":
            member.last_name,

        "date_of_birth":
            member.date_of_birth,

        "sex":
            member.sex,

        "contribution_months":
            member.contribution_months,

        "best_three_year_average_annual_salary":
            str(
                member
                .best_three_year_average_annual_salary
            ),

        "created_at":
            member.created_at,
    }


# ============================================================
# CONTRIBUTIONS — CREATE
# ============================================================


@app.post(
    "/members/{member_id}/contributions"
)
def create_contribution(
    member_id: int,

    request: ContributionCreateRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    if request.year < 1900:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid contribution year."
            ),
        )


    if (
        request.month < 1
        or
        request.month > 12
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Month must be between "
                "1 and 12."
            ),
        )


    if (
        request.insurable_earnings
        <
        0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Insurable earnings "
                "cannot be negative."
            ),
        )


    if (
        request
        .recorded_first_tier_contribution
        is not None
        and
        request
        .recorded_first_tier_contribution
        <
        0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Recorded First-Tier contribution "
                "cannot be negative."
            ),
        )


    existing = db.scalar(
        select(
            ContributionRecord
        )
        .where(
            ContributionRecord.member_id
            ==
            member_id,

            ContributionRecord.year
            ==
            request.year,

            ContributionRecord.month
            ==
            request.month,
        )
    )


    if existing is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "A contribution record already "
                "exists for this member and month."
            ),
        )


    record = ContributionRecord(

        member_id=member_id,

        year=request.year,

        month=request.month,

        insurable_earnings=(
            request.insurable_earnings
        ),

        recorded_first_tier_contribution=(
            request
            .recorded_first_tier_contribution
        ),
    )


    db.add(
        record
    )

    db.commit()

    db.refresh(
        record
    )


    return {

        "id":
            record.id,

        "member_id":
            record.member_id,

        "year":
            record.year,

        "month":
            record.month,

        "insurable_earnings":
            str(
                record.insurable_earnings
            ),

        "recorded_first_tier_contribution":
            (
                str(
                    record
                    .recorded_first_tier_contribution
                )
                if (
                    record
                    .recorded_first_tier_contribution
                    is not None
                )
                else None
            ),
    }


# ============================================================
# CONTRIBUTIONS — LIST
# ============================================================


@app.get(
    "/members/{member_id}/contributions"
)
def get_member_contributions(
    member_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    records = db.scalars(
        select(
            ContributionRecord
        )
        .where(
            ContributionRecord.member_id
            ==
            member_id
        )
        .order_by(
            ContributionRecord.year,
            ContributionRecord.month,
        )
    ).all()


    return {

        "member_id":
            member_id,

        "total_records":
            len(records),

        "contributions": [

            {

                "id":
                    record.id,

                "year":
                    record.year,

                "month":
                    record.month,

                "insurable_earnings":
                    str(
                        record
                        .insurable_earnings
                    ),

                "recorded_first_tier_contribution":
                    (
                        str(
                            record
                            .recorded_first_tier_contribution
                        )
                        if (
                            record
                            .recorded_first_tier_contribution
                            is not None
                        )
                        else None
                    ),
            }

            for record
            in records
        ],
    }


# ============================================================
# CONTRIBUTIONS — UPDATE
# ============================================================


@app.put(
    "/members/{member_id}/contributions/{contribution_id}"
)
def update_contribution(
    member_id: int,

    contribution_id: int,

    request: ContributionUpdateRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    record = db.get(
        ContributionRecord,
        contribution_id,
    )


    if (
        record is None
        or
        record.member_id
        !=
        member_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Contribution record "
                "not found."
            ),
        )


    updates = (
        request.model_dump(
            exclude_unset=True
        )
    )


    if not updates:

        raise HTTPException(
            status_code=400,
            detail=(
                "No contribution fields "
                "were supplied for update."
            ),
        )


    if (
        "year" in updates
        and
        updates["year"]
        is None
    ):

        raise HTTPException(
            status_code=400,
            detail="Year cannot be null.",
        )


    if (
        "month" in updates
        and
        updates["month"]
        is None
    ):

        raise HTTPException(
            status_code=400,
            detail="Month cannot be null.",
        )


    if (
        "insurable_earnings"
        in updates
        and
        updates[
            "insurable_earnings"
        ]
        is None
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Insurable earnings "
                "cannot be null."
            ),
        )


    new_year = updates.get(
        "year",
        record.year,
    )


    new_month = updates.get(
        "month",
        record.month,
    )


    new_earnings = updates.get(
        "insurable_earnings",
        record.insurable_earnings,
    )


    if new_year < 1900:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid contribution year."
            ),
        )


    if (
        new_month < 1
        or
        new_month > 12
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Month must be between "
                "1 and 12."
            ),
        )


    if new_earnings < 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Insurable earnings "
                "cannot be negative."
            ),
        )


    if (
        "recorded_first_tier_contribution"
        in updates
    ):

        recorded_amount = updates[
            "recorded_first_tier_contribution"
        ]


        if (
            recorded_amount
            is not None
            and
            recorded_amount < 0
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Recorded First-Tier contribution "
                    "cannot be negative."
                ),
            )


    duplicate = db.scalar(
        select(
            ContributionRecord
        )
        .where(
            ContributionRecord.member_id
            ==
            member_id,

            ContributionRecord.year
            ==
            new_year,

            ContributionRecord.month
            ==
            new_month,

            ContributionRecord.id
            !=
            contribution_id,
        )
    )


    if duplicate is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "Another contribution record "
                "already exists for this "
                "member and month."
            ),
        )


    for field, value in updates.items():

        setattr(
            record,
            field,
            value,
        )


    db.commit()

    db.refresh(
        record
    )


    return {

        "message":
            "Contribution updated successfully.",

        "contribution": {

            "id":
                record.id,

            "member_id":
                record.member_id,

            "year":
                record.year,

            "month":
                record.month,

            "insurable_earnings":
                str(
                    record
                    .insurable_earnings
                ),

            "recorded_first_tier_contribution":
                (
                    str(
                        record
                        .recorded_first_tier_contribution
                    )
                    if (
                        record
                        .recorded_first_tier_contribution
                        is not None
                    )
                    else None
                ),
        },
    }


# ============================================================
# CONTRIBUTIONS — DELETE
# ============================================================


@app.delete(
    "/members/{member_id}/contributions/{contribution_id}"
)
def delete_contribution(
    member_id: int,

    contribution_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    record = db.get(
        ContributionRecord,
        contribution_id,
    )


    if (
        record is None
        or
        record.member_id
        !=
        member_id
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Contribution record "
                "not found."
            ),
        )


    deleted_record = {

        "id":
            record.id,

        "year":
            record.year,

        "month":
            record.month,
    }


    db.delete(
        record
    )

    db.commit()


    return {

        "message":
            "Contribution deleted successfully.",

        "deleted_contribution":
            deleted_record,
    }


# ============================================================
# CONTRIBUTION HEALTH
# ============================================================


@app.get(
    "/members/{member_id}/contribution-health"
)
def contribution_health(
    member_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    records = db.scalars(
        select(
            ContributionRecord
        )
        .where(
            ContributionRecord.member_id
            ==
            member_id
        )
        .order_by(
            ContributionRecord.year,
            ContributionRecord.month,
        )
    ).all()


    analysis = (
        analyse_contribution_history(
            records
        )
    )


    return {

        "member": {

            "id":
                member.id,

            "name":
                (
                    f"{member.first_name} "
                    f"{member.last_name}"
                ),
        },

        "analysis":
            analysis,

        "diagnostic_note":
            (
                "Missing months identify gaps in "
                "the contribution history currently "
                "stored in PensionIQ. They do not "
                "by themselves prove that SSNIT "
                "failed to receive a contribution."
            ),

        "amount_check_note":
            (
                "Automatic contribution-amount "
                "checking currently applies only "
                "to configured contribution-rate years."
            ),
    }


# ============================================================
# MEMBER DASHBOARD
# ============================================================


@app.get(
    "/members/{member_id}/dashboard"
)
def get_member_dashboard(
    member_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    require_member_ownership(
        member_id,
        current_user,
    )


    member = db.get(
        Member,
        member_id,
    )


    if member is None:

        raise HTTPException(
            status_code=404,
            detail="Member not found.",
        )


    records = db.scalars(
        select(
            ContributionRecord
        )
        .where(
            ContributionRecord.member_id
            ==
            member_id
        )
        .order_by(
            ContributionRecord.year,
            ContributionRecord.month,
        )
    ).all()


    contribution_health = (
        analyse_contribution_history(
            records
        )
    )


    current_age = (
        calculate_current_age(
            member.date_of_birth
        )
    )


    contribution_months = (
        member.contribution_months
    )


    contribution_years = (
        Decimal(
            contribution_months
        )
        /
        Decimal("12")
    )


    if (
        contribution_months
        >=
        180
    ):

        pension_right_value = (
            calculate_pension_right(
                contribution_months
            )
        )

    else:

        pension_right_value = None


    if (
        pension_right_value
        is not None
    ):

        pension_right_percent = (
            pension_right_value
            *
            Decimal("100")
        )

    else:

        pension_right_percent = None


    minimum_pension_months = 180

    maximum_pension_right_months = 420


    months_to_minimum = max(
        0,
        minimum_pension_months
        -
        contribution_months,
    )


    months_to_maximum = max(
        0,
        maximum_pension_right_months
        -
        contribution_months,
    )


    eligible_for_monthly_old_age_pension = (
        contribution_months
        >=
        minimum_pension_months
    )


    maximum_pension_right_reached = (
        contribution_months
        >=
        maximum_pension_right_months
    )


    recorded_history_months = (
        len(
            records
        )
    )


    if recorded_history_months == 0:

        record_alignment_status = (
            "NO_DETAILED_HISTORY"
        )

    elif (
        recorded_history_months
        ==
        contribution_months
    ):

        record_alignment_status = (
            "ALIGNED"
        )

    else:

        record_alignment_status = (
            "TOTAL_AND_HISTORY_DIFFER"
        )


    return {

        "member": {

            "id":
                member.id,

            "first_name":
                member.first_name,

            "last_name":
                member.last_name,

            "full_name":
                (
                    f"{member.first_name} "
                    f"{member.last_name}"
                ),

            "date_of_birth":
                member.date_of_birth,

            "current_age":
                current_age,

            "sex":
                member.sex,

            "best_three_year_average_annual_salary":
                str(
                    member
                    .best_three_year_average_annual_salary
                ),
        },


        "pension_position": {

            "contribution_months":
                contribution_months,

            "contribution_years":
                str(
                    contribution_years
                    .quantize(
                        Decimal("0.01")
                    )
                ),

            "pension_right":
                (
                    str(
                        pension_right_value
                    )
                    if (
                        pension_right_value
                        is not None
                    )
                    else None
                ),

            "pension_right_percent":
                (
                    str(
                        pension_right_percent
                        .quantize(
                            Decimal("0.001")
                        )
                    )
                    if (
                        pension_right_percent
                        is not None
                    )
                    else None
                ),

            "eligible_for_monthly_old_age_pension":
                eligible_for_monthly_old_age_pension,

            "maximum_pension_right_reached":
                maximum_pension_right_reached,

            "months_to_minimum":
                months_to_minimum,

            "months_to_maximum":
                months_to_maximum,

            "minimum_months_required":
                minimum_pension_months,

            "maximum_pension_right_months":
                maximum_pension_right_months,
        },


        "contribution_summary": {

            "stored_contribution_months":
                contribution_months,

            "detailed_records_stored":
                recorded_history_months,

            "record_alignment_status":
                record_alignment_status,

            "health_status":
                contribution_health[
                    "status"
                ],

            "continuity_ratio_percent":
                contribution_health[
                    "continuity_ratio_percent"
                ],

            "missing_month_count":
                contribution_health[
                    "missing_month_count"
                ],

            "amount_mismatch_count":
                contribution_health[
                    "amount_mismatch_count"
                ],

            "total_insurable_earnings":
                contribution_health[
                    "total_insurable_earnings"
                ],

            "total_recorded_first_tier":
                contribution_health[
                    "total_recorded_first_tier"
                ],
        },


        "contribution_health":
            contribution_health,


        "notes": {

            "record_alignment":
                (
                    "The stored contribution-month total "
                    "and detailed contribution history are "
                    "separate data points. A difference "
                    "does not automatically indicate "
                    "an SSNIT error."
                ),

            "missing_months":
                (
                    "Missing months refer only to gaps "
                    "in contribution records currently "
                    "stored in PensionIQ."
                ),

            "pension_right":
                (
                    "Pension-right calculations are "
                    "estimates based on the rules "
                    "configured in the PensionIQ "
                    "actuarial engine."
                ),
        },
    }