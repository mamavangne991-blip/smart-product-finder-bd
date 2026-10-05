import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products.json"
REPORT = ROOT / "worker_reports" / "v5_evidence_score_report.json"

FIELDS = [
    "name", "description", "image", "url",
    "category", "price", "item_id",
    "seller_sku", "seller_id"
]

def has_value(v):
    return v is not None and str(v).strip() != ""

def score_product(p):
    evidence = {
        f: has_value(p.get(f))
        for f in FIELDS
    }

    evidence_count = sum(evidence.values())
    evidence_score = round((evidence_count / len(FIELDS)) * 40)

    source = str(p.get("source") or "").strip().lower()

    if source == "daraz public":
        source_score = 20
    elif source:
        source_score = 10
    else:
        source_score = 0

    research_score = 25 if source == "daraz public" else 10

    price = p.get("price", 0)
    try:
        price = float(price)
    except (TypeError, ValueError):
        price = 0

    if price <= 0:
        price_score = 0
    elif price <= 300:
        price_score = 15
    elif price <= 500:
        price_score = 12
    elif price <= 1000:
        price_score = 9
    else:
        price_score = 6

    title = str(p.get("name") or "").strip()
    title_score = 5 if len(title) >= 20 else 3 if len(title) >= 10 else 1

    total = min(
        100,
        evidence_score +
        source_score +
        research_score +
        price_score +
        title_score
    )

    return {
        "name": p.get("name"),
        "item_id": p.get("item_id"),
        "source": p.get("source"),
        "recommendation_score_v5": total,
        "score_breakdown": {
            "evidence": evidence_score,
            "source": source_score,
            "research": research_score,
            "price": price_score,
            "title": title_score
        },
        "evidence_count": evidence_count,
        "evidence_total": len(FIELDS),
        "missing_fields": [
            f for f, ok in evidence.items() if not ok
        ],
        "status": "PASS" if evidence_count == len(FIELDS) else "INCOMPLETE"
    }

def main():
    data = json.loads(
        PRODUCTS.read_text(encoding="utf-8")
    )

    ranked = [score_product(p) for p in data]
    ranked.sort(
        key=lambda x: x["recommendation_score_v5"],
        reverse=True
    )

    report = {
        "worker": "V5 Real Evidence Score Worker",
        "timestamp": datetime.now().isoformat(),
        "total_products": len(data),
        "results": ranked,
        "status": "PASS"
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("=" * 60)
    print("V5 REAL EVIDENCE SCORE WORKER")
    print("=" * 60)
    print("TOTAL PRODUCTS:", len(data))

    for i, p in enumerate(ranked[:15], 1):
        print(
            f"#{i:02} | SCORE {p['recommendation_score_v5']:02} | "
            f"EVIDENCE {p['evidence_count']}/9 | "
            f"{p['name']}"
        )

    print("REPORT:", REPORT)
    print("WORKER STATUS: PASS")

if __name__ == "__main__":
    main()
