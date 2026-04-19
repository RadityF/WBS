# WBS Frontend MVP (Vue 3)

Frontend ini mengikuti `backend_plan.md` untuk 2 area:
- pelapor anonim (`/report/*`)
- admin (`/admin/*`)

## Fitur yang diimplementasikan
- Submit laporan anonim + attachment (`POST /v1/reports/submit`)
- Tampilkan `ticket_id` + PIN setelah submit
- Cek status laporan (`GET /v1/reports/{ticket_id}/status?pin=...`)
- Reply follow-up untuk status `NEEDS_INFO` (`POST /v1/reports/{ticket_id}/reply`)
- Admin login JWT (`POST /v1/admin/login`)
- Admin list & detail kasus (`GET /v1/admin/cases`, `GET /v1/admin/cases/{ticket_id}`)
- Admin update status (`POST /v1/admin/cases/{ticket_id}/status`)
- Admin trigger reindex KB (`POST /v1/kb/reindex`)

## Setup lokal
1. Pastikan Node.js 18+ terpasang.
2. Install dependency:
   - `npm install`
3. Copy env:
   - `cp .env.example .env`
4. Jalankan dev server:
   - `npm run dev`

Jika backend berjalan di host berbeda, set `VITE_API_BASE_URL`.
Jika kosong, frontend pakai proxy Vite ke `VITE_PROXY_TARGET` (default `http://localhost:8000`).

## Route utama
- Public: `/report/new`, `/report/success`, `/report/status`, `/report/:ticketId`
- Admin: `/admin/login`, `/admin/cases`, `/admin/cases/:ticketId`, `/admin/kb`
