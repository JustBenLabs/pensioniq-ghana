from datetime import (
    UTC,
    date,
    datetime,
    timedelta,
)

from sqlalchemy import select

from ssnit_engine.database.models import (
    Member,
    PasswordResetToken,
)



# ============================================================
# TEST DATA
# ============================================================

TEST_EMAIL = "test@example.com"

TEST_PASSWORD = (
    "StrongTestPassword123!"
)

NEW_TEST_PASSWORD = (
    "NewStrongPassword456!"
)


# ============================================================
# HELPERS
# ============================================================


def registration_payload(
    email: str = TEST_EMAIL,
):

    return {

        "email":
            email,

        "password":
            TEST_PASSWORD,

        "first_name":
            "Test",

        "last_name":
            "Member",

        "date_of_birth":
            "1990-04-16",

        "sex":
            "Male",

        "contribution_months":
            240,

        "best_three_year_average_annual_salary":
            72000,
    }


def register_user(
    client,
    email: str = TEST_EMAIL,
):

    return client.post(

        "/auth/register",

        json=registration_payload(
            email
        ),
    )


def login_user(
    client,
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD,
):

    return client.post(

        "/auth/login",

        json={

            "email":
                email,

            "password":
                password,
        },
    )


def authorization_headers(
    token: str,
):

    return {

        "Authorization":
            f"Bearer {token}"
    }


def register_and_login(
    client,
):

    register_response = (
        register_user(
            client
        )
    )


    assert (
        register_response.status_code
        ==
        200
    )


    login_response = (
        login_user(
            client
        )
    )


    assert (
        login_response.status_code
        ==
        200
    )


    token = (
        login_response
        .json()[
            "access_token"
        ]
    )


    member_id = (
        register_response
        .json()[
            "user"
        ][
            "member_id"
        ]
    )


    return (
        token,
        member_id,
    )


# ============================================================
# REGISTRATION
# ============================================================


def test_register_user(
    client,
):

    response = (
        register_user(
            client
        )
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        data["message"]
        ==
        "Account created successfully."
    )


    assert (
        data["user"]["email"]
        ==
        TEST_EMAIL
    )


    assert (
        data["user"]["member_id"]
        is not None
    )


# ============================================================
# DUPLICATE EMAIL
# ============================================================


def test_duplicate_email_is_rejected(
    client,
):

    first_response = (
        register_user(
            client
        )
    )


    assert (
        first_response.status_code
        ==
        200
    )


    second_response = (
        register_user(
            client
        )
    )


    assert (
        second_response.status_code
        ==
        409
    )


    assert (
        second_response
        .json()[
            "detail"
        ]
        ==
        (
            "An account already exists "
            "for this email address."
        )
    )


# ============================================================
# LOGIN
# ============================================================


def test_login_returns_access_token(
    client,
):

    register_user(
        client
    )


    response = (
        login_user(
            client
        )
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        "access_token"
        in data
    )


    assert (
        isinstance(
            data["access_token"],
            str,
        )
    )


    assert (
        len(
            data["access_token"]
        )
        >
        20
    )


    assert (
        data["token_type"]
        ==
        "bearer"
    )


    assert (
        data["expires_in_seconds"]
        ==
        3600
    )


# ============================================================
# WRONG PASSWORD
# ============================================================


def test_wrong_password_is_rejected(
    client,
):

    register_user(
        client
    )


    response = client.post(

        "/auth/login",

        json={

            "email":
                TEST_EMAIL,

            "password":
                "WrongPassword123!",
        },
    )


    assert (
        response.status_code
        ==
        401
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        "Invalid email or password."
    )


# ============================================================
# UNKNOWN EMAIL
# ============================================================


def test_unknown_email_is_rejected(
    client,
):

    response = client.post(

        "/auth/login",

        json={

            "email":
                "unknown@example.com",

            "password":
                TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        401
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        "Invalid email or password."
    )


# ============================================================
# AUTH / ME
# ============================================================


def test_authenticated_user_can_access_me(
    client,
):

    token, member_id = (
        register_and_login(
            client
        )
    )


    response = client.get(

        "/auth/me",

        headers=(
            authorization_headers(
                token
            )
        ),
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        data["user"]["email"]
        ==
        TEST_EMAIL
    )


    assert (
        data["user"]["is_active"]
        is True
    )


    assert (
        data["member"]["id"]
        ==
        member_id
    )


    assert (
        data["member"]["first_name"]
        ==
        "Test"
    )


    assert (
        data["member"]["last_name"]
        ==
        "Member"
    )


# ============================================================
# NO AUTHENTICATION
# ============================================================


def test_auth_me_requires_authentication(
    client,
):

    response = client.get(
        "/auth/me"
    )


    assert (
        response.status_code
        ==
        401
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        "Authentication required."
    )


# ============================================================
# PROTECTED MEMBER ROUTE
# ============================================================


def test_protected_member_route_requires_authentication(
    client,
):

    register_response = (
        register_user(
            client
        )
    )


    assert (
        register_response.status_code
        ==
        200
    )


    member_id = (
        register_response
        .json()[
            "user"
        ][
            "member_id"
        ]
    )


    response = client.get(
        f"/members/{member_id}"
    )


    assert (
        response.status_code
        ==
        401
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        "Authentication required."
    )


# ============================================================
# OWN MEMBER PROFILE
# ============================================================


def test_user_can_access_own_member_profile(
    client,
):

    token, member_id = (
        register_and_login(
            client
        )
    )


    response = client.get(

        f"/members/{member_id}",

        headers=(
            authorization_headers(
                token
            )
        ),
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        data["id"]
        ==
        member_id
    )


    assert (
        data["first_name"]
        ==
        "Test"
    )


# ============================================================
# MEMBER OWNERSHIP
# ============================================================


def test_user_cannot_access_another_member(
    client,
    db_session,
):

    token, own_member_id = (
        register_and_login(
            client
        )
    )


    headers = (
        authorization_headers(
            token
        )
    )


    # --------------------------------------------------------
    # Own profile must work
    # --------------------------------------------------------

    own_response = client.get(

        f"/members/{own_member_id}",

        headers=headers,
    )


    assert (
        own_response.status_code
        ==
        200
    )


    # --------------------------------------------------------
    # Create another member directly
    # in the TEST database
    # --------------------------------------------------------

    other_member = Member(

        first_name=
            "Other",

        last_name=
            "Member",

        date_of_birth=date(
            1985,
            1,
            1,
        ),

        sex=
            "Female",

        contribution_months=
            180,

        best_three_year_average_annual_salary=
            60000,
    )


    db_session.add(
        other_member
    )


    db_session.commit()


    db_session.refresh(
        other_member
    )


    assert (
        other_member.id
        !=
        own_member_id
    )


    # --------------------------------------------------------
    # Other member must be forbidden
    # --------------------------------------------------------

    forbidden_response = client.get(

        f"/members/{other_member.id}",

        headers=headers,
    )


    assert (
        forbidden_response.status_code
        ==
        403
    )


    assert (
        forbidden_response
        .json()[
            "detail"
        ]
        ==
        (
            "You are not authorized to access "
            "this member's information."
        )
    )


# ============================================================
# DASHBOARD OWNERSHIP
# ============================================================


def test_user_can_access_own_dashboard(
    client,
):

    token, member_id = (
        register_and_login(
            client
        )
    )


    response = client.get(

        f"/members/{member_id}/dashboard",

        headers=(
            authorization_headers(
                token
            )
        ),
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        data["member"]["id"]
        ==
        member_id
    )


    assert (
        data[
            "pension_position"
        ][
            "contribution_months"
        ]
        ==
        240
    )


# ============================================================
# PROFILE UPDATE
# ============================================================


def test_user_can_update_own_profile(
    client,
):

    token, member_id = (
        register_and_login(
            client
        )
    )


    response = client.put(

        f"/members/{member_id}",

        headers=(
            authorization_headers(
                token
            )
        ),

        json={

            "first_name":
                "Updated",

            "last_name":
                "Member",

            "date_of_birth":
                "1990-04-16",

            "sex":
                "Male",

            "contribution_months":
                252,

            "best_three_year_average_annual_salary":
                84000,
        },
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        data["first_name"]
        ==
        "Updated"
    )


    assert (
        data["contribution_months"]
        ==
        252
    )


    assert (
        data[
            "best_three_year_average_annual_salary"
        ]
        ==
        "84000.00"
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================


def test_user_can_change_password(
    client,
):

    token, _ = (
        register_and_login(
            client
        )
    )


    response = client.post(

        "/auth/change-password",

        headers=(
            authorization_headers(
                token
            )
        ),

        json={

            "current_password":
                TEST_PASSWORD,

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response
        .json()[
            "message"
        ]
        ==
        "Password changed successfully."
    )


    # --------------------------------------------------------
    # Old password must fail
    # --------------------------------------------------------

    old_login = (
        login_user(
            client,
            password=TEST_PASSWORD,
        )
    )


    assert (
        old_login.status_code
        ==
        401
    )


    # --------------------------------------------------------
    # New password must work
    # --------------------------------------------------------

    new_login = (
        login_user(
            client,
            password=NEW_TEST_PASSWORD,
        )
    )


    assert (
        new_login.status_code
        ==
        200
    )


    assert (
        "access_token"
        in new_login.json()
    )


# ============================================================
# WRONG CURRENT PASSWORD
# ============================================================


def test_wrong_current_password_cannot_change_password(
    client,
):

    token, _ = (
        register_and_login(
            client
        )
    )


    response = client.post(

        "/auth/change-password",

        headers=(
            authorization_headers(
                token
            )
        ),

        json={

            "current_password":
                "DefinitelyWrong123!",

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        400
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        "Current password is incorrect."
    )


# ============================================================
# SAME PASSWORD
# ============================================================


def test_new_password_must_differ_from_current_password(
    client,
):

    token, _ = (
        register_and_login(
            client
        )
    )


    response = client.post(

        "/auth/change-password",

        headers=(
            authorization_headers(
                token
            )
        ),

        json={

            "current_password":
                TEST_PASSWORD,

            "new_password":
                TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        400
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        (
            "New password must be different "
            "from your current password."
        )
    )


# ============================================================
# PASSWORD TOO SHORT
# ============================================================


def test_new_password_cannot_be_too_short(
    client,
):

    token, _ = (
        register_and_login(
            client
        )
    )


    response = client.post(

        "/auth/change-password",

        headers=(
            authorization_headers(
                token
            )
        ),

        json={

            "current_password":
                TEST_PASSWORD,

            "new_password":
                "short",
        },
    )


    assert (
        response.status_code
        ==
        400
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        (
            "New password must contain between "
            "8 and 128 characters."
        )
    )


# ============================================================
# PASSWORD CHANGE REQUIRES AUTH
# ============================================================


def test_change_password_requires_authentication(
    client,
):

    register_user(
        client
    )


    response = client.post(

        "/auth/change-password",

        json={

            "current_password":
                TEST_PASSWORD,

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        401
    )


    assert (
        response
        .json()[
            "detail"
        ]
        ==
        "Authentication required."
    )

# ============================================================
# FORGOT PASSWORD
# ============================================================


def test_forgot_password_returns_generic_response_for_existing_user(
    client,
    monkeypatch,
):

    register_user(
        client
    )


    monkeypatch.setattr(
        "ssnit_engine.api.secrets.token_urlsafe",
        lambda length: "known-reset-token",
    )


    response = client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response.json()["message"]
        ==
        (
            "If an account exists for this email address, "
            "password reset instructions have been generated."
        )
    )


def test_forgot_password_returns_same_response_for_unknown_email(
    client,
):

    response = client.post(

        "/auth/forgot-password",

        json={
            "email":
                "does-not-exist@example.com"
        },
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response.json()["message"]
        ==
        (
            "If an account exists for this email address, "
            "password reset instructions have been generated."
        )
    )


# ============================================================
# RESET PASSWORD
# ============================================================


def test_user_can_reset_password(
    client,
    monkeypatch,
):

    register_user(
        client
    )


    reset_token = (
        "valid-password-reset-token"
    )


    monkeypatch.setattr(
        "ssnit_engine.api.secrets.token_urlsafe",
        lambda length: reset_token,
    )


    forgot_response = client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    assert (
        forgot_response.status_code
        ==
        200
    )


    reset_response = client.post(

        "/auth/reset-password",

        json={

            "token":
                reset_token,

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        reset_response.status_code
        ==
        200
    )


    assert (
        reset_response.json()["message"]
        ==
        (
            "Password reset successfully. "
            "Please sign in with your new password."
        )
    )


    # --------------------------------------------------------
    # Old password must fail
    # --------------------------------------------------------

    old_login = login_user(
        client,
        password=TEST_PASSWORD,
    )


    assert (
        old_login.status_code
        ==
        401
    )


    # --------------------------------------------------------
    # New password must work
    # --------------------------------------------------------

    new_login = login_user(
        client,
        password=NEW_TEST_PASSWORD,
    )


    assert (
        new_login.status_code
        ==
        200
    )


# ============================================================
# RESET TOKEN IS ONE-TIME USE
# ============================================================


def test_password_reset_token_cannot_be_reused(
    client,
    monkeypatch,
):

    register_user(
        client
    )


    reset_token = (
        "single-use-reset-token"
    )


    monkeypatch.setattr(
        "ssnit_engine.api.secrets.token_urlsafe",
        lambda length: reset_token,
    )


    client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    first_reset = client.post(

        "/auth/reset-password",

        json={

            "token":
                reset_token,

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        first_reset.status_code
        ==
        200
    )


    second_reset = client.post(

        "/auth/reset-password",

        json={

            "token":
                reset_token,

            "new_password":
                "AnotherStrongPassword789!",
        },
    )


    assert (
        second_reset.status_code
        ==
        400
    )


    assert (
        second_reset.json()["detail"]
        ==
        (
            "Invalid or expired "
            "password reset token."
        )
    )


# ============================================================
# EXPIRED RESET TOKEN
# ============================================================


def test_expired_password_reset_token_is_rejected(
    client,
    db_session,
    monkeypatch,
):

    register_user(
        client
    )


    reset_token = (
        "expired-password-reset-token"
    )


    monkeypatch.setattr(
        "ssnit_engine.api.secrets.token_urlsafe",
        lambda length: reset_token,
    )


    client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    reset_record = db_session.scalar(
        select(
            PasswordResetToken
        )
    )


    assert (
        reset_record
        is not None
    )


    reset_record.expires_at = (
        datetime.now(UTC)
        -
        timedelta(
            minutes=1
        )
    )


    db_session.commit()


    response = client.post(

        "/auth/reset-password",

        json={

            "token":
                reset_token,

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        400
    )


    assert (
        response.json()["detail"]
        ==
        (
            "Invalid or expired "
            "password reset token."
        )
    )


# ============================================================
# PREVIOUS RESET TOKEN INVALIDATED
# ============================================================


def test_new_reset_request_invalidates_previous_reset_token(
    client,
    monkeypatch,
):

    register_user(
        client
    )


    generated_tokens = iter(
        [
            "first-reset-token",
            "second-reset-token",
        ]
    )


    monkeypatch.setattr(
        "ssnit_engine.api.secrets.token_urlsafe",
        lambda length:
            next(generated_tokens),
    )


    client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    # --------------------------------------------------------
    # First token must now be invalid
    # --------------------------------------------------------

    old_token_response = client.post(

        "/auth/reset-password",

        json={

            "token":
                "first-reset-token",

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        old_token_response.status_code
        ==
        400
    )


    # --------------------------------------------------------
    # Latest token must work
    # --------------------------------------------------------

    new_token_response = client.post(

        "/auth/reset-password",

        json={

            "token":
                "second-reset-token",

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        new_token_response.status_code
        ==
        200
    )


# ============================================================
# PASSWORD RESET INVALIDATES EXISTING JWT
# ============================================================


def test_password_reset_invalidates_existing_access_token(
    client,
    monkeypatch,
):

    token, _ = (
        register_and_login(
            client
        )
    )


    # Confirm original JWT works.

    before_reset = client.get(

        "/auth/me",

        headers=(
            authorization_headers(
                token
            )
        ),
    )


    assert (
        before_reset.status_code
        ==
        200
    )


    reset_token = (
        "jwt-invalidation-reset-token"
    )


    monkeypatch.setattr(
        "ssnit_engine.api.secrets.token_urlsafe",
        lambda length: reset_token,
    )


    client.post(

        "/auth/forgot-password",

        json={
            "email":
                TEST_EMAIL
        },
    )


    reset_response = client.post(

        "/auth/reset-password",

        json={

            "token":
                reset_token,

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        reset_response.status_code
        ==
        200
    )


    # --------------------------------------------------------
    # JWT issued before reset must now fail.
    # --------------------------------------------------------

    after_reset = client.get(

        "/auth/me",

        headers=(
            authorization_headers(
                token
            )
        ),
    )


    assert (
        after_reset.status_code
        ==
        401
    )


    assert (
        after_reset.json()["detail"]
        ==
        (
            "Authentication token is "
            "no longer valid."
        )
    )


# ============================================================
# INVALID RESET TOKEN
# ============================================================


def test_random_password_reset_token_is_rejected(
    client,
):

    register_user(
        client
    )


    response = client.post(

        "/auth/reset-password",

        json={

            "token":
                "completely-invalid-token",

            "new_password":
                NEW_TEST_PASSWORD,
        },
    )


    assert (
        response.status_code
        ==
        400
    )


    assert (
        response.json()["detail"]
        ==
        (
            "Invalid or expired "
            "password reset token."
        )
    ) 
def test_login_rate_limit_blocks_excessive_attempts(
    client,
):
    """
    Login should be rate limited after
    10 attempts from the same IP within
    the configured time window.
    """

    login_data = {
        "email": "rate-limit-test@example.com",
        "password": "WrongPassword123!",
    }

    # First 10 attempts should reach
    # the normal login logic.
    for _ in range(10):
        response = client.post(
            "/auth/login",
            json=login_data,
        )

        assert response.status_code != 429

    # The 11th attempt should be blocked.
    blocked_response = client.post(
        "/auth/login",
        json=login_data,
    )

    assert blocked_response.status_code == 429

    assert blocked_response.json() == {
        "detail": (
            "Too many requests. "
            "Please try again later."
        )
    }

    assert "Retry-After" in blocked_response.headers       
def test_registration_rejects_future_date_of_birth(
    client,
):
    future_dob = (
        date.today()
        +
        timedelta(days=1)
    )

    response = client.post(
        "/auth/register",
        json={
            "email":
                "future-dob@example.com",
            "password":
                "StrongPassword123!",
            "first_name":
                "Future",
            "last_name":
                "Member",
            "date_of_birth":
                future_dob.isoformat(),
            "sex":
                "Male",
            "contribution_months":
                0,
            "best_three_year_average_annual_salary":
                "0",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Date of birth cannot be "
            "in the future."
    }


def test_registration_rejects_member_younger_than_15(
    client,
):
    young_dob = (
        date.today()
        -
        timedelta(days=365 * 10)
    )

    response = client.post(
        "/auth/register",
        json={
            "email":
                "young-member@example.com",
            "password":
                "StrongPassword123!",
            "first_name":
                "Young",
            "last_name":
                "Member",
            "date_of_birth":
                young_dob.isoformat(),
            "sex":
                "Female",
            "contribution_months":
                0,
            "best_three_year_average_annual_salary":
                "0",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Member must be at least "
            "15 years old."
    }


def test_registration_rejects_implausibly_old_member(
    client,
):
    response = client.post(
        "/auth/register",
        json={
            "email":
                "old-member@example.com",
            "password":
                "StrongPassword123!",
            "first_name":
                "Old",
            "last_name":
                "Member",
            "date_of_birth":
                "1900-01-01",
            "sex":
                "Male",
            "contribution_months":
                0,
            "best_three_year_average_annual_salary":
                "0",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Date of birth produces an "
            "implausible member age."
    }


def test_profile_update_rejects_future_date_of_birth(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    future_dob = (
        date.today()
        +
        timedelta(days=1)
    )

    response = client.put(
        f"/members/{member_id}",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "date_of_birth":
                future_dob.isoformat(),
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Date of birth cannot be "
            "in the future."
    }    
def test_registration_rejects_implausible_contribution_months(
    client,
):
    response = client.post(
        "/auth/register",
        json={
            "email":
                "implausible-months@example.com",
            "password":
                "StrongPassword123!",
            "first_name":
                "Test",
            "last_name":
                "Member",
            "date_of_birth":
                "2006-01-01",
            "sex":
                "Male",
            "contribution_months":
                400,
            "best_three_year_average_annual_salary":
                "0",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution months are not "
            "plausible for the member's age."
    }


def test_profile_update_rejects_implausible_contribution_months(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    response = client.put(
        f"/members/{member_id}",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "date_of_birth":
                "2006-01-01",
            "contribution_months":
                400,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution months are not "
            "plausible for the member's age."
    }


def test_profile_update_revalidates_existing_months_when_dob_changes(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    # First give the member a plausible
    # contribution history for the original DOB.
    update_response = client.put(
        f"/members/{member_id}",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "contribution_months": 120,
        },
    )

    assert update_response.status_code == 200

    # Now make the member much younger.
    # The existing 120 months should no longer
    # be plausible for the proposed DOB.
    response = client.put(
        f"/members/{member_id}",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "date_of_birth":
                "2010-01-01",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution months are not "
            "plausible for the member's age."
    }
def test_create_contribution_rejects_future_period(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    today = date.today()

    future_year = today.year + 1

    response = client.post(
        f"/members/{member_id}/contributions",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "year":
                future_year,
            "month":
                1,
            "insurable_earnings":
                "5000",
            "recorded_first_tier_contribution":
                "675",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution period cannot "
            "be in the future."
    }


def test_update_contribution_rejects_future_period(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    today = date.today()

    create_response = client.post(
        f"/members/{member_id}/contributions",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "year":
                today.year,
            "month":
                1,
            "insurable_earnings":
                "5000",
            "recorded_first_tier_contribution":
                "675",
        },
    )

    assert create_response.status_code == 200

    contribution_id = (
        create_response.json()["id"]
    )

    response = client.put(
        (
            f"/members/{member_id}/"
            f"contributions/{contribution_id}"
        ),
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "year":
                today.year + 1,
            "month":
                1,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution period cannot "
            "be in the future."
    }


def test_create_contribution_rejects_period_before_plausible_start_age(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    # Test registration helper uses an adult DOB.
    # Move the profile DOB to a known value so the
    # age-boundary test is deterministic.
    profile_response = client.put(
        f"/members/{member_id}",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "date_of_birth":
                "2000-06-15",
            "contribution_months":
                0,
        },
    )

    assert profile_response.status_code == 200

    response = client.post(
        f"/members/{member_id}/contributions",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "year":
                2010,
            "month":
                3,
            "insurable_earnings":
                "5000",
            "recorded_first_tier_contribution":
                "675",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution period is not "
            "plausible for the member's age."
    }


def test_update_contribution_rejects_period_before_plausible_start_age(
    client,
):
    token, member_id = (
        register_and_login(
            client
        )
    )

    profile_response = client.put(
        f"/members/{member_id}",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "date_of_birth":
                "2000-06-15",
            "contribution_months":
                0,
        },
    )

    assert profile_response.status_code == 200

    create_response = client.post(
        f"/members/{member_id}/contributions",
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "year":
                2020,
            "month":
                1,
            "insurable_earnings":
                "5000",
            "recorded_first_tier_contribution":
                "675",
        },
    )

    assert create_response.status_code == 200

    contribution_id = (
        create_response.json()["id"]
    )

    response = client.put(
        (
            f"/members/{member_id}/"
            f"contributions/{contribution_id}"
        ),
        headers=(
            authorization_headers(
                token
            )
        ),
        json={
            "year":
                2010,
            "month":
                3,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Contribution period is not "
            "plausible for the member's age."
    }        
def test_create_contribution_rejects_earnings_with_too_many_decimals(
    client,
):
    token, member_id = register_and_login(
        client
    )

    today = date.today()

    response = client.post(
        f"/members/{member_id}/contributions",
        headers=authorization_headers(
            token
        ),
        json={
            "year": today.year,
            "month": 1,
            "insurable_earnings":
                "5000.123",
            "recorded_first_tier_contribution":
                "675.00",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Insurable earnings cannot have "
            "more than 2 decimal places."
    }


def test_create_contribution_rejects_recorded_amount_with_too_many_decimals(
    client,
):
    token, member_id = register_and_login(
        client
    )

    today = date.today()

    response = client.post(
        f"/members/{member_id}/contributions",
        headers=authorization_headers(
            token
        ),
        json={
            "year": today.year,
            "month": 1,
            "insurable_earnings":
                "5000.00",
            "recorded_first_tier_contribution":
                "675.999",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Recorded First-Tier contribution "
            "cannot have more than 2 decimal places."
    }


def test_update_contribution_rejects_earnings_with_too_many_decimals(
    client,
):
    token, member_id = register_and_login(
        client
    )

    today = date.today()

    create_response = client.post(
        f"/members/{member_id}/contributions",
        headers=authorization_headers(
            token
        ),
        json={
            "year": today.year,
            "month": 1,
            "insurable_earnings":
                "5000.00",
            "recorded_first_tier_contribution":
                "675.00",
        },
    )

    assert create_response.status_code == 200

    contribution_id = (
        create_response.json()["id"]
    )

    response = client.put(
        (
            f"/members/{member_id}/"
            f"contributions/{contribution_id}"
        ),
        headers=authorization_headers(
            token
        ),
        json={
            "insurable_earnings":
                "5000.123",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Insurable earnings cannot have "
            "more than 2 decimal places."
    }


def test_update_contribution_rejects_recorded_amount_with_too_many_decimals(
    client,
):
    token, member_id = register_and_login(
        client
    )

    today = date.today()

    create_response = client.post(
        f"/members/{member_id}/contributions",
        headers=authorization_headers(
            token
        ),
        json={
            "year": today.year,
            "month": 1,
            "insurable_earnings":
                "5000.00",
            "recorded_first_tier_contribution":
                "675.00",
        },
    )

    assert create_response.status_code == 200

    contribution_id = (
        create_response.json()["id"]
    )

    response = client.put(
        (
            f"/members/{member_id}/"
            f"contributions/{contribution_id}"
        ),
        headers=authorization_headers(
            token
        ),
        json={
            "recorded_first_tier_contribution":
                "675.999",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail":
            "Recorded First-Tier contribution "
            "cannot have more than 2 decimal places."
    }    