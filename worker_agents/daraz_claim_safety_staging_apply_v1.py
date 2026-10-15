import json
import re
from pathlib import Path

INPUT = Path("worker_reports/daraz_final_recommendation_staging_v2.json")
OUTPUT = Path("worker_reports/daraz_final_recommendation_safety_staging_v1.json")

CLAIMS = {
    "ORIGINAL": [r"\boriginal\b", r"\bgenuine\b", r"\bauthentic\b"],
    "OFFICIAL": [r"\bofficial\b", r"\bauthorized\b"],
    "PREMIUM": [r"\bpremium\b"],
    "AIRPODS": [r"\bairpods?\b"],
}

def detect_claims(name):
    text = str(name or "").lower()
    return [
        claim for claim, patterns in CLAIMS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    ]

def risk_level(claims):
    if "AIRPODS" in claims or len(claims) >= 2:
        return "HIGH"
    if "ORIGINAL" in claims or "OFFICIAL" in claims:
        return "MEDIUM"
    if "PREMIUM" in claims:
        return "LOW"
    return "NONE"

def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    products = data.get("recommendations", [])

    output_products = []
    changed = 0

    for p in products:
        x = dict(p)
        claims = detect_claims(x.get("name", ""))
        risk = risk_level(claims)

        x["seller_claims"] = claims
        x["claim_status"] = (
            "UNVERIFIED_SELLER_CLAIM"
            if claims else "NO_STRONG_CLAIM_DETECTED"
        )
        x["verification_needed"] = bool(claims)
        x["claim_risk"] = risk

        if claims and x.get("recommendation_status") == "RECOMMEND":
            x["previous_recommendation_status"] = "RECOMMEND"
            x["recommendation_status"] = "REVIEW"
            x["safety_gate"] = "BLOCK_UNVERIFIED_CLAIM"
            changed += 1
        else:
            x["safety_gate"] = "PASS"

        output_products.append(x)

    report = {
        **data,
        "worker": "daraz_claim_safety_staging_apply_v1",
        "version": "1.0",
        "mode": "staging_only",
        "status": "STAGING_READY",
        "recommendations": output_products,
        "safety_gate_summary": {
            "input_count": len(products),
            "changed_to_review": changed,
            "claim_products": sum(
                bool(x["seller_claims"]) for x in output_products
            ),
            "high_risk": sum(
                x["claim_risk"] == "HIGH" for x in output_products
            ),
            "medium_risk": sum(
                x["claim_risk"] == "MEDIUM" for x in output_products
            ),
            "low_risk": sum(
                x["claim_risk"] == "LOW" for x in output_products
            ),
        },
        "production_modified": False,
        "git_modified": False,
    }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Regression checks
    assert len(output_products) == 25
    assert changed == 7

    review_claims = [
        x for x in output_products
        if x.get("seller_claims")
    ]
    assert len(review_claims) == 7
    assert all(
        x["recommendation_status"] == "REVIEW"
        for x in review_claims
    )

    unchanged = [
        x for x in output_products
        if not x.get("seller_claims")
    ]
    assert len(unchanged) == 18

    print("=" * 70)
    print("CLAIM SAFETY STAGING APPLY V1")
    print("=" * 70)
    print("Input products       :", len(products))
    print("Claim products       :", len(review_claims))
    print("Changed to REVIEW    :", changed)
    print("Unchanged products   :", len(unchanged))
    print("HIGH risk            :", report["safety_gate_summary"]["high_risk"])
    print("MEDIUM risk          :", report["safety_gate_summary"]["medium_risk"])
    print("LOW risk             :", report["safety_gate_summary"]["low_risk"])
    print()
    print("REGRESSION TEST      : PASS")
    print("STAGING STATUS       : READY")
    print("Production modified  : NO")
    print("Git modified         : NO")
    print("REPORT:", OUTPUT)

if __name__ == "__main__":
    main()
