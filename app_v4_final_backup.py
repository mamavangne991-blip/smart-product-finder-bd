import json
import os
from datetime import datetime

PRODUCT_FILE = "products.json"
SOURCE_FILE = "sources.json"
APPROVED_FILE = "approved_content.txt"

def load_file(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_file(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def score(p):
    return int(p.get("score", 0))

def add_source(sources):
    name = input("Source Name: ").strip()
    source_type = input("Type (Manual/CSV/API): ").strip()
    url = input("Website/Feed URL: ").strip()

    sources.append({
        "id": len(sources) + 1,
        "name": name,
        "type": source_type,
        "url": url,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    save_file(SOURCE_FILE, sources)
    print("✅ Source saved!")

def view_sources(sources):
    if not sources:
        print("No sources found.")
        return

    for s in sources:
        print(f"\n{s['id']}. {s['name']}")
        print(f"Type: {s['type']}")
        print(f"URL: {s['url']}")

def add_product(products):
    name = input("Product Name: ").strip()

    if any(p.get("name", "").lower() == name.lower() for p in products):
        print("⚠️ Product already exists!")
        return

    category = input("Category: ").strip()
    price = input("Price: ").strip()
    link = input("Affiliate Link: ").strip()

    try:
        product_score = int(input("Score (1-100): "))
    except:
        product_score = 50

    products.append({
        "id": max([p.get("id", 0) for p in products], default=0) + 1,
        "name": name,
        "category": category,
        "price": price,
        "affiliate": link,
        "score": max(1, min(product_score, 100))
    })

    save_file(PRODUCT_FILE, products)
    print("✅ Product saved!")

def view_products(products):
    if not products:
        print("No products found.")
        return

    for p in products:
        print(f"\n{p['id']}. {p['name']} | {p.get('score', 0)}/100")
        print(f"Category: {p.get('category', '')}")
        print(f"Price: {p.get('price', '')}")

def top_products(products):
    for p in sorted(products, key=score, reverse=True)[:10]:
        print(f"{p['id']}. {p['name']} | {p.get('score', 0)}/100")

def generate_content(products):
    try:
        pid = int(input("Product ID: "))
    except:
        print("Invalid ID")
        return

    p = next((x for x in products if x.get("id") == pid), None)

    if not p:
        print("Product not found.")
        return

    text = f"""
PRODUCT: {p['name']}
PRICE: {p.get('price', '')}

FACEBOOK POST
🔥 দেখুন {p['name']}!
দৈনন্দিন কাজে উপকারী একটি Product।

👉 বিস্তারিত:
{p.get('affiliate', '')}

YOUTUBE TITLE
{p['name']} Review | এটি কি সত্যিই কাজে লাগে?

HASHTAGS
#ProductReview #OnlineShopping #Bangladesh
"""

    print(text)

    if input("Approve & Save? (y/n): ").lower() == "y":
        with open(APPROVED_FILE, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 40 + "\n" + text)
        print("✅ Approved content saved!")

def statistics(products):
    if not products:
        print("No products found.")
        return

    avg = sum(score(p) for p in products) / len(products)
    best = max(products, key=score)

    print(f"Total Products: {len(products)}")
    print(f"Average Score: {avg:.1f}/100")
    print(f"Best Product: {best['name']} ({score(best)}/100)")

def main():
    products = load_file(PRODUCT_FILE, [])
    sources = load_file(SOURCE_FILE, [])

    while True:
        print("""
================================
 SMART PRODUCT FINDER BD V4 🤖
================================
1. Add Product
2. View Products
3. Top Products
4. Add Product Source
5. View Product Sources
6. Generate & Approve Content
7. Statistics
0. Exit
================================
""")

        choice = input("Choose Option: ").strip()

        if choice == "1":
            add_product(products)
        elif choice == "2":
            view_products(products)
        elif choice == "3":
            top_products(products)
        elif choice == "4":
            add_source(sources)
        elif choice == "5":
            view_sources(sources)
        elif choice == "6":
            generate_content(products)
        elif choice == "7":
            statistics(products)
        elif choice == "0":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
