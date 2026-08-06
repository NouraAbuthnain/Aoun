"""Unified claims workspace for Aoun."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st
from pydantic import ValidationError

from schemas.claim import Attachment, ClaimDraft
from services.claim_builder import finalize_claim
from services.speech_to_text import transcribe_audio
from services.mock_directory import (
    get_default_provider,
    get_diagnosis_codes,
    get_medication_codes,
    get_patients,
    get_procedure_codes,
)

from copy import deepcopy
from services.repository import upsert_claim_record

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


STEP_NAMES = [
    "Patient and insurance",
    "Provider and visit",
    "Clinical documentation",
    "Diagnosis and services",
    "Supporting documents",
]

# Prototype values imported from the hospital billing system.
# Replace these with the real hospital integration later.
IMPORTED_REQUESTED_AMOUNT = 545.0
IMPORTED_CURRENCY = "SAR"


# =========================================================
# Workspace state
# =========================================================


def generate_claim_id() -> str:
    """Generate a readable unique claim identifier."""

    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = uuid4().hex[:6].upper()

    return f"AOUN-{date_part}-{unique_part}"


def initialize_claim_workspace() -> None:
    """Initialize the claim draft and shared UI state."""

    if "claim_draft" not in st.session_state:
        provider = get_default_provider()

        draft = ClaimDraft(
            claim_id=generate_claim_id(),
            provider_id=provider["provider_id"],
            practitioner_id=provider["practitioner_id"],
            admission_date=datetime.combine(
                date.today(),
                datetime.min.time(),
            ),
            requested_amount=IMPORTED_REQUESTED_AMOUNT,
            currency=IMPORTED_CURRENCY,
        )

        st.session_state.claim_draft = draft.model_dump(mode="json")

    if "draft_save_status" not in st.session_state:
        st.session_state.draft_save_status = "Draft saved automatically"


def initialize_wizard_state() -> None:
    """Initialize the claim wizard state."""

    defaults = {
        "active_claim_step": 0,
        "completed_claim_steps": [],
        "confirm_clear_claim": False,
        "claim_workspace_mode": "document",
        "show_review_dialog": False,
        "submission_completed": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_draft() -> ClaimDraft:
    """Return the current claim draft."""

    return ClaimDraft.model_validate(
        st.session_state.claim_draft
    )


def save_draft(draft: ClaimDraft) -> None:
    """Store the current claim draft in session state."""

    draft.updated_at = datetime.now().astimezone()

    st.session_state.claim_draft = draft.model_dump(
        mode="json"
    )

    st.session_state.draft_save_status = "Draft saved ✓"


def clear_claim_workspace() -> None:
    """Clear all current claim information."""

    keys_to_remove = [
        "claim_draft",
        "claim",
        "validation",
        "review_decision",
        "submission_response",
        "validation_result",
        "show_review_dialog",
        "active_claim_step",
        "completed_claim_steps",
        "confirm_clear_claim",
        "claim_workspace_mode",
        "clinical_note",
        "clinical_audio",
        "processed_audio_signature",
        "claim_attachments",
        "selected_patient",
        "encounter_type_input",
        "visit_date_input",
        "discharge_date_input",
        "diagnosis_codes_input",
        "procedure_codes_input",
        "medication_codes_input",
        "draft_save_status",
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)

    st.rerun()


# =========================================================
# Wizard navigation
# =========================================================


def mark_step_complete(step_index: int) -> None:
    """Mark a wizard step as complete."""

    completed = list(
        st.session_state.completed_claim_steps
    )

    if step_index not in completed:
        completed.append(step_index)

    st.session_state.completed_claim_steps = completed


def open_step(step_index: int) -> None:
    """Open a particular wizard step."""

    st.session_state.active_claim_step = step_index


def previous_step() -> None:
    """Return to the previous wizard step."""

    current_step = st.session_state.active_claim_step

    if current_step > 0:
        st.session_state.active_claim_step = current_step - 1


def render_claim_stepper() -> None:
    """Render the vertical Aoun claim workflow."""

    current_step = st.session_state.active_claim_step
    completed_steps = (
        st.session_state.completed_claim_steps
    )

    st.markdown("### Claim progress")

    for index, name in enumerate(STEP_NAMES):
        is_current = index == current_step
        is_complete = index in completed_steps

        is_available = (
            is_current
            or is_complete
            or index == current_step + 1
        )

        state = "✓" if is_complete else str(index + 1)

        clicked = st.button(
            f"{state}  {name}",
            key=f"claim_step_{index}",
            type="primary" if is_current else "secondary",
            disabled=not is_available,
            width="stretch",
        )

        if clicked:
            open_step(index)
            st.rerun()


# =========================================================
# Completion checks
# =========================================================


def patient_step_complete(draft: ClaimDraft) -> bool:
    """Check whether patient information is complete."""

    return bool(
        draft.patient_id
        and draft.patient_age is not None
        and draft.gender != "unknown"
        and draft.insurance_company
        and draft.policy_number
    )


def visit_step_complete(draft: ClaimDraft) -> bool:
    """Check whether provider and visit information is complete."""

    if not draft.provider_id:
        return False

    if not draft.practitioner_id:
        return False

    if not draft.admission_date:
        return False

    if draft.encounter_type in {
        "inpatient",
        "emergency",
        "other",
    }:
        return draft.discharge_date is not None

    return True


def clinical_step_complete(draft: ClaimDraft) -> bool:
    """
    Check whether the doctor typed or recorded a clinical note.

    Both typed notes and STT-generated transcripts are accepted.
    """

    widget_note = st.session_state.get(
        "clinical_note",
        "",
    ).strip()

    saved_note = (
        draft.clinical_notes_ar
        or draft.clinical_notes_en
        or ""
    ).strip()

    final_note = widget_note or saved_note

    return len(final_note) >= 3


def codes_step_complete(draft: ClaimDraft) -> bool:
    """Check whether diagnosis and procedure codes exist."""

    return bool(
        draft.diagnosis_codes
        and draft.procedure_codes
    )


def calculate_completion(draft: ClaimDraft) -> float:
    """Calculate completion for information the doctor is responsible for."""

    checks = [
        patient_step_complete(draft),
        visit_step_complete(draft),
        clinical_step_complete(draft),
        codes_step_complete(draft),
    ]

    return sum(checks) / len(checks)


# =========================================================
# Patient and insurance
# =========================================================


def render_patient_section(
    draft: ClaimDraft,
) -> ClaimDraft:
    """Select a patient and automatically load insurance data."""

    patients = get_patients()

    patient_labels = {
        (
            f"{patient['full_name']} · "
            f"{patient['patient_id']} · "
            f"{patient['national_id']}"
        ): patient
        for patient in patients
    }

    options = [
        "Select a patient",
        *patient_labels.keys(),
    ]

    current_index = 0

    if draft.patient_id:
        for index, label in enumerate(options):
            patient = patient_labels.get(label)

            if (
                patient
                and patient["patient_id"]
                == draft.patient_id
            ):
                current_index = index
                break

    selected_label = st.selectbox(
        "Search patient",
        options=options,
        index=current_index,
        key="selected_patient",
        help="Search by name, patient ID, or national ID.",
    )

    if selected_label == "Select a patient":
        st.info("Select a patient to continue.")
        return draft

    selected_patient = patient_labels[selected_label]

    patient_changed = (
        draft.patient_id
        != selected_patient["patient_id"]
    )

    draft.patient_id = selected_patient["patient_id"]
    draft.patient_age = selected_patient["age"]
    draft.gender = selected_patient["gender"]
    draft.insurance_company = (
        selected_patient["insurance_company"]
    )
    draft.policy_number = selected_patient["policy_number"]

    save_draft(draft)

    details = st.columns(4)

    details[0].metric(
        "Age",
        selected_patient["age"],
    )

    details[1].metric(
        "Gender",
        selected_patient["gender"].title(),
    )

    details[2].metric(
        "Insurance",
        selected_patient["insurance_company"],
    )

    details[3].metric(
        "Eligibility",
        selected_patient[
            "eligibility_status"
        ].title(),
    )

    if (
        selected_patient["eligibility_status"]
        != "active"
    ):
        st.error(
            "The selected insurance policy is not active."
        )
        return draft

    if patient_changed:
        mark_step_complete(0)
        st.session_state.active_claim_step = 1
        st.rerun()

    return draft


# =========================================================
# Provider and visit
# =========================================================


def render_visit_section(
    draft: ClaimDraft,
) -> ClaimDraft:
    """Render provider and encounter information."""

    provider = get_default_provider()

    st.info(
        f"**{provider['practitioner_name']}**  \n"
        f"{provider['specialty']} · "
        f"{provider['department']}  \n"
        f"Provider: {provider['provider_id']}"
    )

    encounter_options = [
        "outpatient",
        "inpatient",
        "emergency",
        "telemedicine",
        "other",
    ]

    encounter_type = st.selectbox(
        "Encounter type",
        options=encounter_options,
        index=encounter_options.index(
            draft.encounter_type
        ),
        key="encounter_type_input",
    )

    visit_date = st.date_input(
        "Visit or admission date",
        value=draft.admission_date.date(),
        key="visit_date_input",
    )

    draft.encounter_type = encounter_type

    draft.admission_date = datetime.combine(
        visit_date,
        datetime.min.time(),
    )

    if encounter_type in {
        "outpatient",
        "telemedicine",
    }:
        draft.discharge_date = draft.admission_date

        st.caption(
            "The discharge date automatically matches "
            "the visit date."
        )

    else:
        discharge_date = st.date_input(
            "Discharge date",
            value=(
                draft.discharge_date.date()
                if draft.discharge_date
                else visit_date
            ),
            key="discharge_date_input",
        )

        draft.discharge_date = datetime.combine(
            discharge_date,
            datetime.min.time(),
        )

    save_draft(draft)

    return draft


# =========================================================
# Clinical documentation
# =========================================================


def detect_note_language(text: str) -> str:
    """Detect whether a note is mainly Arabic or English."""

    arabic_characters = sum(
        1
        for character in text
        if "\u0600" <= character <= "\u06FF"
    )

    latin_characters = sum(
        1
        for character in text
        if character.isascii()
        and character.isalpha()
    )

    if arabic_characters > latin_characters:
        return "ar"

    return "en"


def save_clinical_note(
    draft: ClaimDraft,
    note: str,
) -> ClaimDraft:
    """Save a typed or transcribed note into the draft."""

    clean_note = note.strip()

    if not clean_note:
        draft.clinical_notes_ar = ""
        draft.clinical_notes_en = ""

        save_draft(draft)
        return draft

    language = detect_note_language(clean_note)
    draft.note_language = language

    if language == "ar":
        draft.clinical_notes_ar = clean_note
        draft.clinical_notes_en = ""

    else:
        draft.clinical_notes_en = clean_note
        draft.clinical_notes_ar = ""

    save_draft(draft)

    return draft


def render_clinical_section(
    draft: ClaimDraft,
) -> ClaimDraft:
    """
    Allow the doctor to type or record an editable clinical note.

    Either method enables the Continue button.
    """

    note_key = "clinical_note"

    saved_note = (
        draft.clinical_notes_ar
        or draft.clinical_notes_en
        or ""
    )

    if note_key not in st.session_state:
        st.session_state[note_key] = saved_note

    audio_recording = st.audio_input(
        "Record clinical note",
        key="clinical_audio",
    )

    if audio_recording is not None:
        audio_bytes = audio_recording.getvalue()

        audio_signature = (
            f"{audio_recording.name}:"
            f"{len(audio_bytes)}"
        )

        already_processed = (
            st.session_state.get(
                "processed_audio_signature"
            )
            == audio_signature
        )

        if not already_processed:
            with st.spinner(
                "Transcribing clinical note..."
            ):
                try:
                    transcript = transcribe_audio(
                        audio_bytes=audio_bytes,
                        filename=(
                            audio_recording.name
                            or "clinical_note.wav"
                        ),
                        language=None,
                    )

                except Exception as error:
                    st.error(
                        f"Speech-to-text failed: {error}"
                    )

                else:
                    st.session_state[
                        "processed_audio_signature"
                    ] = audio_signature

                    current_note = st.session_state.get(
                        note_key,
                        "",
                    ).strip()

                    if current_note:
                        updated_note = (
                            f"{current_note}\n{transcript}"
                        )
                    else:
                        updated_note = transcript

                    # Place the transcript in the same editable text area.
                    st.session_state[note_key] = updated_note

                    draft = save_clinical_note(
                        draft,
                        updated_note,
                    )

                    st.success(
                        "Recording converted to text successfully."
                    )

                    st.rerun()

    note = st.text_area(
        "Clinical note",
        key=note_key,
        height=220,
        placeholder=(
            "Write or dictate the clinical note here..."
        ),
    )

    # Save typed text and edited transcripts.
    draft = save_clinical_note(
        draft,
        note,
    )

    st.caption(
        "Write the note or record it. "
        "Either option enables Continue."
    )

    return draft


# =========================================================
# Diagnosis and services
# =========================================================


def parse_codes(value: str) -> list[str]:
    """Convert comma-separated codes into a clean list."""

    return [
        code.strip().upper()
        for code in value.split(",")
        if code.strip()
    ]

def render_codes_section(
    draft: ClaimDraft,
) -> ClaimDraft:
    """Select diagnosis, procedure, and medication codes."""

    diagnosis_records = get_diagnosis_codes()
    procedure_records = get_procedure_codes()
    medication_records = get_medication_codes()

    # Show only billable diagnoses that match the patient's gender.
    available_diagnoses = []

    for diagnosis in diagnosis_records:
        if not diagnosis.get("billable", False):
            continue

        gender_restriction = diagnosis.get("gender_restriction")

        if (
            gender_restriction == "F"
            and draft.gender != "female"
        ):
            continue

        if (
            gender_restriction == "M"
            and draft.gender != "male"
        ):
            continue

        available_diagnoses.append(diagnosis)

    diagnosis_labels = {
        (
            f"{diagnosis['code']} — "
            f"{diagnosis['name']}"
        ): diagnosis["code"]
        for diagnosis in available_diagnoses
    }

    procedure_labels = {
        (
            f"{procedure['code']} — "
            f"{procedure['name']}"
        ): procedure["code"]
        for procedure in procedure_records
    }

    medication_labels = {
        (
            f"{medication['code']} — "
            f"{medication['name']}"
        ): medication["code"]
        for medication in medication_records
    }

    diagnosis_defaults = [
        label
        for label, code in diagnosis_labels.items()
        if code in draft.diagnosis_codes
    ]

    procedure_defaults = [
        label
        for label, code in procedure_labels.items()
        if code in draft.procedure_codes
    ]

    medication_defaults = [
        label
        for label, code in medication_labels.items()
        if code in draft.medication_codes
    ]

    selected_diagnoses = st.multiselect(
        "Diagnosis",
        options=list(diagnosis_labels),
        default=diagnosis_defaults,
        placeholder="Search by diagnosis name or code",
        key="diagnosis_selection",
    )

    selected_procedures = st.multiselect(
        "Required services",
        options=list(procedure_labels),
        default=procedure_defaults,
        placeholder="Search by service name or code",
        key="procedure_selection",
    )

    selected_medications = st.multiselect(
        "Medications",
        options=list(medication_labels),
        default=medication_defaults,
        placeholder="Search by medication name or code",
        key="medication_selection",
    )

    draft.diagnosis_codes = [
        diagnosis_labels[label]
        for label in selected_diagnoses
    ]

    draft.procedure_codes = [
        procedure_labels[label]
        for label in selected_procedures
    ]

    draft.medication_codes = [
        medication_labels[label]
        for label in selected_medications
    ]

    save_draft(draft)

    # Show useful information about selected procedures.
    selected_procedure_records = [
        procedure
        for procedure in procedure_records
        if procedure["code"] in draft.procedure_codes
    ]

    preauthorization_codes = [
        procedure["code"]
        for procedure in selected_procedure_records
        if procedure.get(
            "requires_preauth_standard",
            False,
        )
    ]

    if preauthorization_codes:
        st.warning(
            "Prior authorization may be required for: "
            + ", ".join(preauthorization_codes)
        )

    if draft.diagnosis_codes and draft.procedure_codes:
        st.success(
            "Diagnosis and required service information is complete."
        )

    return draft

# =========================================================
# Supporting documents
# =========================================================


def render_attachments_section(
    draft: ClaimDraft,
) -> ClaimDraft:
    """Upload and store supporting claim documents."""

    st.success(
    "Billing information imported successfully from the hospital system."
)

    st.caption(
        "Upload prescriptions, reports, prior "
        "authorizations, laboratory results, or other "
        "supporting documents."
    )

    uploaded_files = st.file_uploader(
        "Upload supporting documents",
        type=[
            "pdf",
            "png",
            "jpg",
            "jpeg",
            "docx",
        ],
        accept_multiple_files=True,
        key="claim_attachments",
    )

    if uploaded_files:
        existing_names = {
            attachment.name
            for attachment in draft.attachments
        }

        added_files = 0

        for uploaded_file in uploaded_files:
            if uploaded_file.name in existing_names:
                continue

            safe_name = Path(uploaded_file.name).name

            stored_name = (
                f"{draft.claim_id}_{safe_name}"
            )

            file_path = UPLOAD_DIR / stored_name

            file_path.write_bytes(
                uploaded_file.getvalue()
            )

            attachment = Attachment(
                name=safe_name,
                mime_type=(
                    uploaded_file.type
                    or "application/octet-stream"
                ),
                storage_uri=str(file_path),
                category="supporting_document",
                size_bytes=uploaded_file.size,
            )

            draft.attachments.append(attachment)
            existing_names.add(safe_name)
            added_files += 1

        if added_files:
            save_draft(draft)

            st.success(
                f"{added_files} supporting document(s) added."
            )

    if not draft.attachments:
        st.info(
            "No supporting documents have been attached."
        )
        return draft

    st.markdown("#### Attached documents")

    for index, attachment in enumerate(
        list(draft.attachments)
    ):
        name_column, type_column, action_column = (
            st.columns([4, 2, 1])
        )

        with name_column:
            st.write(f"📎 {attachment.name}")

        with type_column:
            st.caption(attachment.mime_type)

        with action_column:
            remove_clicked = st.button(
                "Remove",
                key=(
                    f"remove_attachment_"
                    f"{index}_{attachment.name}"
                ),
                width="content",
            )

        if remove_clicked:
            if attachment.storage_uri:
                stored_file = Path(
                    attachment.storage_uri
                )

                if stored_file.exists():
                    stored_file.unlink()

            draft.attachments.pop(index)
            save_draft(draft)
            st.rerun()

    return draft


# =========================================================
# Review
# =========================================================


def run_mock_claim_validation(
    draft: ClaimDraft,
) -> dict[str, object]:
    """Run a deterministic demonstration validation.

    For the demo, low-back-pain diagnosis M54.5 paired with chest
    radiograph procedure 71045 is treated as a blocking mismatch.
    Correcting either selection produces a ready result.
    """

    diagnosis_codes = set(draft.diagnosis_codes)
    procedure_codes = set(draft.procedure_codes)

    mismatch_detected = (
        "M54.5" in diagnosis_codes
        and "71045" in procedure_codes
    )

    passed_checks = [
        "Patient information complete",
        "Insurance eligibility confirmed",
        "Provider information complete",
        "Clinical documentation complete",
        "Billing information imported",
    ]

    if mismatch_detected:
        return {
            "readiness_score": 50,
            "acceptance_probability": 42,
            "status": "needs_correction",
            "blocking_errors": [
                {
                    "code": "DIAGNOSIS_PROCEDURE_MISMATCH",
                    "title": "Diagnosis and procedure mismatch",
                    "message": (
                        "Low back pain does not clinically support "
                        "a chest radiograph."
                    ),
                    "suggestion": (
                        "Review the diagnosis, select a clinically "
                        "related service, or strengthen the clinical "
                        "justification."
                    ),
                }
            ],
            "warnings": [
                {
                    "code": "CLINICAL_JUSTIFICATION_WEAK",
                    "title": "Clinical justification may be incomplete",
                    "message": (
                        "The clinical note should clearly explain why "
                        "the selected service is medically necessary."
                    ),
                }
            ],
            "passed_checks": passed_checks,
        }

    return {
        "readiness_score": 90,
        "acceptance_probability": 86,
        "status": "ready",
        "blocking_errors": [],
        "warnings": [],
        "passed_checks": [
            *passed_checks,
            "Diagnosis and procedure are compatible",
        ],
    }


def start_claim_review(draft: ClaimDraft) -> None:
    """Finalize and validate the claim before review."""

    try:
        claim = finalize_claim(draft)
    except ValidationError as error:
        st.error(
            "Some required claim information is incomplete."
        )

        for issue in error.errors():
            field = " → ".join(
                str(value)
                for value in issue["loc"]
            )
            st.warning(f"{field}: {issue['msg']}")

        return

    st.session_state.claim = claim.model_dump(mode="json")
    st.session_state.validation_result = (
        run_mock_claim_validation(draft)
    )
    st.session_state.show_review_dialog = True


def _get_primary_issue(
    validation: dict[str, object],
) -> str:
    """Return the first blocking issue title, if present."""

    blocking_errors = validation.get("blocking_errors", [])

    if isinstance(blocking_errors, list) and blocking_errors:
        first_error = blocking_errors[0]

        if isinstance(first_error, dict):
            return str(
                first_error.get(
                    "title",
                    "Validation issue",
                )
            )

    return "No blocking issue"


def _get_patient_name(patient_id: object) -> str:
    """Return the patient display name for history records."""

    patient_id_value = str(patient_id or "")

    for patient in get_patients():
        if str(patient.get("patient_id", "")) == patient_id_value:
            return str(patient.get("full_name", patient_id_value or "—"))

    return patient_id_value or "—"

def save_reviewed_claim_as_draft() -> None:
    """Persist a reviewed claim that needs correction."""

    claim = deepcopy(
        st.session_state.get("claim", {})
    )

    validation = deepcopy(
        st.session_state.get(
            "validation_result",
            {},
        )
    )

    if not claim:
        st.error("No reviewed claim is available.")
        return

    upsert_claim_record(
        claim=claim,
        validation=validation,
        status="needs_correction",
    )

    st.session_state.show_review_dialog = False
    st.session_state.active_claim_step = 3
    st.session_state.draft_save_status = (
        "Needs-correction draft saved ✓"
    )

def submit_reviewed_claim() -> None:
    """Persist a compliant claim as submitted."""

    claim = deepcopy(
        st.session_state.get("claim", {})
    )

    validation = deepcopy(
        st.session_state.get(
            "validation_result",
            {},
        )
    )

    if not claim:
        st.error("No finalized claim is available.")
        return

    blocking_errors = validation.get(
        "blocking_errors",
        [],
    )

    compliance_score = int(
        validation.get(
            "readiness_score",
            0,
        )
    )

    if blocking_errors or compliance_score < 70:
        st.error(
            "This claim still has blocking issues "
            "and cannot be submitted."
        )
        return

    submitted_at = datetime.now().astimezone()

    upsert_claim_record(
        claim=claim,
        validation=validation,
        status="submitted",
        submitted_at=submitted_at,
    )

    st.session_state.show_review_dialog = False
    clear_current_claim_after_submission()

def clear_current_claim_after_submission() -> None:
    """Clear the editor while preserving history and submission data."""

    keys_to_remove = [
        "claim_draft",
        "claim",
        "validation_result",
        "active_claim_step",
        "completed_claim_steps",
        "clinical_note",
        "clinical_audio",
        "processed_audio_signature",
        "claim_attachments",
        "selected_patient",
        "encounter_type_input",
        "visit_date_input",
        "discharge_date_input",
        "diagnosis_selection",
        "procedure_selection",
        "medication_selection",
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)

    st.session_state.submission_completed = True


@st.dialog(
    "Aoun claim validation",
    width="large",
    dismissible=False,
)
def render_review_dialog() -> None:
    """Display the current claim compliance result."""

    result = st.session_state.get("validation_result")

    if not isinstance(result, dict):
        st.error("No validation result is available.")
        return

    compliance_score = int(
        result.get("readiness_score", 0)
    )
    acceptance_probability = int(
        result.get("acceptance_probability", 0)
    )
    blocking_errors = result.get("blocking_errors", [])
    warnings = result.get("warnings", [])
    passed_checks = result.get("passed_checks", [])

    has_blocking_errors = bool(blocking_errors)
    is_ready = (
        not has_blocking_errors
        and compliance_score >= 70
    )

    st.markdown("### Claim compliance result")
    st.caption(
        "The compliance score measures how well the claim meets "
        "clinical, coding, administrative, and payer requirements."
    )

    score_column, probability_column = st.columns(2)

    with score_column:
        st.metric(
            "Claim compliance score",
            f"{compliance_score}%",
            help=(
                "A combined score for claim completeness and compliance "
                "with clinical, coding, administrative, and payer rules."
            ),
        )

    with probability_column:
        st.metric(
            "Estimated acceptance",
            f"{acceptance_probability}%",
            help=(
                "A demonstration estimate of the chance that the payer "
                "will accept the claim."
            ),
        )

    st.progress(compliance_score / 100)

    if is_ready:
        st.success(
            "No blocking compliance issues were detected. "
            "The claim is ready for submission."
        )
    else:
        st.error(
            "The claim does not meet all compliance requirements "
            "and needs correction before submission."
        )

    if isinstance(blocking_errors, list) and blocking_errors:
        st.markdown("### Blocking compliance issues")

        for error in blocking_errors:
            if not isinstance(error, dict):
                continue

            with st.container(border=True):
                st.error(
                    str(error.get("title", "Blocking issue"))
                )
                st.write(str(error.get("message", "")))
                st.caption(
                    "Suggested correction: "
                    + str(
                        error.get(
                            "suggestion",
                            "Review the claim.",
                        )
                    )
                )

    if isinstance(warnings, list) and warnings:
        st.markdown("### Compliance warnings")

        for warning in warnings:
            if not isinstance(warning, dict):
                continue

            with st.container(border=True):
                st.warning(
                    str(warning.get("title", "Warning"))
                )
                st.write(str(warning.get("message", "")))

    if isinstance(passed_checks, list) and passed_checks:
        st.markdown("### Passed compliance checks")

        with st.container(border=True):
            for check in passed_checks:
                st.markdown(f"✓ {check}")

    st.divider()

    back_column, action_column = st.columns(2)

    with back_column:
        if st.button(
            "Return and correct",
            width="stretch",
            key="dialog_return_to_claim",
        ):
            st.session_state.show_review_dialog = False
            st.session_state.active_claim_step = 3
            st.rerun()

    with action_column:
        if is_ready:
            if st.button(
                "Submit claim",
                type="primary",
                width="stretch",
                key="dialog_submit_claim",
            ):
                submit_reviewed_claim()
                st.rerun()
        else:
            if st.button(
                "Save as draft",
                width="stretch",
                key="dialog_save_draft",
            ):
                save_reviewed_claim_as_draft()
                st.rerun()


# =========================================================
# Main page
# =========================================================


def render() -> None:
    """Render the progressive Aoun claim wizard."""

    initialize_claim_workspace()
    initialize_wizard_state()

    draft = get_draft()

    if st.session_state.get("submission_completed", False):
        st.success(
            "Claim submitted successfully for demonstration and added "
            "to History."
        )
        st.session_state.submission_completed = False

    header_left, header_right = st.columns([4, 1])

    with header_left:
        st.title("New Claim")
        st.caption(f"Claim ID: {draft.claim_id}")

    with header_right:
        st.caption(
            st.session_state.draft_save_status
        )

        if st.button(
            "Clear claim",
            width="stretch",
            key="clear_claim_button",
        ):
            st.session_state.confirm_clear_claim = True

    if st.session_state.confirm_clear_claim:
        st.warning(
            "This will permanently clear the current claim draft."
        )

        confirm_column, cancel_column = st.columns(2)

        with confirm_column:
            if st.button(
                "Clear everything",
                type="primary",
                width="stretch",
                key="confirm_clear_claim_button",
            ):
                clear_claim_workspace()

        with cancel_column:
            if st.button(
                "Cancel",
                width="stretch",
                key="cancel_clear_claim_button",
            ):
                st.session_state.confirm_clear_claim = False
                st.rerun()

    completion = calculate_completion(draft)

    st.progress(completion)
    st.caption(f"{completion:.0%} complete")

    stepper_column, content_column = st.columns(
        [1, 2.3],
        gap="large",
    )

    with stepper_column:
        render_claim_stepper()

    with content_column:
        current_step = (
            st.session_state.active_claim_step
        )

        if current_step == 0:
            st.header("Patient and insurance")
            draft = render_patient_section(draft)

        elif current_step == 1:
            st.header("Provider and visit")
            draft = render_visit_section(draft)

        elif current_step == 2:
            st.header("Clinical documentation")
            draft = render_clinical_section(draft)

        elif current_step == 3:
            st.header("Diagnosis and services")
            draft = render_codes_section(draft)

        elif current_step == 4:
            st.header("Supporting documents")
            draft = render_attachments_section(draft)

        st.divider()

        back_column, next_column = st.columns(2)

        with back_column:
            if current_step > 0:
                if st.button(
                    "← Back",
                    width="stretch",
                    key=f"back_step_{current_step}",
                ):
                    previous_step()
                    st.rerun()

        with next_column:
            if current_step == 1:
                can_continue = visit_step_complete(draft)

                if st.button(
                    "Continue →",
                    type="primary",
                    disabled=not can_continue,
                    width="stretch",
                    key="continue_visit",
                ):
                    mark_step_complete(1)
                    st.session_state.active_claim_step = 2
                    st.rerun()

            elif current_step == 2:
                # Either typed text or STT transcription enables Continue.
                can_continue = clinical_step_complete(draft)

                if st.button(
                    "Continue →",
                    type="primary",
                    disabled=not can_continue,
                    width="stretch",
                    key="continue_clinical",
                ):
                    latest_note = st.session_state.get(
                        "clinical_note",
                        "",
                    ).strip()

                    if latest_note:
                        draft = save_clinical_note(
                            draft,
                            latest_note,
                        )

                    mark_step_complete(2)
                    st.session_state.active_claim_step = 3
                    st.rerun()

            elif current_step == 3:
                draft = get_draft()
                can_continue = codes_step_complete(draft)

                if st.button(
                    "Continue →",
                    type="primary",
                    disabled=not can_continue,
                    width="stretch",
                    key="continue_codes",
                ):
                    mark_step_complete(3)
                    st.session_state.active_claim_step = 4
                    st.rerun()

            elif current_step == 4:
                draft = get_draft()

                review_ready = all(
                    [
                        patient_step_complete(draft),
                        visit_step_complete(draft),
                        clinical_step_complete(draft),
                        codes_step_complete(draft),
                    ]
                )

                if st.button(
                    "Review claim",
                    type="primary",
                    disabled=not review_ready,
                    width="stretch",
                    key="review_claim",
                ):
                    mark_step_complete(4)
                    start_claim_review(draft)

            if st.session_state.get("show_review_dialog", False):
                render_review_dialog()