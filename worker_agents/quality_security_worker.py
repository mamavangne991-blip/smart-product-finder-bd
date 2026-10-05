from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "worker_reports"
REPORT = REPORT_DIR / "quality_security_report.json"

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

# --------------------------------------------------
# 1. Required files
# --------------------------------------------------

required_files = [
    "products.json",
    "product_recommendations.json",
    "web_app_v6.py",
    "daraz_api.py",
    "daraz_public_import.py",
    "worker_orchestrator.py",
]

for filename in required_files:
    check(
        f"{filename} exists",
        (ROOT / filename).exists()
    )

# --------------------------------------------------
# 2. JSON integrity
# --------------------------------------------------

json_files = [
    "products.json",
    "product_recommendations.json",
    "daraz_public_products.json",
]

for filename in json_files:
    path = ROOT / filename

    if not path.exists():
        continue

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        check(
            f"{filename} valid JSON",
            True,
            f"type={type(data).__name__}"
        )
    except Exception as exc:
        check(
            f"{filename} valid JSON",
            False,
            str(exc)
        )

# --------------------------------------------------
# 3. Product/recommendation integrity
# --------------------------------------------------

products = []
recs = []

try:
    products = json.loads(
        (ROOT / "products.json").read_text(encoding="utf-8")
    )
except Exception:
    pass

try:
    recs = json.loads(
        (ROOT / "product_recommendations.json").read_text(
            encoding="utf-8"
        )
    )
except Exception:
    pass

if isinstance(products, list) and isinstance(recs, list):

    product_ids = {
        str(p.get("id") or p.get("item_id"))
        for p in products
        if p.get("id") or p.get("item_id")
    }

    rec_ids = {
        str(r.get("id") or r.get("item_id"))
        for r in recs
        if r.get("id") or r.get("item_id")
    }

    check(
        "Recommendation coverage is complete",
        product_ids == rec_ids,
        f"products={len(product_ids)}, recommendations={len(rec_ids)}"
    )

    ranks = [
        r.get("recommendation_rank")
        for r in recs
        if r.get("recommendation_rank") is not None
    ]

    expected = list(range(1, len(ranks) + 1))

    check(
        "Recommendation ranks are sequential",
        sorted(ranks) == expected and len(ranks) == len(set(ranks)),
        f"count={len(ranks)}"
    )

# --------------------------------------------------
# 4. Credential/security scan
# --------------------------------------------------

security_files = [
    "web_app_v6.py",
    "daraz_api.py",
    "daraz_public_import.py",
    "worker_orchestrator.py",
]

secret_patterns = [
    r"app_secret\s*=\s*['\"][^'\"]+['\"]",
    r"client_secret\s*=\s*['\"][^'\"]+['\"]",
    r"access_token\s*=\s*['\"][^'\"]+['\"]",
    r"refresh_token\s*=\s*['\"][^'\"]+['\"]",
    r"daraz_secret\s*=\s*['\"][^'\"]+['\"]",
]

credential_hits = []

for filename in security_files:
    path = ROOT / filename

    if not path.exists():
        continue

    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    for pattern in secret_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            credential_hits.append(filename)

check(
    "No obvious hard-coded credentials",
    not credential_hits,
    f"Files: {sorted(set(credential_hits))}"
)

# --------------------------------------------------
# 5. .env protection
# --------------------------------------------------

env_file = ROOT / ".env"
gitignore = ROOT / ".gitignore"

check(
    ".env is not committed by Git",
    True if not gitignore.exists()
    else ".env" in gitignore.read_text(encoding="utf-8")
)

if env_file.exists():
    try:
        mode = env_file.stat().st_mode & 0o777
        check(
            ".env permissions are restrictive",
            mode & 0o077 == 0,
            oct(mode)
        )
    except Exception as exc:
        check(".env permissions check", False, str(exc))

# --------------------------------------------------
# 6. Python compilation
# --------------------------------------------------

python_files = [
    "web_app_v6.py",
    "daraz_api.py",
    "daraz_public_import.py",
    "worker_orchestrator.py",
]

for filename in python_files:
    path = ROOT / filename

    if not path.exists():
        continue

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True
    )

    check(
        f"{filename} compiles",
        result.returncode == 0,
        result.stderr.strip()
    )

# --------------------------------------------------
# 7. Git status audit — read only
# --------------------------------------------------

git_result = subprocess.run(
    ["git", "status", "--short"],
    cwd=ROOT,
    capture_output=True,
    text=True
)

check(
    "Git status readable",
    git_result.returncode == 0,
    git_result.stderr.strip()
)

# --------------------------------------------------
# Final report
# --------------------------------------------------

status = "PASS" if not issues else "NEEDS_FIX"

report = {
    "worker": "quality_security_worker",
    "mode": "audit_only",
    "status": status,
    "checks": checks,
    "issues": issues,
    "git_push": False,
    "files_deleted": False,
}

REPORT_DIR.mkdir(parents=True, exist_ok=True)

REPORT.write_text(
    json.dumps(
        report,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("========================================")
print(" QUALITY & SECURITY WORKER")
print("========================================")

for item in checks:
    print(f"{item['status']}: {item['check']}")
    if item["detail"]:
        print(f"       {item['detail']}")

print()
print("GIT STATUS:")
print(git_result.stdout.strip() or "(clean)")

print()
print(f"STATUS: {status}")
print(f"REPORT: {REPORT.relative_to(ROOT)}")
print("MODE: AUDIT ONLY / NO FILE MODIFICATION")
print("NO GIT PUSH")
print("NO FILE DELETION")
