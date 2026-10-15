import json
from pathlib import Path

SOURCE = Path("worker_reports/daraz_product_ranking_v4_candidate_report.json")
OUTPUT = Path("worker_reports/daraz_recommendation_v3_candidate_report.json")

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    products = data.get("ranked_products", [])

    recommended = []
    review = []

    for x in products:
        tier = x.get("ranking_tier_v3")
        score = int(x.get("ranking_score_v3", 0))
        claims = x.get("seller_claims", [])
        risk = x.get("claim_risk", "NONE")
        verify = bool(x.get("verification_needed", False))

        item = {
            "item_id": x.get("item_id"),
            "name": x.get("name"),
            "price": x.get("price"),
            "url": x.get("url"),
            "search_keyword": x.get("search_keyword"),
            "ranking_score": score,
            "ranking_tier": tier,
            "ranking_flags": x.get("ranking_flags_v3", []),
            "seller_claims": claims,
            "claim_status": x.get("claim_status"),
            "claim_risk": risk,
            "verification_needed": verify,
        }

        # HARD SAFETY GATE
        if claims or verify:
            item["recommendation_status"] = "REVIEW"
            review.append(item)
        elif tier in ("BEST", "GOOD") and not x.get("ranking_flags_v3"):
            item["recommendation_status"] = (
                "RECOMMEND" if tier == "BEST" else "GOOD_OPTION"
            )
            recommended.append(item)
        else:
            item["recommendation_status"] = "REVIEW"
            review.append(item)

    recommended.sort(
        key=lambda x: x["ranking_score"],
        reverse=True
    )

    for i, x in enumerate(recommended, 1):
        x["recommendation_position"] = i

    report = {
        "worker": "daraz_recommendation_v3_candidate",
        "version": "3.0-candidate",
        "mode": "staging_candidate",
        "production_modified": False,
        "git_modified": False,
        "summary": {
            "input_products": len(products),
            "recommend": sum(x["recommendation_status"] == "RECOMMEND" for x in recommended),
            "good_options": sum(x["recommendation_status"] == "GOOD_OPTION" for x in recommended),
            "review": len(review),
            "claim_products": sum(bool(x.get("seller_claims")) for x in products),
        },
        "recommendations": recommended,
        "review": review,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ RECOMMENDATION V3 CANDIDATE")
    print("=" * 65)
    print("Input       :", len(products))
    print("Recommend   :", report["summary"]["recommend"])
    print("Good options:", report["summary"]["good_options"])
    print("Review      :", report["summary"]["review"])
    print("Claims      :", report["summary"]["claim_products"])
    print("REPORT      :", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
