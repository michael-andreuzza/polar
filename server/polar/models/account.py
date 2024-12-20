from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from polar.config import settings
from polar.enums import AccountType
from polar.kit.db.models import RecordModel
from polar.kit.extensions.sqlalchemy import StringEnum

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User


class Account(RecordModel):
    class Status(str, Enum):
        CREATED = "created"
        ONBOARDING_STARTED = "onboarding_started"
        UNDER_REVIEW = "under_review"
        ACTIVE = "active"

    __tablename__ = "accounts"

    account_type: Mapped[AccountType] = mapped_column(String(255), nullable=False)

    admin_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", use_alter=True))

    stripe_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None
    )
    open_collective_slug: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

    email: Mapped[str | None] = mapped_column(String(254), nullable=True, default=None)

    country: Mapped[str] = mapped_column(String(2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))

    is_details_submitted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_charges_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_payouts_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    processor_fees_applicable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    _platform_fee_percent: Mapped[int | None] = mapped_column(
        Integer, name="platform_fee_percent", nullable=True, default=None
    )
    _platform_fee_fixed: Mapped[int | None] = mapped_column(
        Integer, name="platform_fee_fixed", nullable=True, default=None
    )

    business_type: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

    status: Mapped[Status] = mapped_column(
        StringEnum(Status), nullable=False, default=Status.CREATED
    )
    next_review_threshold: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=settings.ACCOUNT_PAYOUT_REVIEW_THRESHOLDS[0]
    )

    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    @declared_attr
    def admin(cls) -> Mapped["User"]:
        return relationship("User", lazy="raise", foreign_keys="[Account.admin_id]")

    @declared_attr
    def users(cls) -> Mapped[list["User"]]:
        return relationship(
            "User",
            lazy="raise",
            back_populates="account",
            foreign_keys="[User.account_id]",
        )

    @declared_attr
    def organizations(cls) -> Mapped[list["Organization"]]:
        return relationship("Organization", lazy="raise", back_populates="account")

    def is_active(self) -> bool:
        return self.status == Account.Status.ACTIVE

    def is_under_review(self) -> bool:
        return self.status == Account.Status.UNDER_REVIEW

    def is_payout_ready(self) -> bool:
        return self.is_active() and (
            # For Stripe accounts, check if payouts are enabled.
            # Normally, the account shouldn't be active if payouts are not enabled
            # but let's be extra cautious
            self.account_type != AccountType.stripe or self.is_payouts_enabled
        )

    def get_associations_names(self) -> list[str]:
        associations_names: list[str] = []
        for user in self.users:
            associations_names.append(user.email)
        for organization in self.organizations:
            associations_names.append(organization.slug)
        return associations_names

    @property
    def platform_fee(self) -> tuple[int, int]:
        percent = self._platform_fee_percent
        if percent is None:
            percent = settings.PLATFORM_FEE_PERCENT

        fixed = self._platform_fee_fixed
        if fixed is None:
            fixed = settings.PLATFORM_FEE_FIXED

        return percent, fixed
