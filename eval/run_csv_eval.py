from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import app


VIOLATION_CSV = ROOT / "plan" / "Skenario Testing - Pelanggaran.csv"
OOS_CSV = ROOT / "plan" / "Skenario Testing - Out of Scope.csv"
OUTPUT_PATH = ROOT / "eval" / "csv_eval_result.json"


def normalize_status(text: str) -> str:
    t = (text or "").strip().lower()
    if t == "valid":
        return "AI_VALIDATED"
    if t == "need more info":
        return "NEEDS_INFO"
    if t == "invalid":
        return "AUTO_RESOLVED"
    return ""


def expected_scenario_from_status(status: str) -> int | None:
    if status == "AI_VALIDATED":
        return 1
    if status == "NEEDS_INFO":
        return 2
    if status == "AUTO_RESOLVED":
        return 3
    return None


def parse_violation_cases() -> list[dict]:
    rows = []
    last_meta = {"no": "", "kategori": "", "expected_status": "", "expected_kategori": "", "ref": "", "expected_result": ""}

    with open(VIOLATION_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            no = (r.get("No") or "").strip()
            kategori = (r.get("Kategori") or "").strip()
            prompt = (r.get("Input Prompt") or "").strip()
            exp_status_raw = (r.get("Expected Status (Skenario)") or "").strip()
            exp_kategori = (r.get("Expected Kategori") or "").strip()
            ref = (r.get("Referensi Pasal") or "").strip()
            expected_result = (r.get("Expected Result") or "").strip()

            if no:
                last_meta = {
                    "no": no,
                    "kategori": kategori,
                    "expected_status": exp_status_raw,
                    "expected_kategori": exp_kategori,
                    "ref": ref,
                    "expected_result": expected_result,
                }

            if not prompt:
                continue

            status = normalize_status(last_meta["expected_status"])
            scenario = expected_scenario_from_status(status)

            rows.append(
                {
                    "suite": "violation",
                    "case_id": f"V-{last_meta['no']}-{len(rows)+1}",
                    "group_no": last_meta["no"],
                    "group_label": last_meta["kategori"],
                    "text": prompt,
                    "expected_status": status,
                    "expected_scenario": scenario,
                    "expected_category": (last_meta["expected_kategori"] if last_meta["expected_kategori"] != "N/A" else ""),
                    "expected_reference": (last_meta["ref"] if last_meta["ref"] != "N/A" else ""),
                    "expected_result": last_meta["expected_result"],
                }
            )
    return rows


def parse_oos_cases() -> list[dict]:
    rows = []
    last_meta = {"no": "", "kategori": "", "expected_result": ""}

    with open(OOS_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            no = (r.get("No") or "").strip()
            kategori = (r.get("Kategori") or "").strip()
            prompt = (r.get("Input Prompt (Skenario)") or "").strip()
            expected_ai_result = (r.get("Expected AI Result") or "").strip()

            if no:
                last_meta = {"no": no, "kategori": kategori, "expected_result": expected_ai_result}

            if not prompt:
                continue

            rows.append(
                {
                    "suite": "oos",
                    "case_id": f"O-{last_meta['no']}-{len(rows)+1}",
                    "group_no": last_meta["no"],
                    "group_label": last_meta["kategori"],
                    "text": prompt,
                    "expected_status": "AUTO_RESOLVED",
                    "expected_scenario": 3,
                    "expected_category": "",
                    "expected_reference": "",
                    "expected_result": last_meta["expected_result"],
                }
            )
    return rows


def contains_reference(message: str, ref_text: str) -> bool:
    if not ref_text:
        return True
    msg = (message or "").lower()
    ref = ref_text.lower()
    # check minimal tokens from reference
    tokens = [tok for tok in ref.replace("/", " ").replace(".", " ").split() if len(tok) >= 3]
    if not tokens:
        return True
    hit = sum(1 for tok in tokens if tok in msg)
    return hit >= 1


def category_match(expected_category: str, got_category: str) -> bool:
    if not expected_category:
        return True
    return expected_category.lower() in (got_category or "").lower()


def main() -> None:
    cases = parse_violation_cases() + parse_oos_cases()
    client = TestClient(app)

    result_rows = []
    by_suite = defaultdict(lambda: {"n": 0, "scenario_ok": 0, "status_ok": 0, "category_ok": 0, "reference_hint_ok": 0, "both_ok": 0})

    for case in cases:
        submit = client.post("/v1/reports/submit", data={"narrative": case["text"]})
        submit_json = submit.json()
        ticket_id = submit_json["ticket_id"]
        pin = submit_json["pin"]

        status_resp = client.get(f"/v1/reports/{ticket_id}/status", params={"pin": pin})
        detail = status_resp.json()

        got_scenario = detail.get("scenario")
        got_status = detail.get("status")
        got_category = detail.get("category")
        got_message = detail.get("response_to_reporter") or ""

        scenario_ok = got_scenario == case["expected_scenario"]
        status_ok = got_status == case["expected_status"]
        cat_ok = category_match(case["expected_category"], got_category)
        ref_ok = contains_reference(got_message, case["expected_reference"])
        both_ok = scenario_ok and status_ok

        bucket = by_suite[case["suite"]]
        bucket["n"] += 1
        bucket["scenario_ok"] += 1 if scenario_ok else 0
        bucket["status_ok"] += 1 if status_ok else 0
        bucket["category_ok"] += 1 if cat_ok else 0
        bucket["reference_hint_ok"] += 1 if ref_ok else 0
        bucket["both_ok"] += 1 if both_ok else 0

        result_rows.append(
            {
                "case_id": case["case_id"],
                "suite": case["suite"],
                "group_no": case["group_no"],
                "group_label": case["group_label"],
                "expected_scenario": case["expected_scenario"],
                "expected_status": case["expected_status"],
                "expected_category": case["expected_category"],
                "expected_reference": case["expected_reference"],
                "got_scenario": got_scenario,
                "got_status": got_status,
                "got_category": got_category,
                "scenario_ok": scenario_ok,
                "status_ok": status_ok,
                "category_ok": cat_ok,
                "reference_hint_ok": ref_ok,
                "both_ok": both_ok,
                "ticket_id": ticket_id,
                "response_excerpt": got_message[:220],
            }
        )

    total = len(result_rows)
    both_ok_total = sum(1 for row in result_rows if row["both_ok"])
    scenario_ok_total = sum(1 for row in result_rows if row["scenario_ok"])

    summary = {
        "total_cases": total,
        "scenario_accuracy": round(scenario_ok_total / total, 4) if total else 0.0,
        "scenario_status_accuracy": round(both_ok_total / total, 4) if total else 0.0,
        "by_suite": {},
    }

    for suite, stats in by_suite.items():
        n = stats["n"]
        summary["by_suite"][suite] = {
            "n": n,
            "scenario_accuracy": round(stats["scenario_ok"] / n, 4) if n else 0.0,
            "status_accuracy": round(stats["status_ok"] / n, 4) if n else 0.0,
            "category_accuracy": round(stats["category_ok"] / n, 4) if n else 0.0,
            "reference_hint_rate": round(stats["reference_hint_ok"] / n, 4) if n else 0.0,
            "scenario_status_accuracy": round(stats["both_ok"] / n, 4) if n else 0.0,
        }

    report = {"summary": summary, "results": result_rows}
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("== CSV Eval Summary ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nSaved detail: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
