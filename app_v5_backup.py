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
    name = input("Product Name: ").strip()

    if any(p.get("name", "").lower() == name.lower() for p in products):
        print("⚠️ Product already exists!")
        return

    category = input("Category: ").strip()
    price = input("Price: ").strip()
    affiliate = input("Affiliate Link: ").strip()

    try:
        score = int(input("Score (1-100): "))
        score = max(1, min(score, 100))
    except:
        score = 50

    products.append({
        "id": next_id(products),
        "name": name,
        "category": category,
        "price": price,
        "affiliate": affiliate,
        "score": score,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    save_products(products)
    print("✅ Product saved!")

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
    keyword = input("Search: ").lower().strip()

    results = [
        p for p in products
        if keyword in p.get("name", "").lower()
        or keyword in p.get("category", "").lower()
    ]

    if not results:
        print("No matching products.")
        return

    for p in results:
        print(
            f"{p['id']}. {p['name']} | "
            f"{p.get('score', 0)}/100"
        )

def calculate_score(product):
    score = 0

    try:
        price = float(str(product.get("price", "")).replace("BDT", "").strip())
    except:
        price = 0

    if price > 0:
        score += 30

    if product.get("name"):
        score += 30

    if product.get("category"):
        score += 20

    if product.get("source"):
        score += 20

    return min(score, 100)


def top_products(products):
    print("\n--- TOP PRODUCTS ---")

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
