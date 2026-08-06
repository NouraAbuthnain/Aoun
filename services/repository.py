"""Database repository for persistent Aoun claim records."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import select

from database.models import ClaimRecord
from database.session import SessionLocal


def upsert_claim_record(
    *,
    claim: dict[str, Any],
    validation: dict[str, Any],
    status: str,
    submitted_at: datetime | None = None,
) -> ClaimRecord:
    """Insert or update a persistent claim record."""

    claim_id = str(claim["claim_id"])

    blocking_errors = validation.get(
        "blocking_errors",
        [],
    )

    primary_issue = "No blocking issue"

    if blocking_errors:
        first_error = blocking_errors[0]

        if isinstance(first_error, dict):
            primary_issue = str(
                first_error.get(
                    "title",
                    "Validation issue",
                )
            )

    with SessionLocal() as session:
        record = session.scalar(
            select(ClaimRecord).where(
                ClaimRecord.claim_id == claim_id
            )
        )

        if record is None:
            record = ClaimRecord(
                claim_id=claim_id,
                patient_id=str(
                    claim.get("patient_id", "")
                ),
                status=status,
                compliance_score=float(
                    validation.get(
                        "readiness_score",
                        0,
                    )
                ),
                acceptance_probability=float(
                    validation.get(
                        "acceptance_probability",
                        0,
                    )
                ),
                primary_issue=primary_issue,
                claim_json=json.dumps(
                    claim,
                    ensure_ascii=False,
                    default=str,
                ),
                validation_json=json.dumps(
                    validation,
                    ensure_ascii=False,
                    default=str,
                ),
                submitted_at=submitted_at,
            )

            session.add(record)

        else:
            record.patient_id = str(
                claim.get("patient_id", "")
            )
            record.status = status
            record.compliance_score = float(
                validation.get(
                    "readiness_score",
                    0,
                )
            )
            record.acceptance_probability = float(
                validation.get(
                    "acceptance_probability",
                    0,
                )
            )
            record.primary_issue = primary_issue
            record.claim_json = json.dumps(
                claim,
                ensure_ascii=False,
                default=str,
            )
            record.validation_json = json.dumps(
                validation,
                ensure_ascii=False,
                default=str,
            )
            record.updated_at = (
                datetime.now().astimezone()
            )

            if submitted_at is not None:
                record.submitted_at = submitted_at

        session.commit()
        session.refresh(record)

        return record


def list_claim_records() -> list[dict[str, Any]]:
    """Return all persisted claims, newest first."""

    with SessionLocal() as session:
        records = session.scalars(
            select(ClaimRecord).order_by(
                ClaimRecord.updated_at.desc()
            )
        ).all()

        return [
            {
                "id": record.id,
                "claim_id": record.claim_id,
                "patient_id": record.patient_id,
                "status": record.status,
                "readiness_score": (
                    record.compliance_score
                ),
                "acceptance_probability": (
                    record.acceptance_probability
                ),
                "primary_issue": record.primary_issue,
                "claim": json.loads(
                    record.claim_json
                ),
                "validation": json.loads(
                    record.validation_json
                ),
                "created_at": (
                    record.created_at.isoformat()
                    if record.created_at
                    else None
                ),
                "updated_at": (
                    record.updated_at.isoformat()
                    if record.updated_at
                    else None
                ),
                "submitted_at": (
                    record.submitted_at.isoformat()
                    if record.submitted_at
                    else None
                ),
            }
            for record in records
        ]


def get_claim_record(
    claim_id: str,
) -> dict[str, Any] | None:
    """Return one persisted claim by claim identifier."""

    with SessionLocal() as session:
        record = session.scalar(
            select(ClaimRecord).where(
                ClaimRecord.claim_id == claim_id
            )
        )

        if record is None:
            return None

        return {
            "id": record.id,
            "claim_id": record.claim_id,
            "patient_id": record.patient_id,
            "status": record.status,
            "readiness_score": (
                record.compliance_score
            ),
            "acceptance_probability": (
                record.acceptance_probability
            ),
            "primary_issue": record.primary_issue,
            "claim": json.loads(record.claim_json),
            "validation": json.loads(
                record.validation_json
            ),
            "created_at": (
                record.created_at.isoformat()
                if record.created_at
                else None
            ),
            "updated_at": (
                record.updated_at.isoformat()
                if record.updated_at
                else None
            ),
            "submitted_at": (
                record.submitted_at.isoformat()
                if record.submitted_at
                else None
            ),
        }


def delete_claim_record(claim_id: str) -> bool:
    """Delete one persisted claim."""

    with SessionLocal() as session:
        record = session.scalar(
            select(ClaimRecord).where(
                ClaimRecord.claim_id == claim_id
            )
        )

        if record is None:
            return False

        session.delete(record)
        session.commit()

        return True