import json
import re
from pathlib import Path

INPUT = Path("worker_reports/daraz_final_recommendation_staging_v2.json")
OUTPUT = Path("worker_reports/daraz_claim_safety_candidate_v1_report.json")

CLAIMS = {
    "ORIGINAL": [
        r"\boriginal\b",
        r"\bgenuine\b",
        r"\bauthentic\b",
    ],
    "OFFICIAL": [
        r"\bofficial\b",
        r"\bauthorized\b",
    ],
    "PREMIUM": [
        r"\bpremium\b",
    ],
    "AIRPODS": [
        r"\bairpods?\b",
    ],
}

def detect_claims(name):
    text = str(name or "").lower()
    found = []

    for claim, patterns in CLAIMS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            found.append(claim)

    return found

def risk_level(claims):
    strong = set(claims)

    if "AIRPODS" in strong:
        return "HIGH"

    if len(strong) >= 2:
        return "HIGH"

    if "OFFICIAL" in strong or "ORIGINAL" in strong:
        return "MEDIUM"

    if "PREMIUM" in strong:
        return "LOW"

    return "NONE"

def expected_tier(claims):
    risk = risk_level(claims)

    if risk == "HIGH":
        return "REVIEW"

    if risk == "MEDIUM":
        return "REVIEW"

    return None

def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    products = data.get("recommendations", [])

    results = []
    mismatches = []

    for i, product in enumerate(products, 1):
        name = product.get("name", "")
        claims = detect_claims(name)
        risk = risk_level(claims)
        expected = expected_tier(claims)
        current = product.get("recommendation_status")

        item = {
            "position": i,
            "name": name,
            "current_status": current,
            "current_score": product.get("recommendation_score"),
            "seller_claims": claims,
            "claim_status": (
                "UNVERIFIED_SELLER_CLAIM"
                if claims else "NO_STRONG_CLAIM_DETECTED"
            ),
            "verification_needed": bool(claims),
            "claim_risk": risk,
            "expected_safety_tier": expected or "NO_CHANGE",
            "status_mismatch": bool(expected and current == "RECOMMEND"),
        }

        if item["status_mismatch"]:
            mismatches.append(item)

        results.append(item)

    report = {
        "worker": "daraz_claim_safety_candidate_v1",
        "version": "1.0",
        "mode": "read_only_candidate_test",
        "input_count": len(products),
        "claim_detected": sum(bool(x["seller_claims"]) for x in results),
        "verification_needed": sum(x["verification_needed"] for x in results),
        "high_risk": sum(x["claim_risk"] == "HIGH" for x in results),
        "medium_risk": sum(x["claim_risk"] == "MEDIUM" for x in results),
        "low_risk": sum(x["claim_risk"] == "LOW" for x in results),
        "status_mismatches": len(mismatches),
        "production_modified": False,
        "git_modified": False,
        "products": results,
        "mismatches": mismatches,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 70)
    print("CLAIM SAFETY GATE — READ ONLY CANDIDATE TEST")
    print("=" * 70)
    print("Products              :", len(products))
    print("Claims detected       :", report["claim_detected"])
    print("Verification needed   :", report["verification_needed"])
    print("HIGH risk             :", report["high_risk"])
    print("MEDIUM risk           :", report["medium_risk"])
    print("LOW risk              :", report["low_risk"])
    print("Status mismatches     :", report["status_mismatches"])

    print("\n===== CLAIM PRODUCTS =====")
    for x in results:
        if x["seller_claims"]:
            print(
                f'{x["position"]:02d} | '
                f'{",".join(x["seller_claims"]):<24} | '
                f'{x["claim_risk"]:<6} | '
                f'CURRENT={x["current_status"]:<12} | '
                f'EXPECTED={x["expected_safety_tier"]:<8} | '
                f'{x["name"]}'
            )

    print("\n===== SAFETY MISMATCHES =====")
    for x in mismatches:
        print(
            f'{x["position"]:02d} | '
            f'{x["claim_risk"]} | '
            f'{x["name"]}'
        )

    print("\nREPORT:", OUTPUT)
    print("Production data modified: NO")
    print("Git modified by this test: NO")

if __name__ == "__main__":
    main()
