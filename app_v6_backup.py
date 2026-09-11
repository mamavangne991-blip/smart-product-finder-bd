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
        "source": source
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
        )


def show_menu():
    print("""
================================
 SMART PRODUCT FINDER BD V5 🤖
================================
1. Add Product
2. View Products
3. Search Products
4. Top Products
5. Import Products from CSV
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
        elif choice == "0":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
