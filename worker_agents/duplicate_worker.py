import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.json"
REPORT = ROOT / "worker_reports" / "duplicate_report.json"

def norm(value):
    return str(value or "").strip().lower()

def main():
    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))

    groups = defaultdict(list)

    for i, p in enumerate(data):
        item_id = norm(p.get("item_id"))
        seller_sku = norm(p.get("seller_sku"))
        url = norm(p.get("url"))

        if item_id:
            groups[f"item_id:{item_id}"].append(i)

        if seller_sku:
            groups[f"seller_sku:{seller_sku}"].append(i)

        if url:
            groups[f"url:{url}"].append(i)

    duplicate_groups = []

    for key, indexes in groups.items():
        if len(indexes) > 1:
            duplicate_groups.append({
                "key": key,
                "indexes": indexes,
                "products": [
                    {
                        "index": i + 1,
                        "name": data[i].get("name"),
                        "item_id": data[i].get("item_id"),
                        "seller_sku": data[i].get("seller_sku"),
                        "url": data[i].get("url"),
                    }
                    for i in indexes
                ],
            })

    report = {
        "worker": "Duplicate Worker V1",
        "timestamp": datetime.now().isoformat(),
        "total_products": len(data),
        "duplicate_groups": len(duplicate_groups),
        "duplicates_found": bool(duplicate_groups),
        "status": "PASS" if not duplicate_groups else "DUPLICATES_FOUND",
        "groups": duplicate_groups,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("DUPLICATE WORKER V1")
    print("=" * 60)
    print("TOTAL PRODUCTS:", len(data))
    print("DUPLICATE GROUPS:", len(duplicate_groups))

    if duplicate_groups:
        print("\nDUPLICATES:")
        for group in duplicate_groups:
            print("-", group["key"], "->", len(group["indexes"]), "records")
    else:
        print("DUPLICATES: NONE")

    print("REPORT:", REPORT)
    print("WORKER STATUS:", report["status"])

if __name__ == "__main__":
    main()
