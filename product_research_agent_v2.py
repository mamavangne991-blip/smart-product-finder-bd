import json
from datetime import datetime

PRODUCT_FILE = "products.json"
REPORT_FILE = "product_research_report.json"

def load_products():
    try:
        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("products.json পাওয়া যায়নি")
        return []
    except json.JSONDecodeError:
        print("products.json-এর JSON format সমস্যা আছে")
        return []

def make_description(product):
    name = product.get("name") or product.get("title") or "এই প্রোডাক্ট"
    category = product.get("category") or "General"
    price = product.get("price") or "দাম জানতে যোগাযোগ করুন"

    return (
        f"{name} একটি {category} ক্যাটাগরির প্রোডাক্ট। "
        f"বর্তমান মূল্য: {price} BDT। "
        f"কেনার আগে প্রোডাক্টের বিস্তারিত তথ্য ও আসল সোর্স যাচাই করুন।"
    )

def check_product(product):
    name = product.get("name") or product.get("title") or "Unknown Product"
    description = product.get("description") or product.get("details")
    link = product.get("link") or product.get("url") or product.get("affiliate_link")

    missing = []
    draft_description = None

    if not description:
        missing.append("Description")
        draft_description = make_description(product)

    if not link:
        missing.append("Link")

    score = 100 - (len(missing) * 15)

    return {
        "name": name,
        "research_score": max(0, score),
        "missing": missing,
        "draft_description": draft_description,
        "link_status": "READY" if link else "LINK NEEDED"
    }

def main():
    products = load_products()

    print("=" * 55)
    print("SMART PRODUCT FINDER BD")
    print("PRODUCT RESEARCH AGENT V2")
    print("=" * 55)

    if not products:
        print("কোনো Product পাওয়া যায়নি")
        return

    results = []

    for product in products:
        result = check_product(product)
        results.append(result)

        print(f"\nProduct: {result['name']}")
        print(f"Research Score: {result['research_score']}/100")

        if result["missing"]:
            print("Missing:", ", ".join(result["missing"]))

        print("Link Status:", result["link_status"])

        if result["draft_description"]:
            print("Draft Description:")
            print(result["draft_description"])

        print("-" * 55)

    report = {
        "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_products": len(products),
        "results": results
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nReport saved:", REPORT_FILE)
    print("=" * 55)

if __name__ == "__main__":
    main()


