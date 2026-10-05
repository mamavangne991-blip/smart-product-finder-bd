from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.json"
PUBLIC = ROOT / "daraz_public_products.json"
IMPORTER = ROOT / "daraz_public_import.py"
REPORT = ROOT / "worker_reports" / "product_discovery_report.json"

checks = []
issues = []

def check(name, passed, detail=""):
    checks.append({
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail
    })
    if not passed:
        issues.append(f"{name}: {detail}")

# File checks
check("products.json exists", PRODUCTS.exists())
check("daraz_public_products.json exists", PUBLIC.exists())
check("daraz_public_import.py exists", IMPORTER.exists())

products = []
public_products = []

if PRODUCTS.exists():
    try:
        products = json.loads(PRODUCTS.read_text(encoding="utf-8"))
        check("products.json valid JSON", isinstance(products, list))
    except Exception as exc:
        check("products.json valid JSON", False, str(exc))

if PUBLIC.exists():
    try:
        public_products = json.loads(PUBLIC.read_text(encoding="utf-8"))
        check("public Daraz data valid JSON", isinstance(public_products, list))
    except Exception as exc:
        check("public Daraz data valid JSON", False, str(exc))

# Product integrity
daraz_products = [
    p for p in products
    if "daraz.com.bd" in str(p.get("url", "")).lower()
]

check(
    "Daraz products contain item_id",
    all(p.get("item_id") for p in daraz_products),
    f"{sum(bool(p.get('item_id')) for p in daraz_products)}/{len(daraz_products)}"
)

check(
    "Daraz products contain product name",
    all(p.get("name") for p in daraz_products),
    f"{sum(bool(p.get('name')) for p in daraz_products)}/{len(daraz_products)}"
)

check(
    "Daraz products contain price",
    all(p.get("price") is not None for p in daraz_products),
    f"{sum(p.get('price') is not None for p in daraz_products)}/{len(daraz_products)}"
)

check(
    "Daraz products contain URL",
    all(p.get("url") for p in daraz_products),
    f"{sum(bool(p.get("url")) for p in daraz_products)}/{len(daraz_products)}"
)

# Duplicate item IDs
ids = [
    str(p.get("item_id"))
    for p in daraz_products
    if p.get("item_id") is not None
]

duplicates = sorted({
    x for x in ids
    if ids.count(x) > 1
})

check(
    "No duplicate Daraz item IDs",
    not duplicates,
    f"Duplicates: {duplicates}"
)

# Public importer safety audit
if IMPORTER.exists():
    importer_text = IMPORTER.read_text(encoding="utf-8")

    check(
        "Public importer has main guard",
        'if __name__ == "__main__":' in importer_text
    )

    check(
        "Public importer does not expose Daraz secret",
        "app_secret" not in importer_text.lower()
        and "client_secret" not in importer_text.lower()
    )

    check(
        "Public importer writes public data file",
        "daraz_public_products.json" in importer_text
    )

# Compilation
for path in [IMPORTER]:
    if path.exists():
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True
        )
        check(
            f"{path.name} compiles",
            result.returncode == 0,
            result.stderr.strip()
        )

status = "PASS" if not issues else "NEEDS_FIX"

report = {
    "worker": "product_discovery_worker",
    "mode": "audit_only",
    "status": status,
    "products_total": len(products),
    "daraz_products": len(daraz_products),
    "public_products": len(public_products),
    "checks": checks,
    "issues": issues
}

REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("========================================")
print(" PRODUCT DISCOVERY WORKER")
print("========================================")

for item in checks:
    print(f"{item['status']}: {item['check']}")
    if item["detail"]:
        print(f"       {item['detail']}")

print()
print(f"PRODUCTS: {len(products)}")
print(f"DARAZ PRODUCTS: {len(daraz_products)}")
print(f"PUBLIC IMPORT DATA: {len(public_products)}")
print(f"STATUS: {status}")
print(f"REPORT: {REPORT.relative_to(ROOT)}")
print("MODE: AUDIT ONLY / NO FILE MODIFICATION")
