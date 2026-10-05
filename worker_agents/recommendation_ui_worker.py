import json
from pathlib import Path

INPUT = Path("product_recommendations.json")
PRODUCTS = Path("products.json")
REPORT = Path("worker_reports/recommendation_ui_report.json")

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    data = load_json(INPUT)
    products = load_json(PRODUCTS)

    url_map = {}
    for p in products:
        key = str(p.get("item_id") or p.get("id") or p.get("name") or "").strip()
        if key and p.get("url"):
            url_map[key] = p["url"]

    results = []
    missing_url = 0

    for rank, p in enumerate(data, 1):
        item_id = str(p.get("item_id") or p.get("id") or "").strip()
        name = str(p.get("name") or "Unknown Product").strip()

        url = p.get("url") or url_map.get(item_id)

        score = p.get("recommendation_score", p.get("score", 0))
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0

        evidence = p.get("evidence_score")
        if evidence is None:
            evidence = p.get("evidence", 0)

        results.append({
            "rank": rank,
            "name": name,
            "score": score,
            "price": p.get("price"),
            "currency": p.get("currency", "BDT"),
            "source": p.get("source", "Unknown"),
            "evidence": evidence,
            "category": p.get("category"),
            "url": url,
            "has_url": bool(url),
            "item_id": p.get("item_id"),
        })

        if not url:
            missing_url += 1

    results.sort(key=lambda x: (-x["score"], x["rank"]))

    for i, item in enumerate(results, 1):
        item["rank"] = i

    report = {
        "worker": "Recommendation UI Worker V1",
        "total": len(results),
        "ready": len(results) - missing_url,
        "missing_url": missing_url,
        "status": "PASS" if results else "FAIL",
        "results": results,
    }

    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 60)
    print("RECOMMENDATION UI WORKER V1")
    print("=" * 60)
    print("TOTAL:", len(results))
    print("READY:", len(results) - missing_url)
    print("MISSING URL:", missing_url)

    print("\n===== TOP RESULTS =====")
    for p in results[:10]:
        print(
            f"#{p['rank']} | SCORE {p['score']:.0f} | "
            f"৳{p['price']} | {p['name'][:70]}"
        )
        print(
            f"    source={p['source']} "
            f"evidence={p['evidence']} "
            f"url={'YES' if p['has_url'] else 'NO'}"
        )

    print("\nREPORT:", REPORT)
    print("WORKER STATUS:", report["status"])

if __name__ == "__main__":
    main()
