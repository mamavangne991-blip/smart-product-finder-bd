import os
import requests
from flask import Flask, request
from google import genai
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Environment Variables / Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL")  # Make.com Webhook URL

# Gemini Client Setup
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 📱 প্রোডাক্ট ডাটাবেজ (এখানে আপনার প্রয়োজনমতো শত শত প্রোডাক্ট যোগ করতে পারবেন)
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

current_product_index = 0

def generate_caption(product):
    if not client:
        return "API Key missing!"
    
    # আপনার দেওয়া মাস্টার প্রম্পট স্ট্র্যাটেজি অনুযায়ী জেমিনি এআই ক্যাপশন জেনারেট করবে
    prompt = f"""
    Role: You are an expert Digital Marketer, E-commerce Specialist, and Conversion Rate Optimization (CRO) Copywriter focusing on Bangladeshi consumer trends (specifically for Daraz/Gadget Affiliate Marketing).

    Task: Write an extremely compelling, engaging, and high-converting Bengali social media post for an electronics gadget offer.

    Product Details:
    - Product Name: {product['name']}
    - Original Price: {product['original_price']} BDT
    - Offer Price: {product['discount_price']} BDT
    - Highlight Note: {product['sales_badge']}

    Requirements & Output Format:
    1. Catchy Headline: Create a scroll-stopping headline with relevant emojis that creates FOMO or highlights the huge discount.
    2. Emotional/Practical Hook: Explain in 1-2 lines why the user desperately needs this product in their daily life.
    3. Top 3 Feature Bullet Points: Clearly highlight 3 main benefits using bullet points.
    4. Urgency & Offer Call-To-Action (CTA): Add a clear instruction encouraging them to buy now before stock runs out.
    5. Hashtags: Include 5 trending hashtags.

    Keep it concise and clear. Do not use complex markdown syntax.
    """
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt,
    )
    return response.text

# 🌐 Make.com ওয়েবহুকের মাধ্যমে সব সোশ্যাল মিডিয়ায় পোস্ট পাঠানোর ফাংশন
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

# ⏰ অটোমেটেড শিডিউল জব (স্বয়ংক্রিয়ভাবে ব্যাকগ্রাউন্ডে পোস্ট পাঠাবে)
def auto_post_job():
    global current_product_index
    if not BEST_SELLING_GADGETS:
        return
    
    product = BEST_SELLING_GADGETS[current_product_index]
    caption = generate_caption(product)
    
    # ওয়েবহুকের মাধ্যমে সব সোশ্যাল মিডিয়ায় একসাথে রিকোয়েস্ট পাঠানো
    webhook_res = post_to_all_platforms(product, caption)
    print(f"Auto Posted Product #{product['id']} via Webhook: {webhook_res}")
    
    # পরবর্তী প্রোডাক্টের ইনডেক্স আপডেট
    current_product_index = (current_product_index + 1) % len(BEST_SELLING_GADGETS)

# ব্যাকগ্রাউন্ড শিডিউলার শুরু (প্রতি ২ ঘণ্টায় ১টি করে অটো পোস্ট)
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(auto_post_job, 'interval', hours=2)
scheduler.start()

# 🌐 ড্যাশবোর্ড রুট (ওয়েবসাইট হোমপেজ)
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
            <a href="/trigger-post?id={product['id']}" style="display: inline-block; background: #0088cc; color: white; text-decoration: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; font-size: 14px;">🚀 Post to All Social Media</a>
        </div>
        """

    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="bn">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Smart Product Finder BD - Multi-Platform Automation</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto;">
            
            <div style="background: linear-gradient(135deg, #0088cc, #005f9e); color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <h1 style="margin: 0; font-size: 26px;">🚀 Smart Product Finder BD</h1>
                <p style="margin-top: 8px; opacity: 0.9; font-size: 14px;">Multi-Platform AI Affiliate Automation Dashboard</p>
            </div>

            <div style="display: flex; gap: 15px; margin-bottom: 25px;">
                <div style="flex: 1; background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0; color: #777;">মোট প্রোডাক্ট</h4>
                    <h2 style="margin: 5px 0 0 0; color: #0088cc;">{len(BEST_SELLING_GADGETS)}টি</h2>
                </div>
                <div style="flex: 1; background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0; color: #777;">অটো-শিডিউলার</h4>
                    <h2 style="margin: 5px 0 0 0; color: #4caf50;">Every 2 Hours ⏱️</h2>
                </div>
            </div>

            <h2 style="color: #444; margin-bottom: 15px;">📦 প্রোডাক্ট তালিকা</h2>
            {cards_html}

        </div>
    </body>
    </html>
    """
    return dashboard_html

# 🌐 ম্যানুয়াল পোস্ট ট্রিগার রুট
@app.route("/trigger-post")
def trigger_post():
    product_id = request.args.get('id', default=1, type=int)
    product_to_post = next((p for p in BEST_SELLING_GADGETS if p['id'] == product_id), BEST_SELLING_GADGETS[0])
    
    try:
        caption = generate_caption(product_to_post)
        webhook_result = post_to_all_platforms(product_to_post, caption)
        
        return f"""
        <div style="font-family: Arial; padding: 30px; max-width: 600px; margin: 40px auto; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #4caf50;">✅ Multi-Platform Post Triggered!</h2>
            <p><strong>Product:</strong> {product_to_post['name']}</p>
            <h3>Webhook Response:</h3>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 6px;">{webhook_result}</pre>
            <br>
            <a href="/" style="background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">⬅️ Back to Dashboard</a>
        </div>
        """
    except Exception as e:
        return f"<h3>Error:</h3> <p>{str(e)}</p><br><a href='/'>Go Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

