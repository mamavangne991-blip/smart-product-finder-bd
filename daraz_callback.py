from flask import Flask, request

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if code:
        return f"Daraz authorization code received: {code}"
    return "Daraz callback endpoint is working."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
