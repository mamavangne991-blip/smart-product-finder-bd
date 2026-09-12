import json
from datetime import datetime

PRODUCT_FILE = "products.json"

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

def check_product(product):
    name = product.get("name") or product.get("title") or "Unknown Product"
    price = product.get("price") or product.get("current_price")
    category = product.get("category")
    description = product.get("description") or product.get("details")
    source = product.get("source") or product.get("source_name")
    link = product.get("link") or product.get("url")

    missing = []

    if not price:
        missing.append("Price")
    if not category:
        missing.append("Category")
    if not description:
        missing.append("Description")
    if not source:
        missing.append("Source")
    if not link:
        missing.append("Link")

    score = 100 - (len(missing) * 15)

    return {
        "name": name,
        "score": max(0, score),
        "missing": missing
    }

def main():
    products = load_products()

    print("=" * 50)
    print("SMART PRODUCT FINDER BD")
    print("PRODUCT RESEARCH AGENT V1")
    print("=" * 50)

    if not products:
        print("কোনো Product পাওয়া যায়নি")
        return

    print(f"Total Products: {len(products)}")
    print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    for product in products:
        result = check_product(product)

        print(f"Product: {result['name']}")
        print(f"Research Score: {result['score']}/100")

        if result["missing"]:
            print("Missing:", ", ".join(result["missing"]))
        else:
            print("Status: READY")

        print("-" * 50)

if __name__ == "__main__":
    main()
