from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "web_app_v6.py"
PRODUCTS = ROOT / "products.json"
RECOMMENDATIONS = ROOT / "product_recommendations.json"
REPORT = ROOT / "worker_reports" / "web_app_recommendation_report.json"

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

if not APP.exists():
    check("web_app_v6.py exists", False, "File not found")
else:
    text = APP.read_text(encoding="utf-8")

    check(
        "Recommendation file configured",
        "RECOMMENDATION_FILE" in text and "product_recommendations.json" in text
    )

    check(
        "Recommendation scores loaded",
        "recommendation_score" in text and "score_breakdown" in text
    )

    check(
        "Product lookup supports item_id",
        'product.get("id") or product.get("item_id")' in text
    )

    check(
        "Product card score uses recommendation score",
        'product.get("recommendation_score")' in text
    )

    check(
        "Old homepage smart_score sorting detected",
        'key=smart_score' not in text,
        "Homepage still sorts directly with smart_score" if 'key=smart_score' in text else ""
    )

    check(
        "Old homepage item score detected",
        'item_score = smart_score(item)' not in text,
        "Homepage item score still uses smart_score" if 'item_score = smart_score(item)' in text else ""
    )

    check(
        "Old best-value score detected",
        'best_value_score = smart_score(' not in text,
        "Best-value section still uses smart_score" if 'best_value_score = smart_score(' in text else ""
    )

    # Check product card URL ID fallback
    card_id_pattern = r'product_id\s*=\s*html\.escape\(str\(product\.get\("id",\s*""\)\)\)'
    check(
        "Product card URL supports item_id fallback",
        re.search(card_id_pattern, text) is None,
        "Product card still uses id only"
    )

if PRODUCTS.exists() and RECOMMENDATIONS.exists():
    try:
        products = json.loads(PRODUCTS.read_text(encoding="utf-8"))
        recs = json.loads(RECOMMENDATIONS.read_text(encoding="utf-8"))

        rec_map = {
            str(r.get("id") or r.get("item_id")): r
            for r in recs
            if r.get("id") or r.get("item_id")
        }

        matched = 0
        for p in products:
            key = str(p.get("id") or p.get("item_id") or "")
            if key in rec_map:
                matched += 1

        check(
            "Recommendation coverage",
            matched == len(products),
            f"{matched}/{len(products)} products matched"
        )

        ranks = [
            r.get("recommendation_rank")
            for r in recs
            if r.get("recommendation_rank") is not None
        ]

        check(
            "Recommendation ranks sequential",
            sorted(ranks) == list(range(1, len(ranks) + 1)),
            f"Ranks found: {ranks}"
        )

    except Exception as exc:
        check("Recommendation data readable", False, str(exc))
else:
    check(
        "Recommendation data files exist",
        False,
        "products.json or product_recommendations.json missing"
    )

if APP.exists():
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(APP)],
        cwd=ROOT,
        capture_output=True,
        text=True
    )
    check(
        "web_app_v6.py compiles",
        result.returncode == 0,
        result.stderr.strip()
    )

status = "PASS" if not issues else "NEEDS_FIX"

report = {
    "worker": "web_app_recommendation_worker",
    "mode": "audit_only",
    "status": status,
    "checks": checks,
    "issues": issues
}

REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("========================================")
print(" WEB APP RECOMMENDATION WORKER")
print("========================================")
for item in checks:
    print(f"{item['status']}: {item['check']}")
    if item["detail"]:
        print(f"       {item['detail']}")

print()
print(f"STATUS: {status}")
print(f"REPORT: {REPORT.relative_to(ROOT)}")
print("MODE: AUDIT ONLY / NO FILE MODIFICATION")
