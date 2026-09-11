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

SOURCES_FILE = "sources.json"


def get_sources():
    return load_json(SOURCES_FILE, [])


def save_sources(sources):
    save_json(SOURCES_FILE, sources)


def add_source(sources):
    print("\n--- ADD PRODUCT SOURCE ---")

    name = input("Source name: ").strip()
    website = input("Website: ").strip()
    source_type = input("Source type (affiliate/api/csv/manual): ").strip()
    status = input("Status (active/inactive): ").strip() or "active"

    if not name:
        print("Source name is required.")
        return

    for source in sources:
        if source.get("name", "").lower() == name.lower():
            print("Source already exists.")
            return

    sources.append({
        "name": name,
        "website": website,
        "type": source_type,
        "status": status
    })

    save_sources(sources)
    print("Source added successfully.")


def view_sources(sources):
    print("\n--- PRODUCT SOURCES ---")

    if not sources:
        print("No sources added yet.")
        return

    for i, source in enumerate(sources, 1):
        print(
            f"{i}. {source.get('name', 'Unknown')} | "
            f"{source.get('type', 'N/A')} | "
            f"{source.get('status', 'N/A')} | "
            f"{source.get('website', '')}"
        )



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
    rating = input("Rating (0-5): ").strip()
    reviews = input("Number of reviews: ").strip()
    discount = input("Discount (%): ").strip()
    seller_rating = input("Seller rating (0-5): ").strip()
    stock = input("Stock status: ").strip()

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
        "commission": commission,
        "rating": rating,
        "reviews": reviews,
        "discount": discount,
        "seller_rating": seller_rating,
        "stock": stock
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


def edit_source(sources):
    if not sources:
        print("No sources available.")
        return

    view_sources(sources)
    choice = input("Source number to edit: ").strip()

    try:
        index = int(choice) - 1
        source = sources[index]
    except:
        print("Invalid source number.")
        return

    print("Leave blank to keep current value.")

    name = input(f"Name [{source.get('name', '')}]: ").strip()
    website = input(f"Website [{source.get('website', '')}]: ").strip()
    source_type = input(f"Type [{source.get('type', '')}]: ").strip()
    status = input(f"Status [{source.get('status', '')}]: ").strip()

    if name:
        source["name"] = name
    if website:
        source["website"] = website
    if source_type:
        source["type"] = source_type
    if status:
        source["status"] = status

    save_sources(sources)
    print("Source updated successfully.")


def view_products_by_source(products, sources):
    if not sources:
        print("No product sources added yet.")
        return

    view_sources(sources)
    source_name = input("Enter source name: ").strip().lower()

    found = [
        product for product in products
        if source_name == str(product.get("source", "")).strip().lower()
    ]

    print(f"\n--- PRODUCTS FROM SOURCE: {source_name} ---")

    if not found:
        print("No products found for this source.")
        return

    ranked = sorted(found, key=calculate_score, reverse=True)

    for i, product in enumerate(ranked, 1):
        print(
            f"{i}. {product.get('name', 'Unknown')} | "
            f"{product.get('price', 'N/A')} | "
            f"{product.get('category', 'N/A')} | "
            f"{calculate_score(product)}/100"
        )


def source_statistics(products, sources):
    print("\n--- SOURCE STATISTICS ---")

    if not sources:
        print("No sources added yet.")
        return

    for source in sources:
        name = source.get("name", "")
        count = sum(
            1 for product in products
            if str(product.get("source", "")).strip().lower()
            == name.strip().lower()
        )

        print(
            f"{name} | "
            f"Products: {count} | "
            f"Type: {source.get('type', 'N/A')} | "
            f"Status: {source.get('status', 'N/A')}"
        )


def import_products_with_source(products, sources):
    import csv

    if not sources:
        print("No active sources available.")
        return

    active_sources = [
        x for x in sources
        if str(x.get("status", "")).lower() == "active"
    ]

    if not active_sources:
        print("No active sources available.")
        return

    print("\n--- ACTIVE PRODUCT SOURCES ---")
    for i, source in enumerate(active_sources, 1):
        print(f"{i}. {source.get('name', 'Unknown')}")

    try:
        choice = int(input("Choose source number: ").strip())
        source = active_sources[choice - 1]
    except:
        print("Invalid source.")
        return

    filename = input("CSV file name: ").strip()

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            count = 0
            skipped = 0

            for row in reader:
                name = row.get("name", "").strip()
                price = row.get("price", "").strip()
                category = row.get("category", "").strip()

                if not name:
                    skipped += 1
                    continue

                duplicate = any(
                    str(x.get("name", "")).lower() == name.lower()
                    and str(x.get("price", "")) == price
                    and str(x.get("source", "")).lower()
                    == str(source.get("name", "")).lower()
                    for x in products
                )

                if duplicate:
                    skipped += 1
                    continue

                product = {
                    "id": next_id(products),
                    "name": name,
                    "price": price,
                    "category": category,
                    "source": source.get("name", ""),
                    "url": row.get("url", "").strip(),
                    "commission": row.get("commission", "").strip(),
                    "rating": row.get("rating", "").strip(),
                    "reviews": row.get("reviews", "").strip(),
                    "discount": row.get("discount", "").strip(),
                    "seller_rating": row.get("seller_rating", "").strip(),
                    "stock": row.get("stock", "").strip()
                }

                products.append(product)
                count += 1

        save_products(products)

        print(f"\nImported: {count} products")
        print(f"Skipped: {skipped} products")
        print(f"Source: {source.get('name', '')}")

    except FileNotFoundError:
        print("CSV file not found.")
    except Exception as e:
        print("Import error:", e)


def budget_finder(products):
    print("\n--- SMART BUDGET FINDER ---")

    try:
        max_price = float(input("Maximum budget: ").strip())
    except:
        print("Invalid budget.")
        return

    category = input("Category (leave blank for all): ").strip().lower()

    found = []

    for product in products:
        try:
            price_text = str(product.get("price", "0"))
            price = float(
                price_text.replace("BDT", "")
                .replace("৳", "")
                .replace(",", "")
                .strip()
            )
        except:
            continue

        product_category = str(
            product.get("category", "")
        ).lower()

        if price <= max_price:
            if not category or category in product_category:
                found.append(product)

    if not found:
        print("No products found within your budget.")
        return

    found.sort(key=calculate_score, reverse=True)

    print(f"\n--- BEST PRODUCTS UNDER {max_price:.0f} BDT ---")

    for i, product in enumerate(found[:10], 1):
        print(
            f"{i}. {product.get('name', 'Unknown')} | "
            f"{product.get('price', 'N/A')} BDT | "
            f"{product.get('category', 'N/A')} | "
            f"{calculate_score(product)}/100"
        )

    best = found[0]

    print("\n--- SMART BUDGET RECOMMENDATION ---")
    print(f"Best Choice: {best.get('name', 'Unknown')}")
    print(f"Price: {best.get('price', 'N/A')} BDT")
    print(f"Score: {calculate_score(best)}/100")

    url = best.get("url", "")
    if url:
        print(f"Product Link: {url}")


def source_recommendation(products, sources):
    if not sources:
        print("No sources available.")
        return

    print("\n--- SELECT SOURCE ---")
    for i, source in enumerate(sources, 1):
        print(f"{i}. {source.get('name', 'Unknown')}")

    try:
        choice = int(input("Source number: ").strip())
        source = sources[choice - 1]
    except:
        print("Invalid source.")
        return

    source_name = str(source.get("name", "")).lower()

    found = [
        product for product in products
        if str(product.get("source", "")).lower() == source_name
    ]

    if not found:
        print("No products found for this source.")
        return

    found.sort(key=calculate_score, reverse=True)

    print(f"\n--- BEST PRODUCTS FROM {source.get('name', '')} ---")

    for i, product in enumerate(found[:5], 1):
        print(
            f"{i}. {product.get('name', 'Unknown')} | "
            f"{product.get('price', 'N/A')} | "
            f"{calculate_score(product)}/100"
        )


def validate_product(product):
    errors = []

    name = str(product.get("name", "")).strip()
    price_text = str(product.get("price", "")).strip()
    category = str(product.get("category", "")).strip()

    if not name:
        errors.append("Missing product name")

    if not category:
        errors.append("Missing category")

    try:
        price = float(
            price_text.replace("BDT", "")
            .replace("৳", "")
            .replace(",", "")
            .strip()
        )
        if price <= 0:
            errors.append("Invalid price")
    except:
        errors.append("Invalid price")

    return errors


def data_quality_report(products):
    print("\n--- PRODUCT DATA QUALITY REPORT ---")

    if not products:
        print("No products available.")
        return

    valid = 0
    invalid = 0
    duplicate = 0

    seen = set()

    for product in products:
        errors = validate_product(product)

        if errors:
            invalid += 1
        else:
            valid += 1

        key = (
            str(product.get("name", "")).strip().lower(),
            str(product.get("price", "")).strip(),
            str(product.get("source", "")).strip().lower()
        )

        if key in seen:
            duplicate += 1
        else:
            seen.add(key)

    print(f"Total Products      : {len(products)}")
    print(f"Valid Products      : {valid}")
    print(f"Invalid Products    : {invalid}")
    print(f"Duplicate Products  : {duplicate}")

    print("\n--- INVALID PRODUCTS ---")

    found_invalid = False

    for product in products:
        errors = validate_product(product)

        if errors:
            found_invalid = True
            print(
                f"{product.get('name', 'Unknown')} | "
                + ", ".join(errors)
            )

    if not found_invalid:
        print("No invalid products found.")


def validate_import_file():
    import csv

    filename = input("CSV file name to validate: ").strip()

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            total = 0
            valid = 0
            invalid = 0

            print("\n--- IMPORT VALIDATION REPORT ---")

            for row in reader:
                total += 1

                errors = validate_product(row)

                if errors:
                    invalid += 1
                    print(
                        f"Row {total}: "
                        + ", ".join(errors)
                    )
                else:
                    valid += 1

            print("\n--- SUMMARY ---")
            print(f"Total Rows   : {total}")
            print(f"Valid Rows   : {valid}")
            print(f"Invalid Rows : {invalid}")

    except FileNotFoundError:
        print("CSV file not found.")
    except Exception as e:
        print("Validation error:", e)


def smart_import_pipeline(products, sources):
    import csv

    print("\n--- SMART REAL DATA IMPORT PIPELINE ---")

    filename = input("CSV file name: ").strip()

    if not filename:
        print("No file selected.")
        return

    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print("CSV file not found.")
        return
    except Exception as e:
        print("File error:", e)
        return

    if not rows:
        print("CSV file is empty.")
        return

    valid_rows = []
    invalid_rows = []
    duplicate_rows = []

    existing_keys = {
        (
            str(x.get("name", "")).strip().lower(),
            str(x.get("price", "")).strip(),
            str(x.get("source", "")).strip().lower()
        )
        for x in products
    }

    file_keys = set()

    for row_number, row in enumerate(rows, start=2):
        errors = validate_product(row)

        if errors:
            invalid_rows.append(
                (row_number, row, errors)
            )
            continue

        name = str(row.get("name", "")).strip()
        price = str(row.get("price", "")).strip()

        # Source from CSV, or choose default later
        source = str(row.get("source", "")).strip()

        key = (
            name.lower(),
            price,
            source.lower()
        )

        if key in existing_keys or key in file_keys:
            duplicate_rows.append(
                (row_number, row)
            )
            continue

        file_keys.add(key)
        valid_rows.append(row)

    print("\n--- IMPORT PREVIEW ---")
    print(f"Total Rows        : {len(rows)}")
    print(f"Ready to Import   : {len(valid_rows)}")
    print(f"Invalid Rows      : {len(invalid_rows)}")
    print(f"Duplicate Rows    : {len(duplicate_rows)}")

    if valid_rows:
        print("\n--- PRODUCTS TO IMPORT ---")

        for i, row in enumerate(valid_rows[:10], 1):
            print(
                f"{i}. {row.get('name', 'Unknown')} | "
                f"{row.get('price', 'N/A')} | "
                f"{row.get('category', 'N/A')}"
            )

        if len(valid_rows) > 10:
            print(
                f"... and {len(valid_rows) - 10} more products"
            )

    if invalid_rows:
        print("\n--- INVALID ROWS ---")
        for row_number, row, errors in invalid_rows[:5]:
            print(
                f"Row {row_number}: "
                + ", ".join(errors)
            )

    if duplicate_rows:
        print("\n--- DUPLICATE ROWS ---")
        for row_number, row in duplicate_rows[:5]:
            print(
                f"Row {row_number}: "
                f"{row.get('name', 'Unknown')}"
            )

    if not valid_rows:
        print("\nNothing to import.")
        return

    confirm = input(
        "\nImport valid products? (yes/no): "
    ).strip().lower()

    if confirm not in ("yes", "y"):
        print("Import cancelled.")
        return

    source_name = ""

    # If CSV does not have a source, choose one
    if not any(
        str(row.get("source", "")).strip()
        for row in valid_rows
    ):
        active_sources = [
            x for x in sources
            if str(x.get("status", "")).lower()
            == "active"
        ]

        if active_sources:
            print("\n--- SELECT SOURCE ---")

            for i, source in enumerate(
                active_sources, 1
            ):
                print(
                    f"{i}. "
                    f"{source.get('name', 'Unknown')}"
                )

            try:
                choice = int(
                    input("Source number: ").strip()
                )

                source_name = active_sources[
                    choice - 1
                ].get("name", "")

            except:
                print("Invalid source. Import cancelled.")
                return

    imported = 0

    for row in valid_rows:
        row_source = (
            str(row.get("source", "")).strip()
            or source_name
        )

        product = {
            "id": next_id(products),
            "name": str(row.get("name", "")).strip(),
            "price": str(row.get("price", "")).strip(),
            "category": str(
                row.get("category", "")
            ).strip(),
            "source": row_source,
            "url": str(row.get("url", "")).strip(),
            "commission": str(
                row.get("commission", "")
            ).strip(),
            "rating": str(row.get("rating", "")).strip(),
            "reviews": str(row.get("reviews", "")).strip(),
            "discount": str(row.get("discount", "")).strip(),
            "seller_rating": str(
                row.get("seller_rating", "")
            ).strip(),
            "stock": str(row.get("stock", "")).strip()
        }

        products.append(product)
        imported += 1

    save_products(products)

    print("\n--- IMPORT COMPLETE ---")
    print(f"Imported Products : {imported}")
    print(f"Skipped Invalid   : {len(invalid_rows)}")
    print(f"Skipped Duplicate : {len(duplicate_rows)}")
    print(f"Database Total    : {len(products)}")


def smart_score_v2(product):
    """
    Smart Product Score V2
    Maximum score: 100
    Works with old products even if advanced data is missing.
    """

    score = 50.0

    # Product rating: up to 20 points
    try:
        rating = float(product.get("rating", 0) or 0)
        if rating > 5:
            rating = 5
        if rating < 0:
            rating = 0
        score += (rating / 5) * 20
    except:
        pass

    # Reviews: up to 10 points
    try:
        reviews = int(float(product.get("reviews", 0) or 0))
        score += min(reviews / 1000, 1) * 10
    except:
        pass

    # Discount: up to 10 points
    try:
        discount = float(product.get("discount", 0) or 0)
        discount = max(0, min(discount, 100))
        score += (discount / 100) * 10
    except:
        pass

    # Seller rating: up to 5 points
    try:
        seller_rating = float(
            product.get("seller_rating", 0) or 0
        )
        seller_rating = max(0, min(seller_rating, 5))
        score += (seller_rating / 5) * 5
    except:
        pass

    # Stock bonus: up to 3 points
    stock = str(product.get("stock", "")).strip().lower()

    if stock in ("in stock", "available", "yes", "true", "1"):
        score += 3

    # Commission: up to 2 points
    try:
        commission = float(
            str(product.get("commission", 0))
            .replace("%", "")
            .strip()
        )
        score += min(commission / 20, 1) * 2
    except:
        pass

    return round(min(score, 100), 1)


def score_v2_report(products):
    print("\n--- SMART SCORE V2 REPORT ---")

    if not products:
        print("No products available.")
        return

    ranked = sorted(
        products,
        key=smart_score_v2,
        reverse=True
    )

    for i, product in enumerate(ranked[:10], 1):
        old_score = calculate_score(product)
        new_score = smart_score_v2(product)

        print(
            f"{i}. {product.get('name', 'Unknown')} | "
            f"Old: {old_score}/100 | "
            f"V2: {new_score}/100"
        )

    print("\nScore V2 factors:")
    print("Rating + Reviews + Discount + Seller Rating")
    print("+ Stock + Commission")


def edit_advanced_product_data(products):
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

    print("\n--- ADVANCED PRODUCT DATA ---")
    print("Leave blank to keep current value.")

    rating = input(
        f"Rating [{product.get('rating', '')}]: "
    ).strip()

    reviews = input(
        f"Reviews [{product.get('reviews', '')}]: "
    ).strip()

    discount = input(
        f"Discount [{product.get('discount', '')}%]: "
    ).strip()

    seller_rating = input(
        f"Seller Rating [{product.get('seller_rating', '')}]: "
    ).strip()

    stock = input(
        f"Stock [{product.get('stock', '')}]: "
    ).strip()

    if rating:
        product["rating"] = rating

    if reviews:
        product["reviews"] = reviews

    if discount:
        product["discount"] = discount

    if seller_rating:
        product["seller_rating"] = seller_rating

    if stock:
        product["stock"] = stock

    save_products(products)

    print("\nAdvanced data updated successfully.")
    print(
        f"New Smart Score V2: "
        f"{smart_score_v2(product)}/100"
    )


def advanced_product_report(products):
    print("\n--- ADVANCED PRODUCT DATA REPORT ---")

    if not products:
        print("No products available.")
        return

    for i, product in enumerate(products, 1):

        print(
            f"{i}. {product.get('name', 'Unknown')}"
        )

        print(
            f"   Rating: {product.get('rating', 'N/A')} | "
            f"Reviews: {product.get('reviews', 'N/A')}"
        )

        print(
            f"   Discount: {product.get('discount', 'N/A')}% | "
            f"Seller: {product.get('seller_rating', 'N/A')}"
        )

        print(
            f"   Stock: {product.get('stock', 'N/A')} | "
            f"V2 Score: {smart_score_v2(product)}/100"
        )


def show_menu():
    print("""
================================
 SMART PRODUCT FINDER BD V9 🤖
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
15. Add Product Source
16. View Product Sources
17. Edit Product Source
18. View Products by Source
19. Source Statistics
20. Import Products with Source
21. Smart Budget Finder
22. Best Products by Source
23. Product Data Quality Report
24. Validate CSV Before Import
25. Smart Real Data Import Pipeline
26. Smart Score V2 Report
27. Edit Advanced Product Data
28. Advanced Product Data Report
0. Exit
================================
""")


def main():
    products = get_products()
    sources = get_sources()

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
        elif choice == "15":
            add_source(sources)
        elif choice == "16":
            view_sources(sources)
        elif choice == "17":
            edit_source(sources)
        elif choice == "18":
            view_products_by_source(products, sources)
        elif choice == "19":
            source_statistics(products, sources)
        elif choice == "20":
            import_products_with_source(products, sources)
        elif choice == "21":
            budget_finder(products)
        elif choice == "22":
            source_recommendation(products, sources)
        elif choice == "23":
            data_quality_report(products)
        elif choice == "24":
            validate_import_file()
        elif choice == "25":
            smart_import_pipeline(products, sources)
        elif choice == "26":
            score_v2_report(products)
        elif choice == "27":
            edit_advanced_product_data(products)
        elif choice == "28":
            advanced_product_report(products)
        elif choice == "0":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
