import json
from pathlib import Path
from daraz_affiliate_intake_validator import valid_affiliate_url

INPUT = Path("worker_reports/daraz_affiliate_intake_30.json")
OUTPUT = Path("worker_reports/daraz_affiliate_approval_gate_report.json")

def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    records = data.get("records", [])

    approved = []
    pending = []
    rejected = []

    for r in records:
        item_id = str(r.get("item_id") or "").strip()
        affiliate_url = str(r.get("affiliate_url") or "").strip()
        status = str(r.get("status") or "").strip()

        if not affiliate_url:
            pending.append(item_id)
            continue

        if not valid_affiliate_url(affiliate_url):
            rejected.append({
                "item_id": item_id,
                "reason": "INVALID_AFFILIATE_URL",
            })
            continue

        if status != "OFFICIAL_LINK_READY":
            pending.append(item_id)
            continue

        approved.append(item_id)

    report = {
        "worker": "daraz_affiliate_approval_gate",
        "mode": "safe_read_only",
        "input_records": len(records),
        "approved": len(approved),
        "pending": len(pending),
        "rejected": len(rejected),
        "production_write_allowed": False,
        "production_modified": False,
        "git_modified": False,
        "status": "PASS" if not rejected else "REVIEW",
        "approved_item_ids": approved,
        "pending_item_ids": pending,
        "rejected_records": rejected,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("INPUT RECORDS:", len(records))
    print("APPROVED:", len(approved))
    print("PENDING:", len(pending))
    print("REJECTED:", len(rejected))
    print("PRODUCTION WRITE ALLOWED:", False)
    print("PRODUCTION MODIFIED:", False)
    print("GIT MODIFIED:", False)
    print("STATUS:", report["status"])
    print("REPORT:", OUTPUT)

if __name__ == "__main__":
    main()
