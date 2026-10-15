import json
import re
from pathlib import Path
from statistics import median

DISCOVERY = Path("worker_reports/daraz_public_discovery_report.json")
QUALITY = Path("worker_reports/daraz_discovery_quality_report.json")
OUTPUT = Path("worker_reports/daraz_product_ranking_v3_report.json")


def price_number(value):
    if value is None:
        return None
    m = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(m.group()) if m else None


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

        if price and price > 0:
            cohorts.setdefault(keyword, []).append(price)

    medians = {k: median(v) for k, v in cohorts.items() if v}

    ranked = []

    suspicious_terms = [
        "replica", "copy", "fake", "1:1",
        "master copy", "high copy"
    ]

    for p in products:
        item_id = str(p.get("item_id") or "").strip()
        name = str(p.get("name") or "").strip()
        name_lower = name.lower()
        keyword = keyword_by_id.get(item_id, "")
        price = price_number(p.get("price"))
        med = medians.get(keyword)

        score = 0
        flags = []
        reasons = []

        # Data completeness: 20
        if name:
            score += 5
        if item_id:
            score += 5
        if str(p.get("url") or "").startswith(
            "https://www.daraz.com.bd/"
        ):
            score += 5
        if price and price > 0:
            score += 5

        # Relevance: 25 — semantic category mapping
        relevance_map = {
            "home decor": ["decor", "plant", "flower", "vines", "leaf", "home"],
            "hair care": ["shampoo", "conditioner", "hair", "scalp", "oil"],
            "bird": ["bird", "budgie", "cockatiel", "parrot", "finch"],
        }

        relevance_hit = False

        if keyword and keyword in name_lower:
            relevance_hit = True
        else:
            keyword_parts = [x.strip() for x in keyword.split(">")]
            keyword_text = " ".join(keyword_parts)

            for mapped_keyword, terms in relevance_map.items():
                if mapped_keyword in keyword_text and any(
                    term in name_lower for term in terms
                ):
                    relevance_hit = True
                    break

        if relevance_hit:
            score += 25
            reasons.append("keyword_relevant")
        else:
            flags.append("weak_keyword_relevance")

        # Price comparison: 30
        if price and med:
            ratio = price / med

            if 0.80 <= ratio <= 1.10:
                score += 30
                reasons.append("competitive_price")
            elif 0.60 <= ratio < 0.80:
                score += 25
                reasons.append("lower_than_median")
            elif 1.10 < ratio <= 1.35:
                score += 22
                reasons.append("reasonable_price")
            elif 0.40 <= ratio < 0.60:
                score += 12
                flags.append("unusually_low_price")
            elif ratio < 0.40:
                score += 5
                flags.append("extremely_low_price")
            elif ratio <= 2.0:
                score += 15
                flags.append("higher_price")
            else:
                score += 8
                flags.append("very_high_price")

        # Suspicious listing signals: 25
        suspicious = [
            x for x in suspicious_terms
            if x in name_lower
        ]

        if suspicious:
            flags.append("suspicious_listing_terms")
        else:
            score += 15

        # Very low absolute price gets extra review flag
        if price and price < 100:
            flags.append("very_low_absolute_price")

        # Special caution for premium-looking claims
        premium_claims = [
            "airpods",
            "original",
            "official"
        ]

        if any(x in name_lower for x in premium_claims):
            if price and med and price < med * 0.50:
                flags.append("premium_claim_low_price")

        # Seller-claim safety gate
        claim_patterns = {
            "ORIGINAL": [r"\boriginal\b", r"\bgenuine\b", r"\bauthentic\b"],
            "OFFICIAL": [r"\bofficial\b", r"\bauthorized\b"],
            "PREMIUM": [r"\bpremium\b"],
            "AIRPODS": [r"\bairpods?\b"],
        }

        seller_claims = []
        for claim, patterns in claim_patterns.items():
            if any(re.search(pattern, name_lower) for pattern in patterns):
                seller_claims.append(claim)

        if "AIRPODS" in seller_claims or len(seller_claims) >= 2:
            claim_risk = "HIGH"
        elif "ORIGINAL" in seller_claims or "OFFICIAL" in seller_claims:
            claim_risk = "MEDIUM"
        elif "PREMIUM" in seller_claims:
            claim_risk = "LOW"
        else:
            claim_risk = "NONE"

        claim_status = (
            "UNVERIFIED_SELLER_CLAIM"
            if seller_claims
            else "NO_STRONG_CLAIM_DETECTED"
        )

        verification_needed = bool(seller_claims)

        # Final classification
        score = max(0, min(100, score))

        if seller_claims:
            tier = "REVIEW"
        elif flags:
            tier = "REVIEW"
        elif score >= 90:
            tier = "BEST"
        elif score >= 75:
            tier = "GOOD"
        else:
            tier = "REVIEW"

        ranked.append({
            **p,
            "search_keyword": keyword,
            "price_median": med,
            "price_ratio_to_median": (
                round(price / med, 3)
                if price and med else None
            ),
            "ranking_score_v3": score,
            "ranking_tier_v3": tier,
            "ranking_reasons_v3": reasons,
            "ranking_flags_v3": flags,
            "seller_claims": seller_claims,
            "claim_status": claim_status,
            "verification_needed": verification_needed,
            "claim_risk": claim_risk
        })

    ranked.sort(
        key=lambda x: x["ranking_score_v3"],
        reverse=True
    )

    for i, p in enumerate(ranked, 1):
        p["ranking_position_v3"] = i

    summary = {
        "input_products": len(ranked),
        "best": sum(
            x["ranking_tier_v3"] == "BEST"
            for x in ranked
        ),
        "good": sum(
            x["ranking_tier_v3"] == "GOOD"
            for x in ranked
        ),
        "review": sum(
            x["ranking_tier_v3"] == "REVIEW"
            for x in ranked
        )
    }

    report = {
        "worker": "daraz_product_ranking_v3_worker",
        "version": "4.0",
        "mode": "read_only_ranking",
        "production_modified": False,
        "git_modified": False,
        "summary": summary,
        "price_medians": medians,
        "ranked_products": ranked
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ PRODUCT RANKING WORKER V3")
    print("=" * 65)
    print("Input :", summary["input_products"])
    print("BEST  :", summary["best"])
    print("GOOD  :", summary["good"])
    print("REVIEW:", summary["review"])

    print("\nTOP 10:")
    for p in ranked[:10]:
        print(
            f'{p["ranking_position_v3"]:02d}. '
            f'{p["name"]} | ৳{p["price"]} | '
            f'{p["search_keyword"]} | '
            f'score={p["ranking_score_v3"]} | '
            f'{p["ranking_tier_v3"]}'
        )

    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")


if __name__ == "__main__":
    main()
