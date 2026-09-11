import json
import os
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


def calculate_score(product):
    score = 0

    try:
        price = float(product["price"])
    except:
        price = 0

    if price > 0 and price <= 1000:
        score += 20
    elif price <= 3000:
        score += 15
    elif price <= 10000:
        score += 10

    score += int(product.get("problem_score", 0)) * 4
    score += int(product.get("demand_score", 0)) * 4
    score += int(product.get("content_score", 0)) * 2

    return min(score, 100)


def add_product(products):
    print("\n--- ADD PRODUCT ---")

    name = input("Product Name: ")
    category = input("Category: ")
    price = input("Price: ")
    affiliate_link = input("Affiliate Link: ")

    print("\nRate from 1 to 10")

    problem_score = input("Problem Solving Score: ")
    demand_score = input("Demand Score: ")
    content_score = input("Content Potential Score: ")

    product = {
        "id": len(products) + 1,
        "name": name,
        "category": category,
        "price": price,
        "affiliate_link": affiliate_link,
        "problem_score": problem_score,
        "demand_score": demand_score,
        "content_score": content_score,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    product["score"] = calculate_score(product)

    products.append(product)
    save_products(products)

    print("\n✅ Product Added!")
    print("Score:", product["score"], "/100")


def view_products(products):
    if not products:
        print("\nNo products found.")
        return

    print("\n--- PRODUCT LIST ---")

    for p in products:
        print(f"""
ID: {p['id']}
Name: {p['name']}
Category: {p['category']}
Price: {p['price']}
Score: {p['score']}/100
""")


def search_products(products):
    keyword = input("\nSearch Keyword: ").lower()

    results = [
        p for p in products
        if keyword in p["name"].lower()
        or keyword in p["category"].lower()
    ]

    if not results:
        print("\nNo matching products.")
        return

    for p in results:
        print(
            f"{p['id']} | {p['name']} | "
            f"Price: {p['price']} | Score: {p['score']}"
        )


def best_products(products):
    if not products:
        print("\nNo products found.")
        return

    sorted_products = sorted(
        products,
        key=lambda x: x.get("score", 0),
        reverse=True
    )

    print("\n🔥 BEST PRODUCTS")

    for p in sorted_products[:10]:
        print(
            f"{p['name']} | Score: {p['score']}/100 | "
            f"Price: {p['price']}"
        )


def get_product_by_id(products):
    product_id = input("Enter Product ID: ")

    try:
        product_id = int(product_id)
    except:
        print("Invalid ID.")
        return None

    for p in products:
        if p["id"] == product_id:
            return p

    print("Product not found.")
    return None


def generate_content(products):
    product = get_product_by_id(products)

    if not product:
        return

    name = product["name"]
    price = product["price"]
    link = product["affiliate_link"]

    print("\n========== FACEBOOK POST ==========\n")

    print(
        f"""🔥 নতুন একটি দরকারি পণ্য!

আপনার দৈনন্দিন কাজকে আরও সহজ করতে পারে — {name}।

💰 মূল্য: {price}

কেন এটি আপনার কাজে লাগতে পারে?

✅ দৈনন্দিন ব্যবহারে উপযোগী
✅ সহজ এবং সুবিধাজনক
✅ নিজের প্রয়োজন অনুযায়ী ব্যবহার করা যায়

👉 বিস্তারিত দেখতে:
{link}

#UsefulProduct #OnlineShopping #Bangladesh
"""
    )

    print("\n========== SHORT VIDEO HOOK ==========\n")

    print(
        f"""আপনি কি এমন একটি পণ্য খুঁজছেন
যেটা আপনার দৈনন্দিন কাজ সহজ করতে পারে?

আজকে দেখুন — {name}।

দাম ও বিস্তারিত জানতে নিচের লিংক দেখুন।
{link}
"""
    )

    print("\n========== YOUTUBE TITLE ==========\n")

    print(f"{name} কি সত্যিই কাজে লাগে? | Price: {price}")


def export_products(products):
    if not products:
        print("\nNo products to export.")
        return

    filename = "products_export.txt"

    with open(filename, "w", encoding="utf-8") as f:
        for p in products:
            f.write(
                f"ID: {p['id']}\n"
                f"Name: {p['name']}\n"
                f"Category: {p['category']}\n"
                f"Price: {p['price']}\n"
                f"Score: {p['score']}\n"
                f"Link: {p['affiliate_link']}\n"
                f"{'-'*30}\n"
            )

    print(f"\n✅ Exported: {filename}")


def statistics(products):
    if not products:
        print("\nNo data available.")
        return

    total = len(products)

    average_score = sum(
        p.get("score", 0)
        for p in products
    ) / total

    print("\n========== STATISTICS ==========")
    print("Total Products:", total)
    print("Average Score:", round(average_score, 2))

    best = max(
        products,
        key=lambda x: x.get("score", 0)
    )

    print("Best Product:", best["name"])
    print("Best Score:", best["score"])


def main():
    products = load_products()

    while True:

        print("""
╔══════════════════════════════════╗
║ SMART PRODUCT FINDER BD 🤖🛍️     ║
╠══════════════════════════════════╣
║ 1. Add Product                  ║
║ 2. View Products                ║
║ 3. Search Products              ║
║ 4. Best Products                ║
║ 5. Generate Marketing Content   ║
║ 6. Export Product List          ║
║ 7. Statistics                   ║
║ 0. Exit                         ║
╚══════════════════════════════════╝
""")

        choice = input("Choose Option: ")

        if choice == "1":
            add_product(products)

        elif choice == "2":
            view_products(products)

        elif choice == "3":
            search_products(products)

        elif choice == "4":
            best_products(products)

        elif choice == "5":
            generate_content(products)

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


