import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs


PRODUCT_FILE = Path("products.json")


def load_products():
    if not PRODUCT_FILE.exists():
        return []

    try:
        return json.loads(PRODUCT_FILE.read_text())
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
        seller_rating = float(
            product.get("seller_rating", 0) or 0
        )
        score += max(0, min(seller_rating, 5)) / 5 * 5
    except Exception:
        pass

    stock = str(product.get("stock", "")).lower()

    if stock in (
        "in stock",
        "available",
        "yes",
        "true",
        "1"
    ):
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


def html_page(products, keyword="", budget=""):
    cards = ""

    if products:
        ranked = sorted(
            products,
            key=smart_score,
            reverse=True
        )

        for p in ranked:
            name = p.get("name", "Unknown")
            price = p.get("price", "N/A")
            category = p.get("category", "N/A")
            score = smart_score(p)
            url = p.get("url", "")

            buy_button = ""

            if url:
                buy_button = (
                    f'<a href="{url}" '
                    'target="_blank">View Product</a>'
                )

            cards += f"""
            <div class="card">
                <h2>{name}</h2>
                <p>💰 Price: {price} BDT</p>
                <p>📦 Category: {category}</p>
                <p>⭐ Smart Score: {score}/100</p>
                {buy_button}
            </div>
            """

    else:
        cards = "<h3>No products found.</h3>"

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Smart Product Finder BD</title>

<style>
body {{
    font-family: Arial;
    background: #f4f6f8;
    margin: 0;
    padding: 20px;
}}

.container {{
    max-width: 900px;
    margin: auto;
}}

h1 {{
    text-align: center;
}}

.search {{
    background: white;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}}

input {{
    padding: 10px;
    margin: 5px;
    width: 40%;
}}

button {{
    padding: 10px 20px;
    cursor: pointer;
}}

.card {{
    background: white;
    padding: 15px;
    margin: 10px 0;
    border-radius: 10px;
}}

a {{
    display: inline-block;
    padding: 10px;
    background: #333;
    color: white;
    text-decoration: none;
    border-radius: 5px;
}}
</style>
</head>

<body>

<div class="container">

<h1>🤖 SMART PRODUCT FINDER BD</h1>

<div class="search">

<form method="GET">

<input
type="text"
name="q"
placeholder="Search product..."
value="{keyword}"
>

<input
type="number"
name="budget"
placeholder="Maximum budget"
value="{budget}"
>

<button type="submit">
Search
</button>

</form>

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

        keyword = params.get("q", [""])[0].lower()

        budget_text = params.get("budget", [""])[0]

        budget = None

        try:
            if budget_text:
                budget = float(budget_text)
        except Exception:
            pass

        products = load_products()

        filtered = []

        for product in products:

            name = str(
                product.get("name", "")
            ).lower()

            category = str(
                product.get("category", "")
            ).lower()

            if keyword:
                if (
                    keyword not in name
                    and keyword not in category
                ):
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

        self.wfile.write(
            page.encode("utf-8")
        )


print("=" * 45)
print("SMART PRODUCT FINDER BD - WEB APP")
print("=" * 45)
print("Open in browser:")
print("http://127.0.0.1:8080")
print("=" * 45)

server = HTTPServer(
    ("127.0.0.1", 8080),
    Handler
)

server.serve_forever()
