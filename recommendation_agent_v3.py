import json
from pathlib import Path
import re

INPUT = Path("products.json")
OUTPUT = Path("product_recommendations.json")

def num(v, default=0):
    try:
        return float(v)
    except:
        return default

def text(v):
    return str(v or "").strip()

def score_product(p):
    name = text(p.get("name"))
    desc = text(p.get("description"))
    category = text(p.get("category"))
    image = text(p.get("image"))
    url = text(p.get("url"))
    source = text(p.get("source")).lower()
    price = num(p.get("price"))

    # 1. Research/data quality: 0-25
    research = num(p.get("research_score"), 0)

    if research > 0:
        research_part = min(25, research * 0.25)
    else:
        # Public/imported product হলে available evidence দিয়ে score
        evidence = 0
        evidence += 5 if name else 0
        evidence += 5 if desc else 0
        evidence += 5 if category else 0
        evidence += 5 if image else 0
        evidence += 5 if url else 0
        research_part = evidence

    # 2. Product information quality: 0-20
    info = 0
    if name and len(name) >= 15:
        info += 5
    if desc and len(desc) >= 40:
        info += 5
    if category:
        info += 4
    if image:
        info += 3
    if url:
        info += 3

    # 3. Source reliability: 0-15
    if "daraz" in source or "daraz.com.bd" in url.lower():
        source_part = 15
    elif source:
        source_part = 10
    else:
        source_part = 5

    # 4. Price score: 0-20
    if price <= 0:
        price_part = 0
    elif price <= 300:
        price_part = 20
    elif price <= 500:
        price_part = 17
    elif price <= 800:
        price_part = 14
    elif price <= 1200:
        price_part = 11
    elif price <= 2000:
        price_part = 8
    else:
        price_part = 5

    # 5. Product title quality / specificity: 0-10
    title_part = 0

    if name:
        words = re.findall(r"\w+", name, flags=re.UNICODE)

        if len(words) >= 3:
            title_part += 3
        if len(words) >= 6:
            title_part += 2
        if any(x in name.lower() for x in [
            "100g", "200g", "300", "500g", "ml",
            "25w", "7 feet", "10000mah", "2200 sprays"
        ]):
            title_part += 2
        if category:
            title_part += 2
        if image:
            title_part += 1

    title_part = min(10, title_part)

    total = round(
        research_part +
        info +
        source_part +
        price_part +
        title_part,
        2
    )

    p["recommendation_score"] = total

    p["score_breakdown"] = {
        "research": round(research_part, 2),
        "information": info,
        "source": source_part,
        "price": price_part,
        "title_quality": title_part
    }

    return p


def main():
    if not INPUT.exists():
        print("ERROR: products.json পাওয়া যায়নি")
        return

    products = json.loads(
        INPUT.read_text(encoding="utf-8")
    )

    ranked = [score_product(dict(p)) for p in products]

    def sort_key(x):
        try:
            score = float(x.get("recommendation_score", 0))
        except:
            score = 0.0

        try:
            price = float(str(x.get("price", 0)).replace(",", ""))
        except:
            price = 0.0

        return (score, -price)

    ranked.sort(key=sort_key, reverse=True)

    OUTPUT.write_text(
        json.dumps(
            ranked,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("=" * 60)
    print("FINAL RECOMMENDATION ENGINE V3")
    print("=" * 60)
    print("TOTAL PRODUCTS:", len(ranked))
    print()

    for i, p in enumerate(ranked[:15], 1):
        b = p.get("score_breakdown", {})
        print(
            f"#{i} | SCORE {p['recommendation_score']} | "
            f"৳{p.get('price')} | "
            f"{p.get('name','')[:90]}"
        )
        print(
            f"    research={b.get('research')} "
            f"info={b.get('information')} "
            f"source={b.get('source')} "
            f"price={b.get('price')} "
            f"title={b.get('title_quality')}"
        )

    print()
    print("Saved:", OUTPUT)
    print("V3 ENGINE: PASS")


if __name__ == "__main__":
    main()
