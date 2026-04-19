# Frontend MVP Plan - Whistleblowing System (WBS)

## Goal
Bangun frontend MVP berbasis Vue.js untuk 2 area utama:
1) pelapor anonim submit laporan dan cek status,
2) admin mengelola kasus sampai resolved,
sepenuhnya selaras dengan backend plan FastAPI yang sudah disepakati.

## Fixed Decisions
- Framework: Vue 3 + Vite
- Routing: Vue Router
- State management: Pinia
- HTTP client: Axios
- Auth admin: JWT dari backend
- Pelapor: anonim via `ticket_id` + PIN
- Scope: MVP only

## MVP Scope
- [ ] Pelapor anonim submit narasi + bukti opsional (multipart)
- [ ] Tampilkan `ticket_id` + PIN pada halaman sukses submit
- [ ] Cek status laporan by `ticket_id + PIN`
- [ ] Balas follow-up untuk skenario 2 (maksimal mengikuti backend)
- [ ] Admin login
- [ ] Admin list kasus + filter/search dasar
- [ ] Admin detail kasus
- [ ] Admin update status kasus hingga resolved/archive
- [ ] Admin trigger reindex Knowledge Base

## Out of Scope (MVP)
- [ ] Multi-role admin kompleks (auditor/supervisor/legal)
- [ ] Dashboard analytics lanjutan
- [ ] Notification center production-grade
- [ ] Realtime websocket updates
- [ ] Advanced file preview/OCR

## Technical Plan

### 1) Fondasi Project
- [ ] Inisialisasi project `frontend` dengan Vue 3 + Vite
- [ ] Setup struktur folder modular (`public-report`, `admin`, `shared`)
- [ ] Setup environment (`VITE_API_BASE_URL`)
- [ ] Konfigurasi router + route guard admin
- [ ] Konfigurasi Axios instance + interceptor JWT

### 2) Public Module - Anonymous Reporting
- [ ] Halaman submit laporan (`/report/new`)
- [ ] Form narasi + upload attachment opsional
- [ ] Integrasi `POST /v1/reports/submit`
- [ ] Halaman sukses submit (`/report/success`) untuk tampilkan `ticket_id` + PIN

### 3) Public Module - Status & Follow-up
- [ ] Halaman cek status (`/report/status`) input `ticket_id` + PIN
- [ ] Integrasi `GET /v1/reports/{ticket_id}/status?pin=...`
- [ ] Halaman detail status laporan (`/report/:ticketId`)
- [ ] Form reply follow-up (`POST /v1/reports/{ticket_id}/reply`)
- [ ] Validasi dan handling error untuk PIN salah/ticket tidak ditemukan

### 4) Admin Module
- [ ] Halaman login admin (`/admin/login`)
- [ ] Integrasi `POST /v1/admin/login`
- [ ] Halaman list kasus (`/admin/cases`) dari `GET /v1/admin/cases`
- [ ] Halaman detail kasus (`/admin/cases/:ticketId`) dari `GET /v1/admin/cases/{ticket_id}`
- [ ] Aksi update status (`POST /v1/admin/cases/{ticket_id}/status`)
- [ ] Halaman utilitas KB (`/admin/kb`) untuk trigger `POST /v1/kb/reindex`

### 5) State Management & Data Contract
- [ ] `adminAuthStore` untuk login/logout/token
- [ ] `adminCaseStore` untuk list/detail/update status
- [ ] `publicReportStore` untuk submit/status/reply
- [ ] Sinkronisasi enum status/scenario dengan contract backend

### 6) UX, Safety, dan Error Handling (MVP)
- [ ] Loading/skeleton di halaman kritikal
- [ ] Error state standar (401, 404, timeout, 422)
- [ ] Session handling pelapor tanpa menyimpan PIN permanen
- [ ] Route guard + auto-redirect saat token admin expired

### 7) Testing & QA
- [ ] Unit test komponen form utama (submit laporan, login, cek status)
- [ ] Integration test flow pelapor: submit -> success -> cek status
- [ ] E2E smoke test admin: login -> list -> detail -> update status
- [ ] UAT skenario backend: scenario 1, 2 (follow-up), 3 (auto-resolved)

## Route Map (MVP)

### Public
- `/report/new`
- `/report/success`
- `/report/status`
- `/report/:ticketId`

### Admin
- `/admin/login`
- `/admin/cases`
- `/admin/cases/:ticketId`
- `/admin/kb`

## API Mapping (MVP)

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
- Target delivery MVP: 2 sprint
- Sprint 1 fokus modul pelapor + pondasi admin
- Sprint 2 fokus detail admin, update status, reindex KB, hardening error handling
- Validasi akhir wajib terhadap backend environment aktif (FastAPI, Qdrant, Ollama)
