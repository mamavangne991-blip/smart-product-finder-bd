import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.json"
REPORT = ROOT / "worker_reports" / "evidence_report.json"

FIELDS = [
    "name",
    "description",
    "image",
    "url",
    "category",
    "price",
    "item_id",
    "seller_sku",
    "seller_id",
]

def has_value(value):
    return value is not None and str(value).strip() != ""

def audit_product(product):
    evidence = {field: has_value(product.get(field)) for field in FIELDS}
    present = sum(evidence.values())
    missing = [field for field, ok in evidence.items() if not ok]

    return {
        "name": product.get("name"),
        "source": product.get("source"),
        "item_id": product.get("item_id"),
        "evidence_fields": present,
        "evidence_total": len(FIELDS),
        "evidence_score": round(present / len(FIELDS) * 100, 2),
        "missing_fields": missing,
        "status": "PASS" if not missing else "INCOMPLETE",
        "evidence": evidence,
    }

def main():
    if not PRODUCTS.exists():
        print("ERROR: products.json not found")
        return

    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))

    results = [audit_product(p) for p in data]

    report = {
        "worker": "Evidence Worker V1",
        "timestamp": datetime.now().isoformat(),
        "total_products": len(data),
        "pass": sum(r["status"] == "PASS" for r in results),
        "incomplete": sum(r["status"] == "INCOMPLETE" for r in results),
        "results": results,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("EVIDENCE WORKER V1")
    print("=" * 60)
    print("TOTAL:", report["total_products"])
    print("PASS:", report["pass"])
    print("INCOMPLETE:", report["incomplete"])
    print("REPORT:", REPORT)
    print("WORKER STATUS:", "PASS" if report["total_products"] else "NO DATA")

if __name__ == "__main__":
    main()
