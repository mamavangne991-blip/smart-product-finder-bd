import os
import requests
from google import genai

# Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini Setup
client = genai.Client(api_key=GEMINI_API_KEY)

# 📱 ইলেকট্রনিক্স গ্যাজেট লিস্ট (অতিরিক্ত সেল হওয়া আইটেমগুলো র‍্যাংক অনুযায়ী প্রথমে রাখা হয়েছে)
BEST_SELLING_GADGETS = [
    {
        "name": "TWS M10 / F9 Bluetooth Wireless Earbuds with Power Bank",
        "original_price": "850",
        "discount_price": "349",
        "sales_badge": "🔥 ২০,০০০+ পিস বিক্রি হয়েছে! (Top Seller)",
        "affiliate_link": "https://www.daraz.com.bd/" # আপনার দারাজ অ্যাফিলিয়েট লিংক
    },
    {
        "name": "T800 Ultra Smartwatch with Large HD Display",
        "original_price": "1800",
        "discount_price": "790",
        "sales_badge": "⚡ দারাজের সেরা বিক্রীত স্মার্টওয়াচ",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "name": "10000mAh Fast Charging Dual USB Power Bank",
        "original_price": "1500",
        "discount_price": "890",
        "sales_badge": "🔋 কাস্টমারদের সেরা পছন্দ",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "name": "26cm LED Ring Light with Tripod Stand for Video & Content Creation",
        "original_price": "1200",
        "discount_price": "550",
        "sales_badge": "📸 ট্রেন্ডিং কনটেন্ট ক্রিয়েটর চয়েস",
        "affiliate_link": "https://www.daraz.com.bd/"
    },
    {
        "name": "K8 / K9 Wireless Lavalier Microphone for Type-C & iPhone",
        "original_price": "950",
        "discount_price": "420",
        "sales_badge": "🎙️ ৫,০০০+ রিভিউ ও হাই স্যাটিসফ্যাকশন",
        "affiliate_link": "https://www.daraz.com.bd/"
    }
]

def generate_caption(product):
    prompt = f"""
    Create an extremely catchy and high-converting Bengali social media post for Daraz affiliate marketing.
    Product: {product['name']}
    Original Price: {product['original_price']} BDT
    Discount Price: {product['discount_price']} BDT
    Highlight Note: {product['sales_badge']}
    
    Structure:
    1. Attention grabbing headline with Emojis.
    2. Mention that it's a huge discount / best-selling gadget.
    3. Bullet points of top 3 features.
    4. Call to action to buy immediately.
    Keep it concise and clear.
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

def post_to_telegram(caption, product_link):
    message = f"{caption}\n\n🛒 **অফার মূল্যে কিনতে লিংকে ক্লিক করুন:**\n👉 {product_link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload)
    return res.json()

if __name__ == "__main__":
    # টপ সেলিং প্রডাক্ট থেকে প্রথম আইটেমটি পিক করা হচ্ছে
    product_to_post = BEST_SELLING_GADGETS[0] 
    
    print(f"Generating AI Caption for Best Selling Gadget: {product_to_post['name']}...")
    caption = generate_caption(product_to_post)
    
    print("Posting to Telegram Channel...")
    result = post_to_telegram(caption, product_to_post["affiliate_link"])
    print("Completed!", result)
    
