import json
import os
import csv
from datetime import datetime

DATA_FILE = "products.json"


def load_products():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_products(products):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def get_next_id(products):
    if not products:
        return 1
    return max(p.get("id", 0) for p in products) + 1


def safe_score(value):
    try:
        value = int(value)
        return max(1, min(value, 10))
    except:
        return 5


def calculate_score(product):
    problem = safe_score(product.get("problem_score", 5))
    demand = safe_score(product.get("demand_score", 5))
    content = safe_score(product.get("content_score", 5))

    score = problem * 4 + demand * 3 + content * 3
    return min(score, 100)


def get_link(product):
    return product.get(
        "affiliate",
        product.get("affiliate_link", "Not available")
    )


def is_duplicate(products, name):
    return any(
        p.get("name", "").lower().strip()
        == name.lower().strip()
        for p in products
    )


def add_product(products):
    print("\n--- ADD PRODUCT ---")

    name = input("Product Name: ").strip()

    if is_duplicate(products, name):
        print("⚠️ This product already exists!")
        return

    category = input("Category: ").strip()
    price = input("Price: ").strip()
    affiliate = input("Affiliate Link: ").strip()

    problem = safe_score(input("Problem Score (1-10): "))
    demand = safe_score(input("Demand Score (1-10): "))
    content = safe_score(input("Content Score (1-10): "))

    product = {
        "id": get_next_id(products),
        "name": name,
        "category": category,
        "price": price,
        "affiliate": affiliate,
        "problem_score": problem,
        "demand_score": demand,
        "content_score": content,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    product["score"] = calculate_score(product)

    products.append(product)
    save_products(products)

    print("\n✅ Product Added!")
    print(f"⭐ Score: {product['score']}/100")


def import_csv(products):
    filename = input("\nCSV filename: ").strip()

    if not os.path.exists(filename):
        print("❌ File not found.")
        return

    added = 0
    skipped = 0

    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                name = row.get("name", "").strip()

                if not name or is_duplicate(products, name):
                    skipped += 1
                    continue

                product = {
                    "id": get_next_id(products),
                    "name": name,
                    "category": row.get("category", "Other"),
                    "price": row.get("price", ""),
                    "affiliate": row.get(
                        "affiliate",
                        row.get("affiliate_link", "")
                    ),
                    "problem_score": safe_score(
                        row.get("problem_score", 5)
                    ),
                    "demand_score": safe_score(
                        row.get("demand_score", 5)
                    ),
                    "content_score": safe_score(
                        row.get("content_score", 5)
                    ),
                    "created": datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    )
                }

                product["score"] = calculate_score(product)
                products.append(product)
                added += 1

        save_products(products)

        print(f"\n✅ Added: {added}")
        print(f"⚠️ Skipped: {skipped}")

    except Exception as e:
        print("❌ Import error:", e)


def view_products(products):
    if not products:
        print("\nNo products found.")
        return

    print("\n--- ALL PRODUCTS ---")

    for p in products:
        print(
            f"\nID: {p['id']}"
            f"\nName: {p['name']}"
            f"\nCategory: {p.get('category', '')}"
            f"\nPrice: {p.get('price', '')}"
            f"\nScore: {p.get('score', 0)}/100"
        )


def search_products(products):
    keyword = input("\nSearch: ").lower().strip()

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
            f"{p.get('category', '')} | "
            f"Score: {p.get('score', 0)}"
        )


def category_filter(products):
    category = input("\nEnter Category: ").lower().strip()

    results = [
        p for p in products
        if p.get("category", "").lower() == category
    ]

    if not results:
        print("No products found in this category.")
        return

    print(f"\n--- {category.upper()} ---")

    for p in results:
        print(
            f"{p['id']}. {p['name']} | "
            f"Score: {p.get('score', 0)}/100"
        )


def best_products(products):
    if not products:
        print("\nNo products found.")
        return

    ranked = sorted(
        products,
        key=lambda x: x.get("score", 0),
        reverse=True
    )

    print("\n🏆 TOP PRODUCTS")

    for i, p in enumerate(ranked[:10], 1):
        print(
            f"{i}. {p['name']} "
            f"| Score: {p.get('score', 0)}/100"
        )


def find_product(products, product_id):
    for p in products:
        if p.get("id") == product_id:
            return p
    return None


def generate_content(products):
    try:
        product_id = int(input("\nProduct ID: "))
    except:
        print("Invalid ID.")
        return

    p = find_product(products, product_id)

    if not p:
        print("Product not found.")
        return

    name = p["name"]
    price = p.get("price", "")
    link = get_link(p)

    content = f"""
SMART PRODUCT CONTENT
=====================

PRODUCT: {name}
PRICE: {price}

FACEBOOK POST
-------------
🔥 আপনার দৈনন্দিন জীবনে কাজে লাগতে পারে {name}!

✨ সহজ ব্যবহার
✨ প্রয়োজনীয় ও সুবিধাজনক
✨ দৈনন্দিন কাজে সহায়ক

💰 মূল্য: {price}

👉 বিস্তারিত দেখতে:
{link}


YOUTUBE TITLE
-------------
{name} কি সত্যিই কাজে লাগে? | Honest Review


SHORTS SCRIPT
-------------
আপনি কি এমন একটি দরকারি Product খুঁজছেন
যেটা আপনার দৈনন্দিন কাজ সহজ করতে পারে?

আজকে দেখুন — {name}।

বিস্তারিত জানতে নিচের লিংক দেখুন।


HASHTAGS
--------
#{name.replace(" ", "")}
#ProductReview
#UsefulProducts
#OnlineShopping
#Bangladesh
"""

    print(content)

    save = input(
        "\nSave this content? (y/n): "
    ).lower().strip()

    if save == "y":
        filename = f"content_{p['id']}.txt"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(content)

        print(f"✅ Saved: {filename}")


def export_products(products):
    filename = "product_export_v3.txt"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        for p in products:
            f.write(
                f"ID: {p['id']}\n"
                f"Name: {p['name']}\n"
                f"Category: {p.get('category', '')}\n"
                f"Price: {p.get('price', '')}\n"
                f"Link: {get_link(p)}\n"
                f"Score: {p.get('score', 0)}/100\n"
                + "-" * 35 + "\n"
            )

    print(f"✅ Exported: {filename}")


def statistics(products):
    if not products:
        print("\nNo products found.")
        return

    total = len(products)

    average = sum(
        p.get("score", 0)
        for p in products
    ) / total

    best = max(
        products,
        key=lambda x: x.get("score", 0)
    )

    categories = set(
        p.get("category", "")
        for p in products
    )

    print("\n--- STATISTICS ---")
    print(f"Total Products: {total}")
    print(f"Categories: {len(categories)}")
    print(f"Average Score: {average:.1f}/100")
    print(
        f"Best Product: {best['name']} "
        f"({best.get('score', 0)}/100)"
    )


def show_menu():
    print("""
========================================
 SMART PRODUCT FINDER BD 🤖🛍️ V3
========================================

1. Add Product
2. Import Products from CSV
3. View Products
4. Search Products
5. Category Filter
6. Top Products
7. Generate Marketing Content
8. Export Product List
9. Statistics

0. Exit
========================================
""")


def main():
    products = load_products()

    while True:
        show_menu()

        choice = input("Choose Option: ").strip()

        if choice == "1":
            add_product(products)

        elif choice == "2":
            import_csv(products)

        elif choice == "3":
            view_products(products)

        elif choice == "4":
            search_products(products)

        elif choice == "5":
            category_filter(products)

        elif choice == "6":
            best_products(products)

        elif choice == "7":
            generate_content(products)

        elif choice == "8":
            export_products(products)

        elif choice == "9":
            statistics(products)

        elif choice == "0":
            print("Goodbye! 👋")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
