from datetime import date, datetime
from decimal import Decimal
from datetime import (
    UTC,
    datetime,
)

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ssnit_engine.database.connection import Base


class Member(Base):

    __tablename__ = "members"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )


    sex: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )


    contribution_months: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )


    best_three_year_average_annual_salary: Mapped[
        float
    ] = mapped_column(
        Numeric(
            14,
            2,
        ),
        default=0,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        nullable=False,
    )

# ============================================================
# SAVED RETIREMENT PLAN
# ============================================================


class RetirementPlan(Base):

    __tablename__ = "retirement_plans"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    # One active saved plan per PensionIQ member.
    member_id: Mapped[int] = mapped_column(
        ForeignKey(
            "members.id"
        ),
        unique=True,
        index=True,
        nullable=False,
    )


    # ========================================================
    # WHAT-IF RETIREMENT SCENARIO ASSUMPTIONS
    # ========================================================

    scenario_additional_contribution_months: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )


    scenario_projected_annual_salary: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            14,
            2,
        ),
        nullable=True,
    )


    scenario_retirement_age: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )


    # ========================================================
    # RETIREMENT GOAL ASSUMPTIONS
    # ========================================================

    goal_target_monthly_pension: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            14,
            2,
        ),
        nullable=True,
    )


    goal_projected_annual_salary: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(
            14,
            2,
        ),
        nullable=True,
    )


    goal_retirement_age: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )


    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=lambda: datetime.now(
            UTC
        ),
        nullable=False,
    )


    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=lambda: datetime.now(
            UTC
        ),
        onupdate=lambda: datetime.now(
            UTC
        ),
        nullable=False,
    )

class ContributionRecord(Base):

    __tablename__ = "contribution_records"

    __table_args__ = (
        UniqueConstraint(
            "member_id",
            "year",
            "month",
            name="uq_member_contribution_month",
        ),
    )


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id"),
        nullable=False,
        index=True,
    )


    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


    insurable_earnings: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )


    recorded_first_tier_contribution: Mapped[
        float | None
    ] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

class User(Base):

    __tablename__ = "users"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )


    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id"),
        unique=True,
        index=True,
        nullable=False,
    )


    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    token_version: Mapped[int] = mapped_column(
    Integer,
    default=0,
    nullable=False,
)
class PasswordResetToken(Base):

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
