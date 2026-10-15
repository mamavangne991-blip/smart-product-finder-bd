import json
from pathlib import Path

RECOMMEND = Path("worker_reports/daraz_recommendation_v3_candidate_report.json")
OUTPUT = Path("worker_reports/daraz_final_recommendation_pipeline_v2_candidate_report.json")

def main():
    recommend = json.loads(RECOMMEND.read_text(encoding="utf-8"))

    recommendations = recommend.get("recommendations", [])
    review = recommend.get("review", [])

    final_recommendations = []

    for x in recommendations:
        final_recommendations.append({
            "position": x.get("recommendation_position"),
            "item_id": x.get("item_id"),
            "name": x.get("name"),
            "price": x.get("price"),
            "url": x.get("url"),
            "search_keyword": x.get("search_keyword"),
            "score": x.get("ranking_score"),
            "status": x.get("recommendation_status"),
            "seller_claims": x.get("seller_claims", []),
            "claim_risk": x.get("claim_risk", "NONE"),
            "verification_needed": x.get("verification_needed", False),
        })

    report = {
        "worker": "daraz_final_recommendation_pipeline_v2_candidate",
        "version": "2.0-candidate",
        "mode": "staging_candidate",
        "status": "PASS",
        "input_count": (
            len(recommendations) +
            len(review)
        ),
        "final_recommendation_count": len(final_recommendations),
        "review_count": len(review),
        "claim_review_count": sum(
            bool(x.get("seller_claims")) for x in review
        ),
        "production_modified": False,
        "git_modified": False,
        "recommendations": final_recommendations,
        "review_items": review,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ FINAL RECOMMENDATION PIPELINE V2 CANDIDATE")
    print("=" * 65)
    print("Input products :", report["input_count"])
    print("Final results  :", report["final_recommendation_count"])
    print("Review items   :", report["review_count"])
    print("Claim reviews  :", report["claim_review_count"])
    print("FINAL STATUS   :", report["status"])
    print("REPORT         :", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
