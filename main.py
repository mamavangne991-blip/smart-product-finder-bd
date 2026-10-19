
import os
import json
import requests
from flask import Flask, request
from google import genai
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 📂 ফাইল থেকে অসংখ্য প্রোডাক্ট স্বয়ংক্রিয়ভাবে লোড করার ফাংশন
def load_products():
    if os.path.exists("products.json"):
        with open("products.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "id": 1,
            "name": "Default Gadget Item",
            "original_price": "500",
            "discount_price": "199",
            "sales_badge": "🔥 হট ডিল",
            "affiliate_link": "https://www.daraz.com.bd/"
        }
    ]

current_product_index = 0

def generate_caption(product):
    if not client:
        return "API Key missing!"
    
    prompt = f"""
    Role: You are an expert Digital Marketer and Copywriter for Bangladeshi e-commerce (Daraz/Affiliate).
    Task: Write an engaging Bengali social media caption for this product offer.

    Product Name: {product['name']}
    Original Price: {product['original_price']} BDT
    Offer Price: {product['discount_price']} BDT
    Badge: {product['sales_badge']}

    Requirements:
    1. Catchy headline with emojis.
    2. Short practical hook.
    3. 3 benefit bullet points.
    4. Call to Action (CTA) with link: {product['affiliate_link']}
    5. 5 trending hashtags.
    """
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    return response.text

def post_to_all_platforms(product, caption):
    if not MAKE_WEBHOOK_URL:
        return {"status": "Webhook URL missing"}
    
    payload = {
        "product_name": product["name"],
        "caption": caption,
        "discount_price": product["discount_price"],
        "original_price": product["original_price"],
        "badge": product["sales_badge"],
        "affiliate_link": product["affiliate_link"]
    }
    res = requests.post(MAKE_WEBHOOK_URL, json=payload)
    return res.json()

def auto_post_job():
    global current_product_index
    products = load_products()
    if not products:
        return
    
    product = products[current_product_index % len(products)]
    caption = generate_caption(product)
    webhook_res = post_to_all_platforms(product, caption)
    print(f"Auto Posted: {webhook_res}")
    
    current_product_index += 1

# ব্যাকগ্রাউন্ড শিডিউলার (প্রতি ২ ঘণ্টা পরপর অটো পোস্ট)
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(auto_post_job, 'interval', hours=2)
scheduler.start()

@app.route("/")
def home():
    products = load_products()
    cards_html = ""
    for product in products:
        cards_html += f"""
        <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <span style="background: #e1f5fe; color: #0288d1; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">{product['sales_badge']}</span>
            <h3 style="margin: 12px 0 8px 0; color: #333;">{product['name']}</h3>
            <p style="margin: 0 0 15px 0; color: #666;">
                মূল্য: <span style="text-decoration: line-through; color: #888;">৳{product['original_price']}</span> 
                <strong style="color: #e53935; font-size: 18px; margin-left: 8px;">৳{product['discount_price']}</strong>
            </p>
            <a href="/trigger-post?id={product['id']}" style="display: inline-block; background: #0088cc; color: white; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; font-size: 14px;">🚀 Post to All Social Media</a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="bn">
    <head><meta charset="UTF-8"><title>Smart Product Finder BD</title></head>
    <body style="font-family: Arial; background-color: #f4f6f9; margin: 0; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #0088cc, #005f9e); color: white; padding: 25px; border-radius: 12px; text-align: center;">
                <h1 style="margin:0;">🚀 Smart Product Finder BD</h1>
                <p>Dynamic Multi-Platform Affiliate System ({len(products)} Products Loaded)</p>
            </div>
            <h2 style="color: #444; margin-top: 25px;">📦 প্রোডাক্ট তালিকা</h2>
            {cards_html}
        </div>
    </body>
    </html>
    """

@app.route("/trigger-post")
def trigger_post():
    product_id = request.args.get('id', default=1, type=int)
    products = load_products()
    product_to_post = next((p for p in products if p['id'] == product_id), products[0])
    
    try:
        caption = generate_caption(product_to_post)
        webhook_result = post_to_all_platforms(product_to_post, caption)
        return f"<h3>✅ Success! Post sent to Make.com</h3><pre>{webhook_result}</pre><br><a href='/'>Back</a>"
    except Exception as e:
        return f"<h3>Error:</h3> <p>{str(e)}</p><br><a href='/'>Go Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

