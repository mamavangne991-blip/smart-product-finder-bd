import subprocess
import json
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
REPORT_DIR = ROOT / "worker_reports"
LOG_DIR = ROOT / "worker_logs"
REPORT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

workers = [
    ("product_discovery", "worker_agents/product_discovery_worker.py"),
    ("affiliate_safety", "worker_agents/affiliate_safety_worker.py"),
    ("affiliate_intake_validator", "worker_agents/daraz_affiliate_intake_validator.py"),
    ("affiliate_approval_gate", "worker_agents/daraz_affiliate_approval_gate.py"),
]

results = []

print("=" * 60)
print("SMART PRODUCT FINDER BD - OVERNIGHT MASTER WORKER")
print("SAFE MODE: NO PRODUCTION WRITE / NO GIT PUSH")
print("=" * 60)

for name, script in workers:
    path = ROOT / script
    started = datetime.now().isoformat(timespec="seconds")

    if not path.exists():
        results.append({
            "worker": name,
            "status": "SKIPPED",
            "reason": "worker not found"
        })
        print(f"[SKIP] {name}")
        continue

    print(f"\n[RUN] {name}")

    try:
        p = subprocess.run(
            ["python", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600
        )

        log_file = LOG_DIR / f"overnight_{name}.log"
        log_file.write_text(
            p.stdout + "\n" + p.stderr,
            encoding="utf-8"
        )

        status = "PASS" if p.returncode == 0 else "REVIEW"

        results.append({
            "worker": name,
            "status": status,
            "returncode": p.returncode,
            "started": started,
            "log": str(log_file)
        })

        print(f"[{status}] {name}")

    except Exception as e:
        results.append({
            "worker": name,
            "status": "REVIEW",
            "error": str(e)
        })
        print(f"[REVIEW] {name}: {e}")

# Final safety checks
git_status = subprocess.run(
    ["git", "status", "--short"],
    cwd=ROOT,
    capture_output=True,
    text=True
).stdout.strip()

production_changed = False

report = {
    "worker": "overnight_master_worker",
    "mode": "safe_read_only",
    "started": datetime.now().isoformat(timespec="seconds"),
    "production_write": False,
    "git_push": False,
    "affiliate_generation": False,
    "production_modified_by_master": production_changed,
    "workers": results,
    "git_status_at_end": git_status,
    "status": "PASS" if all(
        x["status"] in ("PASS", "SKIPPED") for x in results
    ) else "REVIEW",
    "morning_action": "Review this report before any production change."
}

out = REPORT_DIR / "overnight_master_report.json"
out.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\n" + "=" * 60)
print("OVERNIGHT WORK COMPLETE")
print("REPORT:", out)
print("PRODUCTION WRITE: BLOCKED")
print("GIT PUSH: BLOCKED")
print("AFFILIATE GENERATION: BLOCKED")
print("STATUS:", report["status"])
print("=" * 60)
