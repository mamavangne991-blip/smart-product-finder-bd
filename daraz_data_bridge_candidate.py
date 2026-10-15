import json
from pathlib import Path
from datetime import datetime

SRC = Path("daraz_public_products.json")
OUT = Path("worker_reports/daraz_data_bridge_candidate.json")

REQUIRED = [
    "name", "price", "url", "category",
    "item_id", "seller_sku", "seller_id",
    "description", "image"
]

def clean(v):
    if v is None:
        return ""
    return str(v).strip()

if not SRC.exists():
    raise SystemExit("FAIL: daraz_public_products.json not found")

data = json.loads(SRC.read_text(encoding="utf-8"))

if not isinstance(data, list):
    raise SystemExit("FAIL: source is not a list")

valid = []
rejected = []
seen = set()

for i, p in enumerate(data, 1):
    if not isinstance(p, dict):
        rejected.append({"index": i, "reason": "not_object"})
        continue

    item_id = clean(p.get("item_id"))

    if not item_id:
        rejected.append({"index": i, "reason": "missing_item_id"})
        continue

    if item_id in seen:
        rejected.append({"index": i, "reason": "duplicate_item_id"})
        continue

    missing = [k for k in REQUIRED if not clean(p.get(k))]

    if missing:
        rejected.append({
            "index": i,
            "item_id": item_id,
            "reason": "missing_fields",
            "fields": missing
        })
        continue

    seen.add(item_id)

    valid.append({
        "name": clean(p.get("name")),
        "price": clean(p.get("price")),
        "currency": clean(p.get("currency")) or "BDT",
        "url": clean(p.get("url")),
        "category": clean(p.get("category")),
        "item_id": item_id,
        "seller_sku": clean(p.get("seller_sku")),
        "seller_id": clean(p.get("seller_id")),
        "brand": clean(p.get("brand")),
        "description": clean(p.get("description")),
        "image": clean(p.get("image")),
    })

OUT.parent.mkdir(parents=True, exist_ok=True)

report = {
    "created": datetime.now().isoformat(timespec="seconds"),
    "safe_mode": True,
    "production_modified": False,
    "source": str(SRC),
    "output": str(OUT),
    "source_records": len(data),
    "valid_records": len(valid),
    "rejected_records": len(rejected),
    "required_fields": REQUIRED,
    "valid_products": valid,
    "rejected": rejected,
    "decision": (
        "READY_FOR_BRIDGE_TEST"
        if valid and not rejected
        else "REVIEW_REQUIRED"
    )
}

OUT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("=" * 65)
print("DARAZ SAFE DATA BRIDGE — CANDIDATE TEST")
print("=" * 65)
print("SOURCE:", SRC)
print("SOURCE RECORDS:", len(data))
print("VALID:", len(valid))
print("REJECTED:", len(rejected))

for p in valid:
    print(
        "PASS |",
        p["item_id"],
        "|",
        p["name"][:70]
    )

for r in rejected:
    print("REJECT |", r)

print("\nDECISION:", report["decision"])
print("OUTPUT:", OUT)
print("\nPRODUCTION MODIFIED: NO")
print("PRODUCTS.JSON MODIFIED: NO")
print("CREDENTIALS USED: NO")
print("=" * 65)
