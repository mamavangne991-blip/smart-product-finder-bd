import json
import os
from datetime import datetime

DATA_FILE = "products.json"
EXPORT_FILE = "product_export.txt"


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


def calculate_score(product):
    problem = int(product.get("problem_score", 0))
    demand = int(product.get("demand_score", 0))
    content = int(product.get("content_score", 0))

    score = (problem * 4) + (demand * 3) + (content * 3)
    return min(score, 100)


def safe_number(text):
    while True:
        try:
            value = int(input(text))
            if 1 <= value <= 10:
                return value
            print("Please enter a number from 1 to 10.")
        except ValueError:
            print("Invalid number. Try again.")


def add_product(products):
    print("\n--- ADD PRODUCT ---")

    name = input("Product Name: ").strip()
    category = input("Category: ").strip()
    price = input("Price: ").strip()
    affiliate = input("Affiliate Link: ").strip()

    duplicate = any(
        p["name"].lower() == name.lower()
        for p in products
    )

    if duplicate:
        print("\n⚠️ This product already exists!")
        return

    problem = safe_number("Problem Solving Score (1-10): ")
    demand = safe_number("Demand Score (1-10): ")
    content = safe_number("Content Potential Score (1-10): ")

    product = {
        "id": len(products) + 1,
        "name": name,
        "category": category,
        "price": price,
        "affiliate": affiliate,
        "problem_score": problem,
        "demand_score": demand,
        "content_score": content,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    product["score"] = calculate_score(product)

    products.append(product)
    save_products(products)

    print("\n✅ Product Added!")
    print(f"⭐ Score: {product['score']}/100")


def view_products(products):
    if not products:
        print("\nNo products found.")
        return

    print("\n--- ALL PRODUCTS ---")

    for p in products:
        print(
            f"\nID: {p['id']}"
            f"\nName: {p['name']}"
            f"\nCategory: {p['category']}"
            f"\nPrice: {p['price']}"
            f"\nScore: {p['score']}/100"
        )


def search_products(products):
    keyword = input("\nSearch keyword: ").lower().strip()

    results = [
        p for p in products
        if keyword in p["name"].lower()
        or keyword in p["category"].lower()
    ]

    if not results:
        print("No matching products found.")
        return

    print("\n--- SEARCH RESULTS ---")

    for p in results:
        print(f"{p['id']}. {p['name']} | Score: {p['score']}/100")


def best_products(products):
    if not products:
        print("\nNo products found.")
        return

    ranked = sorted(
        products,
        key=lambda x: x["score"],
        reverse=True
    )

    print("\n🏆 BEST PRODUCTS")

    for i, p in enumerate(ranked[:10], start=1):
        print(
            f"{i}. {p['name']}"
            f" | Score: {p['score']}/100"
        )


def find_product(products, product_id):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


def generate_marketing_content(products):
    if not products:
        print("\nNo products found.")
        return

    try:
        product_id = int(input("\nEnter Product ID: "))
    except ValueError:
        print("Invalid Product ID.")
        return

    p = find_product(products, product_id)

    if not p:
        print("Product not found.")
        return

    name = p["name"]
    price = p["price"]

    print("\n--- MARKETING CONTENT ---")

    print("\n📘 FACEBOOK POST:")
    print(
        f"🔥 নতুন {name} এখন পাওয়া যাচ্ছে!\n"
        f"💰 Price: {price}\n"
        f"✅ আপনার দৈনন্দিন কাজে দারুণ উপকারী।\n"
        f"👉 বিস্তারিত জানতে বা অর্ডার করতে ক্লিক করুন:\n"
        f"{p.get('affiliate', p.get('affiliate_link', 'Not available'))}"
    )

    print("\n🎬 YOUTUBE TITLE:")
    print(f"{name} Review | কেন এই Product আপনার দরকার?")

    print("\n📱 SHORTS SCRIPT:")
    print(
        f"আপনি কি {name} খুঁজছেন?\n"
        f"এই Product আপনার দৈনন্দিন কাজ সহজ করতে পারে।\n"
        f"আজই বিস্তারিত দেখে নিন!"
    )

    print("\n# HASHTAGS:")
    print(
        f"#{name.replace(' ', '')} "
        "#ProductReview #BestProduct #Shopping"
    )


def export_products(products):
    if not products:
        print("\nNo products found.")
        return

    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        f.write("SMART PRODUCT FINDER BD\n")
        f.write("=" * 35 + "\n\n")

        for p in products:
            f.write(
                f"ID: {p['id']}\n"
                f"Name: {p['name']}\n"
                f"Category: {p['category']}\n"
                f"Price: {p['price']}\n"
                f"Affiliate Link: {p.get('affiliate', p.get('affiliate_link', 'Not available'))}\n"
                f"Score: {p['score']}/100\n"
                f"{'-' * 35}\n"
            )

    print(f"\n✅ Export complete: {EXPORT_FILE}")


def statistics(products):
    print("\n--- STATISTICS ---")
    print(f"Total Products: {len(products)}")

    if products:
        average = sum(
            p["score"] for p in products
        ) / len(products)

        best = max(
            products,
            key=lambda x: x["score"]
        )

        print(f"Average Score: {average:.1f}/100")
        print(
            f"Best Product: {best['name']} "
            f"({best['score']}/100)"
        )


def show_menu():
    print("\n" + "=" * 36)
    print(" SMART PRODUCT FINDER BD 🤖🛍️")
    print("=" * 36)
    print("1. Add Product")
    print("2. View Products")
    print("3. Search Products")
    print("4. Best Products")
    print("5. Generate Marketing Content")
    print("6. Export Product List")
    print("7. Statistics")
    print("0. Exit")
    print("=" * 36)


def main():
    products = load_products()

    while True:
        show_menu()
        choice = input("\nChoose Option: ").strip()

        if choice == "1":
            add_product(products)

        elif choice == "2":
            view_products(products)

        elif choice == "3":
            search_products(products)

        elif choice == "4":
            best_products(products)

        elif choice == "5":
            generate_marketing_content(products)

        elif choice == "6":
            export_products(products)

        elif choice == "7":
            statistics(products)

        elif choice == "0":
            print("\nGoodbye! 👋")
            break

        else:
            print("\nInvalid option.")


if __name__ == "__main__":
    main()
