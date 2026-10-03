import json
import time
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
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass


def load_token():
    if not TOKEN_FILE.exists():
        return None

    return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))


def _sign_api_request(api_path, params):
    """
    Daraz/LazOP style request signing.
    The signature is generated locally and the App Secret is never printed.
    """
    if not APP_KEY or not APP_SECRET:
        raise RuntimeError("DARAZ_APP_KEY or DARAZ_APP_SECRET is missing")

    params = {str(k): str(v) for k, v in params.items() if v is not None}
    params["app_key"] = APP_KEY
    params["sign_method"] = "sha256"

    sorted_items = sorted(params.items())
    query_string = "".join(
        urllib.parse.quote(str(k), safe="-_.~")
        + urllib.parse.quote(str(v), safe="-_.~")
        for k, v in sorted_items
    )

    sign_string = api_path + query_string
    signature = hashlib.sha256(
        (APP_SECRET + sign_string + APP_SECRET).encode("utf-8")
    ).hexdigest().upper()

    params["sign"] = signature
    return params


def create_access_token(code):
    if not code:
        raise ValueError("Authorization code is required")

    api_path = "/auth/token/create"
    params = _sign_api_request(
        api_path,
        {
            "code": code,
        },
    )

    response = requests.get(
        API_BASE_URL + api_path,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    save_token(data)
    return data


def refresh_access_token():
    token_data = load_token()

    if not token_data:
        raise RuntimeError("No saved Daraz token found")

    refresh_token = token_data.get("refresh_token")

    if not refresh_token:
        raise RuntimeError("No refresh_token found")

    api_path = "/auth/token/refresh"
    params = _sign_api_request(
        api_path,
        {
            "refresh_token": refresh_token,
        },
    )

    response = requests.get(
        API_BASE_URL + api_path,
        params=params,
        timeout=30,
    )
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
    print("App Key:", APP_KEY)
    print("App Secret:", "SET" if APP_SECRET else "EMPTY")
    print("Callback URL:", CALLBACK_URL)
    print()
    print("Authorization URL:")
    print(get_authorization_url())
