import json
import urllib.parse
import urllib.request
import re
import html

INPUT_FILE = "products.json"
OUTPUT_FILE = "products_enriched_v5.json"

BASE_URL = "https://www.daraz.com.bd/catalog/"

def search_daraz(product_name):
    try:
        query = urllib.parse.quote_plus(product_name)
        url = BASE_URL + "?q=" + query

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 11)"
            }
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            page = response.read().decode("utf-8", errors="ignore")

        results = []

        # Daraz product URLs
        links = re.findall(
            r'https://www\.daraz\.com\.bd/products/[^"\s<>]+',
            page
        )

        titles = re.findall(
            r'"name"\s*:\s*"([^"]{5,300})"',
            page
        )

        prices = re.findall(
            r'"price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            page
        )

        seen = set()

        for i, link in enumerate(links):
            link = html.unescape(link)

            if link in seen:
                continue

            seen.add(link)

            title = ""
            price = ""

            if i < len(titles):
                title = html.unescape(titles[i])

            if i < len(prices):
                price = prices[i]

            results.append({
                "title": title,
                "price": price,
                "url": link
            })

            if len(results) >= 10:
                break

        return results

    except Exception as e:
        return []


def normalize(text):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(text).lower()
    ).strip()


def calculate_match(product_name, result_title):
    product_words = set(normalize(product_name).split())
    result_words = set(normalize(result_title).split())

    if not product_words or not result_words:
        return 0

    matched = product_words.intersection(result_words)

    return round(
        len(matched) / len(product_words) * 100,
        2
    )


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

output = []

print("=" * 60)
print("DARAZ PRODUCT RESEARCH AGENT V5")
print("=" * 60)
print()

for index, product in enumerate(products, 1):

    item = product.copy()

    name = item.get("name", "Unknown Product")

    print(f"[{index}/{len(products)}] Searching Daraz: {name}")

    results = search_daraz(name)

    matched_results = []

    for result in results:

        match_score = calculate_match(
            name,
            result.get("title", "")
        )

        result["match_score"] = match_score

        if match_score >= 50:
            matched_results.append(result)

    matched_results.sort(
        key=lambda x: x.get("match_score", 0),
        reverse=True
    )

    if matched_results:

        best = matched_results[0]

        item["research_status"] = "DARAZ MATCH FOUND"
        item["research_title"] = best.get("title", "")
        item["research_url"] = best.get("url", "")
        item["market_price"] = best.get("price", "")
        item["match_score"] = best.get("match_score", 0)

        item["link_status"] = "SOURCE FOUND"

        item["research_score"] = min(
            100,
            60 + best.get("match_score", 0) * 0.4
        )

        item["missing_data"] = []

        item["daraz_results"] = matched_results[:5]

        print("  MATCH:", best.get("title", ""))
        print("  PRICE:", best.get("price", ""))
        print("  MATCH SCORE:", best.get("match_score", 0))

    else:

        item["research_status"] = "NO CONFIDENT MATCH"
        item["research_title"] = ""
        item["research_url"] = ""
        item["market_price"] = ""
        item["match_score"] = 0

        item["link_status"] = "LINK NEEDED"

        item["research_score"] = 30

        item["missing_data"] = [
            "Daraz Product Match"
        ]

        item["daraz_results"] = []

        print("  NO CONFIDENT MATCH")

    output.append(item)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

found = sum(
    1 for item in output
    if item.get("research_status") == "DARAZ MATCH FOUND"
)

print()
print("=" * 60)
print("DARAZ PRODUCT RESEARCH AGENT V5 COMPLETE")
print("=" * 60)
print("Total Products:", len(output))
print("Daraz Matches:", found)
print("No Confident Match:", len(output) - found)
print("Saved:", OUTPUT_FILE)
print()
print("Original products.json was NOT changed.")

