import json

products = json.load(open("products.json", encoding="utf-8"))
output = []

for product in products:
    item = product.copy()
    name = item.get("name", "Unknown Product")
    category = item.get("category", "General")
    price = item.get("price", "N/A")

    description = item.get("description") or item.get("details")
    link = item.get("link") or item.get("url")

    missing = []

    if not description:
        missing.append("Description")
        item["draft_description"] = (
            f"{name} একটি {category} ক্যাটাগরির প্রোডাক্ট। "
            f"বর্তমান মূল্য: {price} BDT। "
            "কেনার আগে বিস্তারিত তথ্য ও আসল সোর্স যাচাই করুন।"
        )

    if not link:
        missing.append("Link")

    item["research_score"] = 100 - len(missing) * 15
    item["link_status"] = "READY" if link else "LINK NEEDED"
    item["missing_data"] = missing

    output.append(item)

with open("products_enriched.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("=" * 50)
print("PRODUCT RESEARCH AGENT V3 SUCCESS")
print("=" * 50)
print("Total Products:", len(output))
print("Saved: products_enriched.json")
print("Original products.json was not changed")
