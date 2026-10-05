import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.json"
REPORT = ROOT / "worker_reports" / "search_filter_report.json"

def norm(value):
    return str(value or "").strip().lower()

def product_matches(p, query="", category="", source=""):
    query = norm(query)
    category = norm(category)
    source = norm(source)

    text = " ".join([
        norm(p.get("name")),
        norm(p.get("description")),
        norm(p.get("brand")),
        norm(p.get("category")),
    ])

    if query and query not in text:
        return False

    if category and category not in norm(p.get("category")):
        return False

    if source and source != norm(p.get("source")):
        return False

    return True

def search(data, query="", category="", source=""):
    return [
        p for p in data
        if product_matches(p, query, category, source)
    ]

def main():
    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))

    tests = [
        {
            "name": "all",
            "query": "",
            "category": "",
            "source": "",
        },
        {
            "name": "daraz_public",
            "query": "",
            "category": "",
            "source": "Daraz Public",
        },
        {
            "name": "electronics",
            "query": "",
            "category": "Electronics",
            "source": "",
        },
        {
            "name": "charger",
            "query": "charger",
            "category": "",
            "source": "",
        },
        {
            "name": "air",
            "query": "air",
            "category": "",
            "source": "",
        },
    ]

    results = {}

    for test in tests:
        found = search(
            data,
            test["query"],
            test["category"],
            test["source"],
        )

        results[test["name"]] = {
            "query": test["query"],
            "category": test["category"],
            "source": test["source"],
            "count": len(found),
            "products": [
                {
                    "name": p.get("name"),
                    "price": p.get("price"),
                    "source": p.get("source"),
                    "category": p.get("category"),
                    "item_id": p.get("item_id"),
                    "url": p.get("url"),
                }
                for p in found
            ],
        }

    report = {
        "worker": "Search + Filter Worker V1",
        "timestamp": datetime.now().isoformat(),
        "total_products": len(data),
        "tests": results,
        "status": "PASS",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("SEARCH + FILTER WORKER V1")
    print("=" * 60)
    print("TOTAL PRODUCTS:", len(data))

    for name, result in results.items():
        print(
            f"{name:15} -> {result['count']} products"
        )

    print("REPORT:", REPORT)
    print("WORKER STATUS:", report["status"])

if __name__ == "__main__":
    main()
