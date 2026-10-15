import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
REPORT = Path("worker_reports/overnight_master_v3_report.json")
LOG = Path("worker_logs/overnight_master_v3.log")

LOG.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)

PRODUCTION = Path("products.json")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(cmd):
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    return p.returncode, p.stdout[-4000:], p.stderr[-4000:]

before_hash = sha256(PRODUCTION)

# শুধু active production files + active worker files
active_files = [
    "web_app_v6.py",
    "app_v10.py",
    "daraz_api.py",
    "daraz_callback.py",
    "daraz_config.py",
    "product_research_agent.py",
    "product_research_agent_v2.py",
]

worker_dir = Path("worker_agents")
if worker_dir.exists():
    for p in sorted(worker_dir.glob("*.py")):
        name = p.name.lower()
        if not any(x in name for x in ["backup", ".bak", "_old", "_archive"]):
            active_files.append(str(p))

results = []

# Compile active files only
compile_failed = []
for f in active_files:
    if not Path(f).exists():
        continue
    rc, out, err = run(f"python -m py_compile {f}")
    if rc != 0:
        compile_failed.append({
            "file": f,
            "error": err[-1000:]
        })

results.append({
    "task": "active_python_compile",
    "status": "PASS" if not compile_failed else "REVIEW",
    "failed": compile_failed,
})

# Safe credential scan
scan_files = [
    "web_app_v6.py",
    "app_v10.py",
    "daraz_api.py",
]

unsafe = []
safe_env_refs = []

for f in scan_files:
    p = Path(f)
    if not p.exists():
        continue

    for i, line in enumerate(
        p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
    ):
        low = line.lower()

        if "os.getenv(" in low or "os.environ.get(" in low:
            if any(x in low for x in [
                "daraz_app_key",
                "daraz_app_secret",
                "access_token",
                "client_secret",
                "api_secret",
            ]):
                safe_env_refs.append(f"{f}:{i}")

        # literal credential assignment-এর সম্ভাব্য pattern
        if any(key in low for key in [
            "daraz_app_secret =",
            "daraz_app_key =",
            "client_secret =",
            "api_secret =",
        ]):
            if "os.getenv(" not in low and "os.environ.get(" not in low:
                unsafe.append(f"{f}:{i}")

results.append({
    "task": "credential_scan",
    "status": "PASS" if not unsafe else "REVIEW",
    "unsafe_matches": unsafe,
    "safe_environment_references": safe_env_refs,
})

# Existing safety workers — read-only
workers = [
    "worker_agents/product_discovery_worker.py",
    "worker_agents/affiliate_safety_worker.py",
    "worker_agents/daraz_affiliate_intake_validator.py",
    "worker_agents/daraz_affiliate_approval_gate.py",
    "worker_agents/daraz_discovery_quality_worker.py",
]

worker_results = []

for w in workers:
    if not Path(w).exists():
        worker_results.append({"worker": w, "status": "MISSING"})
        continue

    rc, out, err = run(f"python {w}")
    worker_results.append({
        "worker": w,
        "status": "PASS" if rc == 0 else "REVIEW",
        "output": out[-1500:],
        "error": err[-1000:] if rc else "",
    })

results.extend(worker_results)

after_hash = sha256(PRODUCTION)

overall = (
    "PASS"
    if before_hash == after_hash
    and not compile_failed
    and not unsafe
    and all(x["status"] == "PASS" for x in worker_results if x["status"] != "MISSING")
    else "REVIEW"
)

report = {
    "worker": "overnight_master_worker_v3",
    "timestamp": datetime.now().isoformat(),
    "mode": "safe_read_only",
    "overall_status": overall,
    "production_hash_before": before_hash,
    "production_hash_after": after_hash,
    "production_unchanged": before_hash == after_hash,
    "production_write": False,
    "affiliate_generation": False,
    "git_commit": False,
    "git_push": False,
    "results": results,
}

REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print("======================================")
print("OVERNIGHT MASTER WORKER V3")
print("======================================")
print("STATUS:", overall)
print("PRODUCTION UNCHANGED:", before_hash == after_hash)
print("PRODUCTION WRITE:", False)
print("AFFILIATE GENERATION:", False)
print("GIT COMMIT:", False)
print("GIT PUSH:", False)
print("ACTIVE COMPILE FAILURES:", len(compile_failed))
print("UNSAFE CREDENTIAL MATCHES:", len(unsafe))
print("REPORT:", REPORT)
