import json
import os
import csv
from datetime import datetime

PRODUCT_FILE = "products.json"
SOURCE_FILE = "sources.json"
APPROVED_FILE = "approved_content.txt"

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_products():
    return load_json(PRODUCT_FILE, [])

def save_products(products):
    save_json(PRODUCT_FILE, products)

def next_id(products):
    return max([p.get("id", 0) for p in products], default=0) + 1

def add_product(products):
    print("\n--- ADD PRODUCT ---")

    name = input("Product name: ").strip()
    price = input("Price: ").strip()
    category = input("Category: ").strip()
    source = input("Source: ").strip()
    url = input("Product/Affiliate URL: ").strip()
    commission = input("Commission (%): ").strip()

    if not name:
        print("Product name is required.")
        return

    # Duplicate check
    for product in products:
        if (
            product.get("name", "").strip().lower() == name.lower()
            and str(product.get("price", "")).strip() == price
        ):
            print("Duplicate product already exists.")
            return

    product = {
        "id": next_id(products),
        "name": name,
        "price": price,
        "category": category,
        "source": source,
        "url": url,
        "commission": commission
    }

    products.append(product)
    save_products(products)

    print("Product added successfully.")
    print(f"Smart Score: {calculate_score(product)}/100")


def view_products(products):
    if not products:
        print("No products found.")
        return

    print("\n--- PRODUCTS ---")
    for p in products:
        print(
            f"{p['id']}. {p['name']} | "
            f"{p.get('category', '')} | "
            f"{p.get('price', '')} | "
            f"{p.get('score', 0)}/100"
        )

def search_products(products):
    query = input("Search: ").strip().lower()

    if not query:
        print("Please enter a search term.")
        return

    found = []

    for product in products:
        text = " ".join([
            str(product.get("name", "")),
            str(product.get("category", "")),
            str(product.get("source", ""))
        ]).lower()

        if query in text:
            found.append(product)

    print(f"\n--- SEARCH RESULTS ({len(found)}) ---")

    if not found:
        print("No products found.")
        return

    ranked = sorted(
        found,
        key=calculate_score,
        reverse=True
    )

    for i, product in enumerate(ranked, 1):
        score = calculate_score(product)

        print(
            f"{i}. {product.get('name', 'Unknown')} | "
            f"{product.get('category', 'N/A')} | "
            f"{product.get('price', 'N/A')} | {score}/100"
            + (f" | {product.get('source', '')}" if product.get('source') else "")
        )

    best = ranked[0]
    best_score = calculate_score(best)

    print("\n--- SMART RECOMMENDATION ---")
    print(f"Best Product: {best.get('name', 'Unknown')}")
    print(f"Price: {best.get('price', 'N/A')}")
    print(f"Category: {best.get('category', 'N/A')}")
    print(f"Score: {best_score}/100")

    if best_score >= 90:
        print("Recommendation: Excellent choice.")
    elif best_score >= 75:
        print("Recommendation: Very good choice.")
    elif best_score >= 60:
        print("Recommendation: Good choice.")
    else:
        print("Recommendation: Needs more evaluation.")


def calculate_score(product):
    score = 0

    name = str(product.get("name", "")).strip()
    category = str(product.get("category", "")).strip()
    source = str(product.get("source", "")).strip()

    try:
        price = float(str(product.get("price", "")).replace("BDT", "").strip())
    except:
        price = 0

    # Product information
    if name:
        score += 25
    if category:
        score += 15
    if source:
        score += 15

    # Price attractiveness
    if 300 <= price <= 800:
        score += 30
    elif 801 <= price <= 1500:
        score += 20
    elif price > 0:
        score += 10

    # Popular product keywords
    keywords = [
        "earbuds", "smart watch", "speaker",
        "power bank", "charger", "headphone",
        "phone", "mobile", "camera"
    ]

    if any(k in name.lower() for k in keywords):
        score += 15

    return min(score, 100)


def remove_duplicates(products):
    seen = set()
    unique = []

    for product in products:
        key = (
            str(product.get("name", "")).strip().lower(),
            str(product.get("price", "")).strip(),
            str(product.get("category", "")).strip()
        )

        if key not in seen:
            seen.add(key)
            unique.append(product)

    return unique


def top_products(products):
    print("\n--- TOP PRODUCTS ---")

    products[:] = remove_duplicates(products)
    save_products(products)

    ranked = sorted(
        products,
        key=calculate_score,
        reverse=True
    )

    for i, product in enumerate(ranked[:10], 1):
        score = calculate_score(product)
        print(
            f"{i}. {product.get('name', 'Unknown')} | "
            f"{product.get('category', 'N/A')} | "
            f"{product.get('price', 'N/A')} | {score}/100"
            + (f" | {product.get('source', '')}" if product.get('source') else "")
        )


def export_products_csv(products):
    import csv

    filename = input("Export file name [products_export.csv]: ").strip()
    if not filename:
        filename = "products_export.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name", "price", "category", "source", "url", "commission", "score"]
        )
        writer.writeheader()

        for product in products:
            writer.writerow({
                "id": product.get("id", ""),
                "name": product.get("name", ""),
                "price": product.get("price", ""),
                "category": product.get("category", ""),
                "source": product.get("source", ""),
                "url": product.get("url", ""),
                "commission": product.get("commission", ""),
                "score": calculate_score(product)
            })

    print(f"Exported {len(products)} products to {filename}")


def product_stats(products):
    print("\n--- PRODUCT STATISTICS ---")
    print(f"Total Products : {len(products)}")

    if not products:
        return

    scores = [calculate_score(p) for p in products]
    print(f"Average Score  : {sum(scores)/len(scores):.1f}/100")
    print(f"Best Score     : {max(scores)}/100")

    categories = {}
    for p in products:
        c = p.get("category", "Unknown")
        categories[c] = categories.get(c, 0) + 1

    print("\nCategories:")
    for category, count in sorted(categories.items()):
        print(f"- {category}: {count}")


def recommend_category(products):
    category = input("Category: ").strip().lower()

    found = [
        p for p in products
        if category in p.get("category", "").lower()
    ]

    if not found:
        print("No products found in this category.")
        return

    found.sort(key=calculate_score, reverse=True)

    print("\n--- CATEGORY RECOMMENDATIONS ---")
    for i, p in enumerate(found[:5], 1):
        print(
            f"{i}. {p.get('name','Unknown')} | "
            f"{p.get('price','N/A')} | "
            f"{calculate_score(p)}/100"
        )


def dashboard(products):
    print("\n================================")
    print("       SMART DASHBOARD")
    print("================================")

    total=len(products)
    print(f"Total Products : {total}")

    if not products:
        print("No products available.")
        return

    scores=[calculate_score(x) for x in products]
    print(f"Average Score  : {sum(scores)/len(scores):.1f}/100")
    print(f"Best Score     : {max(scores)}/100")

    ranked=sorted(products,key=calculate_score,reverse=True)
    best=ranked[0]

    print("\nBEST PRODUCT")
    print(f"Name     : {best.get('name','Unknown')}")
    print(f"Price    : {best.get('price','N/A')}")
    print(f"Category : {best.get('category','N/A')}")
    print(f"Score    : {calculate_score(best)}/100")

    print("\n================================")


def product_details(products):
    query = input("Product name or ID: ").strip().lower()

    found = []
    for product in products:
        if (
            query == str(product.get("id", "")).lower()
            or query in str(product.get("name", "")).lower()
        ):
            found.append(product)

    if not found:
        print("Product not found.")
        return

    for i, product in enumerate(found, 1):
        print("\n--- PRODUCT DETAILS ---")
        print(f"ID         : {product.get('id', 'N/A')}")
        print(f"Name       : {product.get('name', 'N/A')}")
        print(f"Price      : {product.get('price', 'N/A')}")
        print(f"Category   : {product.get('category', 'N/A')}")
        print(f"Source     : {product.get('source', 'N/A')}")
        print(f"URL        : {product.get('url', 'Not added')}")
        print(f"Commission : {product.get('commission', 'Not added')}%")
        print(f"Score      : {calculate_score(product)}/100")


def compare_products(products):
    print("\n--- SMART PRODUCT COMPARISON ---")
    q1 = input("First product name/ID: ").strip().lower()
    q2 = input("Second product name/ID: ").strip().lower()

    def find_one(query):
        for product in products:
            if (
                query == str(product.get("id", "")).lower()
                or query in str(product.get("name", "")).lower()
            ):
                return product
        return None

    p1 = find_one(q1)
    p2 = find_one(q2)

    if not p1 or not p2:
        print("One or both products were not found.")
        return

    s1 = calculate_score(p1)
    s2 = calculate_score(p2)

    print("\n--- COMPARISON RESULT ---")
    print(f"1. {p1.get('name')} | Price: {p1.get('price')} | Score: {s1}/100")
    print(f"2. {p2.get('name')} | Price: {p2.get('price')} | Score: {s2}/100")

    if s1 > s2:
        winner = p1
        score = s1
    elif s2 > s1:
        winner = p2
        score = s2
    else:
        winner = None
        score = s1

    print("\n--- SMART VERDICT ---")
    if winner:
        print(f"Recommended: {winner.get('name')}")
        print(f"Reason: Higher Smart Score ({score}/100)")
    else:
        print("Both products have the same Smart Score.")
        print("Compare price and product features before buying.")


def affiliate_recommendation(products):
    if not products:
        print("No products available.")
        return

    ranked = sorted(products, key=calculate_score, reverse=True)
    best = ranked[0]

    print("\n--- BEST AFFILIATE-READY PRODUCT ---")
    print(f"Product    : {best.get('name', 'Unknown')}")
    print(f"Price      : {best.get('price', 'N/A')}")
    print(f"Score      : {calculate_score(best)}/100")
    print(f"Source     : {best.get('source', 'Not added')}")
    print(f"URL        : {best.get('url', 'Affiliate link not added')}")
    print(f"Commission : {best.get('commission', 'Not added')}%")

    if best.get("url"):
        print("\nStatus: Ready for affiliate promotion.")
    else:
        print("\nStatus: Add an affiliate URL before promotion.")


def edit_product(products):
    query = input("Product name or ID to edit: ").strip().lower()

    target = None
    for product in products:
        if (
            query == str(product.get("id", "")).lower()
            or query in str(product.get("name", "")).lower()
        ):
            target = product
            break

    if not target:
        print("Product not found.")
        return

    print("\nLeave blank to keep current value.")

    name = input(f"Name [{target.get('name', '')}]: ").strip()
    price = input(f"Price [{target.get('price', '')}]: ").strip()
    category = input(f"Category [{target.get('category', '')}]: ").strip()
    source = input(f"Source [{target.get('source', '')}]: ").strip()
    url = input(f"URL [{target.get('url', '')}]: ").strip()
    commission = input(f"Commission [{target.get('commission', '')}]: ").strip()

    if name:
        target["name"] = name
    if price:
        target["price"] = price
    if category:
        target["category"] = category
    if source:
        target["source"] = source
    if url:
        target["url"] = url
    if commission:
        target["commission"] = commission

    save_products(products)
    print("Product updated successfully.")
    print(f"New Smart Score: {calculate_score(target)}/100")


def marketing_text_generator(products):
    query = input("Product name or ID: ").strip().lower()

    product = None
    for p in products:
        if (
            query == str(p.get("id", "")).lower()
            or query in str(p.get("name", "")).lower()
        ):
            product = p
            break

    if not product:
        print("Product not found.")
        return

    score = calculate_score(product)
    name = product.get("name", "this product")
    price = product.get("price", "N/A")
    category = product.get("category", "")
    url = product.get("url", "")

    print("\n========== MARKETING TEXT ==========")
    print(f"🔥 {name} এখন আপনার জন্য একটি দারুণ পছন্দ!")
    print(f"💰 Price: {price} BDT")
    print(f"📦 Category: {category}")
    print(f"⭐ Smart Score: {score}/100")

    if score >= 90:
        print("✅ আমাদের Smart Product Finder অনুযায়ী এটি একটি Strong Recommendation!")

    if url:
        print(f"🔗 Buy Here: {url}")
    else:
        print("🔗 Buy Link: Add affiliate/product URL first")

    print("\n#SmartShopping #BestProduct #ProductFinder")
    print("====================================")


def show_menu():
    print("""
================================
 SMART PRODUCT FINDER BD V6 🤖
================================
1. Add Product
2. View Products
3. Search Products
4. Top Products
5. Import Products from CSV
6. Export Products to CSV
7. Product Statistics
8. Category Recommendation
9. Dashboard
10. Product Details
11. Compare Products
12. Best Affiliate Product
13. Edit Product
14. Generate Marketing Text
0. Exit
================================
""")


def main():
    products = get_products()

    while True:
        show_menu()
        choice = input("Choose Option: ").strip()

        if choice == "1":
            add_product(products)
        elif choice == "2":
            view_products(products)
        elif choice == "3":
            search_products(products)
        elif choice == "4":
            top_products(products)
        elif choice == "5":
            import_products_from_csv(products)
        elif choice == "6":
            export_products_csv(products)
        elif choice == "7":
            product_stats(products)
        elif choice == "8":
            recommend_category(products)
        elif choice == "9":
            dashboard(products)
        elif choice == "10":
            product_details(products)
        elif choice == "11":
            compare_products(products)
        elif choice == "12":
            affiliate_recommendation(products)
        elif choice == "13":
            edit_product(products)
        elif choice == "14":
            marketing_text_generator(products)
        elif choice == "0":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
