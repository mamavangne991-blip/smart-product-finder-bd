import json
import re
from pathlib import Path

SOURCE = Path("worker_reports/daraz_discovery_quality_report.json")
OUTPUT = Path("worker_reports/daraz_product_ranking_report.json")

def price_number(value):
    if value is None:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(m.group()) if m else None

def rank_product(p):
    score = 0
    flags = []

    name = str(p.get("name") or "").strip()
    price = price_number(p.get("price"))

    if name:
        score += 25
    if p.get("item_id"):
        score += 20
    if str(p.get("url") or "").startswith("https://www.daraz.com.bd/"):
        score += 20

    if price is not None and price > 0:
        score += 20
        if price < 100:
            score -= 15
            flags.append("very_low_price")
        elif price > 10000:
            score -= 5
            flags.append("high_price")

    name_lower = name.lower()

    suspicious_terms = [
        "replica", "copy", "1:1", "fake", "master copy", "high copy"
    ]

    found = [x for x in suspicious_terms if x in name_lower]
    if found:
        score -= 25
        flags.append("suspicious_listing_terms")

    score = max(0, min(100, score))

    if score >= 80:
        tier = "BEST_CANDIDATE"
    elif score >= 65:
        tier = "GOOD_CANDIDATE"
    else:
        tier = "REVIEW"

    return score, tier, flags

def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source: {SOURCE}")

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    products = data.get("pass", [])

    ranked = []

    for p in products:
        score, tier, flags = rank_product(p)

        item = dict(p)
        item["ranking_score"] = score
        item["ranking_tier"] = tier
        item["ranking_flags"] = flags
        ranked.append(item)

    ranked.sort(
        key=lambda x: (
            x["ranking_score"],
            -(price_number(x.get("price")) or 999999)
        ),
        reverse=True
    )

    for i, p in enumerate(ranked, 1):
        p["ranking_position"] = i

    summary = {
        "input_products": len(products),
        "ranked_products": len(ranked),
        "best_candidates": sum(
            x["ranking_tier"] == "BEST_CANDIDATE" for x in ranked
        ),
        "good_candidates": sum(
            x["ranking_tier"] == "GOOD_CANDIDATE" for x in ranked
        ),
        "review": sum(
            x["ranking_tier"] == "REVIEW" for x in ranked
        ),
    }

    report = {
        "worker": "daraz_product_ranking_worker",
        "version": "1.0",
        "mode": "read_only_product_ranking",
        "production_modified": False,
        "git_modified": False,
        "source": str(SOURCE),
        "summary": summary,
        "ranked_products": ranked,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 60)
    print("DARAZ PRODUCT RANKING WORKER")
    print("=" * 60)
    print("Input products  :", summary["input_products"])
    print("Ranked products :", summary["ranked_products"])
    print("Best candidates :", summary["best_candidates"])
    print("Good candidates :", summary["good_candidates"])
    print("Review          :", summary["review"])

    print("\nTOP 10 CANDIDATES:")
    for p in ranked[:10]:
        print(
            f'{p["ranking_position"]:02d}. '
            f'{p["name"]} | ৳{p["price"]} | '
            f'score={p["ranking_score"]} | '
            f'{p["ranking_tier"]}'
        )

    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
