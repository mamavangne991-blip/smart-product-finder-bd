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
            product_map = {}
            for product in products:
                for key in ("id", "item_id"):
                    value = str(product.get(key) or "").strip()
                    if not value:
                        continue
                    product_map[value] = product
                    if value.startswith("daraz-"):
                        product_map[value[len("daraz-"):]] = product
                    else:
                        product_map["daraz-" + value] = product

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
                # Keep ranked recommendations first, but do not hide
                # valid products that are absent from the recommendation list.
                def normalized_ids(item):
                    ids = set()
                    for key in ("id", "item_id"):
                        value = str(item.get(key) or "").strip()
                        if not value:
                            continue
                        ids.add(value)
                        if value.startswith("daraz-"):
                            ids.add(value[len("daraz-"):])
                        else:
                            ids.add("daraz-" + value)
                    return ids

                seen_ids = set()
                for item in final_products:
                    seen_ids.update(normalized_ids(item))

                for product in products:
                    ids = normalized_ids(product)
                    if ids and ids.intersection(seen_ids):
                        continue
                    final_products.append(product)
                    seen_ids.update(ids)

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
* {{ box-sizing: border-box; }}
:root {{ color-scheme: light; }}
body {{
  margin: 0; padding: 20px;
  font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
  color: #172033; background: #f3f6fb;
  line-height: 1.55;
}}
.container {{ width: 100%; max-width: 960px; margin: 0 auto; }}
.header {{
  padding: 28px 22px; margin-bottom: 20px;
  color: #fff; text-align: center;
  background: linear-gradient(135deg, #124eae, #3985ee);
  border-radius: 22px; box-shadow: 0 8px 25px rgba(25, 75, 150, .15);
}}
.header h1 {{ margin: 0 0 10px; font-size: clamp(25px, 5vw, 38px); line-height: 1.2; overflow-wrap: anywhere; }}
.subtitle {{ font-size: clamp(15px, 3.5vw, 18px); opacity: .94; }}
.search-box {{
  padding: 20px; margin-bottom: 22px; background: #fff;
  border: 1px solid #e1e8f2; border-radius: 18px;
  box-shadow: 0 5px 18px rgba(31, 55, 90, .05);
}}
.search-box form {{ display: grid; gap: 12px; }}
.search-row {{ display: grid; grid-template-columns: minmax(0, 1fr); gap: 10px; }}
.search-box input, .search-box select {{
  width: 100%; min-width: 0; min-height: 48px; margin: 0;
  padding: 12px 14px; font: inherit; color: #172033;
  background: #fff; border: 1px solid #cbd5e1; border-radius: 11px;
}}
.search-box button, button {{
  min-height: 48px; padding: 12px 18px; font: inherit;
  font-weight: 700; color: #fff; background: #1768d2;
  border: 0; border-radius: 11px; cursor: pointer;
  transition: background-color .15s ease, transform .15s ease;
}}
.search-box button:hover, button:hover {{ background: #1055b4; }}
.search-box input:focus-visible, .search-box select:focus-visible,
button:focus-visible, a:focus-visible {{
  outline: 3px solid #8ab8ff; outline-offset: 3px;
}}
.result-count {{
  padding: 12px 15px; margin: 16px 0;
  color: #174ea6; background: #e8f1ff;
  border-radius: 12px; font-weight: 750;
}}
.card {{
  position: relative; padding: 20px; margin-bottom: 16px;
  overflow-wrap: anywhere; background: #fff;
  border: 1px solid #e1e8f2; border-radius: 18px;
  box-shadow: 0 6px 20px rgba(24, 55, 95, .06);
}}
.card h2 {{ margin: 5px 0 12px; color: #172033; font-size: clamp(19px, 4vw, 25px); line-height: 1.4; }}
.meta {{ color: #667085; font-size: .95rem; line-height: 1.6; }}
.price {{
  display: inline-block; margin: 8px 8px 8px 0; padding: 7px 11px;
  color: #1459b8; background: #eaf3ff; border-radius: 10px;
  font-size: 1.08rem; font-weight: 800;
}}
.score {{
  display: inline-block; margin: 8px 0; padding: 7px 11px;
  color: #137547; background: #e7f8ee; border-radius: 10px; font-weight: 800;
}}
.best-card {{ border: 2px solid #2878e5; background: linear-gradient(180deg, #fff, #f7faff); }}
.best-badge {{ margin-bottom: 10px; color: #1759b5; font-weight: 800; }}
.rank {{ position: absolute; top: 14px; right: 14px; font-weight: 800; color: #475467; }}
.details-btn, .buy-btn {{
  display: inline-flex; align-items: center; justify-content: center;
  min-height: 44px; margin: 8px 8px 0 0; padding: 11px 16px;
  color: #fff; background: #1768d2; border-radius: 11px;
  text-decoration: none; font-weight: 700; overflow-wrap: anywhere;
}}
.details-btn:hover, .buy-btn:hover {{ background: #1055b4; }}
.empty {{
  padding: 28px 20px; text-align: center; background: #fff;
  border: 1px solid #e1e8f2; border-radius: 16px;
}}
@media (min-width: 680px) {{
  body {{ padding: 28px; }}
  .search-row {{ grid-template-columns: minmax(0, 2fr) minmax(140px, 1fr) minmax(0, 1fr); }}
}}
@media (max-width: 480px) {{
  body {{ padding: 12px; }}
  .header {{ padding: 22px 14px; border-radius: 17px; }}
  .search-box {{ padding: 14px; }}
  .card {{ padding: 16px; }}
  .rank {{ top: 9px; right: 9px; }}
  .details-btn, .buy-btn {{ width: 100%; margin-right: 0; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ scroll-behavior: auto !important; transition: none !important; }}
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
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 20px;
  font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
  color: #172033; background: #f3f6fb; line-height: 1.6;
}}
.container {{ width: 100%; max-width: 760px; margin: 0 auto; }}
.card {{
  padding: clamp(18px, 4vw, 30px); background: #fff;
  border: 1px solid #e1e8f2; border-radius: 20px;
  box-shadow: 0 8px 28px rgba(31, 55, 90, .07);
}}
.card h1 {{ margin-top: 0; font-size: clamp(24px, 5vw, 34px); line-height: 1.3; overflow-wrap: anywhere; }}
.row {{ padding: 14px 0; border-bottom: 1px solid #e8edf4; overflow-wrap: anywhere; }}
.score {{ margin: 20px 0; font-size: 20px; font-weight: 800; color: #137547; }}
.reasons {{ margin: 20px 0; line-height: 1.7; }}
.buy-btn, .back-btn {{
  display: inline-flex; align-items: center; justify-content: center;
  min-height: 46px; margin: 10px 8px 0 0; padding: 12px 18px;
  color: #fff; background: #1768d2; border-radius: 11px;
  text-decoration: none; font-weight: 700; overflow-wrap: anywhere;
}}
.buy-btn:hover, .back-btn:hover {{ background: #1055b4; }}
a:focus-visible {{ outline: 3px solid #8ab8ff; outline-offset: 3px; }}
@media (max-width: 480px) {{
  body {{ padding: 12px; }}
  .card {{ border-radius: 16px; }}
  .buy-btn, .back-btn {{ width: 100%; margin-right: 0; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; }}
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
href="https://www.facebook.com/sharer/sharer.php?u={html.escape((os.environ.get('PUBLIC_BASE_URL', '').rstrip('/') or 'http://127.0.0.1:8080') + '/product?id=' + str(product.get('id') or product.get('item_id') or ''), quote=True)}"
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

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

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

                # Fallback: product-detail pages may reference products
                # that are not in the final recommendation subset.
                raw_products = []

                try:
                    raw_data = json.loads(
                        PRODUCT_FILE.read_text(encoding="utf-8")
                    )
                    raw_products = (
                        raw_data
                        if isinstance(raw_data, list)
                        else raw_data.get("products", [])
                    )
                except Exception:
                    raw_products = []

                for product in raw_products:

                    candidates = {
                        str(product.get("id") or ""),
                        str(product.get("item_id") or ""),
                    }

                    # Support Daraz IDs in both forms:
                    # daraz-530238363 and 530238363
                    if product_id.startswith("daraz-"):
                        candidates.add(
                            product_id.replace("daraz-", "", 1)
                        )
                    else:
                        candidates.add(
                            "daraz-" + product_id
                        )

                    if product_id in candidates:
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
