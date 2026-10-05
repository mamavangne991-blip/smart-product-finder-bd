from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "web_app_v6.py"

source = TARGET.read_text(encoding="utf-8")

old_top = '''def get_top_three_products(products):

    return sorted(
        products,
        key=smart_score,
        reverse=True
    )[:3]
'''

new_top = '''def get_top_three_products(products):
    return sorted(
        products,
        key=lambda item: (
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )[:3]
'''

old_best = '''    return max(
        valid_products,
        key=best_value_score
    )
'''

new_best = '''    return min(
        valid_products,
        key=lambda item: (
            item.get("recommendation_rank")
            if item.get("recommendation_rank") is not None
            else 999999
        )
    )
'''

if old_top not in source:
    print("ERROR: TOP 3 old block not found")
    sys.exit(1)

if old_best not in source:
    print("ERROR: BEST VALUE old block not found")
    sys.exit(1)

backup = ROOT / (
    "web_app_v6_before_final_recommendation_selection_fix_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".py"
)

shutil.copy2(TARGET, backup)

source = source.replace(old_top, new_top, 1)
source = source.replace(old_best, new_best, 1)

TARGET.write_text(source, encoding="utf-8")

import py_compile
py_compile.compile(str(TARGET), doraise=True)

print("=" * 50)
print("FINAL RECOMMENDATION SELECTION FIX")
print("=" * 50)
print("PASS: TOP 3 uses recommendation_rank")
print("PASS: Best Value uses recommendation_rank")
print("PASS: web_app_v6.py compiles")
print("BACKUP:", backup.name)
print("NO GIT PUSH")
print("NO FILE DELETION")
print("STATUS: PASS")
