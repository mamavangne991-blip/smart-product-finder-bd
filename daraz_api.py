import json
import time
import hmac
import hashlib
import urllib.parse
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

APP_KEY = os.getenv("DARAZ_APP_KEY")
APP_SECRET = os.getenv("DARAZ_APP_SECRET")

CALLBACK_URL = os.getenv("DARAZ_CALLBACK_URL")
AUTH_URL = "https://api.daraz.com.bd/oauth/authorize"
API_BASE_URL = os.getenv("DARAZ_API_BASE", "https://api.daraz.com.bd/rest")

TOKEN_FILE = Path("daraz_token.json")


def get_authorization_url():
    params = {
        "response_type": "code",
        "force_auth": "true",
        "redirect_uri": CALLBACK_URL,
        "client_id": APP_KEY,
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def save_token(token_data):
    TOKEN_FILE.write_text(
        json.dumps(token_data, indent=2),
        encoding="utf-8"
    )


def load_token():
    if not TOKEN_FILE.exists():
        return None

    return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))


def create_access_token(code):
    url = API_BASE_URL + "/auth/token/create"

    params = {
        "code": code
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    save_token(data)

    return data


def get_access_token():
    token_data = load_token()

    if not token_data:
        return None

    return token_data.get("access_token")


if __name__ == "__main__":
    print("Daraz OAuth/API module ready.")
    print()
    print("Authorization URL:")
    print(get_authorization_url())
