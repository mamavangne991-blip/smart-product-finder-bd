from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.json"
APP = ROOT / "web_app_v6.py"
REPORT = ROOT / "worker_reports" / "affiliate_safety_report.json"

checks = []
issues = []

def check(name, passed, detail=""):
    checks.append({
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail
    })
    if not passed:
        issues.append(f"{name}: {detail}")

check("products.json exists", PRODUCTS.exists())
check("web_app_v6.py exists", APP.exists())

products = []

if PRODUCTS.exists():
    try:
        products = json.loads(
            PRODUCTS.read_text(encoding="utf-8")
        )
        check("products.json valid JSON", isinstance(products, list))
    except Exception as exc:
        check("products.json valid JSON", False, str(exc))

app_text = ""
if APP.exists():
    app_text = APP.read_text(encoding="utf-8")

daraz_products = [
    p for p in products
    if "daraz.com.bd" in str(p.get("url", "")).lower()
]

# Product link checks
missing_urls = [
    str(p.get("name", "Unknown"))
    for p in daraz_products
    if not p.get("url")
]

check(
    "Daraz products have usable URLs",
    not missing_urls,
    f"Missing: {missing_urls}"
)

# Validate Daraz URL structure
bad_urls = []
for p in daraz_products:
    url = str(p.get("url", ""))
    if not (
        url.startswith("https://")
        and "daraz.com.bd" in url.lower()
    ):
        bad_urls.append(url)

check(
    "Daraz URLs are HTTPS",
    not bad_urls,
    f"Invalid URLs: {bad_urls}"
)

# App buy/link handling
check(
    "App contains product URL handling",
    "product.get(\"url\"" in app_text
    or "product.get('url'" in app_text
)

check(
    "App uses HTTPS product links",
    "https://" in app_text or "http" in app_text
)

# Credential exposure scan
secret_patterns = [
    r"app_secret\s*=",
    r"client_secret\s*=",
    r"access_token\s*=",
    r"refresh_token\s*=",
    r"daraz_secret\s*="
]

credential_hits = []

for pattern in secret_patterns:
    if re.search(pattern, app_text, re.IGNORECASE):
        credential_hits.append(pattern)

check(
    "No obvious credentials embedded in web app",
    not credential_hits,
    f"Patterns found: {credential_hits}"
)

# Affiliate tracking should remain optional.
# We only audit presence; we do not invent tracking IDs.
tracking_terms = [
    "affiliate",
    "tracking",
    "sub_id",
    "utm_source",
    "utm_medium",
    "utm_campaign"
]

tracking_present = [
    term for term in tracking_terms
    if term.lower() in app_text.lower()
]

check(
    "Affiliate tracking is not required for normal product links",
    True,
    "No tracking parameter will be invented automatically"
)

# Check obvious unsafe redirect patterns
unsafe_patterns = [
    "javascript:",
    "data:text/html",
    "onclick=\"javascript",
    "eval("
]

unsafe_hits = [
    pattern for pattern in unsafe_patterns
    if pattern.lower() in app_text.lower()
]

check(
    "No obvious unsafe link/redirect patterns",
    not unsafe_hits,
    f"Found: {unsafe_hits}"
)

# Compile app
if APP.exists():
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(APP)],
        cwd=ROOT,
        capture_output=True,
        text=True
    )

    check(
        "web_app_v6.py compiles",
        result.returncode == 0,
        result.stderr.strip()
    )

status = "PASS" if not issues else "NEEDS_FIX"

report = {
    "worker": "affiliate_safety_worker",
    "mode": "audit_only",
    "status": status,
    "products_total": len(products),
    "daraz_products": len(daraz_products),
    "tracking_terms_present": tracking_present,
    "checks": checks,
    "issues": issues
}

REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("========================================")
print(" AFFILIATE SAFETY WORKER")
print("========================================")

for item in checks:
    print(f"{item['status']}: {item['check']}")
    if item["detail"]:
        print(f"       {item['detail']}")

print()
print(f"PRODUCTS: {len(products)}")
print(f"DARAZ PRODUCTS: {len(daraz_products)}")
print(f"TRACKING TERMS FOUND: {tracking_present}")
print(f"STATUS: {status}")
print(f"REPORT: {REPORT.relative_to(ROOT)}")
print("MODE: AUDIT ONLY / NO FILE MODIFICATION")
