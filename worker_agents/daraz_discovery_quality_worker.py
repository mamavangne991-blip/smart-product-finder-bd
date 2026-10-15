import json
import re
from pathlib import Path

SOURCE = Path("worker_reports/daraz_public_discovery_report.json")
OUTPUT = Path("worker_reports/daraz_discovery_quality_report.json")

def price_number(value):
    if value is None:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(m.group()) if m else None

def quality_score(p):
    score = 0
    reasons = []

    name = str(p.get("name") or "").strip()
    url = str(p.get("url") or "").strip()
    item_id = p.get("item_id")
    price = price_number(p.get("price"))

    if name:
        score += 25
    else:
        reasons.append("missing_name")

    if item_id:
        score += 25
    else:
        reasons.append("missing_item_id")

    if url.startswith("https://www.daraz.com.bd/"):
        score += 25
    else:
        reasons.append("invalid_or_missing_daraz_url")

    if price is not None and price > 0:
        score += 25
    else:
        reasons.append("invalid_price")

    # Suspiciously low prices are flagged, not automatically deleted.
    suspicious = price is not None and price < 100

    if suspicious:
        reasons.append("suspiciously_low_price")

    if score >= 100 and not suspicious:
        status = "PASS"
    elif score >= 75:
        status = "REVIEW"
    else:
        status = "REJECT"

    return score, status, reasons


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))

    all_products = []
    for result in data.get("results", []):
        all_products.extend(result.get("products", []))

    seen = set()
    unique = []
    duplicates = 0

    for p in all_products:
        key = str(p.get("item_id") or p.get("url") or p.get("name") or "").strip()

        if not key:
            continue

        if key in seen:
            duplicates += 1
            continue

        seen.add(key)
        unique.append(p)

    passed = []
    review = []
    rejected = []

    for p in unique:
        score, status, reasons = quality_score(p)

        item = dict(p)
        item["quality_score"] = score
        item["quality_status"] = status
        item["quality_reasons"] = reasons

        if status == "PASS":
            passed.append(item)
        elif status == "REVIEW":
            review.append(item)
        else:
            rejected.append(item)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "worker": "daraz_discovery_quality_worker",
        "version": "1.0",
        "mode": "read_only_quality_filter",
        "production_modified": False,
        "git_modified": False,
        "source": str(SOURCE),
        "summary": {
            "input_products": len(all_products),
            "unique_products": len(unique),
            "duplicates": duplicates,
            "pass": len(passed),
            "review": len(review),
            "reject": len(rejected),
        },
        "pass": passed,
        "review": review,
        "reject": rejected,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 55)
    print("DARAZ DISCOVERY QUALITY WORKER")
    print("=" * 55)
    print("Input products :", len(all_products))
    print("Unique         :", len(unique))
    print("Duplicates     :", duplicates)
    print("PASS           :", len(passed))
    print("REVIEW         :", len(review))
    print("REJECT         :", len(rejected))
    print()
    print("Report:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

    print("\nTOP QUALITY PRODUCTS:")
    for p in sorted(
        passed,
        key=lambda x: x["quality_score"],
        reverse=True
    )[:10]:
        print(
            f'- {p["name"]} | ৳{p["price"]} | '
            f'score={p["quality_score"]} | id={p["item_id"]}'
        )


if __name__ == "__main__":
    main()
