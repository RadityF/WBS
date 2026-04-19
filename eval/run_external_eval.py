from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import app


CASES_PATH = ROOT / "eval" / "external_cases_v1.json"
OUTPUT_PATH = ROOT / "eval" / "external_eval_result.json"


def expected_status(scenario: int) -> str:
    if scenario == 1:
        return "AI_VALIDATED"
    if scenario == 2:
        return "NEEDS_INFO"
    return "AUTO_RESOLVED"


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    client = TestClient(app)

    result_rows = []
    by_expected = defaultdict(lambda: {"n": 0, "scenario_ok": 0, "status_ok": 0, "both_ok": 0})

    for case in cases:
        cid = case["id"]
        text = case["text"]
        exp_scenario = int(case["expected_scenario"])
        exp_status = expected_status(exp_scenario)

        submit = client.post("/v1/reports/submit", data={"narrative": text})
        submit_json = submit.json()
        ticket_id = submit_json["ticket_id"]
        pin = submit_json["pin"]

        status_resp = client.get(f"/v1/reports/{ticket_id}/status", params={"pin": pin})
        detail = status_resp.json()

        got_scenario = detail.get("scenario")
        got_status = detail.get("status")
        got_category = detail.get("category")
        got_message = detail.get("response_to_reporter")

        scenario_ok = got_scenario == exp_scenario
        status_ok = got_status == exp_status
        both_ok = scenario_ok and status_ok

        bucket = by_expected[exp_scenario]
        bucket["n"] += 1
        bucket["scenario_ok"] += 1 if scenario_ok else 0
        bucket["status_ok"] += 1 if status_ok else 0
        bucket["both_ok"] += 1 if both_ok else 0

        result_rows.append(
            {
                "id": cid,
                "expected_scenario": exp_scenario,
                "expected_status": exp_status,
                "got_scenario": got_scenario,
                "got_status": got_status,
                "got_category": got_category,
                "scenario_ok": scenario_ok,
                "status_ok": status_ok,
                "both_ok": both_ok,
                "ticket_id": ticket_id,
                "response_excerpt": (got_message or "")[:180],
            }
        )

    total = len(result_rows)
    both_ok_total = sum(1 for row in result_rows if row["both_ok"])
    scenario_ok_total = sum(1 for row in result_rows if row["scenario_ok"])

    summary = {
        "total_cases": total,
        "scenario_accuracy": round(scenario_ok_total / total, 4) if total else 0.0,
        "scenario_status_accuracy": round(both_ok_total / total, 4) if total else 0.0,
        "by_expected": {},
    }

    for exp, stats in by_expected.items():
        n = stats["n"]
        summary["by_expected"][str(exp)] = {
            "n": n,
            "scenario_accuracy": round(stats["scenario_ok"] / n, 4) if n else 0.0,
            "status_accuracy": round(stats["status_ok"] / n, 4) if n else 0.0,
            "scenario_status_accuracy": round(stats["both_ok"] / n, 4) if n else 0.0,
        }

    report = {"summary": summary, "results": result_rows}
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("== External Eval Summary ==")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nSaved detail: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
