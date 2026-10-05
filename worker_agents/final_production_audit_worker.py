import json
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "worker_reports"
REPORT_DIR.mkdir(exist_ok=True)

PRODUCTS = ROOT / "products.json"
RECS = ROOT / "product_recommendations.json"
PUBLIC = ROOT / "daraz_public_products.json"
WEB = ROOT / "web_app_v6.py"
IMPORTER = ROOT / "daraz_public_import.py"

report = {
    "worker": "final_production_audit_worker",
    "timestamp": datetime.now().isoformat(),
    "mode": "READ_ONLY / NO FILE MODIFICATION / NO GIT PUSH / NO FILE DELETION",
    "checks": [],
}

def check(name, passed, detail=""):
    report["checks"].append({
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
    })
    print(("PASS: " if passed else "FAIL: ") + name)
    if detail:
        print("       " + detail)

print("=" * 55)
print("SMART PRODUCT FINDER BD")
print("FINAL PRODUCTION AUDIT WORKER")
print("=" * 55)

# ---------------------------------------------------------
# File existence
# ---------------------------------------------------------
for path in [PRODUCTS, RECS, PUBLIC, WEB, IMPORTER]:
    check(
        f"File exists: {path.name}",
        path.exists(),
    )

# ---------------------------------------------------------
# JSON integrity
# ---------------------------------------------------------
def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

products = load_json(PRODUCTS)
recs = load_json(RECS)
public = load_json(PUBLIC)

check("products.json valid", isinstance(products, list),
      f"type={type(products).__name__}")
check("product_recommendations.json valid", isinstance(recs, list),
      f"type={type(recs).__name__}")
check("daraz_public_products.json valid", isinstance(public, list),
      f"type={type(public).__name__}")

# ---------------------------------------------------------
# Recommendation integrity
# ---------------------------------------------------------
if isinstance(products, list) and isinstance(recs, list):
    product_ids = {
        str(p.get("id") or p.get("item_id"))
        for p in products
        if p.get("id") is not None or p.get("item_id") is not None
    }

    rec_ids = {
        str(r.get("id") or r.get("item_id"))
        for r in recs
        if r.get("id") is not None or r.get("item_id") is not None
    }

    missing = sorted(product_ids - rec_ids)
    extra = sorted(rec_ids - product_ids)

    check(
        "Recommendation coverage complete",
        not missing and not extra,
        f"products={len(product_ids)}, recommendations={len(rec_ids)}, "
        f"missing={missing}, extra={extra}"
    )

    ranks = []
    for r in recs:
        try:
            ranks.append(int(r.get("recommendation_rank")))
        except Exception:
            pass

    expected = list(range(1, len(recs) + 1))
    check(
        "Recommendation ranks sequential",
        sorted(ranks) == expected,
        f"expected={expected}, actual={sorted(ranks)}"
    )

    scores = []
    for r in recs:
        try:
            scores.append(float(r.get("recommendation_score")))
        except Exception:
            pass

    check(
        "Recommendation scores present",
        len(scores) == len(recs),
        f"scores={len(scores)}/{len(recs)}"
    )

# ---------------------------------------------------------
# Web app consistency
# ---------------------------------------------------------
if WEB.exists():
    web = WEB.read_text(encoding="utf-8")

    check(
        "Web app recommendation file connected",
        "RECOMMENDATION_FILE" in web
    )

    check(
        "Web app recommendation score connected",
        "recommendation_score" in web
    )

    check(
        "Web app recommendation rank connected",
        "recommendation_rank" in web
    )

    check(
        "Product lookup supports item_id fallback",
        'product.get("item_id")' in web
    )

    check(
        "Product card supports item_id fallback",
        'product.get("id") or product.get("item_id")' in web
    )

    # Detect old ranking logic in important selection functions.
    top_three_old = (
        "def get_top_three_products(products):" in web
        and re.search(
            r"def get_top_three_products\(products\):.*?"
            r"key=smart_score",
            web,
            re.S
        )
    )

    best_value_old = (
        "def get_best_value_product(products):" in web
        and re.search(
            r"def get_best_value_product\(products\):.*?"
            r"key=best_value_score",
            web,
            re.S
        )
    )

    check(
        "No old TOP 3 smart_score selection",
        not bool(top_three_old)
    )

    check(
        "No old Best Value smart_score selection",
        not bool(best_value_old)
    )

# ---------------------------------------------------------
# Public Daraz data
# ---------------------------------------------------------
if isinstance(public, list):
    missing_fields = []

    for p in public:
        if not p.get("item_id"):
            missing_fields.append("item_id")
        if not p.get("name"):
            missing_fields.append("name")
        if p.get("price") in (None, ""):
            missing_fields.append("price")
        if not p.get("url"):
            missing_fields.append("url")

    check(
        "Public Daraz products required fields",
        not missing_fields,
        f"products={len(public)}"
    )

    item_ids = [
        str(p.get("item_id"))
        for p in public
        if p.get("item_id") is not None
    ]

    duplicates = sorted({
        x for x in item_ids if item_ids.count(x) > 1
    })

    check(
        "No duplicate public Daraz item IDs",
        not duplicates,
        f"duplicates={duplicates}"
    )

# ---------------------------------------------------------
# Python compilation
# ---------------------------------------------------------
compile_targets = [
    WEB,
    IMPORTER,
    ROOT / "daraz_api.py",
    ROOT / "worker_orchestrator.py",
]

for path in compile_targets:
    if path.exists():
        import py_compile
        try:
            py_compile.compile(
                str(path),
                doraise=True
            )
            check(f"Compile: {path.name}", True)
        except Exception as e:
            check(f"Compile: {path.name}", False, str(e))

# ---------------------------------------------------------
# Backup/test inventory — informational only
# ---------------------------------------------------------
backup_files = sorted(
    p.name for p in ROOT.iterdir()
    if (
        "backup" in p.name.lower()
        or "before_" in p.name.lower()
        or "test" in p.name.lower()
        or p.name.endswith(".bak")
    )
)

report["backup_test_inventory"] = backup_files

print()
print("BACKUP/TEST FILES:", len(backup_files))
for name in backup_files[:30]:
    print(" -", name)

passed = sum(
    1 for c in report["checks"]
    if c["status"] == "PASS"
)
failed = sum(
    1 for c in report["checks"]
    if c["status"] == "FAIL"
)

report["summary"] = {
    "checks": len(report["checks"]),
    "passed": passed,
    "failed": failed,
    "status": "PASS" if failed == 0 else "NEEDS_REVIEW",
}

report_path = REPORT_DIR / "final_production_audit_report.json"
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("=" * 55)
print("FINAL PRODUCTION AUDIT COMPLETE")
print("CHECKS:", len(report["checks"]))
print("PASS:", passed)
print("FAIL:", failed)
print("STATUS:", report["summary"]["status"])
print("REPORT:", report_path)
print("MODE: READ-ONLY / NO FILE MODIFICATION")
print("NO GIT PUSH")
print("NO FILE DELETION")
print("=" * 55)

sys.exit(0 if failed == 0 else 1)
