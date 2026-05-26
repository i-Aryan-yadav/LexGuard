from app.services.risk_service import RiskService

r = RiskService()

cases = [
    ("imm-term", "The Client reserves the right to terminate immediately without notice if, in its sole judgment, the other party has breached.", "Termination", False, False, 7.0, "High"),
    ("unlimited", "The liability of the contractor under this agreement shall be unlimited and no cap shall apply.", "Liability", False, False, 5.0, "Medium"),
    ("no-limit", "No limitation shall apply to damages arising from this agreement.", "Liability", False, False, 4.0, "Medium"),
    ("biased-arb", "The sole arbitrator shall be appointed exclusively by the Client.", "Dispute Resolution", False, False, 3.0, "Low"),
    ("forfeiture", "The security deposit of INR 50,000 shall be forfeited if the tenant vacates before the notice period.", "Financial Risk", False, False, 7.0, "High"),
    ("sees-fit", "The Company may determine deliverables as it sees fit.", "Liability", False, False, 1.0, "Low"),
    ("mutual-arb", "Both parties agree disputes shall be resolved through binding arbitration, each party appointing one arbitrator.", "Dispute Resolution", True, False, 0.0, None),
    ("definitions", "For the purposes of this Agreement, the term Client means the party in the signature block.", "NON_RISK", False, True, 0.0, "Informational"),
    ("indemnity", "The contractor shall indemnify and hold harmless the Client from any and all claims, losses, or damages.", "Indemnity", False, False, 4.0, "Medium"),
]

all_ok = True
with open("result.txt", "w", encoding="utf-8") as f:
    for label, text, ctype, mutual, skip, min_s, exp in cases:
        res = r.analyze_risk(text, ctype, is_mutual=mutual, skip_risk=skip)
        score_ok = res.risk_score >= min_s
        if exp is None:
            level_ok = res.risk_level != "High"
        else:
            level_ok = res.risk_level == exp
        ok = score_ok and level_ok
        if not ok:
            all_ok = False
        tag = "PASS" if ok else "FAIL"
        line = f"[{tag}] {label}: score={res.risk_score} level={res.risk_level} (exp_min={min_s} exp_lvl={exp})\n"
        f.write(line)
        f.write(f"  reasons: {res.risk_reasons}\n")
    f.write("ALL PASS\n" if all_ok else "SOME FAIL\n")

import sys
sys.exit(0 if all_ok else 1)
