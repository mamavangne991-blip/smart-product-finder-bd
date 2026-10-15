import json
from pathlib import Path
from urllib.parse import urlparse

INPUT = Path("worker_reports/daraz_affiliate_intake_30.json")
OUTPUT = Path("worker_reports/daraz_affiliate_intake_validation_report.json")

ALLOWED_HOSTS = {
    "s.daraz.com.bd",
    "daraz.com.bd",
    "www.daraz.com.bd",
}

def valid_affiliate_url(url):
    url = str(url or "").strip()
    if not url:
        return False

    p = urlparse(url)

    return (
        p.scheme == "https"
        and p.netloc.lower() in ALLOWED_HOSTS
        and bool(p.path.strip("/"))
    )

def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    records = data.get("records", [])

    valid = []
    pending = []
    invalid = []

    for record in records:
        item_id = str(record.get("item_id") or "").strip()
        affiliate_url = str(record.get("affiliate_url") or "").strip()

        if not affiliate_url:
            pending.append(item_id)
            continue

        if valid_affiliate_url(affiliate_url):
            valid.append(item_id)
        else:
            invalid.append({
                "item_id": item_id,
                "affiliate_url": affiliate_url,
            })

    report = {
        "worker": "daraz_affiliate_intake_validator",
        "mode": "safe_read_only",
        "input_records": len(records),
        "valid_official_links": len(valid),
        "pending_official_links": len(pending),
        "invalid_links": len(invalid),
        "affiliate_links_generated": 0,
        "production_modified": False,
        "git_modified": False,
        "status": "PASS" if not invalid else "REVIEW",
        "valid_item_ids": valid,
        "pending_item_ids": pending,
        "invalid_records": invalid,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("INPUT RECORDS:", len(records))
    print("VALID OFFICIAL LINKS:", len(valid))
    print("PENDING OFFICIAL LINKS:", len(pending))
    print("INVALID LINKS:", len(invalid))
    print("AFFILIATE LINKS GENERATED:", 0)
    print("STATUS:", report["status"])
    print("PRODUCTION MODIFIED:", False)
    print("GIT MODIFIED:", False)
    print("REPORT:", OUTPUT)

if __name__ == "__main__":
    main()
