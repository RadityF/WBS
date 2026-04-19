# Monitoring Plan - WBS AI Quality & Reliability

## Tujuan
Menjaga kualitas klasifikasi skenario (S1/S2/S3), ketepatan status kasus,
dan stabilitas layanan RAG/LLM agar tidak regress setelah perubahan model/prompt/KB.

## Baseline Saat Ini
- Sumber evaluasi: `eval/external_eval_result.json`
- Ringkasan baseline terbaru:
  - `total_cases=21`
  - `scenario_accuracy=1.0`
  - `scenario_status_accuracy=1.0`
  - `S1=1.0, S2=1.0, S3=1.0`

Catatan: baseline ini harus dianggap awal, bukan jaminan produksi jangka panjang.

## KPI Kualitas (Model)
- `scenario_accuracy_overall`
- `scenario_accuracy_s1`
- `scenario_accuracy_s2`
- `scenario_accuracy_s3`
- `scenario_status_accuracy`
- `pasal_presence_rate_s1s2` (berapa persen S1/S2 punya rujukan pasal valid)
- `needs_info_overuse_rate` (S2 berlebihan)
- `auto_resolved_false_positive_rate` (kasus relevan jatuh ke S3)

## KPI Operasional (Sistem)
- `submit_success_rate`
- `ticket_collision_rate`
- `qdrant_search_error_rate`
- `ollama_generate_error_rate`
- `llm_json_invalid_rate`
- `p95_submit_to_decision_ms`
- `p95_qdrant_search_ms`
- `p95_ollama_generate_ms`

## Event Logging Wajib
Setiap laporan simpan event terstruktur:
- `ticket_id`, `timestamp`
- `model_embed`, `model_llm`, `prompt_version`
- top retrieval hits (category, source_group, score)
- decision path (`normal`, `correction_retry`, `fallback_oos`, `fallback_needs_info`, `hard_stop`)
- AI output ringkas (`scenario`, `category`, `has_legal_reference`)

## Alert Rules
- `scenario_accuracy_s1 < 0.90` selama 2 run eval berturut-turut -> High alert
- `scenario_accuracy_s3 < 0.97` -> Critical alert
- `llm_json_invalid_rate > 0.05` harian -> Medium alert
- `qdrant_search_error_rate > 0.02` harian -> High alert
- `p95_submit_to_decision_ms > 15000` -> Medium alert

## Evaluasi Berkala

### Harian
- Jalankan smoke test 6-10 kasus (S1,S2,S3 seimbang).
- Cek service health (`/health`, Ollama tags, Qdrant collections).

### Mingguan
- Jalankan external eval:
  - `python3 eval/run_external_eval.py`
- Simpan hasil dengan timestamp ke folder history (disarankan):
  - `eval/history/external_eval_YYYYMMDD.json`
- Review semua mismatch secara manual.

### Bulanan
- Tambah 10-20 kasus baru ke external suite dari kasus nyata anonim.
- Re-kalibrasi threshold/boost jika drift.

## SOP Saat KPI Turun
1. Freeze perubahan prompt/model.
2. Ambil 20 mismatch teratas.
3. Klasifikasikan root cause:
   - retrieval miss
   - prompt reasoning miss
   - consistency/fallback policy miss
4. Patch kecil bertahap + re-run external eval.
5. Deploy hanya jika S1 naik dan S3 tidak turun.

## Anti-Bias Rules
- Dataset `external_cases_v1.json` tidak boleh diubah saat tuning aktif.
- Tuning hanya pakai dataset dev terpisah.
- Laporan KPI wajib menampilkan per kelas (S1/S2/S3), bukan rata-rata saja.

## Rencana Implementasi Monitoring Teknis
- Tahap 1 (cepat):
  - structured logs JSON ke file
  - script evaluasi + history snapshot
- Tahap 2:
  - kirim metrics ke Prometheus/Grafana (atau OpenTelemetry)
  - dashboard KPI kualitas + KPI latency
- Tahap 3:
  - alert otomatis ke Slack/Telegram/email

## Command Operasional
- External eval:
  - `python3 eval/run_external_eval.py`
- Quick syntax check:
  - `python3 -m compileall app`
