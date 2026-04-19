# Ringkasan Testing WBS Backend (FastAPI + Qdrant + Ollama)

Dokumen ini merangkum seluruh testing yang sudah dilakukan selama implementasi dan tuning pipeline RAG/AI decision.

## 1) Scope Testing
- Konektivitas layanan (`Ollama`, `Qdrant`).
- Validasi ingestion knowledge base ke vector DB.
- Retrieval sanity check (score dan ranking).
- End-to-end flow anon report -> AI decision -> status.
- Evaluasi skenario dengan dataset internal dan eksternal.

## 2) Hasil Konektivitas dan Integrasi
- **Ollama**: sukses (`/api/tags`, `/api/embed`, `/api/generate`).
  - Model terdeteksi: `embeddinggemma:latest`, `yinw1590/gemma4-e2b-text:latest`.
  - Dimensi embedding terukur: `768`.
- **Qdrant**:
  - Awal sempat gagal karena format URL `.env` salah.
  - Setelah perbaikan URL, koneksi sukses.

## 3) Hasil Ingestion KB
- Ingestion awal (single collection): berhasil.
- Setelah refactor split collection:
  - `indexed_total = 51`
  - `indexed_violation = 21`
  - `indexed_oos = 30`

## 4) Hasil Retrieval Sanity
- Uji contoh kategori resmi dari KB pelanggaran (7 query):
  - Top-1 kategori benar: `7/7 (100%)`.
- Uji paraphrase awal menunjukkan beberapa borderline miss (khusus konflik kepentingan), lalu dituning.

## 5) Hasil End-to-End (Internal Varied Cases)
- Dataset internal campuran: 12 kasus (S1/S2/S3).
- Setelah perbaikan pipeline/fallback:
  - S1: `3/3`
  - S2: `4/4`
  - S3: `5/5`
  - Total: `12/12 (100%)`

## 6) Hasil External Evaluation (Dataset Terpisah)
Sumber dataset: `eval/external_cases_v1.json` (21 kasus total; 7 S1, 7 S2, 7 S3).

### Riwayat Run (jujur, termasuk regressions)
1. **Run awal eksternal**
   - Overall: `95.24%`
   - S1: `85.71%`, S2: `100%`, S3: `100%`
   - Miss utama: kasus S1 fraud turun ke S2.

2. **Run setelah tuning agresif S1 (sempat regress)**
   - Overall: `90.48%`
   - S1: `100%`, S2: `71.43%`, S3: `100%`
   - Masalah: sebagian S2 terdorong jadi S1.

3. **Run berikutnya (penyeimbangan)**
   - Overall: `90.48%`
   - S1: `85.71%`, S2: `85.71%`, S3: `100%`

4. **Run berikutnya**
   - Overall: `95.24%`
   - S1: `85.71%`, S2: `100%`, S3: `100%`
   - Sisa miss: pelecehan (S1) masih jatuh ke S2.

5. **Run final (setelah perbaikan sinyal + consistency + fallback)**
   - Overall: `100%`
   - S1: `100%`, S2: `100%`, S3: `100%`
   - Detail hasil tersimpan di: `eval/external_eval_result.json`.

## 7) Bug dan Isu yang Ditemukan
- **Ticket collision** (`UNIQUE constraint failed: reports.ticket_id`) saat batch test cepat.
  - Perbaikan: format ticket ID diperkuat + retry insert.
- **Non-relevant case nyangkut `NEEDS_INFO`** (harusnya S3).
  - Perbaikan: consistency retry + fallback OOS jika tanpa legal reference.
- **Trade-off tuning S1 vs S2** sempat terjadi.
  - Perbaikan: ambiguity enforcement + strong evidence promotion + signal refinement.

## 8) Perubahan Teknis yang Berpengaruh pada Hasil
- Split collection Qdrant: `violation` vs `oos`.
- Retrieval ranking: vector score + keyword boost + category vote bonus.
- AI decision flow: rank -> AI decide -> consistency check -> correction retry -> fallback teknis.
- Penegakan legal reference untuk S1/S2.
- Rule penurunan ke S3 untuk konteks OOS tanpa pasal valid.

## 9) Artefak Testing
- External cases: `eval/external_cases_v1.json`
- Runner external eval: `eval/run_external_eval.py`
- Latest external result: `eval/external_eval_result.json`
- Monitoring plan: `monitoring_plan.md`

## 10) Kesimpulan
- Secara fungsional, pipeline sudah stabil untuk 3 skenario pada dataset test saat ini.
- Jalur OOS sekarang konsisten `AUTO_RESOLVED`.
- Jalur pelanggaran (S1/S2) sudah lebih konsisten terhadap keberadaan bukti dan rujukan pasal.
- Meski hasil terakhir 100% pada external suite saat ini, kualitas tetap perlu dijaga dengan evaluasi berkala agar tidak regress.
