from pathlib import Path

APP = Path("app_v10.py")

def test_app_exists():
    assert APP.exists(), "app_v10.py missing"

def test_recommendation_data_connected():
    text = APP.read_text(encoding="utf-8", errors="ignore").lower()

    assert (
        "product_recommendations.json" in text
        or "recommendation_ui_report.json" in text
    ), "Recommendation UI data is not connected to app_v10"

def test_recommendation_ui_present():
    text = APP.read_text(encoding="utf-8", errors="ignore").lower()

    keywords = [
        "recommendation",
        "score",
        "daraz",
    ]

    missing = [x for x in keywords if x not in text]
    assert not missing, f"Missing UI keywords: {missing}"

if __name__ == "__main__":
    tests = [
        test_app_exists,
        test_recommendation_data_connected,
        test_recommendation_ui_present,
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

    print("INTEGRATION TEST: PASS")
