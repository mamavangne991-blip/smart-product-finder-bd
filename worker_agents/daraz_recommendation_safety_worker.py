import json
from pathlib import Path
from urllib.parse import urlparse

SOURCE = Path("worker_reports/daraz_recommendation_v2_report.json")
OUTPUT = Path("worker_reports/daraz_recommendation_safety_report.json")

def valid_url(url):
    try:
        p = urlparse(url or "")
        return (
            p.scheme == "https"
            and p.netloc.endswith("daraz.com.bd")
        )
    except Exception:
        return False

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))

    recommendations = data.get("recommendations", [])
    review = data.get("review", [])

    checked = 0
    passed = 0
    failed = 0
    failures = []
    seen = set()

    for p in recommendations:
        checked += 1
        reasons = []

        item_id = str(p.get("item_id") or "")
        url = p.get("url")
        name = (p.get("name") or "").strip()
        price = p.get("price")

        if not item_id:
            reasons.append("missing_item_id")

        if not name:
            reasons.append("missing_name")

        if not valid_url(url):
            reasons.append("invalid_daraz_url")

        try:
            if float(price) <= 0:
                reasons.append("invalid_price")
        except Exception:
            reasons.append("invalid_price")

        key = item_id or url or name
        if key in seen:
            reasons.append("duplicate")
        seen.add(key)

        if p.get("recommendation_status") not in (
            "RECOMMEND",
            "GOOD_OPTION",
        ):
            reasons.append("invalid_recommendation_status")

        if reasons:
            failed += 1
            failures.append({
                "name": name,
                "item_id": item_id,
                "reasons": reasons,
            })
        else:
            passed += 1

    review_leak = []
    for p in recommendations:
        if p.get("recommendation_status") == "REVIEW":
            review_leak.append(p.get("name"))

    report = {
        "worker": "daraz_recommendation_safety_worker",
        "version": "1.0",
        "mode": "read_only_validation",
        "production_modified": False,
        "git_modified": False,
        "input_recommendations": len(recommendations),
        "input_review": len(review),
        "checked": checked,
        "passed": passed,
        "failed": failed,
        "review_leak_count": len(review_leak),
        "failures": failures,
        "review_leaks": review_leak,
        "status": (
            "PASS"
            if failed == 0 and len(review_leak) == 0
            else "REVIEW"
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ RECOMMENDATION SAFETY WORKER")
    print("=" * 65)
    print("Recommendations:", len(recommendations))
    print("Checked        :", checked)
    print("Passed         :", passed)
    print("Failed         :", failed)
    print("Review leaks   :", len(review_leak))
    print("STATUS         :", report["status"])
    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
