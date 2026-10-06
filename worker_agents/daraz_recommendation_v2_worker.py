import json
from pathlib import Path

SOURCE = Path("worker_reports/daraz_product_ranking_v3_report.json")
OUTPUT = Path("worker_reports/daraz_recommendation_v2_report.json")

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    products = data.get("ranked_products", [])

    recommended = []
    review = []

    for p in products:
        tier = p.get("ranking_tier_v3")
        score = int(p.get("ranking_score_v3", 0))

        item = {
            "item_id": p.get("item_id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "url": p.get("url"),
            "search_keyword": p.get("search_keyword"),
            "ranking_score": score,
            "ranking_tier": tier,
            "ranking_flags": p.get("ranking_flags_v3", []),
        }

        if tier in ("BEST", "GOOD") and not p.get("ranking_flags_v3"):
            item["recommendation_status"] = (
                "RECOMMEND" if tier == "BEST"
                else "GOOD_OPTION"
            )
            recommended.append(item)
        else:
            item["recommendation_status"] = "REVIEW"
            review.append(item)

    recommended.sort(
        key=lambda x: x["ranking_score"],
        reverse=True
    )

    for i, p in enumerate(recommended, 1):
        p["recommendation_position"] = i

    summary = {
        "input_products": len(products),
        "recommend": sum(
            x["recommendation_status"] == "RECOMMEND"
            for x in recommended
        ),
        "good_options": sum(
            x["recommendation_status"] == "GOOD_OPTION"
            for x in recommended
        ),
        "review": len(review),
    }

    report = {
        "worker": "daraz_recommendation_v2_worker",
        "version": "2.0",
        "mode": "read_only_recommendation",
        "production_modified": False,
        "git_modified": False,
        "summary": summary,
        "recommendations": recommended,
        "review": review,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 65)
    print("DARAZ RECOMMENDATION WORKER V2")
    print("=" * 65)
    print("Input       :", summary["input_products"])
    print("Recommend   :", summary["recommend"])
    print("Good options:", summary["good_options"])
    print("Review      :", summary["review"])

    print("\nTOP RECOMMENDATIONS:")
    for p in recommended[:10]:
        print(
            f'{p["recommendation_position"]:02d}. '
            f'{p["name"]} | ৳{p["price"]} | '
            f'{p["search_keyword"]} | '
            f'score={p["ranking_score"]} | '
            f'{p["recommendation_status"]}'
        )

    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified: NO")

if __name__ == "__main__":
    main()
