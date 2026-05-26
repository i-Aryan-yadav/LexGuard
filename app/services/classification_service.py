"""
Hybrid Classification Service.

Stage 1 — Rule-based keyword detection (primary, deterministic).
Stage 2 — Embedding cosine similarity (refinement for ambiguous clauses).
Stage 3 — Exclusion gate: Definitions / Signatures → NON_RISK.

Final score = 0.7 × rule_score + 0.3 × embedding_score

Title boost: if heading contains key risk terms, rule_score × 1.25.
Mutual detection: sets is_mutual=True to dampen risk signals downstream.
Performance guardrail: clauses in large contracts (>100) skip embedding if rule_score ≥ 0.7.
"""

import re
import json
import os
from app.core.config import settings
from app.core.logging import logger
from app.services.contextual_classifier import contextual_classifier

# ─────────────────────────────────────────────────────────────────────────────
# Rule-based keyword map:  clause_type → list of regex patterns
# ─────────────────────────────────────────────────────────────────────────────
RULE_KEYWORDS: dict[str, list[str]] = {
    "Termination": [
        r'\bterminat\w*\b',
        r'\bnotice of termination\b',
        r'\bexpiry\b',
    ],
    "Indemnity": [
        r'\bindemnif\w*\b',
        r'\bindemnity\b',
        r'\bhold harmless\b',
        r'\bdefend and indemnify\b',
    ],
    "Financial Risk": [
        r'\bsecurity deposit\b',
        r'\bsecurity amount\b',
        r'\bforfeit\w*\b',
        r'\bdeposit shall\b',
        r'\badvance deposit\b',
    ],
    "Dispute Resolution": [
        r'\barbitration\b',
        r'\bdispute resolution\b',
        r'\bmediation\b',
        r'\badjudication\b',
    ],
    "Liability": [
        r'\bliabilit\w*\b',
        r'\bliable\b',
        r'\bcompensation\b',
        r'\bdamages\b',
        r'\bindirect loss\b',
        r'\bconsequential\b',
    ],
    "Governing Law": [
        r'\bgoverning law\b',
        r'\bgovernment\w*\b',
        r'\bjurisdiction\b',
        r'\bapplicable law\b',
        r'\blocal laws\b',
    ],
    "Confidentiality": [
        r'\bconfidential\w*\b',
        r'\bnon-?disclosure\b',
        r'\bproprietary information\b',
    ],
    "Force Majeure": [
        r'\bforce majeure\b',
        r'\bact of god\b',
        r'\bunforeseeable\b',
    ],
    "Payment": [
        r'\bpayment\b',
        r'\brent\b',
        r'\bfee\b',
        r'\binvoice\b',
        r'\binstalment\b',
        r'\binstallment\b',
        r'\bamount due\b',
    ],
    "Renewal": [
        r'\brenewal\b',
        r'\brenew\b',
        r'\bauto-?renew\b',
        r'\bextension of term\b',
    ],
    "Assignment": [
        r'\bassign\w*\b',
        r'\bsublet\b',
        r'\btransfer of rights\b',
    ],
    # Non-risk types (exclusion gate)
    "NON_RISK": [
        r'\bdefinitions?\b',
        r'\bmeans\s+[""""]',
        r'\bherein defined\b',
        r'\binterpretation\b',
        r'\bsigned by\b',
        r'\bwitness\b',
        r'\bsignature\b',
        r'\bin witness whereof\b',
        r'\bschedule [a-z]\b',
        r'\bfor and on behalf of\b',
        r'\bexecuted (by|on)\b',
    ],
}

# Headings that boost rule_score
TITLE_BOOST_TERMS = {
    "termination", "terminate", "security deposit", "arbitration",
    "indemnity", "indemnification", "liability", "forfeiture",
    "dispute", "penalty", "compensation"
}

# Mutual qualifiers that reduce risk directionally
MUTUAL_TERMS = [
    r'\bboth parties\b',
    r'\beach party\b',
    r'\bmutually\b',
    r'\breciprocal\b',
]

# Types that never get risk-scored
EXCLUDED_TYPES = {"NON_RISK"}


class ClassificationService:

    def __init__(self):
        self._compiled_rules: dict[str, list[re.Pattern]] = {}
        self._compile_rules()

    # ── Rule compilation ──────────────────────────────────────────────────────

    def _compile_rules(self):
        for ctype, patterns in RULE_KEYWORDS.items():
            self._compiled_rules[ctype] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    # ── Public API ────────────────────────────────────────────────────────────

    def classify_clause(
        self,
        clause_text: str,
        heading: str | None = None,
        total_clauses: int = 0,
        skip_risk: bool = False,
    ) -> dict:
        """
        Returns:
            {
                clause_type      : str,
                confidence_score : float,
                is_mutual        : bool,
                rule_score       : float,
                # embedding_score is removed (legacy)
            }
        """
        text_lower = clause_text.lower()

        # ── Stage 1: Rule-based scoring ───────────────────────────────────────
        rule_scores: dict[str, float] = {}
        for ctype, patterns in self._compiled_rules.items():
            hits = sum(1 for p in patterns if p.search(text_lower))
            if hits:
                # Normalise: each hit adds proportional weight, cap at 1.0
                rule_scores[ctype] = min(1.0, hits / max(1, len(patterns)) * 2.5)

        # ── Title Boost ───────────────────────────────────────────────────────
        if heading:
            heading_lower = heading.lower()
            for term in TITLE_BOOST_TERMS:
                if term in heading_lower:
                    # Find the clause type this term typically maps to and boost it
                    for ctype in rule_scores:
                        if ctype != "NON_RISK":
                            rule_scores[ctype] = min(1.0, rule_scores[ctype] * 1.25)
                    break

        # ── Exclusion gate: NON_RISK wins immediately ─────────────────────────
        if rule_scores.get("NON_RISK", 0.0) >= 0.6:
            return {
                "clause_type": "NON_RISK",
                "confidence_score": rule_scores["NON_RISK"],
                "is_mutual": False,
                "rule_score": rule_scores["NON_RISK"],
            }

        # Remove NON_RISK from further scoring
        rule_scores.pop("NON_RISK", None)

        # ── Best rule match ───────────────────────────────────────────────────
        best_rule_type = max(rule_scores, key=rule_scores.get) if rule_scores else "Unknown"
        best_rule_score = rule_scores.get(best_rule_type, 0.0)

        # ── Mutual detection ──────────────────────────────────────────────────
        is_mutual = any(
            re.search(p, text_lower) for p in MUTUAL_TERMS
        )

        if best_rule_score > 0 and best_rule_score >= settings.HIGH_RULE_SCORE_THRESHOLD:
             # Logic 1: High confidence rule -> Deterministic Win
             final_type = best_rule_type
             final_score = best_rule_score
             # Classifier is skipped for performance/determinism
             # risk_confidence is implicitly high for rules
        else:
             # Logic 2: Weak/No Rule -> Consult Contextual Classifier
             
             # Optimization: If very long contract (>150 clauses) and weak rule, maybe skip classifier 
             # unless ambiguous? For now, we follow the "Hybrid" plan.
             
             try:
                 prediction = contextual_classifier.predict(clause_text)
                 
                 # Hybrid Decision:
                 # If classifier has strong opinion (>0.6), use it
                 # If classifier is weak too, fallback to weak rule or Unknown
                 
                 # Let's say we trust classifier if > 0.6
                 if prediction['clause_confidence'] > 0.6:
                     final_type = prediction['clause_type']
                     final_score = prediction['clause_confidence']
                 elif best_rule_score > 0.3:
                     # Fallback to weak rule if classifier is also weak
                     final_type = best_rule_type
                     final_score = best_rule_score
                 else:
                     final_type = "Unknown"
                     final_score = 0.0
                     
             except Exception as e:
                 logger.error(f"Classifier prediction error: {e}")
                 # Fallback to best rule effort
                 final_type = best_rule_type if best_rule_score > 0 else "Unknown"
                 final_score = best_rule_score

        return {
            "clause_type": final_type,
            "confidence_score": round(final_score, 4),
            "is_mutual": is_mutual,
            "rule_score": round(best_rule_score, 4),
            "risk_level": prediction.get("risk_level", "Unknown") if 'prediction' in locals() else "Unknown",
            "risk_confidence": prediction.get("risk_confidence", 0.0) if 'prediction' in locals() else 0.0,
        }

classification_service = ClassificationService()
