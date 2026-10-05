import json
import re
import html
import requests
from pathlib import Path
from bs4 import BeautifulSoup

OUTPUT = Path("daraz_public_products.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 11) "
        "AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
    )
}


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    print("HTTP:", r.status_code, "|", url)
    if r.status_code != 200:
        raise RuntimeError("Product page পাওয়া যায়নি।")
    return html.unescape(r.text)


def extract_product(url):
    if not (
        url.startswith("https://www.daraz.com.bd/")
        or url.startswith("https://s.daraz.com.bd/")
    ):
        raise ValueError("শুধু Daraz Bangladesh product URL দিন।")

    page = fetch(url)

    # Short URL হলে আসল product URL বের করা
    m = re.search(
        r'https://www\.daraz\.com\.bd/products/[^"\']+-i\d+-s\d+\.html',
        page,
    )
    product_url = m.group(0) if m else url

    if product_url != url:
        print("PRODUCT URL FOUND: YES")
        page = fetch(product_url)

    soup = BeautifulSoup(page, "html.parser")

    data = {
        "url": product_url,
        "name": None,
        "price": None,
        "currency": "BDT",
        "item_id": None,
        "seller_sku": None,
        "brand": None,
        "category": None,
        "description": None,
        "image": None,
        "seller_id": None,
    }

    # Name
    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        data["name"] = og["content"]
    else:
        title = soup.find("title")
        if title:
            data["name"] = title.get_text(" ", strip=True)

    # Price
    m = re.search(r'"pdt_price"\s*:\s*"([^"]+)"', page)
    if m:
        p = re.search(r"[0-9][0-9,.]*", m.group(1))
        if p:
            data["price"] = p.group(0).replace(",", "")

    # Item ID + SKU
    m = re.search(r"-i(\d+)-s(\d+)\.html", page)
    if m:
        data["item_id"] = m.group(1)
        data["seller_sku"] = m.group(2)

    # Brand
    m = re.search(r'"@type":"Brand","name":"([^"]+)"', page)
    if m:
        data["brand"] = m.group(1)

    # Category
    m = re.search(r'"category":"([^"]+)"', page)
    if m:
        data["category"] = m.group(1)

    # Description
    m = re.search(r'"description":"([^"]+)"', page)
    if m:
        data["description"] = m.group(1)

    # Image
    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        data["image"] = og["content"]

    # Seller ID
    m = re.search(r'"sellerId":"([^"]+)"', page)
    if m:
        data["seller_id"] = m.group(1)

    return data


def load_existing():
    if not OUTPUT.exists():
        return []

    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_products(products):
    OUTPUT.write_text(
        json.dumps(products, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    print("Daraz Public Batch Importer")
    print("প্রতি লাইনে একটি Daraz product URL দিন।")
    print("শেষ করতে খালি Enter চাপুন।")
    print()

    urls = []

    while True:
        url = input("URL: ").strip()
        if not url:
            break
        urls.append(url)

    if not urls:
        print("কোনো URL দেওয়া হয়নি।")
        return

    existing = load_existing()
    existing_ids = {
        str(p.get("item_id"))
        for p in existing
        if p.get("item_id")
    }

    added = 0
    skipped = 0
    failed = 0

    for url in urls:
        try:
            data = extract_product(url)

            item_id = str(data.get("item_id") or "")

            if item_id and item_id in existing_ids:
                print("SKIP: duplicate item_id:", item_id)
                skipped += 1
                continue

            existing.append(data)

            if item_id:
                existing_ids.add(item_id)

            added += 1

            print("ADDED:", data.get("name"))
            print("PRICE:", data.get("price"))
            print("ITEM ID:", data.get("item_id"))
            print()

        except Exception as e:
            failed += 1
            print("FAILED:", url)
            print("REASON:", type(e).__name__, str(e))
            print()

    save_products(existing)

    print("=== IMPORT SUMMARY ===")
    print("INPUT:", len(urls))
    print("ADDED:", added)
    print("SKIPPED:", skipped)
    print("FAILED:", failed)
    print("TOTAL SAVED:", len(existing))
    print("SAVED:", OUTPUT)


if __name__ == "__main__":
    main()
