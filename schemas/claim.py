"""Pydantic schemas for Aoun healthcare claims."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Gender = Literal["male", "female", "other", "unknown"]

EncounterType = Literal[
    "outpatient",
    "inpatient",
    "emergency",
    "telemedicine",
    "other",
]

NoteLanguage = Literal["ar", "en"]


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


class ClaimStatus(str, Enum):
    """Possible lifecycle states for a healthcare claim."""

    DRAFT = "draft"
    VALIDATING = "validating"
    NEEDS_CORRECTION = "needs_correction"
    READY = "ready"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INFORMATION_REQUESTED = "information_requested"
    PENDING = "pending"
    FAILED = "failed"


class Attachment(BaseModel):
    """Metadata describing a supporting claim attachment."""

    name: str = Field(min_length=1)
    mime_type: str = "application/octet-stream"
    storage_uri: str | None = None
    category: str = "supporting_document"
    size_bytes: int | None = Field(default=None, ge=0)


class ClaimDraft(BaseModel):
    """
    Incomplete claim data while the healthcare professional is documenting.

    Draft fields are optional because the claim is progressively completed.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    claim_id: str = Field(min_length=3)

    # Patient
    patient_id: str | None = None
    patient_age: int | None = Field(default=None, ge=0, le=130)
    gender: Gender = "unknown"

    # Insurance
    insurance_company: str | None = None
    policy_number: str | None = None

    # Provider
    provider_id: str | None = None
    practitioner_id: str | None = None

    # Visit
    encounter_type: EncounterType = "outpatient"
    admission_date: datetime = Field(default_factory=utc_now)
    discharge_date: datetime | None = None

    # Clinical information
    diagnosis_codes: list[str] = Field(default_factory=list)
    procedure_codes: list[str] = Field(default_factory=list)
    medication_codes: list[str] = Field(default_factory=list)

    note_language: NoteLanguage = "en"
    clinical_notes_ar: str = ""
    clinical_notes_en: str = ""

    # Financial and authorization
    requested_amount: float | None = Field(default=None, ge=0)
    currency: str = "SAR"
    prior_authorization: str | None = None

    # Supporting information
    attachments: list[Attachment] = Field(default_factory=list)

    claim_status: ClaimStatus = ClaimStatus.DRAFT
    rejection_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator(
        "diagnosis_codes",
        "procedure_codes",
        "medication_codes",
    )
    @classmethod
    def normalize_codes(cls, values: list[str]) -> list[str]:
        """Normalize codes and remove blanks and duplicates."""

        normalized: list[str] = []

        for value in values:
            code = str(value).strip().upper()

            if code and code not in normalized:
                normalized.append(code)

        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize the currency code."""

        return value.strip().upper()

    @model_validator(mode="after")
    def normalize_encounter_dates(self) -> "ClaimDraft":
        """
        Apply encounter-specific date behavior.

        Outpatient and telemedicine encounters normally begin and end on
        the same date, so discharge defaults to the admission date.
        """

        if (
            self.encounter_type in {"outpatient", "telemedicine"}
            and self.discharge_date is None
        ):
            self.discharge_date = self.admission_date

        return self


class Claim(BaseModel):
    """Complete claim ready for validation or submission."""

    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    claim_id: str = Field(min_length=3)

    patient_id: str = Field(min_length=1)
    patient_age: int = Field(ge=0, le=130)
    gender: Gender = "unknown"

    insurance_company: str = Field(min_length=1)
    policy_number: str = Field(min_length=1)

    provider_id: str = Field(min_length=1)
    practitioner_id: str = Field(min_length=1)

    encounter_type: EncounterType
    admission_date: datetime
    discharge_date: datetime | None = None

    diagnosis_codes: list[str] = Field(default_factory=list)
    procedure_codes: list[str] = Field(default_factory=list)
    medication_codes: list[str] = Field(default_factory=list)

    clinical_notes_ar: str = ""
    clinical_notes_en: str = ""

    requested_amount: float = Field(ge=0)
    currency: str = "SAR"
    prior_authorization: str | None = None

    attachments: list[Attachment] = Field(default_factory=list)

    claim_status: ClaimStatus = ClaimStatus.DRAFT
    rejection_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator(
        "diagnosis_codes",
        "procedure_codes",
        "medication_codes",
    )
    @classmethod
    def normalize_codes(cls, values: list[str]) -> list[str]:
        """Normalize codes and remove blanks and duplicates."""

        normalized: list[str] = []

        for value in values:
            code = str(value).strip().upper()

            if code and code not in normalized:
                normalized.append(code)

        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize the currency code."""

        return value.strip().upper()

    @model_validator(mode="after")
    def validate_dates(self) -> "Claim":
        """Ensure the discharge date is not before admission."""

        if (
            self.discharge_date is not None
            and self.discharge_date < self.admission_date
        ):
            raise ValueError(
                "Discharge date cannot be earlier than admission date."
            )

        return self