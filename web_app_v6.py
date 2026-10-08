import os
import json
import html
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PRODUCT_FILE = Path("products.json")
RECOMMENDATION_FILE = Path("product_recommendations.json")


def load_products():
    if not PRODUCT_FILE.exists():
        return []

    try:
        products = json.loads(PRODUCT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    # Production final recommendation pipeline is the authoritative
    # recommendation source for the web UI.
    final_file = Path(
        "worker_reports/daraz_final_recommendation_pipeline_report.json"
    )

    if final_file.exists():
        try:
            final_report = json.loads(
                final_file.read_text(encoding="utf-8")
            )

            recommendations = final_report.get("recommendations", [])
            product_map = {
                str(product.get("id") or product.get("item_id") or ""): product
                for product in products
            }

            # Fill missing production Daraz products from the validated
            # discovery report without modifying products.json.
            discovery_file = Path(
                "worker_reports/daraz_public_discovery_report.json"
            )
            if discovery_file.exists():
                try:
                    discovery = json.loads(
                        discovery_file.read_text(encoding="utf-8")
                    )

                    def collect_products(value):
                        found = []
                        if isinstance(value, dict):
                            if value.get("item_id") is not None:
                                found.append(value)
                            for child in value.values():
                                found.extend(collect_products(child))
                        elif isinstance(value, list):
                            for child in value:
                                found.extend(collect_products(child))
                        return found

                    for item in collect_products(discovery):
                        iid = str(item.get("item_id") or "")
                        if iid and iid not in product_map:
                            product_map[iid] = dict(item)
                except Exception:
                    pass

            final_products = []

            for rec in recommendations:
                item_id = str(rec.get("item_id") or "")
                product = product_map.get(item_id)

                if not product:
                    continue

                product["recommendation_rank"] = rec.get("position")
                product["recommendation_score"] = rec.get("score")
                product["recommendation_status"] = rec.get("status")

                final_products.append(product)

            if final_products:
                return final_products

        except Exception:
            pass

    return products

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

    stock = str(
        product.get("stock", "")
    ).strip().lower()

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


def recommendation_reasons(product):
    reasons = []

    try:
        rating = float(product.get("rating", 0) or 0)

        if rating >= 4:
            reasons.append("High product rating")
    except Exception:
        pass

    try:
        reviews = float(product.get("reviews", 0) or 0)

        if reviews >= 100:
            reasons.append("Good number of customer reviews")
    except Exception:
        pass

    try:
        discount = float(product.get("discount", 0) or 0)

        if discount >= 10:
            reasons.append("Good discount available")
    except Exception:
        pass

    try:
        seller_rating = float(
            product.get("seller_rating", 0) or 0
        )

        if seller_rating >= 4:
            reasons.append("Highly rated seller")
    except Exception:
        pass

    stock = str(
        product.get("stock", "")
    ).strip().lower()

    if stock in (
        "in stock",
        "available",
        "yes",
        "true",
        "1"
    ):
        reasons.append("Currently available in stock")

    if not reasons:
        reasons.append(
            "Ranked based on available product information"
        )

    return reasons


def product_card(product, rank=None, best=False):
    product_id = html.escape(
        str(product.get("id") or product.get("item_id") or "")
    )

    name = html.escape(
        str(product.get("name", "Unknown"))
    )

    category = html.escape(
        str(product.get("category", "N/A"))
    )

    price = html.escape(
        str(product.get("price", "N/A"))
    )

    score = product.get("recommendation_score")
    if score is None:
        score = smart_score(product)
    try:
        score = int(float(score))
    except Exception:
        score = int(smart_score(product))

    badge = ""

    if best:
        badge = (
            '<div class="best-badge">'
            '🏆 BEST RECOMMENDATION'
            '</div>'
        )

    rank_text = ""

    if rank is not None:
        rank_text = (
            f'<div class="rank">#{rank}</div>'
        )

    return f"""
    <div class="card {'best-card' if best else ''}">

        {badge}

        {rank_text}

        <h2>{name}</h2>

        <div class="meta">
            📦 {category}
        </div>

        <div class="price">
            💰 {price} BDT
        </div>

        <div class="score">
            ⭐ Smart Score:
            <b>{score}/100</b>
        </div>

        <a
            class="details-btn"
            href="/product?id={product_id}"
        >
            View Details →
        </a>

    </div>
    """



def best_value_score(product):
    price = get_price(product)
    score = smart_score(product)

    if price <= 0:
        return 0

    return score / price



def get_best_value_product(products):
    valid_products = [
        product
        for product in products
        if get_price(product) > 0
    ]

    if not valid_products:
        return None

    return min(
        valid_products,
        key=lambda item: (
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )



def get_top_three_products(products):
    return sorted(
        products,
        key=lambda item: (
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )[:3]


def home_page(products, keyword="", budget="", category_filter="", sort_by="score"):
    def recommendation_score(item):
        value = item.get("recommendation_score")
        if value is None:
            return smart_score(item)
        try:
            return int(float(value))
        except Exception:
            return smart_score(item)

    ranked = sorted(
        products,
        key=lambda item: (
            0 if str(item.get("affiliate_url", "")).strip() else 1,
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )

    cards = ""

    valid_best_values = [
        product
        for product in products
        if get_price(product) > 0
    ]

    best_value = None
    if valid_best_values:
        best_value = min(
            valid_best_values,
            key=lambda item: (
                item.get("recommendation_rank")
                if item.get("recommendation_rank") is not None
                else 999999
            )
        )

    best_value_card = ""

    top_three = sorted(
        products,
        key=lambda item: (
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )[:3]

    top_three_card = """
    <div class="top-three-title">
        🏆 TOP 3 SMART PRODUCTS
    </div>
    """

    for index, item in enumerate(top_three, 1):

        item_name = html.escape(
            str(item.get("name", "Unknown"))
        )

        item_price = html.escape(
            str(item.get("price", "N/A"))
        )

        item_score = recommendation_score(item)

        top_three_card += f"""
        <div class="card">

            <div class="best-badge">
                🏆 TOP #{index}
            </div>

            <h2>{item_name}</h2>

            <div class="price">
                💰 Price: {item_price} BDT
            </div>

            <div class="score">
                ⭐ Smart Score:
                <b>{item_score}/100</b>
            </div>

            <a class="details-btn"
               href="/product?id={html.escape(str(item.get("id") or item.get("item_id") or ""))}">
                View Details →
            </a>

        </div>
        """

    if best_value:

        best_value_name = html.escape(
            str(best_value.get("name", "Unknown"))
        )

        best_value_price = html.escape(
            str(best_value.get("price", "N/A"))
        )

        best_value_score = recommendation_score(
            best_value
        )

        best_value_card = f"""
        <div class="card best-card">

            <div class="best-badge">
                💰 BEST VALUE PRODUCT
            </div>

            <h2>
                {best_value_name}
            </h2>

            <div class="price">
                💰 Price:
                {best_value_price} BDT
            </div>

            <div class="score">
                ⭐ Smart Score:
                <b>{best_value_score}/100</b>
            </div>

        </div>
        """

    if ranked:

        cards += product_card(
            ranked[0],
            rank=1,
            best=True
        )

        for i, product in enumerate(
            ranked[1:],
            2
        ):
            cards += product_card(
                product,
                rank=i
            )

    else:
        cards = """
        <div class="empty">
            <h3>No products found 😔</h3>
            <p>
                Try another search
                or increase your budget.
            </p>
        </div>
        """

    safe_keyword = html.escape(
        keyword,
        quote=True
    )

    safe_budget = html.escape(
        budget,
        quote=True
    )

    safe_category = html.escape(
        category_filter,
        quote=True
    )

    score_selected = (
        "selected"
        if sort_by == "score"
        else ""
    )

    low_selected = (
        "selected"
        if sort_by == "price_low"
        else ""
    )

    high_selected = (
        "selected"
        if sort_by == "price_high"
        else ""
    )

    return f"""<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1"
>

<title>
Smart Product Finder BD
</title>

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
    font-weight: bold;
    margin-bottom: 10px;
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

.meta,
.price,
.score {{
    margin: 10px 0;
}}

.details-btn,
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

<h1>
🤖 SMART PRODUCT FINDER BD
</h1>

<div class="subtitle">
Find products based on
budget and smart ranking
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

<input
type="text"
name="category"
placeholder="Category..."
value="{safe_category}"
>

</div>

<select
name="sort"
style="
width:100%;
padding:13px;
border-radius:8px;
border:1px solid #ccc;
font-size:16px;
margin-top:8px;
"
>

<option
value="score"
{score_selected}
>
⭐ Best Smart Score
</option>

<option
value="price_low"
{low_selected}
>
💰 Price: Low to High
</option>

<option
value="price_high"
{high_selected}
>
💸 Price: High to Low
</option>

</select>

<br>

<button type="submit">
🔍 Find Best Products
</button>

</form>

</div>

{best_value_card}

{top_three_card}

<div class="result-count">

Products Found:
{len(ranked)}

</div>

{cards}

</div>

</body>

</html>
"""


def product_page(product):

    name = html.escape(
        str(product.get("name", "Unknown"))
    )

    category = html.escape(
        str(product.get("category", "N/A"))
    )

    price = html.escape(
        str(product.get("price", "N/A"))
    )

    rating = html.escape(
        str(product.get("rating", "N/A"))
    )

    reviews = html.escape(
        str(product.get("reviews", "N/A"))
    )

    discount = html.escape(
        str(product.get("discount", "N/A"))
    )

    seller_rating = html.escape(
        str(product.get("seller_rating", "N/A"))
    )

    stock = html.escape(
        str(product.get("stock", "N/A"))
    )

    score = smart_score(product)

    reasons = recommendation_reasons(
        product
    )

    reason_html = "".join(
        f"<li>{html.escape(reason)}</li>"
        for reason in reasons
    )

    url = str(
        product.get("affiliate_url")
        or product.get("product_url")
        or product.get("url", "")
    ).strip()

    buy_button = ""

    if url:

        safe_url = html.escape(
            url,
            quote=True
        )

        buy_button = f"""
        <a
        class="buy-btn"
        href="{safe_url}"
        target="_blank"
        rel="noopener noreferrer"
        >
        🔗 View Product
        </a>
        """

    else:

        buy_button = """
        <div class="no-link">
        🔗 Affiliate/Product Link coming soon
        </div>
        """

    return f"""<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1"
>

<title>
{name}
</title>

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
    max-width: 700px;
    margin: auto;
}}

.card {{
    background: white;
    padding: 22px;
    border-radius: 15px;
}}

.row {{
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}}

.score {{
    font-size: 20px;
    margin: 20px 0;
}}

.reasons {{
    margin: 20px 0;
}}

.buy-btn,
.back-btn {{
    display: inline-block;
    padding: 13px 18px;
    margin-top: 10px;
    background: #222;
    color: white;
    text-decoration: none;
    border-radius: 8px;
}}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>
{name}
</h1>

<div class="row">
📦 Category: {category}
</div>

<div class="row">
💰 Price: {price} BDT
</div>

<div class="row">
⭐ Rating: {rating}/5
</div>

<div class="row">
💬 Reviews: {reviews}
</div>

<div class="row">
🏷 Discount: {discount}%
</div>

<div class="row">
🏪 Seller Rating:
{seller_rating}/5
</div>

<div class="row">
📦 Stock: {stock}
</div>

<div class="score">
🧠 Smart Score:
<b>{score}/100</b>
</div>

<div class="reasons">

<h3>
Why recommended?
</h3>

<ul>

{reason_html}

</ul>

</div>

{buy_button}

<br>

<a
class="back-btn"
href="https://www.facebook.com/sharer/sharer.php?u=http://127.0.0.1:8080{html.escape(self.path if False else '', quote=True)}"
target="_blank"
rel="noopener noreferrer"
>
📤 Share Product
</a>

<br>

<a
class="back-btn"
href="/"
>
← Back to Products
</a>

</div>

</div>

</body>

</html>
"""


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        parsed = urlparse(self.path)

        params = parse_qs(
            parsed.query
        )

        products = load_products()

        if parsed.path == "/product":

            product_id = params.get(
                "id",
                [""]
            )[0]

            selected = None

            for product in products:

                if str(
                    product.get("id") or product.get("item_id") or ""
                ) == product_id:

                    selected = product
                    break

            if not selected:

                self.send_response(404)

                self.send_header(
                    "Content-type",
                    "text/html; charset=utf-8"
                )

                self.end_headers()

                self.wfile.write(
                    b"<h1>Product not found</h1>"
                )

                return

            page = product_page(
                selected
            )

        else:

            keyword = params.get(
                "q",
                [""]
            )[0].strip().lower()

            budget_text = params.get(
                "budget",
                [""]
            )[0].strip()

            category_filter = params.get(
                "category",
                [""]
            )[0].strip().lower()

            sort_by = params.get(
                "sort",
                ["score"]
            )[0].strip()

            if sort_by not in (
                "score",
                "price_low",
                "price_high"
            ):
                sort_by = "score"

            budget = None

            if budget_text:

                try:

                    budget = float(
                        budget_text.replace(
                            ",",
                            ""
                        )
                    )

                except Exception:

                    budget = None

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
                        and keyword
                        not in category
                    ):
                        continue

                if category_filter:

                    if (
                        category_filter
                        not in category
                    ):
                        continue

                if budget is not None:

                    if (
                        get_price(product)
                        > budget
                    ):
                        continue

                filtered.append(
                    product
                )

            page = home_page(
                filtered,
                keyword,
                budget_text,
                category_filter,
                sort_by
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




if __name__ == "__main__":

    print("=" * 45)
    print("SMART PRODUCT FINDER BD - WEB APP V6")
    print("=" * 45)
    print("Open in browser:")
    print("http://127.0.0.1:8080")
    print("=" * 45)

    server = HTTPServer(
        ("0.0.0.0", int(os.environ.get("PORT", "8080"))),
        Handler
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nWeb App stopped.")
        server.server_close()
