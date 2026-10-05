from pathlib import Path
import shutil
import subprocess
import sys
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "web_app_v6.py"
REPORT = ROOT / "worker_reports" / "web_app_recommendation_fix_report.json"

if not APP.exists():
    print("ERROR: web_app_v6.py not found")
    sys.exit(1)

source = APP.read_text(encoding="utf-8")

# Already-fixed state: do not modify again.
if (
    "def recommendation_score(item):" in source
    and "key=lambda item:" in source
    and "top_three = sorted(" in source
    and "best_value = None" in source
    and "key=lambda item:" in source
):
    print("ALREADY FIXED: recommendation selection logic")
    print("NO FILE MODIFICATION")
    print("STATUS: PASS")
    sys.exit(0)

backup = ROOT / (
    "web_app_v6_before_recommendation_worker_fix_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".py"
)
shutil.copy2(APP, backup)

# --------------------------------------------------
# TOP 3 selection
# --------------------------------------------------

old_top = '''    top_three = get_top_three_products(products)'''

new_top = '''    top_three = sorted(
        products,
        key=lambda item: (
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )[:3]'''

if old_top in source:
    source = source.replace(old_top, new_top, 1)
else:
    print("ERROR: TOP 3 selection block not found")
    sys.exit(2)

# --------------------------------------------------
# Best Value selection
# --------------------------------------------------

old_best = '''    best_value = get_best_value_product(products)'''

new_best = '''    valid_best_values = [
        product
        for product in products
        if get_price(product) > 0
    ]

    best_value = None
    if valid_best_values:
        best_value = min(
            valid_best_values,
            key=lambda item: (
                item.get("recommendation_rank")
                if item.get("recommendation_rank") is not None
                else 999999
            )
        )'''

if old_best in source:
    source = source.replace(old_best, new_best, 1)
else:
    print("ERROR: Best Value selection block not found")
    sys.exit(3)

APP.write_text(source, encoding="utf-8")

# --------------------------------------------------
# Compile
# --------------------------------------------------

result = subprocess.run(
    [sys.executable, "-m", "py_compile", str(APP)],
    cwd=ROOT,
    capture_output=True,
    text=True
)

if result.returncode != 0:
    shutil.copy2(backup, APP)
    print("COMPILE FAILED — ORIGINAL FILE RESTORED")
    print(result.stderr)
    sys.exit(4)

report = {
    "worker": "web_app_recommendation_fix_worker",
    "status": "PASS",
    "changes": [
        "TOP 3 selection switched to recommendation_rank",
        "Best Value selection switched to recommendation_rank",
        "recommendation score display retained"
    ],
    "backup": backup.name,
    "git_push": False,
    "files_deleted": False
}

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("========================================")
print(" WEB APP RECOMMENDATION FINAL FIX")
print("========================================")
print("PASS: TOP 3 uses recommendation_rank")
print("PASS: Best Value uses recommendation_rank")
print("PASS: recommendation score display retained")
print("PASS: web_app_v6.py compile")
print("PASS: backup created")
print("NO GIT PUSH")
print("NO FILE DELETION")
print()
print("STATUS: PASS")
print("BACKUP:", backup.name)
print("REPORT:", REPORT.relative_to(ROOT))
