import json
from pathlib import Path

INPUT = Path("products.json")
OUTPUT = Path("product_recommendations.json")


def num(v, default=0):
    try:
        return float(v)
    except:
        return default


def evidence_score(p):
    fields = [
        "name",
        "description",
        "image",
        "url",
        "category",
        "price",
        "item_id",
        "seller_sku",
        "seller_id",
    ]
    return sum(bool(p.get(x)) for x in fields)


def source_score(p):
    source = str(p.get("source") or "").lower()

    if source == "daraz public":
        return 20
    if "daraz" in source:
        return 18
    return 5


def price_score(price):
    price = num(price)

    if price <= 0:
        return 0
    if price <= 300:
        return 20
    if price <= 500:
        return 18
    if price <= 800:
        return 15
    if price <= 1200:
        return 12
    if price <= 1800:
        return 9
    if price <= 2500:
        return 6
    return 3


def title_score(name):
    n = str(name or "").strip()

    if not n:
        return 0
    if len(n) >= 40:
        return 10
    if len(n) >= 20:
        return 8
    if len(n) >= 10:
        return 6
    return 3


def research_score(p):
    # Real research score থাকলে সেটি ব্যবহার করবে।
    value = p.get("research_score")

    if value is not None:
        try:
            return min(25, max(0, float(value)))
        except:
            pass

    # বর্তমানে বাস্তব Daraz Public data-কে baseline research value।
    if str(p.get("source") or "").lower() == "daraz public":
        return 25

    # Demo / incomplete source
    return 10


def calculate(p):
    info = evidence_score(p)

    # Evidence 9/9 -> 20
    # Evidence 8/9 -> 18
    # Evidence 7/9 -> 16
    # এভাবে নামবে।
    data_score = round((info / 9) * 20)

    source = source_score(p)
    price = price_score(p.get("price"))
    title = title_score(p.get("name"))
    research = research_score(p)

    total = round(research + data_score + source + price + title)

    return total, {
        "research": research,
        "data_completeness": data_score,
        "source": source,
        "price": price,
        "title": title,
        "evidence_fields": info,
    }


def main():
    if not INPUT.exists():
        print("ERROR: products.json not found")
        return

    data = json.loads(INPUT.read_text(encoding="utf-8"))

    ranked = []

    for p in data:
        score, breakdown = calculate(p)

        item = dict(p)
        item["recommendation_score"] = score
        item["score_breakdown"] = breakdown

        ranked.append(item)

    ranked.sort(
        key=lambda x: (
            float(x.get("recommendation_score", 0)),
            int(x.get("score_breakdown", {}).get("evidence_fields", 0)),
            float(x.get("price", 0) or 0) * -1,
        ),
        reverse=True,
    )

    OUTPUT.write_text(
        json.dumps(ranked, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print("FINAL RECOMMENDATION ENGINE V4")
    print("=" * 60)
    print("TOTAL PRODUCTS:", len(ranked))
    print()

    for i, p in enumerate(ranked[:15], 1):
        b = p["score_breakdown"]

        print(
            f"#{i:02} | SCORE {p['recommendation_score']} | "
            f"৳{p.get('price')} | "
            f"{str(p.get('name') or '')[:75]}"
        )

        print(
            f"     research={b['research']} "
            f"info={b['data_completeness']} "
            f"source={b['source']} "
            f"price={b['price']} "
            f"title={b['title']} "
            f"evidence={b['evidence_fields']}/9"
        )

    print()
    print("Saved:", OUTPUT)
    print("V4 ENGINE: PASS")


if __name__ == "__main__":
    main()
