"""Utilities for converting claim drafts into complete claims."""

from __future__ import annotations

from schemas.claim import Claim, ClaimDraft, ClaimStatus


def finalize_claim(draft: ClaimDraft) -> Claim:
    """
    Convert a completed draft into a claim.

    Pydantic raises a validation error when required information is missing.
    """

    data = draft.model_dump(
        exclude={
            "note_language",
            "updated_at",
        }
    )

    data["claim_status"] = ClaimStatus.VALIDATING

    return Claim.model_validate(data)