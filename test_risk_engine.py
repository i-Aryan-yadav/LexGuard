"""Accurate signal validation — correct expectations per single-clause scoring."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.services.risk_service import RiskService

risk = RiskService()

cases = [
    # --- Bug report cases that were failing ---
    {
        "label": "Immediate termination / sole judgment (Clause 3.4)",
        "text": "The Client reserves the right to terminate immediately without notice if, in its sole judgment, the other party has breached this agreement.",
        "clause_type": "Termination",
        "is_mutual": False,
        "skip_risk": False,
        #  reserves right to terminate (+4) + without notice (+4) + sole judgment (+3) = 11 -> capped 10
        "expected_min_score": 7.0,
        "expected_level": "High",
    },
    {
        "label": "Liability shall be unlimited / no cap",
        "text": "The liability of the contractor under this agreement shall be unlimited and no cap shall apply.",
        "clause_type": "Liability",
        "is_mutual": False,
        "skip_risk": False,
        # unlimited liability (+5) + no cap (+5) = 10
        "expected_min_score": 7.0,
        "expected_level": "High",
    },
    {
        "label": "No limitation shall apply",
        "text": "Notwithstanding anything to the contrary, no limitation shall apply to damages arising from this agreement.",
        "clause_type": "Liability",
        "is_mutual": False,
        "skip_risk": False,
        # no limitation shall apply (+7) = 7 -> High (score raised with Unlimited Liability signal)
        "expected_min_score": 7.0,
        "expected_level": "High",
    },
    {
        "label": "Biased arbitration — appointed exclusively (single signal)",
        "text": "The sole arbitrator shall be appointed exclusively by the Client and shall have full authority to resolve the dispute.",
        "clause_type": "Dispute Resolution",
        "is_mutual": False,
        "skip_risk": False,
        # sole arbitrator (+7) = 7 -> High (score raised: unilateral arbitrator appointment is High Risk)
        "expected_min_score": 7.0,
        "expected_level": "High",
    },
    {
        "label": "Security deposit forfeiture",
        "text": "The security deposit of INR 50,000 shall be forfeited if the tenant vacates before the notice period.",
        "clause_type": "Financial Risk",
        "is_mutual": False,
        "skip_risk": False,
        # forfeiture (+4) + deposit risk (+3) = 7 -> High
        "expected_min_score": 7.0,
        "expected_level": "High",
    },
    {
        "label": "Power reservation — as it sees fit",
        "text": "The Company may determine the scope of work and deliverables as it sees fit without consulting the contractor.",
        "clause_type": "Liability",
        "is_mutual": False,
        "skip_risk": False,
        # as it sees fit (+2) = 2 -> Low
        "expected_min_score": 1.0,
        "expected_level": "Low",
    },
    {
        "label": "Balanced mutual arbitration (must NOT be High)",
        "text": "Both parties agree that all disputes shall be resolved through binding arbitration, with each party appointing one arbitrator.",
        "clause_type": "Dispute Resolution",
        "is_mutual": True,
        "skip_risk": False,
        "expected_min_score": 0.0,
        "expected_level": None,  # any level OK, but NOT High
    },
    {
        "label": "Definitions NON_RISK (must be Informational)",
        "text": "For the purposes of this Agreement, the term Client means the party identified in the signature block.",
        "clause_type": "NON_RISK",
        "is_mutual": False,
        "skip_risk": True,
        "expected_min_score": 0.0,
        "expected_level": "Informational",
    },
    {
        "label": "One-sided indemnity (Medium risk)",
        "text": "The contractor shall indemnify and hold harmless the Client from any and all claims, losses, or damages.",
        "clause_type": "Indemnity",
        "is_mutual": False,
        "skip_risk": False,
        # broad indemnity (+3) + one-way bonus (+2) = 5 -> Medium
        "expected_min_score": 4.0,
        "expected_level": "Medium",
    },
]

all_ok = True
for c in cases:
    r = risk.analyze_risk(c["text"], c["clause_type"], is_mutual=c["is_mutual"], skip_risk=c["skip_risk"])
    score_ok = r.risk_score >= c["expected_min_score"]
    if c["expected_level"] is None:
        level_ok = r.risk_level != "High"
    else:
        level_ok = r.risk_level == c["expected_level"]

    ok = score_ok and level_ok
    if not ok:
        all_ok = False
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {c['label']}")
    print(f"       score={r.risk_score}  level={r.risk_level}  (expected: min={c['expected_min_score']}, level={c['expected_level']})")
    print(f"       snippet='{r.risky_snippet}'  party='{r.exposed_party}'  cat='{r.risk_category}'")
    print()

print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
sys.exit(0 if all_ok else 1)
