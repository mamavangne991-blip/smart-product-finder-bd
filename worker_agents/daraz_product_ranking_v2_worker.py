import json
import re
from pathlib import Path
from statistics import median

DISCOVERY = Path("worker_reports/daraz_public_discovery_report.json")
QUALITY = Path("worker_reports/daraz_discovery_quality_report.json")
OUTPUT = Path("worker_reports/daraz_product_ranking_v2_report.json")


def price_number(value):
    if value is None:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(m.group()) if m else None


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def main():
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    quality = json.loads(QUALITY.read_text(encoding="utf-8"))

    keyword_by_id = {}

    for result in discovery.get("results", []):
        keyword = str(result.get("keyword") or "").lower().strip()
        for p in result.get("products", []):
            item_id = str(p.get("item_id") or "").strip()
            if item_id:
                keyword_by_id[item_id] = keyword

    products = quality.get("pass", [])

    cohorts = {}

    for p in products:
        item_id = str(p.get("item_id") or "").strip()
        keyword = keyword_by_id.get(item_id, "")
        price = price_number(p.get("price"))

        if price is not None and price > 0:
            cohorts.setdefault(keyword, []).append(price)

    medians = {
        k: median(v)
        for k, v in cohorts.items()
        if v
    }

    ranked = []

    suspicious_terms = {
        "replica", "copy", "fake", "1:1",
        "master copy", "high copy"
    }

    for p in products:
        item_id = str(p.get("item_id") or "").strip()
        name = str(p.get("name") or "").strip()
        name_lower = name.lower()
        keyword = keyword_by_id.get(item_id, "")
        price = price_number(p.get("price"))

        score = 0
        reasons = []
        flags = []

        # Relevance: 35
        name_words = tokens(name)
        key_words = tokens(keyword)

        overlap = len(name_words & key_words)

        if keyword and keyword in name_lower:
            relevance = 35
            reasons.append("exact_keyword_match")
        elif overlap:
            relevance = 25
            reasons.append("partial_keyword_match")
        else:
            relevance = 5
            flags.append("weak_keyword_relevance")

        score += relevance

        # Data completeness: 20
        completeness = 0

        if name:
            completeness += 5
        if item_id:
            completeness += 5
        if str(p.get("url") or "").startswith(
            "https://www.daraz.com.bd/"
        ):
            completeness += 5
        if price is not None and price > 0:
            completeness += 5

        score += completeness

        # Price value: 30
        price_score = 0

        if price is not None and price > 0 and keyword in medians:
            med = medians[keyword]

            ratio = price / med

            if 0.70 <= ratio <= 1.00:
                price_score = 30
                reasons.append("competitive_price")
            elif 1.00 < ratio <= 1.30:
                price_score = 24
                reasons.append("reasonable_price")
            elif 0.45 <= ratio < 0.70:
                price_score = 22
                reasons.append("low_price_review_needed")
                flags.append("unusually_low_vs_median")
            elif ratio < 0.45:
                price_score = 10
                flags.append("very_low_vs_median")
            elif 1.30 < ratio <= 2.00:
                price_score = 16
                reasons.append("higher_than_median")
            else:
                price_score = 10
                flags.append("very_high_vs_median")
        elif price is not None and price > 0:
            price_score = 15

        score += price_score

        # Risk / listing signals: 15
        risk_score = 15

        found = [
            term for term in suspicious_terms
            if term in name_lower
        ]

        if found:
            risk_score -= 15
            flags.append("suspicious_listing_terms")

        if price is not None and price < 100:
            risk_score -= 5
            flags.append("very_low_absolute_price")

        risk_score = max(0, risk_score)
        score += risk_score

        score = max(0, min(100, score))

        if flags:
            tier = "REVIEW"
        elif score >= 85:
            tier = "BEST"
        elif score >= 70:
            tier = "GOOD"
        else:
            tier = "REVIEW"

        ranked.append({
            **p,
            "search_keyword": keyword,
            "price_median_for_keyword": medians.get(keyword),
            "ranking_score_v2": score,
            "ranking_tier_v2": tier,
            "ranking_reasons_v2": reasons,
            "ranking_flags_v2": flags,
        })

    ranked.sort(
        key=lambda x: x["ranking_score_v2"],
        reverse=True
    )

    for i, p in enumerate(ranked, 1):
        p["ranking_position_v2"] = i

    summary = {
        "input_products": len(products),
        "best": sum(
            x["ranking_tier_v2"] == "BEST"
            for x in ranked
        ),
        "good": sum(
            x["ranking_tier_v2"] == "GOOD"
            for x in ranked
        ),
        "review": sum(
            x["ranking_tier_v2"] == "REVIEW"
            for x in ranked
        ),
    }

    report = {
        "worker": "daraz_product_ranking_v2_worker",
        "version": "2.0",
        "mode": "read_only_ranking",
        "production_modified": False,
        "git_modified": False,
        "summary": summary,
        "price_medians": medians,
        "ranked_products": ranked,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ PRODUCT RANKING WORKER V2")
    print("=" * 65)
    print("Input products :", summary["input_products"])
    print("BEST           :", summary["best"])
    print("GOOD           :", summary["good"])
    print("REVIEW         :", summary["review"])

    print("\nPRICE MEDIANS:")
    for k, v in medians.items():
        print(f"- {k}: ৳{v:.0f}")

    print("\nTOP 10:")
    for p in ranked[:10]:
        print(
            f'{p["ranking_position_v2"]:02d}. '
            f'{p["name"]} | ৳{p["price"]} | '
            f'{p["search_keyword"]} | '
            f'score={p["ranking_score_v2"]} | '
            f'{p["ranking_tier_v2"]}'
        )

    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")


if __name__ == "__main__":
    main()
