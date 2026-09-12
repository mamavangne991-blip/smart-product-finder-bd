import json
import urllib.parse
import urllib.request
import re
import html

INPUT_FILE = "products.json"
OUTPUT_FILE = "products_enriched_v4.json"

def web_search(query):
    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            page = response.read().decode("utf-8", errors="ignore")

        results = []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.S
        )

        matches = pattern.findall(page)

        for link, title in matches[:5]:
            title = re.sub("<.*?>", "", title)
            title = html.unescape(title).strip()

            if link.startswith("//"):
                link = "https:" + link

            results.append({
                "title": title,
                "url": link
            })

        return results

    except Exception as e:
        return []


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

output = []

print("=" * 55)
print("PRODUCT RESEARCH AGENT V4")
print("=" * 55)
print("Searching real web results...")
print()

for index, product in enumerate(products, 1):

    item = product.copy()

    name = item.get("name", "Unknown Product")
    category = item.get("category", "General")
    price = item.get("price", "N/A")

    print(f"[{index}/{len(products)}] Searching: {name}")

    search_query = f"{name} price Bangladesh"
    results = web_search(search_query)

    item["research_query"] = search_query

    if results:

        best = results[0]

        item["research_status"] = "SEARCH FOUND"
        item["research_title"] = best["title"]
        item["research_url"] = best["url"]
        item["research_results_count"] = len(results)

        item["research_score"] = 85
        item["link_status"] = "SEARCH LINK FOUND"
        item["missing_data"] = []

        item["research_sources"] = results

        print("  FOUND:", best["title"])
        print("  LINK:", best["url"])

    else:

        item["research_status"] = "SEARCH FAILED"
        item["research_title"] = ""
        item["research_url"] = ""
        item["research_results_count"] = 0

        item["research_score"] = 50
        item["link_status"] = "LINK NEEDED"

        item["missing_data"] = [
            "Real Product Source",
            "Verified Description"
        ]

        item["research_sources"] = []

        print("  NO RESULT")

    item["draft_description"] = (
        f"{name} একটি {category} ক্যাটাগরির প্রোডাক্ট। "
        f"বর্তমান তালিকাভুক্ত মূল্য: {price} BDT। "
        "কেনার আগে product source, price এবং specifications যাচাই করুন।"
    )

    output.append(item)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

found = sum(
    1 for p in output
    if p.get("research_status") == "SEARCH FOUND"
)

print()
print("=" * 55)
print("PRODUCT RESEARCH AGENT V4 SUCCESS")
print("=" * 55)
print("Total Products:", len(output))
print("Search Found:", found)
print("Search Failed:", len(output) - found)
print("Saved:", OUTPUT_FILE)
print("Original products.json was NOT changed")

