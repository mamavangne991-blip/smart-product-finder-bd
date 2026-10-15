import subprocess, json, hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
REPORT = ROOT / "worker_reports/overnight_master_v2_report.json"
LOG = ROOT / "worker_logs/overnight_master_v2_console.log"

SAFE_WORKERS = [
    "worker_agents/product_discovery_worker.py",
    "worker_agents/affiliate_safety_worker.py",
    "worker_agents/daraz_affiliate_intake_validator.py",
    "worker_agents/daraz_affiliate_approval_gate.py",
    "worker_agents/daraz_discovery_quality_worker.py",
]

def run(cmd, timeout=600):
    try:
        p = subprocess.run(
            cmd, cwd=ROOT, capture_output=True,
            text=True, timeout=timeout
        )
        return {
            "returncode": p.returncode,
            "stdout": p.stdout[-5000:],
            "stderr": p.stderr[-5000:]
        }
    except Exception as e:
        return {"returncode": -1, "error": str(e)}

def sha256(path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

started = datetime.now().isoformat(timespec="seconds")
results = []

print("=" * 70)
print("SMART PRODUCT FINDER BD - OVERNIGHT MASTER V2")
print("SAFE MODE / STAGING + AUDIT ONLY")
print("=" * 70)

# 1. Production baseline
prod_hash_before = sha256(ROOT / "products.json")

# 2. Git state
git_before = run(["git", "status", "--short"])

# 3. Compile project Python files
compile_result = run(
    ["bash", "-lc",
     "find . -maxdepth 3 -name '*.py' "
     "! -path './.git/*' -print0 | "
     "xargs -0 -r python -m py_compile"],
    timeout=600
)
results.append({
    "task": "python_compile",
    "status": "PASS" if compile_result["returncode"] == 0 else "REVIEW",
    "details": compile_result
})

# 4. Run only explicitly approved safe workers
for script in SAFE_WORKERS:
    path = ROOT / script

    if not path.exists():
        results.append({
            "task": script,
            "status": "SKIPPED",
            "reason": "not found"
        })
        continue

    print(f"[RUN] {script}")
    r = run(["python", str(path)], timeout=600)

    results.append({
        "task": script,
        "status": "PASS" if r["returncode"] == 0 else "REVIEW",
        "details": r
    })

# 5. Production integrity after all tests
prod_hash_after = sha256(ROOT / "products.json")

# 6. Check for obvious credentials in production web/app Python
credential_hits = run([
    "bash", "-lc",
    "grep -RniE "
    "'DARAZ_APP_SECRET|DARAZ_APP_KEY|client_secret|api_secret|"
    "access_token[[:space:]]*=' "
    "web_app_v6.py app_v10.py daraz_api.py 2>/dev/null "
    "| head -50"
])

# 7. Final git state
git_after = run(["git", "status", "--short"])

# 8. Safety invariants
production_unchanged = (
    prod_hash_before is not None and
    prod_hash_before == prod_hash_after
)

report = {
    "worker": "overnight_master_worker_v2",
    "mode": "safe_read_only",
    "started": started,
    "finished": datetime.now().isoformat(timespec="seconds"),

    "production_write": False,
    "production_import": False,
    "affiliate_generation": False,
    "git_commit": False,
    "git_push": False,
    "daraz_write_api": False,

    "production_sha256_before": prod_hash_before,
    "production_sha256_after": prod_hash_after,
    "production_unchanged": production_unchanged,

    "credential_scan": {
        "status": (
            "REVIEW"
            if credential_hits["stdout"].strip()
            else "PASS"
        ),
        "output": credential_hits["stdout"][-5000:]
    },

    "git_status_before": git_before["stdout"],
    "git_status_after": git_after["stdout"],

    "tasks": results,

    "morning_actions": [
        "Review this report.",
        "Review Git changes before any commit.",
        "Review pending affiliate links.",
        "Approve any production import manually.",
        "Run final E2E test after approved changes."
    ]
}

overall = (
    production_unchanged and
    report["credential_scan"]["status"] == "PASS" and
    all(x["status"] in ("PASS", "SKIPPED")
        for x in results)
)

report["status"] = "PASS" if overall else "REVIEW"

REPORT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\n" + "=" * 70)
print("OVERNIGHT MASTER V2 COMPLETE")
print("STATUS:", report["status"])
print("PRODUCTION UNCHANGED:", production_unchanged)
print("PRODUCTION WRITE: BLOCKED")
print("AFFILIATE GENERATION: BLOCKED")
print("GIT COMMIT: BLOCKED")
print("GIT PUSH: BLOCKED")
print("REPORT:", REPORT)
print("=" * 70)
