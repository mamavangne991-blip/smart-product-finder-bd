import json

INPUT_FILE = "products_enriched.json"
OUTPUT_FILE = "product_recommendations.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

recommendations = []

for product in products:
    item = product.copy()

    price = item.get("price", 0)
    research_score = item.get("research_score", 0)

    try:
        price = float(price)
    except (ValueError, TypeError):
        price = 0

    if price > 0:
        price_bonus = min(20, 2000 / price * 10)
    else:
        price_bonus = 0

    recommendation_score = round(
        research_score + price_bonus,
        2
    )

    item["recommendation_score"] = recommendation_score
    recommendations.append(item)

recommendations.sort(
    key=lambda x: x["recommendation_score"],
    reverse=True
)

for rank, product in enumerate(recommendations, start=1):
    product["recommendation_rank"] = rank

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        recommendations,
        f,
        ensure_ascii=False,
        indent=2
    )

print("=" * 50)
print("RECOMMENDATION AGENT V1 SUCCESS")
print("=" * 50)
print("Total Products:", len(recommendations))
print()

print("TOP 5 RECOMMENDATIONS")

for product in recommendations[:5]:
    name = product.get("name", "Unknown Product")
    score = product["recommendation_score"]
    rank = product["recommendation_rank"]

    print(f"#{rank} {name} | Score: {score}")

print()
print("Saved:", OUTPUT_FILE)
