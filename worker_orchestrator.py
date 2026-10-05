from pathlib import Path
import subprocess
import sys
import time
import json

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT / "worker_reports"
RUN_DIR = REPORT_DIR / "orchestrator_runs"
RUN_DIR.mkdir(parents=True, exist_ok=True)

WORKERS = [
    ("evidence_worker", "worker_agents/evidence_worker.py"),
    ("duplicate_worker", "worker_agents/duplicate_worker.py"),
    ("search_filter_worker", "worker_agents/search_filter_worker.py"),
    ("evidence_score_worker", "worker_agents/evidence_score_worker.py"),
    ("recommendation_ui_worker", "worker_agents/recommendation_ui_worker.py"),
    ("test_recommendation_ui_worker", "worker_agents/test_recommendation_ui_worker.py"),
    ("test_app_v10_ui_integration", "worker_agents/test_app_v10_ui_integration.py"),
    ("web_app_recommendation_worker", "worker_agents/web_app_recommendation_worker.py"),
    ("web_app_recommendation_fix_worker", "worker_agents/web_app_recommendation_fix_worker.py"),
    ("product_discovery_worker", "worker_agents/product_discovery_worker.py"),
    ("affiliate_safety_worker", "worker_agents/affiliate_safety_worker.py"),
    ("quality_security_worker", "worker_agents/quality_security_worker.py"),
    ("final_production_audit_worker", "worker_agents/final_production_audit_worker.py"),
]

def run_worker(name, script):
    path = ROOT / script
    output_file = RUN_DIR / f"{name}.log"

    if not path.exists():
        msg = f"NOT FOUND: {script}"
        output_file.write_text(msg, encoding="utf-8")
        return {
            "worker": name,
            "script": script,
            "status": "NOT_FOUND",
            "returncode": None,
        }

    start = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )

        elapsed = round(time.time() - start, 2)
        combined = (
            "=== STDOUT ===\n"
            + result.stdout
            + "\n=== STDERR ===\n"
            + result.stderr
        )
        output_file.write_text(combined, encoding="utf-8")

        return {
            "worker": name,
            "script": script,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "seconds": elapsed,
            "log": str(output_file.relative_to(ROOT)),
        }

    except subprocess.TimeoutExpired:
        output_file.write_text(
            "WORKER TIMEOUT: exceeded 300 seconds",
            encoding="utf-8",
        )
        return {
            "worker": name,
            "script": script,
            "status": "TIMEOUT",
            "returncode": None,
        }

    except Exception as exc:
        output_file.write_text(
            f"WORKER ERROR: {type(exc).__name__}: {exc}",
            encoding="utf-8",
        )
        return {
            "worker": name,
            "script": script,
            "status": "ERROR",
            "returncode": None,
        }


def main():
    print("========================================")
    print(" SMART PRODUCT FINDER BD")
    print(" WORKER ORCHESTRATOR")
    print("========================================")
    print("Mode: SAFE / SEQUENTIAL / NO GIT PUSH")
    print()

    results = []

    for index, (name, script) in enumerate(WORKERS, 1):
        print(f"[{index}/{len(WORKERS)}] Running: {name}")
        result = run_worker(name, script)
        results.append(result)
        print(f"       STATUS: {result['status']}")
        print()

    summary = {
        "project": "Smart Product Finder BD",
        "mode": "safe_sequential",
        "git_push": False,
        "workers": results,
    }

    summary_file = RUN_DIR / "orchestrator_summary.json"
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    passed = sum(r["status"] == "PASS" for r in results)
    failed = sum(r["status"] != "PASS" for r in results)

    print("========================================")
    print(" ORCHESTRATOR COMPLETE")
    print("========================================")
    print(f"PASS: {passed}")
    print(f"NOT PASS: {failed}")
    print(f"SUMMARY: {summary_file.relative_to(ROOT)}")
    print("========================================")


if __name__ == "__main__":
    main()
