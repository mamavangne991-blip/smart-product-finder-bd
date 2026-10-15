import json
from pathlib import Path

SOURCE = Path("worker_reports/daraz_product_ranking_report.json")
OUTPUT = Path("worker_reports/daraz_recommendation_candidate_report.json")


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))

    products = data.get("ranked_products", [])

    candidates = []
    review = []

    for p in products:
        score = int(p.get("ranking_score", 0))
        tier = p.get("ranking_tier")

        item = {
            "item_id": p.get("item_id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "url": p.get("url"),
            "ranking_score": score,
            "ranking_tier": tier,
            "ranking_position": p.get("ranking_position"),
            "recommendation_status": (
                "RECOMMEND"
                if tier == "BEST_CANDIDATE" and score >= 80
                else "GOOD_OPTION"
                if tier == "GOOD_CANDIDATE" and score >= 65
                else "REVIEW"
            ),
        }

        if item["recommendation_status"] in (
            "RECOMMEND",
            "GOOD_OPTION",
        ):
            candidates.append(item)
        else:
            review.append(item)

    candidates.sort(
        key=lambda x: (
            x["recommendation_status"] == "RECOMMEND",
            x["ranking_score"],
        ),
        reverse=True,
    )

    for i, item in enumerate(candidates, start=1):
        item["recommendation_position"] = i

    report = {
        "worker": "daraz_recommendation_candidate_worker",
        "version": "1.0",
        "mode": "read_only_recommendation_candidate_generation",
        "production_modified": False,
        "git_modified": False,
        "source": str(SOURCE),
        "summary": {
            "input_ranked_products": len(products),
            "recommend": sum(
                1 for x in candidates
                if x["recommendation_status"] == "RECOMMEND"
            ),
            "good_options": sum(
                1 for x in candidates
                if x["recommendation_status"] == "GOOD_OPTION"
            ),
            "review": len(review),
        },
        "recommendation_candidates": candidates,
        "review_products": review,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("DARAZ RECOMMENDATION CANDIDATE WORKER")
    print("=" * 60)
    print("Input ranked products :", len(products))
    print("Recommend             :", report["summary"]["recommend"])
    print("Good options          :", report["summary"]["good_options"])
    print("Review                :", report["summary"]["review"])

    print("\nTOP RECOMMENDATION CANDIDATES:")

    for p in candidates[:10]:
        print(
            f'{p["recommendation_position"]:02d}. '
            f'{p["name"]} | ৳{p["price"]} | '
            f'score={p["ranking_score"]} | '
            f'{p["recommendation_status"]}'
        )

    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")


if __name__ == "__main__":
    main()
