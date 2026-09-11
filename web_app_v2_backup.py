import json
import html
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PRODUCT_FILE = Path("products.json")


def load_products():
    if not PRODUCT_FILE.exists():
        return []

    try:
        return json.loads(PRODUCT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def get_price(product):
    try:
        text = str(product.get("price", "0"))
        return float(
            text.replace("BDT", "")
            .replace("৳", "")
            .replace(",", "")
            .strip()
        )
    except Exception:
        return 0.0


def smart_score(product):
    score = 50.0

    try:
        rating = float(product.get("rating", 0) or 0)
        score += max(0, min(rating, 5)) / 5 * 20
    except Exception:
        pass

    try:
        reviews = float(product.get("reviews", 0) or 0)
        score += min(reviews / 1000, 1) * 10
    except Exception:
        pass

    try:
        discount = float(product.get("discount", 0) or 0)
        score += max(0, min(discount, 100)) / 100 * 10
    except Exception:
        pass

    try:
        seller_rating = float(product.get("seller_rating", 0) or 0)
        score += max(0, min(seller_rating, 5)) / 5 * 5
    except Exception:
        pass

    stock = str(product.get("stock", "")).strip().lower()

    if stock in ("in stock", "available", "yes", "true", "1"):
        score += 3

    try:
        commission = float(
            str(product.get("commission", 0))
            .replace("%", "")
            .strip()
        )
        score += min(commission / 20, 1) * 2
    except Exception:
        pass

    return round(min(score, 100), 1)


def product_card(product, rank=None, best=False):
    name = html.escape(str(product.get("name", "Unknown")))
    category = html.escape(str(product.get("category", "N/A")))
    price = html.escape(str(product.get("price", "N/A")))
    score = smart_score(product)
    url = str(product.get("url", "")).strip()

    badge = ""

    if best:
        badge = '<div class="best-badge">🏆 BEST RECOMMENDATION</div>'

    rank_text = ""

    if rank is not None:
        rank_text = f'<div class="rank">#{rank}</div>'

    buy_button = ""

    if url:
        safe_url = html.escape(url, quote=True)
        buy_button = (
            f'<a class="buy-btn" href="{safe_url}" '
            'target="_blank" rel="noopener noreferrer">'
            'View Product →</a>'
        )

    return f"""
    <div class="card {'best-card' if best else ''}">
        {badge}
        {rank_text}
        <h2>{name}</h2>
        <div class="meta">📦 {category}</div>
        <div class="price">💰 {price} BDT</div>
        <div class="score">⭐ Smart Score: <b>{score}/100</b></div>
        {buy_button}
    </div>
    """


def html_page(products, keyword="", budget=""):
    ranked = sorted(products, key=smart_score, reverse=True)

    cards = ""

    if ranked:
        best = ranked[0]

        cards += product_card(best, rank=1, best=True)

        for i, product in enumerate(ranked[1:], 2):
            cards += product_card(product, rank=i)

    else:
        cards = """
        <div class="empty">
            <h3>No products found 😔</h3>
            <p>Try another search or increase your budget.</p>
        </div>
        """

    safe_keyword = html.escape(keyword, quote=True)
    safe_budget = html.escape(budget, quote=True)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Smart Product Finder BD</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    padding: 15px;
}}

.container {{
    max-width: 850px;
    margin: auto;
}}

.header {{
    text-align: center;
    margin-bottom: 20px;
}}

.header h1 {{
    margin-bottom: 5px;
}}

.subtitle {{
    opacity: 0.7;
}}

.search-box {{
    background: white;
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 20px;
}}

input {{
    width: 100%;
    padding: 13px;
    margin: 6px 0;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 16px;
}}

button {{
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
}}

.result-count {{
    margin: 15px 0;
    font-weight: bold;
}}

.card {{
    position: relative;
    background: white;
    padding: 18px;
    margin-bottom: 15px;
    border-radius: 14px;
}}

.best-card {{
    border: 2px solid #222;
}}

.best-badge {{
    display: inline-block;
    margin-bottom: 10px;
    font-weight: bold;
}}

.rank {{
    position: absolute;
    top: 15px;
    right: 15px;
    font-weight: bold;
}}

.card h2 {{
    margin-top: 5px;
    padding-right: 50px;
}}

.meta {{
    margin: 8px 0;
}}

.price {{
    font-size: 18px;
    margin: 8px 0;
}}

.score {{
    margin: 10px 0;
}}

.buy-btn {{
    display: inline-block;
    padding: 12px 16px;
    background: #222;
    color: white;
    text-decoration: none;
    border-radius: 8px;
}}

.empty {{
    background: white;
    padding: 30px;
    text-align: center;
    border-radius: 14px;
}}

@media (min-width: 700px) {{
    .search-row {{
        display: flex;
        gap: 10px;
    }}

    .search-row input {{
        margin: 0;
    }}
}}
</style>
</head>

<body>

<div class="container">

<div class="header">
    <h1>🤖 SMART PRODUCT FINDER BD</h1>
    <div class="subtitle">
        Find products based on budget and smart ranking
    </div>
</div>

<div class="search-box">
    <form method="GET">
        <div class="search-row">
            <input
                type="text"
                name="q"
                placeholder="Search product or category..."
                value="{safe_keyword}"
            >

            <input
                type="number"
                name="budget"
                placeholder="Maximum budget"
                value="{safe_budget}"
            >
        </div>

        <br>

        <button type="submit">
            🔍 Find Best Products
        </button>
    </form>
</div>

<div class="result-count">
    Products Found: {len(ranked)}
</div>

{cards}

</div>

</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        params = parse_qs(parsed.query)

        keyword = params.get("q", [""])[0].strip().lower()
        budget_text = params.get("budget", [""])[0].strip()

        budget = None

        if budget_text:
            try:
                budget = float(budget_text.replace(",", ""))
            except Exception:
                budget = None

        products = load_products()
        filtered = []

        for product in products:
            name = str(product.get("name", "")).lower()
            category = str(product.get("category", "")).lower()

            if keyword:
                if keyword not in name and keyword not in category:
                    continue

            if budget is not None:
                if get_price(product) > budget:
                    continue

            filtered.append(product)

        page = html_page(
            filtered,
            keyword,
            budget_text
        )

        self.send_response(200)
        self.send_header(
            "Content-type",
            "text/html; charset=utf-8"
        )
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))


print("=" * 45)
print("SMART PRODUCT FINDER BD - WEB APP V2")
print("=" * 45)
print("Open in browser:")
print("http://127.0.0.1:8080")
print("=" * 45)

server = HTTPServer(("127.0.0.1", 8080), Handler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nWeb App stopped.")
    server.server_close()
