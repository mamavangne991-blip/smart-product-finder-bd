from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import re
import json

BASE = "http://127.0.0.1:18080"
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "worker_reports/search_filter_runtime_v2_report.json"

tests = [
    ("shampoo_under_500", {"q": "shampoo", "budget": "500"}),
    ("shampoo_under_1000", {"q": "shampoo", "budget": "1000"}),
    ("charger_under_1000", {"q": "charger", "budget": "1000"}),
    ("empty_search", {}),
]

results = []

for name, params in tests:
    url = BASE + "/"
    if params:
        url += "?" + urlencode(params)

    try:
        with urlopen(url, timeout=10) as r:
            body = r.read().decode("utf-8", errors="ignore")
            status = r.status

        found = re.findall(
            r"Products Found:\s*</?[^>]*>\s*(\d+)",
            body,
            re.IGNORECASE
        )

        results.append({
            "test": name,
            "url": url,
            "http": status,
            "body_bytes": len(body),
            "products_found": found,
            "tresemme_present": "TRESemme" in body,
            "shampoo_present": "Shampoo" in body,
            "charger_present": "Charger" in body,
        })

    except Exception as e:
        results.append({
            "test": name,
            "url": url,
            "error": str(e),
        })

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    json.dumps(results, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 60)
print("SMART PRODUCT FINDER BD")
print("SEARCH/FILTER RUNTIME V2 WORKER")
print("=" * 60)
print("MODE: READ-ONLY")
print("PARAMETERS: q + budget")
print("NO FILE MODIFICATION")
print("NO GIT PUSH")
print()

for r in results:
    print("TEST:", r["test"])
    print("URL :", r["url"])
    print("HTTP:", r.get("http"))
    print("FOUND:", r.get("products_found"))
    print("TRESemme:", r.get("tresemme_present"))
    print("Shampoo:", r.get("shampoo_present"))
    print("Charger:", r.get("charger_present"))
    if "error" in r:
        print("ERROR:", r["error"])
    print("-" * 60)

print("REPORT:", REPORT)
print("=" * 60)
