import json
import re
import requests
import html
from pathlib import Path
from bs4 import BeautifulSoup


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    print("HTTP:", r.status_code)
    if r.status_code != 200:
        raise RuntimeError("Product page পাওয়া যায়নি।")
    return html.unescape(r.text)


def main():
    URL = input("Daraz product URL দিন: ").strip()

    if not (
        URL.startswith("https://www.daraz.com.bd/")
        or URL.startswith("https://s.daraz.com.bd/")
    ):
        print("শুধু Daraz Bangladesh product URL দিন।")
        raise SystemExit

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
    }

    def fetch(url):
        r = requests.get(url, headers=HEADERS, timeout=30)
        print("HTTP:", r.status_code)
        if r.status_code != 200:
            print("Product page পাওয়া যায়নি।")
            raise SystemExit
        return html.unescape(r.text)

    page = fetch(URL)

    # Short URL হলে আসল product URL বের করা
    m = re.search(
        r'https://www\.daraz\.com\.bd/products/[^"\']+-i\d+-s\d+\.html',
        page
    )

    product_url = m.group(0) if m else URL

    if product_url != URL:
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
        p = re.search(r'[0-9][0-9,.]*', m.group(1))
        if p:
            data["price"] = p.group(0).replace(",", "")

    # Item ID + SKU
    m = re.search(r'-i(\d+)-s(\d+)\.html', page)
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

    Path("daraz_public_products.json").write_text(
        json.dumps([data], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print("NAME:", data["name"])
    print("PRICE:", data["price"])
    print("BRAND:", data["brand"])
    print("CATEGORY:", data["category"])
    print("ITEM ID:", data["item_id"])
    print("SELLER SKU:", data["seller_sku"])
    print("SELLER ID:", data["seller_id"])
    print("IMAGE:", "YES" if data["image"] else "NO")
    print("DESCRIPTION:", "YES" if data["description"] else "NO")
    print()
    print("Saved: daraz_public_products.json")


if __name__ == "__main__":
    main()
