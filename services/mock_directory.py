"""Access Aoun's combined prototype data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "aoun_data.json"
)


@lru_cache(maxsize=1)
def load_demo_data() -> dict[str, Any]:
    """Load and cache all Aoun prototype data."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Aoun demo data was not found: {DATA_PATH}"
        )

    with DATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    required_sections = {
        "patients",
        "providers",
        "system_reference_data",
    }

    missing_sections = required_sections - data.keys()

    if missing_sections:
        missing = ", ".join(
            sorted(missing_sections)
        )

        raise ValueError(
            "Aoun demo data is missing sections: "
            f"{missing}"
        )

    return data


def get_patients() -> list[dict[str, Any]]:
    """Return all patient records."""

    return load_demo_data()["patients"]


def find_patient(
    patient_id: str,
) -> dict[str, Any] | None:
    """Find a patient by patient identifier."""

    return next(
        (
            patient
            for patient in get_patients()
            if patient["patient_id"] == patient_id
        ),
        None,
    )


def get_providers() -> list[dict[str, Any]]:
    """Return all provider records."""

    return load_demo_data()["providers"]


def get_default_provider() -> dict[str, Any]:
    """Return the default logged-in provider."""

    providers = get_providers()

    if not providers:
        raise ValueError(
            "No providers are configured."
        )

    return providers[0]


def get_reference_data() -> dict[str, Any]:
    """Return code and payer reference data."""

    return load_demo_data()[
        "system_reference_data"
    ]


def get_diagnosis_codes() -> list[dict[str, Any]]:
    """Return diagnosis-code records."""

    return get_reference_data().get(
        "diagnosis_codes",
        [],
    )


def get_procedure_codes() -> list[dict[str, Any]]:
    """Return procedure-code records."""

    return get_reference_data().get(
        "procedure_codes",
        [],
    )


def get_medication_codes() -> list[dict[str, Any]]:
    """Return medication-code records."""

    return get_reference_data().get(
        "medication_codes",
        [],
    )


def get_insurance_policies() -> list[dict[str, Any]]:
    """Return insurance-policy records."""

    return get_reference_data().get(
        "insurance_policies",
        [],
    )


def find_diagnosis(
    code: str,
) -> dict[str, Any] | None:
    """Find a diagnosis by code."""

    normalized_code = code.strip().upper()

    return next(
        (
            diagnosis
            for diagnosis in get_diagnosis_codes()
            if (
                diagnosis["code"].strip().upper()
                == normalized_code
            )
        ),
        None,
    )


def find_procedure(
    code: str,
) -> dict[str, Any] | None:
    """Find a procedure by code."""

    normalized_code = code.strip().upper()

    return next(
        (
            procedure
            for procedure in get_procedure_codes()
            if (
                procedure["code"].strip().upper()
                == normalized_code
            )
        ),
        None,
    )


def find_medication(
    code: str,
) -> dict[str, Any] | None:
    """Find a medication by code."""

    normalized_code = code.strip().upper()

    return next(
        (
            medication
            for medication in get_medication_codes()
            if (
                medication["code"].strip().upper()
                == normalized_code
            )
        ),
        None,
    )


def find_policy(
    company: str,
    tier: str,
) -> dict[str, Any] | None:
    """Find an insurance policy by company and tier."""

    normalized_company = company.strip().lower()
    normalized_tier = tier.strip().lower()

    return next(
        (
            policy
            for policy in get_insurance_policies()
            if (
                policy["company"].strip().lower()
                == normalized_company
                and policy["tier"].strip().lower()
                == normalized_tier
            )
        ),
        None,
    )