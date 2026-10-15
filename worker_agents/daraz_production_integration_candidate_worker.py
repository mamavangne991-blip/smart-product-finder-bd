import json
from pathlib import Path

SOURCE = Path("worker_reports/daraz_final_recommendation_staging_v2.json")
OUTPUT = Path("worker_reports/daraz_production_integration_candidate.json")

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))

    candidates = []

    for p in data["recommendations"]:
        candidates.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "category": p["category"],
            "source": p["source"],
            "url": p["url"],
            "item_id": p["item_id"],
            "recommendation_rank": p["recommendation_rank"],
            "recommendation_score": p["recommendation_score"],
            "recommendation_status": p["recommendation_status"],
        })

    report = {
        "worker": "daraz_production_integration_candidate_worker",
        "version": "1.0",
        "mode": "production_safe_candidate",
        "status": "PASS",
        "candidate_count": len(candidates),
        "source": str(SOURCE),
        "target": "product_recommendations.json",
        "overwrite_performed": False,
        "production_modified": False,
        "git_modified": False,
        "candidates": candidates,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ PRODUCTION INTEGRATION CANDIDATE")
    print("=" * 65)
    print("Source       :", SOURCE)
    print("Candidates   :", len(candidates))
    print("Target       : product_recommendations.json")
    print("Overwrite    : NO")
    print("STATUS       :", report["status"])
    print("REPORT       :", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
