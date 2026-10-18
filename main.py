import os
import requests
from flask import Flask
from google import genai

app = Flask(__name__)

# Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini Setup
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 📱 ইলেকট্রনিক্স গ্যাজেট লিস্ট
BEST_SELLING_GADGETS = [
    {
        "id": 1,
        "name": "TWS M10 / F9 Bluetooth Wireless Earbuds with Power Bank",
        "original_price": "850",
        "discount_price": "349",
        "sales_badge": "🔥 ২০,০০০+ পিস বিক্রি হয়েছে!",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "id": 2,
        "name": "T800 Ultra Smartwatch with Large HD Display",
        "original_price": "1800",
        "discount_price": "790",
        "sales_badge": "⚡ দারাজের সেরা বিক্রীত স্মার্টওয়াচ",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "id": 3,
        "name": "10000mAh Fast Charging Dual USB Power Bank",
        "original_price": "1500",
        "discount_price": "890",
        "sales_badge": "🔋 কাস্টমারদের সেরা পছন্দ",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "id": 4,
        "name": "26cm LED Ring Light with Tripod Stand for Content Creation",
        "original_price": "1200",
        "discount_price": "550",
        "sales_badge": "📸 ট্রেন্ডিং কনটেন্ট ক্রিয়েটর চয়েস",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "id": 5,
        "name": "K8 / K9 Wireless Lavalier Microphone",
        "original_price": "950",
        "discount_price": "420",
        "sales_badge": "🎙️ ৫,০০০+ রিভিউ ও হাই স্যাটিসফ্যাকশন",
        "affiliate_link": "https://www.daraz.com.bd/"
    }
]

def generate_caption(product):
    if not client:
        return "API Key missing!"
    prompt = f"""
    Create an extremely catchy Bengali social media post for Daraz affiliate marketing.
    Product: {product['name']}
    Original Price: {product['original_price']} BDT
    Discount Price: {product['discount_price']} BDT
    Highlight Note: {product['sales_badge']}

    Structure:
    1. Attention grabbing headline with Emojis.
    2. Mention that it's a huge discount / best-selling gadget.
    3. Bullet points of top 3 features.
    4. Call to action to buy immediately.
    Keep it concise and clear. Do not use markdown symbols that break payload.
    """
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    return response.text

def post_to_telegram(caption, product_link):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return {"status": "Telegram tokens missing"}
    
    message = f"{caption}\n\n🛒 অফার মূল্যে কিনতে লিংকে ক্লিক করুন:\n👉 {product_link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    res = requests.post(url, json=payload)
    return res.json()

# 🌐 সুন্দর ড্যাশবোর্ড রুট
@app.route("/")
def home():
    cards_html = ""
    for product in BEST_SELLING_GADGETS:
        cards_html += f"""
        <div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <span style="background: #e1f5fe; color: #0288d1; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">{product['sales_badge']}</span>
            <h3 style="margin: 12px 0 8px 0; color: #333;">{product['name']}</h3>
            <p style="margin: 0 0 15px 0; color: #666;">
                মূল্য: <span style="text-decoration: line-through; color: #888;">৳{product['original_price']}</span> 
                <strong style="color: #e53935; font-size: 18px; margin-left: 8px;">৳{product['discount_price']}</strong>
            </p>
            <a href="/trigger-post?id={product['id']}" style="display: inline-block; background: #0088cc; color: white; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; font-size: 14px;">🚀 Generate AI Post</a>
        </div>
        """

    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="bn">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Smart Product Finder BD - Admin Dashboard</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #0088cc, #005f9e); color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <h1 style="margin: 0; font-size: 26px;">🚀 Smart Product Finder BD</h1>
                <p style="margin-top: 8px; opacity: 0.9; font-size: 14px;">AI-Powered Affiliate Automation Dashboard</p>
            </div>

            <!-- Stats -->
            <div style="display: flex; gap: 15px; margin-bottom: 25px;">
                <div style="flex: 1; background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0; color: #777;">মোট প্রোডাক্ট</h4>
                    <h2 style="margin: 5px 0 0 0; color: #0088cc;">{len(BEST_SELLING_GADGETS)}টি</h2>
                </div>
                <div style="flex: 1; background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0; color: #777;">ইঞ্জিন স্ট্যাটাস</h4>
                    <h2 style="margin: 5px 0 0 0; color: #4caf50;">Active 🟢</h2>
                </div>
            </div>

            <h2 style="color: #444; margin-bottom: 15px;">📦 ট্রেন্ডিং প্রোডাক্ট লিস্ট</h2>
            {cards_html}

        </div>
    </body>
    </html>
    """
    return dashboard_html

# 🌐 পোস্ট জেনারেট রুট
@app.route("/trigger-post")
def trigger_post():
    from flask import request
    product_id = request.args.get('id', default=1, type=int)
    
    # আইডি অনুযায়ী প্রোডাক্ট নির্বাচন
    product_to_post = next((p for p in BEST_SELLING_GADGETS if p['id'] == product_id), BEST_SELLING_GADGETS[0])
    
    try:
        caption = generate_caption(product_to_post)
        result = post_to_telegram(caption, product_to_post["affiliate_link"])
        return f"""
        <div style="font-family: Arial; padding: 30px; max-width: 600px; margin: 40px auto; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #4caf50;">✅ AI Post Generated Successfully!</h2>
            <p><strong>Product:</strong> {product_to_post['name']}</p>
            <h3>Response:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 6px; overflow-x: auto;">{result}</pre>
            <br>
            <a href="/" style="background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">⬅️ Back to Dashboard</a>
        </div>
        """
    except Exception as e:
        return f"<h3>Error:</h3> <p>{str(e)}</p><br><a href='/'>Go Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

