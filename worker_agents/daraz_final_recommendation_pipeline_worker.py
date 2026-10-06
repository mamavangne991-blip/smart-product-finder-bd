import json
from pathlib import Path

RANKING = Path("worker_reports/daraz_product_ranking_v3_report.json")
RECOMMEND = Path("worker_reports/daraz_recommendation_v2_report.json")
SAFETY = Path("worker_reports/daraz_recommendation_safety_report.json")
OUTPUT = Path("worker_reports/daraz_final_recommendation_pipeline_report.json")

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    ranking = load(RANKING)
    recommend = load(RECOMMEND)
    safety = load(SAFETY)

    recommendations = recommend.get("recommendations", [])
    review = recommend.get("review", [])

    safety_pass = safety.get("status") == "PASS"

    final_recommendations = []

    if safety_pass:
        for p in recommendations:
            final_recommendations.append({
                "position": p.get("recommendation_position"),
                "item_id": p.get("item_id"),
                "name": p.get("name"),
                "price": p.get("price"),
                "url": p.get("url"),
                "search_keyword": p.get("search_keyword"),
                "score": p.get("ranking_score"),
                "status": p.get("recommendation_status"),
            })

    report = {
        "worker": "daraz_final_recommendation_pipeline_worker",
        "version": "1.0",
        "mode": "read_only_finalization",
        "status": "PASS" if safety_pass else "BLOCKED",
        "input_count": ranking.get("summary", {}).get("input_products"),
        "final_recommendation_count": len(final_recommendations),
        "review_count": len(review),
        "safety_status": safety.get("status"),
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
    print("DARAZ FINAL RECOMMENDATION PIPELINE")
    print("=" * 65)
    print("Input products :", report["input_count"])
    print("Final results  :", report["final_recommendation_count"])
    print("Review items   :", report["review_count"])
    print("Safety status  :", report["safety_status"])
    print("FINAL STATUS   :", report["status"])
    print()
    print("REPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
