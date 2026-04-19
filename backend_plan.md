# Backend MVP Plan - Whistleblowing System (WBS)

## Goal
Bangun backend MVP berbasis FastAPI untuk pelapor anonim dengan alur:
1) submit laporan, 2) proses RAG (Qdrant + Ollama), 3) klasifikasi skenario 1/2/3,
4) kirim kasus ke admin hingga resolved.

## Fixed Decisions
- Framework API: FastAPI
- Vector DB: Qdrant
- Embedding model (Ollama): `embeddinggemma:latest`
- LLM model (Ollama): `yinw1590/gemma4-e2b-text:latest`
- Pelapor: anonim + `ticket_id` + PIN
- Scope: MVP only
- Role admin: single role (`admin`)

## MVP Scope
- [x] Pelapor anonim submit narasi + bukti opsional
- [x] Generate `ticket_id` + PIN (PIN disimpan hash)
- [x] RAG retrieval + LLM classification (scenario 1/2/3)
- [x] Follow-up interaktif untuk scenario 2 (max 3x)
- [x] Auto-resolve untuk scenario 3
- [x] Admin login + list/detail/update status kasus
- [x] Endpoint reindex Knowledge Base ke Qdrant

## Out of Scope (MVP)
- [x] Multi-role workflow kompleks (auditor/supervisor/legal)
- [x] Notifikasi omnichannel (WA/SMS/email production grade)
- [x] OCR forensics, deduplikasi lintas kasus, analytics lanjutan
- [x] Fine-tuning / active learning

## Technical Plan

### 1) Fondasi Project
- [x] Struktur project FastAPI modular (`reports`, `rag`, `admin`, `kb`)
- [x] Konfigurasi environment (`.env`)
- [x] SQLAlchemy models + DB init
- [x] Health endpoint

### 2) Anonymous Reporting
- [x] Endpoint submit laporan (`/v1/reports/submit`) multipart
- [x] Simpan attachment ke local storage
- [x] Endpoint status by `ticket_id + PIN`
- [x] Endpoint reply follow-up by `ticket_id + PIN`
- [x] Rate limiting sederhana anti brute force

### 3) RAG Pipeline
- [x] Ollama embedding client (`embeddinggemma:latest`)
- [x] Qdrant search `top_k=5`, `threshold=0.65`
- [x] Prompt assembly + guardrails
- [x] Ollama LLM JSON strict output
- [x] Pydantic validation + retry 1x
- [x] Mapping scenario -> status report

### 4) Knowledge Base Ingestion
- [x] Parse `Knowledge Base.xlsx` sheet `Pelanggaran`
- [x] Parse `Knowledge Base.xlsx` sheet `Out of Scope (Skenario 3)`
- [x] Upsert vectors + metadata ke Qdrant
- [x] Admin endpoint trigger reindex

### 5) Admin Module
- [x] Admin seed user
- [x] JWT login endpoint
- [x] List kasus + detail
- [x] Update status hingga resolved/archive

### 6) Observability & Safety (MVP)
- [x] Audit log status change
- [x] PII mask sederhana sebelum LLM
- [x] Error fallback saat timeout/JSON invalid

## Data Model (MVP)
- `admin_users`
- `reports`
- `report_messages`
- `report_attachments`
- `report_followup_questions`
- `ai_analysis_results`
- `case_status_logs`

## API Surface (MVP)

### Public (Anon)
- `POST /v1/reports/submit`
- `GET /v1/reports/{ticket_id}/status?pin=...`
- `POST /v1/reports/{ticket_id}/reply`

### Admin
- `POST /v1/admin/login`
- `GET /v1/admin/cases`
- `GET /v1/admin/cases/{ticket_id}`
- `POST /v1/admin/cases/{ticket_id}/status`
- `POST /v1/kb/reindex`

## Execution Notes
- Default DB untuk local dev: SQLite (bisa diganti Postgres via `DATABASE_URL`)
- Qdrant dan Ollama wajib running agar pipeline RAG aktif.
