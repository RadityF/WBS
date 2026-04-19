from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AiAnalysisResult, Report, ReportFollowupQuestion, ReportMessage
from app.schemas import AiOutput
from app.services.ollama_client import OllamaClient, parse_json_loose
from app.services.qdrant_service import QdrantService
from app.services.utils import generate_ticket_id, mask_pii


SYSTEM_PROMPT = """
Kamu adalah Integrity AI untuk Whistleblowing System.

ATURAN WAJIB:
1. Gunakan hanya konteks retrieval yang diberikan. Jangan mengarang pasal di luar konteks.
2. Putuskan skenario final (1,2,3) berdasarkan narasi user + konteks ranked.
3. Jika skenario 1 atau 2, isi pasal_utama dan pasal_kandidat dari konteks yang tersedia (uu/pasal wajib terisi).
4. Jika konteks lebih cocok out-of-scope atau tidak ada rujukan hukum valid, pilih skenario 3.
5. Jika skenario 3, pasal_utama boleh null dan referensi_hukum bisa kosong.
6. DILARANG pilih skenario 1/2 jika pasal_utama tidak punya `uu` atau `pasal`.
7. Output HARUS JSON valid sesuai schema. Tanpa teks tambahan.
8. Bahasa Indonesia, netral, profesional, tidak menghakimi.

KRITERIA SKENARIO:
- Skenario 1: minimal 3 dari 5 terpenuhi (pelaku, jenis pelanggaran, waktu, lokasi, bukti/saksi).
- Skenario 2: ada indikasi pelanggaran tetapi info belum lengkap.
- Skenario 3: non-pelanggaran etik/hukum (out-of-scope).

ATURAN PENGAMBILAN KEPUTUSAN:
- Jika indikator fakta menunjukkan >=3/5 terpenuhi dan ada bukti konkret, prioritaskan skenario 1,
  selama rujukan pasal tersedia dari konteks.
- Jangan terlalu konservatif mengubah ke skenario 2 jika unsur valid sudah cukup.
""".strip()


ROLE_HINTS = {
    "manajer",
    "manager",
    "staff",
    "staf",
    "supervisor",
    "direktur",
    "kepala",
    "atasan",
    "tim",
    "admin",
    "pegawai",
    "karyawan",
    "bernama",
    "inisial",
    "pak",
    "bu",
}

VIOLATION_ACTION_HINTS = {
    "menerima",
    "memberi",
    "transfer",
    "suap",
    "pelicin",
    "gratifikasi",
    "mark-up",
    "markup",
    "penggelapan",
    "fraud",
    "menyalin",
    "copy",
    "membocorkan",
    "mengakses",
    "menyentuh",
    "pesan",
    "seksual",
    "pelecehan",
    "menunjuk",
    "titipan",
    "menggunakan",
}

LOCATION_HINTS = {
    "lobby",
    "ruang",
    "server",
    "gudang",
    "kantor",
    "restoran",
    "hotel",
    "lantai",
    "meeting",
    "lokasi",
}

EVIDENCE_HINTS = {
    "bukti",
    "cctv",
    "saksi",
    "invoice",
    "chat",
    "rekaman",
    "log",
    "mutasi",
    "screenshot",
    "email",
    "dokumen",
    "lampir",
    "foto",
}

VIOLATION_SEVERITY_HINTS = {
    "pelecehan",
    "tidak senonoh",
    "sentuh",
    "menyentuh",
    "paksa",
    "seksual",
    "pesan",
    "suap",
    "gratifikasi",
    "mark-up",
    "markup",
    "penggelapan",
    "fraud",
    "database",
    "kebocoran",
}


def _has_legal_reference(ai: AiOutput) -> bool:
    if ai.pasal_utama and (ai.pasal_utama.uu or ai.pasal_utama.pasal):
        return True
    for ref in ai.referensi_hukum:
        if ref.uu or ref.pasal:
            return True
    return False


def _decision_consistency_error(ai: AiOutput, top_source_group: str) -> Optional[str]:
    has_legal = _has_legal_reference(ai)

    if ai.skenario in (1, 2) and not has_legal:
        return "Skenario 1/2 wajib memiliki rujukan pasal yang valid (uu/pasal)."

    if ai.skenario == 3 and has_legal:
        return "Skenario 3 tidak boleh menyertakan rujukan pasal sebagai keputusan utama."

    if top_source_group == "oos" and ai.skenario in (1, 2) and not has_legal:
        return "Top retrieval mengarah ke out-of-scope, tetapi keputusan belum konsisten."

    return None


def _build_correction_prompt(
    masked_user_text: str,
    contexts: list[dict],
    previous_raw_output: str,
    error_reason: str,
) -> str:
    base = _build_prompt(masked_user_text, contexts)
    return (
        f"{base}\n\n"
        f"OUTPUT SEBELUMNYA (TIDAK VALID):\n{previous_raw_output}\n\n"
        f"ALASAN TIDAK VALID: {error_reason}\n"
        "Perbaiki keputusan. WAJIB taati aturan berikut:\n"
        "- Jika skenario 1/2, isi pasal_utama atau referensi_hukum dengan uu/pasal yang valid dari konteks.\n"
        "- Jika tidak ada rujukan pasal valid dari konteks, pilih skenario 3.\n"
        "- Output hanya JSON valid, tanpa teks lain."
    )


def _fallback_oos(top_category: Optional[str]) -> AiOutput:
    redirect = top_category or "GA/HR/IT"
    return AiOutput(
        kategori=None,
        skenario=3,
        alasan="Fallback teknis: keputusan AI tidak konsisten, konteks dominan out-of-scope.",
        referensi_hukum=[],
        urgensi="LOW",
        summary=None,
        respons_pelapor=(
            "Laporan Anda kami kategorikan sebagai non-pelanggaran etik/hukum. "
            "Silakan gunakan kanal operasional yang sesuai (GA/HR/IT)."
        ),
        follow_up_questions=[],
        needs_human_review=False,
        needs_escalation=False,
        ticket_id=None,
        redirect_to=redirect,
    )


def _fallback_needs_info() -> AiOutput:
    return AiOutput(
        kategori=None,
        skenario=2,
        alasan="Fallback teknis: output AI tidak valid setelah retry.",
        referensi_hukum=[],
        urgensi="MEDIUM",
        summary=None,
        respons_pelapor="Kami membutuhkan klarifikasi tambahan untuk memproses laporan Anda.",
        follow_up_questions=[
            "Siapa pihak yang Anda laporkan (jabatan/inisial)?",
            "Kapan kejadian terjadi?",
            "Apa bukti atau saksi yang tersedia?",
        ],
        needs_human_review=True,
        needs_escalation=False,
        ticket_id=None,
    )


def _fallback_oos_from_needs_info(parsed: AiOutput, top_category: Optional[str]) -> AiOutput:
    redirect = top_category or parsed.kategori or "GA/HR/IT"
    return AiOutput(
        kategori=parsed.kategori,
        skenario=3,
        alasan="Keputusan dikoreksi ke skenario 3 karena tidak ada rujukan pasal valid.",
        referensi_hukum=[],
        pasal_utama=None,
        pasal_kandidat=[],
        urgensi="LOW",
        summary=parsed.summary,
        respons_pelapor=parsed.respons_pelapor,
        follow_up_questions=[],
        needs_human_review=False,
        needs_escalation=False,
        ticket_id=None,
        redirect_to=redirect,
    )


def _build_prompt(masked_user_text: str, contexts: list[dict]) -> str:
    context_blocks = []
    for i, item in enumerate(contexts, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[KONTEKS {i}]",
                    f"kategori: {item.get('kategori', '')}",
                    f"referensi: {item.get('uu_ref', '')}",
                    f"source_group: {item.get('source_group', '')}",
                    f"retrieval_score: {item.get('retrieval_score', '')}",
                    f"isi: {item.get('text', '')}",
                ]
            )
        )

    schema_hint = {
        "kategori": "string|null",
        "skenario": "1|2|3",
        "alasan": "string",
        "referensi_hukum": [{"uu": "string|null", "pasal": "string|null", "ayat": "string|null", "isi_singkat": "string|null"}],
        "pasal_utama": {
            "uu": "string|null",
            "pasal": "string|null",
            "ayat": "string|null",
            "alasan_relevansi": "string|null",
            "skor_relatif": "number|null",
        },
        "pasal_kandidat": [
            {
                "uu": "string|null",
                "pasal": "string|null",
                "ayat": "string|null",
                "alasan_relevansi": "string|null",
                "skor_relatif": "number|null",
            }
        ],
        "urgensi": "LOW|MEDIUM|HIGH|CRITICAL",
        "summary": "string|null",
        "respons_pelapor": "string",
        "follow_up_questions": ["string"],
        "needs_human_review": "bool",
        "needs_escalation": "bool",
        "ticket_id": "string|null",
        "redirect_to": "string|null",
    }

    signal_summary = _extract_case_signals(masked_user_text)
    signal_block = (
        "ANALISIS FAKTA OTOMATIS (SINYAL PENDUKUNG, BUKAN KEPUTUSAN FINAL):\n"
        f"- pelaku_teridentifikasi: {signal_summary['has_actor']}\n"
        f"- jenis_pelanggaran_terindikasi: {signal_summary['has_action']}\n"
        f"- waktu_tersebut: {signal_summary['has_time']}\n"
        f"- lokasi_tersebut: {signal_summary['has_location']}\n"
        f"- bukti_atau_saksi: {signal_summary['has_evidence']}\n"
        f"- score_5w1h: {signal_summary['score']}/5\n"
        f"- evidence_hits: {signal_summary['evidence_hits']}"
    )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{signal_block}\n\n"
        f"KONTEKS RANKED:\n{chr(10).join(context_blocks)}\n\n"
        f"LAPORAN USER:\n{masked_user_text}\n\n"
        f"Schema JSON: {json.dumps(schema_hint, ensure_ascii=False)}"
    )


def _extract_case_signals(user_text: str) -> dict:
    text = user_text.lower()

    has_actor = any(h in text for h in ROLE_HINTS)
    has_action = any(h in text for h in VIOLATION_ACTION_HINTS)
    has_location = any(h in text for h in LOCATION_HINTS)
    has_evidence = any(h in text for h in EVIDENCE_HINTS)

    month_pattern = r"\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b"
    time_pattern = r"\b(pukul|jam|kemarin|tadi|malam|siang|sore|tanggal)\b"
    has_time = bool(re.search(month_pattern, text) or re.search(time_pattern, text) or re.search(r"\b\d{1,2}[:.]\d{2}\b", text))

    evidence_hits = sum(1 for h in EVIDENCE_HINTS if h in text)
    severity_hits = sum(1 for h in VIOLATION_SEVERITY_HINTS if h in text)
    score = sum([1 if has_actor else 0, 1 if has_action else 0, 1 if has_time else 0, 1 if has_location else 0, 1 if has_evidence else 0])

    return {
        "has_actor": "YA" if has_actor else "TIDAK",
        "has_action": "YA" if has_action else "TIDAK",
        "has_time": "YA" if has_time else "TIDAK",
        "has_location": "YA" if has_location else "TIDAK",
        "has_evidence": "YA" if has_evidence else "TIDAK",
        "score": score,
        "evidence_hits": evidence_hits,
        "severity_hits": severity_hits,
        "bool_has_evidence": has_evidence,
    }


def _enforce_signal_consistency(parsed: AiOutput, user_text: str) -> AiOutput:
    signal = _extract_case_signals(user_text)
    score = int(signal["score"])
    has_evidence = bool(signal["bool_has_evidence"])
    severity_hits = int(signal["severity_hits"])
    text = user_text.lower()

    # Jika AI memilih skenario 1 tetapi sinyal fakta lemah, turunkan ke skenario 2.
    if parsed.skenario == 1 and (score < 3 or (not has_evidence and severity_hits < 2)):
        return AiOutput(
            kategori=parsed.kategori,
            skenario=2,
            alasan=(
                "Indikasi pelanggaran ada, namun detail fakta belum cukup kuat untuk validasi penuh "
                f"(score_5w1h={score}/5, bukti={'ada' if has_evidence else 'tidak ada'})."
            ),
            referensi_hukum=parsed.referensi_hukum,
            pasal_utama=parsed.pasal_utama,
            pasal_kandidat=parsed.pasal_kandidat,
            urgensi="MEDIUM" if parsed.urgensi in ("LOW", "MEDIUM") else parsed.urgensi,
            summary=parsed.summary,
            respons_pelapor=(
                "Kami menangkap indikasi pelanggaran, namun masih perlu detail tambahan agar kasus bisa diproses sebagai laporan valid."
            ),
            follow_up_questions=[
                "Siapa pihak yang terlibat (jabatan/inisial)?",
                "Kapan dan di mana kejadian terjadi?",
                "Bukti atau saksi apa yang dapat mendukung laporan ini?",
            ],
            needs_human_review=True,
            needs_escalation=parsed.needs_escalation,
            ticket_id=None,
            redirect_to=parsed.redirect_to,
        )

    return parsed


def _force_ambiguous_to_needs_info(parsed: AiOutput, user_text: str) -> AiOutput:
    text = user_text.lower()
    uncertainty_terms = {"sepertinya", "diduga", "kayaknya", "saya dengar", "katanya", "belum tahu", "belum punya bukti"}
    uncertainty_hit = any(term in text for term in uncertainty_terms)
    signal = _extract_case_signals(user_text)
    score = int(signal["score"])

    if parsed.skenario == 1 and uncertainty_hit and score <= 3:
        return AiOutput(
            kategori=parsed.kategori,
            skenario=2,
            alasan="Narasi masih ambigu dan memerlukan klarifikasi tambahan sebelum validasi penuh.",
            referensi_hukum=parsed.referensi_hukum,
            pasal_utama=parsed.pasal_utama,
            pasal_kandidat=parsed.pasal_kandidat,
            urgensi="MEDIUM" if parsed.urgensi in ("LOW", "MEDIUM") else parsed.urgensi,
            summary=parsed.summary,
            respons_pelapor="Laporan Anda terindikasi pelanggaran, namun masih ambigu. Mohon lengkapi detail inti kejadian.",
            follow_up_questions=[
                "Siapa pihak yang terlibat (jabatan/inisial)?",
                "Kapan dan di mana kejadian berlangsung?",
                "Bukti atau saksi apa yang dapat mendukung laporan ini?",
            ],
            needs_human_review=True,
            needs_escalation=parsed.needs_escalation,
            ticket_id=None,
            redirect_to=parsed.redirect_to,
        )

    return parsed


def _promote_strong_evidence_to_s1(parsed: AiOutput, user_text: str) -> AiOutput:
    if parsed.skenario != 2:
        return parsed

    if not _has_legal_reference(parsed):
        return parsed

    text = user_text.lower()
    signal = _extract_case_signals(user_text)
    score = int(signal["score"])
    evidence_hits = int(signal["evidence_hits"])

    strong_evidence_terms = {
        "bukti",
        "cctv",
        "saksi",
        "invoice",
        "rekaman",
        "log",
        "mutasi",
        "screenshot",
        "dokumen",
        "foto",
    }
    evidence_term_hit = any(term in text for term in strong_evidence_terms)

    harassment_terms = {"pelecehan", "tidak senonoh", "sentuh", "menyentuh", "paksa", "seksual"}
    harassment_hit = any(term in text for term in harassment_terms)

    if score >= 4 and (evidence_hits >= 1 or evidence_term_hit or harassment_hit):
        return AiOutput(
            kategori=parsed.kategori,
            skenario=1,
            alasan="Narasi mengandung unsur fakta kuat dan bukti pendukung; dipromosikan ke skenario 1.",
            referensi_hukum=parsed.referensi_hukum,
            pasal_utama=parsed.pasal_utama,
            pasal_kandidat=parsed.pasal_kandidat,
            urgensi=parsed.urgensi,
            summary=parsed.summary,
            respons_pelapor=(
                "Laporan Anda memenuhi kriteria awal valid dan akan diteruskan untuk proses investigasi."
            ),
            follow_up_questions=[],
            needs_human_review=parsed.needs_human_review,
            needs_escalation=parsed.needs_escalation,
            ticket_id=None,
            redirect_to=parsed.redirect_to,
        )

    return parsed


def _keyword_boost(query_text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0

    q = query_text.lower()
    tokens = set(re.findall(r"[a-zA-Z0-9]+", q))
    matches = 0
    for kw in keywords:
        k = str(kw).strip().lower()
        if not k:
            continue
        if " " in k:
            if k in q:
                matches += 1
        else:
            if k in tokens:
                matches += 1
    return min(matches * 0.02, 0.08)


def _rank_hits_with_boost(user_text: str, hits):
    ranked = []
    for hit in hits:
        keywords = hit.metadata.get("keywords") or []
        boost = _keyword_boost(user_text, keywords)
        adjusted = hit.score + boost
        ranked.append((adjusted, boost, hit))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked


def _category_vote_bonus(ranked_hits) -> dict[str, float]:
    counts = Counter()
    for adjusted, _boost, hit in ranked_hits[:5]:
        category = str(hit.metadata.get("kategori") or "")
        if not category:
            continue
        counts[category] += adjusted

    if not counts:
        return {}

    max_score = max(counts.values())
    bonuses: dict[str, float] = {}
    for category, score in counts.items():
        if score >= max_score * 0.85:
            bonuses[category] = 0.03
    return bonuses


def _validate_ai_output(raw: str) -> Optional[AiOutput]:
    try:
        obj = parse_json_loose(raw)
        if isinstance(obj, dict):
            skenario = obj.get("skenario")
            if isinstance(skenario, str) and skenario.strip().isdigit():
                obj["skenario"] = int(skenario.strip())

            urgensi = obj.get("urgensi")
            if isinstance(urgensi, str):
                obj["urgensi"] = urgensi.strip().upper()

            followups = obj.get("follow_up_questions")
            if followups is None:
                obj["follow_up_questions"] = []
            elif isinstance(followups, str):
                obj["follow_up_questions"] = [followups]

            refs = obj.get("referensi_hukum")
            if refs is None:
                obj["referensi_hukum"] = []
            elif isinstance(refs, dict):
                obj["referensi_hukum"] = [refs]

            pasal_utama = obj.get("pasal_utama")
            if pasal_utama is not None and not isinstance(pasal_utama, dict):
                obj["pasal_utama"] = None

            pasal_kandidat = obj.get("pasal_kandidat")
            if pasal_kandidat is None:
                obj["pasal_kandidat"] = []
            elif isinstance(pasal_kandidat, dict):
                obj["pasal_kandidat"] = [pasal_kandidat]

        return AiOutput.model_validate(obj)
    except Exception:
        return None


def analyze_report(db: Session, report: Report, user_text: str) -> AiOutput:
    ollama = OllamaClient()
    qdrant = QdrantService()

    masked = mask_pii(user_text)
    query_vector = ollama.embed(masked)

    violation_hits = qdrant.search(query_vector, settings.rag_top_k, settings.qdrant_collection_violation)
    oos_hits = qdrant.search(query_vector, settings.rag_top_k, settings.qdrant_collection_oos)

    ranked_violation = _rank_hits_with_boost(masked, violation_hits)
    ranked_oos = _rank_hits_with_boost(masked, oos_hits)

    vote_bonus = _category_vote_bonus(ranked_violation)
    if vote_bonus:
        adjusted_violation = []
        for adjusted, boost, hit in ranked_violation:
            category = str(hit.metadata.get("kategori") or "")
            cat_bonus = vote_bonus.get(category, 0.0)
            adjusted_violation.append((adjusted + cat_bonus, boost + cat_bonus, hit))
        ranked_violation = sorted(adjusted_violation, key=lambda x: x[0], reverse=True)

    ranked_all = sorted(ranked_violation + ranked_oos, key=lambda x: x[0], reverse=True)
    valid_hits = [x for x in ranked_all if x[0] >= settings.rag_min_score]

    # Hard stop only: retrieval kosong total / tidak ada kandidat layak.
    if not valid_hits:
        ai = AiOutput(
            kategori=None,
            skenario=3,
            alasan="Hard stop: retrieval tidak menemukan konteks yang layak.",
            referensi_hukum=[],
            urgensi="LOW",
            summary=None,
            respons_pelapor=(
                "Laporan Anda belum cukup terhubung ke referensi pelanggaran. "
                "Silakan tambahkan detail jika ini pelanggaran etik/hukum."
            ),
            follow_up_questions=[],
            needs_human_review=False,
            needs_escalation=False,
            ticket_id=None,
            redirect_to="GA/HR/IT",
        )
        _persist_ai_result(db, report, ai, raw_output=json.dumps(ai.model_dump(), ensure_ascii=False))
        _apply_ai_to_report(db, report, ai)
        return ai

    top_source_group = str(valid_hits[0][2].metadata.get("source_group") or "")
    top_category = str(valid_hits[0][2].metadata.get("kategori") or "")

    contexts = []
    for adjusted, boost, hit in valid_hits[: settings.rag_top_k]:
        contexts.append(
            {
                "text": hit.text,
                **hit.metadata,
                "retrieval_score": round(adjusted, 4),
                "retrieval_boost": round(boost, 4),
            }
        )

    prompt = _build_prompt(masked, contexts)
    raw = ollama.generate_json(prompt)
    parsed = _validate_ai_output(raw)
    consistency_error = None
    if parsed is None:
        consistency_error = "Output JSON tidak valid."
    else:
        consistency_error = _decision_consistency_error(parsed, top_source_group)

    if consistency_error is not None:
        correction_prompt = _build_correction_prompt(masked, contexts, raw, consistency_error)
        raw_retry = ollama.generate_json(correction_prompt)
        parsed_retry = _validate_ai_output(raw_retry)

        retry_error = None
        if parsed_retry is None:
            retry_error = "Output JSON tetap tidak valid setelah koreksi."
        else:
            retry_error = _decision_consistency_error(parsed_retry, top_source_group)

        if retry_error is None and parsed_retry is not None:
            parsed = parsed_retry
            raw = raw_retry
        else:
            if top_source_group == "oos":
                parsed = _fallback_oos(top_category)
            else:
                parsed = _fallback_needs_info()
            raw = json.dumps(parsed.model_dump(), ensure_ascii=False)

    # Jika LLM tetap memberi skenario 1/2 tanpa pasal valid untuk konteks OOS,
    # turunkan ke scenario 3 agar tidak macet di NEEDS_INFO.
    if top_source_group == "oos":
        has_legal = _has_legal_reference(parsed)
        if parsed.skenario in (1, 2) and not has_legal:
            parsed = _fallback_oos_from_needs_info(parsed, top_category)
            raw = json.dumps(parsed.model_dump(), ensure_ascii=False)

    parsed = _enforce_signal_consistency(parsed, masked)
    parsed = _force_ambiguous_to_needs_info(parsed, masked)
    parsed = _promote_strong_evidence_to_s1(parsed, masked)
    raw = json.dumps(parsed.model_dump(), ensure_ascii=False)

    _persist_ai_result(db, report, parsed, raw_output=raw)
    _apply_ai_to_report(db, report, parsed)
    return parsed


def _persist_ai_result(db: Session, report: Report, ai: AiOutput, raw_output: str) -> None:
    db.add(
        AiAnalysisResult(
            report_id=report.id,
            llm_model=settings.ollama_llm_model,
            embed_model=settings.ollama_embed_model,
            raw_output=raw_output,
        )
    )
    db.flush()

    if ai.follow_up_questions:
        db.query(ReportFollowupQuestion).filter(ReportFollowupQuestion.report_id == report.id).delete()
        for q in ai.follow_up_questions[:3]:
            db.add(ReportFollowupQuestion(report_id=report.id, question=q, answered=False))


def _apply_ai_to_report(db: Session, report: Report, ai: AiOutput) -> None:
    report.category = ai.kategori
    report.scenario = ai.skenario
    report.urgency = ai.urgensi
    report.summary = ai.summary
    report.reason = ai.alasan
    report.latest_response_to_reporter = ai.respons_pelapor

    if ai.skenario == 1:
        report.status = "AI_VALIDATED"
        if not report.ticket_id:
            report.ticket_id = generate_ticket_id()
    elif ai.skenario == 2:
        report.status = "NEEDS_INFO"
    else:
        report.status = "AUTO_RESOLVED"

    db.add(
        ReportMessage(
            report_id=report.id,
            sender_type="system",
            message_type="ai_response",
            content=ai.respons_pelapor,
        )
    )
    db.flush()


def can_access_with_pin(report: Report) -> Tuple[bool, Optional[str]]:
    if report.pin_locked_until and report.pin_locked_until > datetime.utcnow():
        return False, "PIN terkunci sementara, coba lagi nanti"
    return True, None


def lock_pin_if_needed(report: Report) -> None:
    if report.pin_failed_attempts >= settings.report_pin_max_attempts:
        report.pin_locked_until = datetime.utcnow() + timedelta(minutes=settings.report_pin_lock_minutes)
