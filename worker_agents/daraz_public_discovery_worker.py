import json, requests
from pathlib import Path

URL = "https://www.daraz.com.bd/catalog/"
REPORT = Path("worker_reports/daraz_public_discovery_report.json")

def search(keyword, limit=10):
    r = requests.get(
        URL,
        params={"q": keyword, "from": "input", "ajax": "true", "page": "1"},
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.daraz.com.bd/",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()

    items = (data.get("mods") or {}).get("listItems") or []
    total = (data.get("mainInfo") or {}).get("totalResults")

    products = []
    seen = set()

    for x in items:
        if not isinstance(x, dict):
            continue

        item_id = x.get("itemId") or x.get("item_id") or x.get("id")
        name = x.get("name") or x.get("title") or x.get("itemTitle")
        price = x.get("price") or x.get("salePrice") or x.get("priceShow")
        url = x.get("productUrl") or x.get("itemUrl") or x.get("url")

        if isinstance(url, str):
            url = url.strip()
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = "https://www.daraz.com.bd" + url
            elif url.startswith("www.daraz.com.bd/"):
                url = "https://" + url

        key = str(item_id or url or name or "")

        if not key or key in seen:
            continue

        seen.add(key)

        products.append({
            "item_id": item_id,
            "name": name,
            "price": price,
            "url": url,
        })

        if len(products) >= limit:
            break

    return {
        "keyword": keyword,
        "total_results": total,
        "raw_items": len(items),
        "discovered": len(products),
        "products": products,
    }


def main():
    keywords = ["shampoo", "charger", "earbuds"]
    results = []

    print("DARAZ PUBLIC DISCOVERY WORKER")
    print("=" * 50)

    for keyword in keywords:
        print(f"\nSEARCH: {keyword}")

        try:
            result = search(keyword)
            results.append(result)

            print("Total:", result["total_results"])
            print("Found:", result["discovered"])

            for p in result["products"]:
                print(
                    "-",
                    p["name"],
                    "|",
                    p["price"],
                    "|",
                    p["item_id"],
                )

        except Exception as e:
            print("ERROR:", e)

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    REPORT.write_text(
        json.dumps(
            {
                "worker": "daraz_public_discovery_worker",
                "mode": "public_search_discovery_only",
                "production_modified": False,
                "git_modified": False,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nREPORT:", REPORT)
    print("Production data modified: NO")
    print("Git modified: NO")


if __name__ == "__main__":
    main()
