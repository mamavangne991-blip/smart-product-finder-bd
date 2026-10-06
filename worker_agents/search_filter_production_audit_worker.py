from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

REPORTS = {
    "runtime_v2": ROOT / "worker_reports/search_filter_runtime_v2_report.json",
    "count_audit": ROOT / "worker_reports/search_filter_count_audit_report.json",
}

results = []

def load_report(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

runtime = load_report(REPORTS["runtime_v2"])
count = load_report(REPORTS["count_audit"])

results.append(("runtime_v2_report_exists", runtime is not None))
results.append(("count_audit_report_exists", count is not None))

if runtime:
    by_test = {x.get("test"): x for x in runtime if isinstance(x, dict)}

    results.append((
        "shampoo_500_http_200",
        by_test.get("shampoo_under_500", {}).get("http") == 200
    ))
    results.append((
        "shampoo_1000_http_200",
        by_test.get("shampoo_under_1000", {}).get("http") == 200
    ))
    results.append((
        "charger_1000_http_200",
        by_test.get("charger_under_1000", {}).get("http") == 200
    ))

if count:
    by_test = {x.get("test"): x for x in count if isinstance(x, dict)}

    shampoo500 = by_test.get("shampoo_500", {})
    shampoo1000 = by_test.get("shampoo_1000", {})
    charger1000 = by_test.get("charger_1000", {})

    results.append((
        "shampoo_500_returns_zero",
        "0" in shampoo500.get("nearby_numbers", [])
    ))
    results.append((
        "shampoo_1000_returns_one",
        "1" in shampoo1000.get("nearby_numbers", [])
    ))
    results.append((
        "charger_1000_returns_two",
        "2" in charger1000.get("nearby_numbers", [])
    ))

status = "PASS" if all(ok for _, ok in results) else "FAIL"

report = {
    "worker": "search_filter_production_audit_worker",
    "mode": "READ_ONLY",
    "status": status,
    "checks": [
        {"check": name, "pass": ok}
        for name, ok in results
    ],
}

out = ROOT / "worker_reports/search_filter_production_audit_report.json"
out.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 60)
print("SEARCH/FILTER PRODUCTION AUDIT WORKER")
print("=" * 60)
print("MODE: READ-ONLY")
print()

for name, ok in results:
    print(("PASS" if ok else "FAIL") + ":", name)

print()
print("FINAL STATUS:", status)
print("REPORT:", out)
print("NO FILE DELETION")
print("NO GIT PUSH")
print("=" * 60)

raise SystemExit(0 if status == "PASS" else 1)
