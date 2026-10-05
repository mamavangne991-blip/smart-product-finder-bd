import json
from pathlib import Path

INPUT = Path("products.json")
OUTPUT = Path("product_recommendations.json")

def num(v, default=0):
    try:
        return float(v)
    except:
        return default

def score_product(p):
    research = num(p.get("research_score"), 50)
    price = num(p.get("price"))

    # Research quality: 0-50
    research_part = min(50, max(0, research * 0.5))

    # Data completeness: 0-20
    fields = [
        p.get("name"),
        p.get("price"),
        p.get("category"),
        p.get("description"),
        p.get("image"),
        p.get("url"),
    ]
    completeness = (sum(bool(x) for x in fields) / len(fields)) * 20

    # Source quality: 0-15
    source = str(p.get("source", "")).lower()
    if "daraz" in source:
        source_part = 15
    elif source:
        source_part = 10
    else:
        source_part = 5

    # Price reasonableness: 0-15
    if price <= 0:
        price_part = 0
    elif price <= 300:
        price_part = 15
    elif price <= 500:
        price_part = 13
    elif price <= 1000:
        price_part = 10
    elif price <= 2000:
        price_part = 7
    else:
        price_part = 4

    total = round(
        research_part +
        completeness +
        source_part +
        price_part,
        2
    )

    p["recommendation_score"] = total
    p["score_breakdown"] = {
        "research": round(research_part, 2),
        "data_completeness": round(completeness, 2),
        "source": source_part,
        "price": price_part
    }

    return p

def main():
    if not INPUT.exists():
        print("ERROR: products.json পাওয়া যায়নি")
        return

    products = json.loads(INPUT.read_text(encoding="utf-8"))

    ranked = [score_product(dict(p)) for p in products]
    ranked.sort(
        key=lambda x: x.get("recommendation_score", 0),
        reverse=True
    )

    OUTPUT.write_text(
        json.dumps(ranked, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 60)
    print("RECOMMENDATION ENGINE V2")
    print("=" * 60)
    print("TOTAL PRODUCTS:", len(ranked))
    print()

    for i, p in enumerate(ranked[:15], 1):
        print(
            f"#{i} | SCORE {p['recommendation_score']} | "
            f"৳{p.get('price')} | "
            f"{p.get('name','')[:100]}"
        )

    print()
    print("Saved:", OUTPUT)
    print("V2 ENGINE: PASS")

if __name__ == "__main__":
    main()
