import os
import requests
from google import genai

# Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini Setup
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_caption(product_name, original_price, discount_price):
    prompt = f"""
    Create an attractive Bengali social media post for Daraz affiliate marketing.
    Product: {product_name}
    Original Price: {original_price} BDT
    Discount Price: {discount_price} BDT
    Include emojis, clear bullet points, and a strong call to action (CTA). Keep it concise and catchy.
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

def post_to_telegram(caption, product_link):
    message = f"{caption}\n\n👉 **কেনার লিংক:** {product_link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload)
    return res.json()

if __name__ == "__main__":
    # ডেমো প্রডাক্ট ডেটা
    sample_product = {
        "name": "Wireless Bluetooth Earbuds Pro",
        "original_price": "1500",
        "discount_price": "750",
        "affiliate_link": "https://www.daraz.com.bd/"
    }
    
    print("Generating AI Caption...")
    caption = generate_caption(
        sample_product["name"], 
        sample_product["original_price"], 
        sample_product["discount_price"]
    )
    
    print("Posting to Telegram Channel...")
    result = post_to_telegram(caption, sample_product["affiliate_link"])
    print("Completed!", result)
        
