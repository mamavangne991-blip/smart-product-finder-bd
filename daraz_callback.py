from flask import Flask, request
import json
import time
from pathlib import Path

app = Flask(__name__)

TOKEN_FILE = Path("daraz_token.json")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return "Daraz authorization failed. Please try again.", 400

    if code:
        TOKEN_FILE.write_text(
            json.dumps(
                {
                    "authorization_code": code,
                    "received_at": int(time.time())
                },
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        try:
            TOKEN_FILE.chmod(0o600)
        except OSError:
            pass

        return (
            "Daraz authorization code received successfully. "
            "You can close this page."
        )

    return "Daraz callback endpoint is working."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
