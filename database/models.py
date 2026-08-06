"""Database models for Aoun."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""


class ClaimRecord(Base):
    """Persisted claim, validation, and submission information."""

    __tablename__ = "claim_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    claim_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    patient_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )

    compliance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    acceptance_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    primary_issue: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    claim_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    validation_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now().astimezone(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now().astimezone(),
        onupdate=lambda: datetime.now().astimezone(),
        nullable=False,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )