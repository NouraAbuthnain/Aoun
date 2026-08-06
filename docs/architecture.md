# Architecture
Aoun is a provider-side quality middleware layer. Streamlit presents claim entry, validation, review, submission, history and analytics. Pydantic owns the canonical domain schema. LangGraph coordinates deterministic fan-out/fan-in validation, conditional review routing, interrupt/resume and checkpointing. SQLAlchemy persists business records and audit events in SQLite. The mock NPHIES client guarantees a complete offline demo.

## Trust boundaries
- No real NPHIES connection is claimed.
- Public dataset labels are not treated as Saudi adjudication ground truth.
- External LLM, STT and TTS calls are disabled by default for privacy.
- Coding compatibility rules are demonstrative and must be replaced by licensed, governed Saudi rule sets before clinical deployment.
