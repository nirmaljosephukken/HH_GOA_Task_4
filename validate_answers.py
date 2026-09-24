"""
Validate the answer files against the README's answer format and the policy:
  * every required field present with the right type and enum values
  * every ID exists in the dataset (transactions, cards, customers, closed cases)
  * exposure == sum of affected amounts; legitimate => empty episode, 0 exposure, no SAR
  * sar.file agrees with FILE_REPORT in the final actions; routes match the policy table
  * final == initial when no evidence was requested

    python validate_answers.py            (exit code 1 if any problem)
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from agent.config import SETTINGS
from agent.policy import route

PATTERNS = {"card_testing", "card_not_present_fraud", "card_not_present_new_device", "out_of_region_use",
            "account_takeover", "undocumented", "none"}
ACTIONS = {"ALLOW_TRANSACTION", "DECLINE_TRANSACTION", "MONITOR_CARD", "MONITOR_CONNECTED_CARDS", "WARN_CUSTOMER",
           "VERIFY_WITH_CUSTOMER", "STEP_UP_AUTH", "BLOCK_CARD", "BLOCK_ALL_CARDS", "GENERATE_REPORT", "CREATE_CASE",
           "FILE_REPORT", "ESCALATE_TO_ANALYST", "CLOSE_NO_FRAUD"}


def main() -> int:
    t = pd.read_csv(SETTINGS.prepared_dir / "txn.csv.gz", usecols=["txn_id", "amount", "card_id", "customer_id",
                                                                     "device_profile"], dtype={"txn_id": str})
    amounts = dict(zip(t.txn_id, t.amount))
    cards, custs = set(t.card_id), set(t.customer_id)
    devices = set(t.device_profile.dropna())
    ccs = set(pd.read_csv(SETTINGS.prepared_dir / "closed_cases.csv", usecols=["case_id"]).case_id)
    pack = pd.read_csv(SETTINGS.prepared_dir / "case_pack.csv", dtype=str)
    problems = []
    for cid in pack.case_id:
        p = SETTINGS.cases_dir / f"{cid}.json"
        if not p.exists():
            problems.append(f"{cid}: missing answer file")
            continue
        a = json.loads(p.read_text())
        c = a["case"]
        err = lambda m: problems.append(f"{cid}: {m}")  # noqa: E731
        for k in ("case_id", "case", "evidence_requests", "next_best_actions", "sar", "stop_reason", "tool_calls",
                  "tokens", "latency_s"):
            if k not in a:
                err(f"missing {k}")
        if c["status"] not in ("open", "closed_fraud", "closed_legitimate", "escalated"):
            err("bad status")
        if c["verdict"] not in ("fraud", "legitimate", "uncertain"):
            err("bad verdict")
        if c["pattern"] not in PATTERNS:
            err("bad pattern")
        if c["pattern"] == "undocumented" and not c["pattern_description"]:
            err("undocumented without description")
        for x in c["affected_txn_ids"] + ([c["first_suspicious_txn_id"]] if c["first_suspicious_txn_id"] else []):
            if x not in amounts:
                err(f"unknown txn {x}")
        for k in c["connected_card_ids"]:
            if k not in cards:
                err(f"unknown card {k}")
        for d in c["connected_device_profiles"]:
            if d not in devices:
                err(f"unknown device profile {d!r}")
        for k in c["similar_prior_cases"]:
            if k not in ccs:
                err(f"unknown closed case {k}")
        exp = round(sum(abs(amounts[x]) for x in c["affected_txn_ids"] if x in amounts), 2)
        if abs(exp - c["exposure_usd"]) > 0.01:
            err(f"exposure {c['exposure_usd']} != sum {exp}")
        if c["verdict"] == "legitimate" and (c["affected_txn_ids"] or c["exposure_usd"] or a["sar"]["file"]):
            err("legitimate verdict with episode/exposure/SAR")
        for e in c["evidence"]:
            if set(e) != {"claim", "source", "ref", "entity_ids"} or e["source"] not in ("graph", "document", "customer", "external"):
                err("bad evidence item")
        nba = a["next_best_actions"]
        for stage in ("initial", "final"):
            for x in nba[stage]:
                if x["action"] not in ACTIONS:
                    err(f"unknown action {x['action']}")
                if x["route"] != route(x["action"], c["exposure_usd"] if x["action"] == "BLOCK_CARD" else 0):
                    err(f"route mismatch {x['action']} {x['route']}")
        if not a["evidence_requests"] and nba["initial"] != nba["final"]:
            err("final differs from initial without an evidence request")
        final_names = [x["action"] for x in nba["final"]]
        if a["sar"]["file"] != ("FILE_REPORT" in final_names):
            err("sar.file disagrees with FILE_REPORT")
        s = a["sar"]
        if s["file"]:
            if not s["narrative"] or not s["subjects"] or len(s["activity_dates"]) != 2:
                err("incomplete SAR")
            for sub in s["subjects"]:
                if sub not in cards and sub not in custs and sub not in devices:
                    err(f"unknown SAR subject {sub}")
        elif s["narrative"] or s["subjects"] or s["total_amount_usd"] or s["activity_dates"]:
            err("SAR fields must be empty when file is false")
        if not c["written_to_graph"]:
            err("not written to graph")
        for r in a["evidence_requests"]:
            if r["type"] not in ("customer_validation", "step_up_auth", "analyst_info"):
                err("bad evidence request type")
    for p in problems:
        print("PROBLEM", p)
    print(f"checked {len(pack)} cases: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
