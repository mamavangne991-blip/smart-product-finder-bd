import json
from pathlib import Path

INPUT = Path("product_recommendations.json")
REPORT = Path("worker_reports/recommendation_ui_report.json")

def test_input_exists():
    assert INPUT.exists(), "product_recommendations.json missing"

def test_recommendation_records_have_ui_fields():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    assert data, "No recommendation records"

    for p in data[:10]:
        assert p.get("name"), "Missing name"
        assert p.get("recommendation_score") is not None, "Missing score"
        if str(p.get("source", "")).lower() == "daraz public":
            assert p.get("url"), "Daraz Public product missing URL"

def test_report_path_ready():
    assert REPORT.parent.exists(), "worker_reports directory missing"

if __name__ == "__main__":
    tests = [
        test_input_exists,
        test_recommendation_records_have_ui_fields,
        test_report_path_ready,
    ]

    failed = 0
    for test in tests:
        try:
            test()
            print("PASS:", test.__name__)
        except Exception as e:
            failed += 1
            print("FAIL:", test.__name__, "|", e)

    print(f"\nTESTS: {len(tests)} | FAILED: {failed}")

    if failed:
        raise SystemExit(1)

    print("RED TEST: NOT RED — implementation may already satisfy current contract")
