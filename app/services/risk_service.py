"""
Legal Risk Engine — 10-Signal Multi-Factor Scoring.

Replaces flat type-based scoring with a deterministic signal engine:
- Each signal fires on specific phrase patterns
- Directionality detection via simple SVO extraction
- Boilerplate dampening for standard legal qualifiers
- Precise risky_snippet extraction (6-12 words, not full clause)
- risk_category classification
- Tiered output: Informational / Low (1-3) / Medium (4-6) / High (7-10)
"""

import re
from dataclasses import dataclass, field
from app.domain.risk_rules import RiskAnalysisResult
from app.core.logging import logger


# ─────────────────────────────────────────────────────────────────────────────
# Signal definitions
# Each signal: (name, pattern_list, score, category, snippet_hint)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RiskSignal:
    name: str
    patterns: list[re.Pattern]
    score: float
    category: str
    snippet_hint: str   # Short representative phrase for display


RISK_SIGNALS: list[RiskSignal] = [
    RiskSignal(
        name="Unlimited Liability",
        patterns=[
            # Core forms
            re.compile(r'\bunlimited\s+liabilit\w*\b', re.I),
            re.compile(r'\bno\s+limit\s+on\s+liabilit\w*\b', re.I),
            re.compile(r'\bliabilit\w*\s+shall\s+not\s+be\s+limited\b', re.I),
            re.compile(r'\bwithout\s+limit\s+(of|on)\s+liabilit\w*\b', re.I),
            # Expanded phrasings
            re.compile(r'\bliabilit\w*\s+shall\s+be\s+unlimited\b', re.I),
            re.compile(r'\bshall\s+be\s+unlimited\b', re.I),
            re.compile(r'\bno\s+limitation\s+shall\s+apply\b', re.I),
            re.compile(r'\bshall\s+not\s+be\s+subject\s+to\s+any\s+cap\b', re.I),
            re.compile(r'\bwithout\s+limitation\s+of\s+liabilit\w*\b', re.I),
            re.compile(r'\bno\s+cap\s+shall\s+apply\b', re.I),
            re.compile(r'\bno\s+financial\s+cap\b', re.I),
            # Additional alternative phrasings
            re.compile(r'\bno\s+limitation\s+on\s+liabilit\w*\b', re.I),
            re.compile(r'\bliabilit\w*\s+without\s+limit\b', re.I),
            re.compile(r'\bno\s+maximum\s+liabilit\w*\b', re.I),
        ],
        score=7.0,  # Raised: standalone unlimited liability is inherently High Risk
        category="Financial Exposure",
        snippet_hint="unlimited liability",
    ),
    RiskSignal(
        name="Forfeiture Right",
        patterns=[
            re.compile(r'\bshall\s+be\s+forfeit\w*\b', re.I),
            re.compile(r'\bforfeit\w*\s+the\s+(deposit|amount|security)\b', re.I),
            re.compile(r'\bdeposit\s+shall\s+be\s+forfeit\w*\b', re.I),
            re.compile(r'\bno\s+refund\b', re.I),
            re.compile(r'\bnon-?refundable\b', re.I),
        ],
        score=4.0,
        category="Financial Exposure",
        snippet_hint="shall be forfeited",
    ),
    RiskSignal(
        name="One-sided Termination",
        patterns=[
            # Core forms
            re.compile(r'\bat\s+(its|his|her|the\s+\w+\'?s?)\s+sole\s+discretion\b', re.I),
            re.compile(r'\bwithout\s+cause\b', re.I),
            re.compile(r'\bwithout\s+(prior\s+)?notice\b', re.I),
            re.compile(r'\bterminate\s+(this\s+agreement\s+)?immediately\b', re.I),
            re.compile(r'\bunilateral\w*\s+terminat\w*\b', re.I),
            # Expanded phrasings
            re.compile(r'\breserves\s+the\s+right\s+to\s+terminat\w*\b', re.I),
            re.compile(r'\bmay\s+terminat\w*\s+immediately\b', re.I),
            re.compile(r'\bterminat\w*\s+without\s+(prior\s+)?notice\b', re.I),
            re.compile(r'\bin\s+its\s+sole\s+judgment\b', re.I),
            re.compile(r'\bat\s+its\s+sole\s+judgment\b', re.I),
            re.compile(r'\bin\s+its\s+absolute\s+discretion\b', re.I),
            re.compile(r'\bat\s+its\s+discretion\s+terminat\w*\b', re.I),
            
            # New vocabulary additions (Phase 2)
            re.compile(r'\bwithout\s+prior\s+notice\b', re.I),
            re.compile(r'\bas\s+it\s+deems\s+appropriate\s+to\s+terminat\w*\b', re.I),
        ],
        score=4.0,
        category="Power Imbalance",
        snippet_hint="terminate immediately without notice",
    ),
    RiskSignal(
        name="Unqualified Discretion",
        patterns=[
            # Core forms
            re.compile(r'\babsolute\s+discretion\w*\b', re.I),
            re.compile(r'\bsole\s+judgment\b', re.I),
            re.compile(r'\bsole\s+discretion\w*\b', re.I),
            re.compile(r'\bfinal\s+decision\s+of\s+the\s+\w+\b', re.I),
            # Expanded phrasings
            re.compile(r'\bin\s+its\s+(sole|absolute)\s+(judgment|discretion\w*)\b', re.I),
            re.compile(r'\bat\s+its\s+(sole|absolute)\s+(judgment|discretion\w*)\b', re.I),
            re.compile(r'\bexclusive\s+judgment\b', re.I),
            re.compile(r'\bentirely\s+at\s+(its|their|his|her)\s+discretion\b', re.I),
            
            # New vocabulary additions (Phase 2)
            re.compile(r'\bas\s+it\s+deems\s+appropriate\b', re.I),
            re.compile(r'\bat\s+its\s+discretion\b', re.I), # Caution: ensure not generic, usually safe with high score
        ],
        score=3.0,
        category="Power Imbalance",
        snippet_hint="sole judgment",
    ),
    RiskSignal(
        name="Power Reservation",
        patterns=[
            # Core forms
            re.compile(r'\breserves\s+the\s+right\b', re.I),
            re.compile(r'\bat\s+its\s+discretion\b', re.I),
            re.compile(r'\bas\s+(it|he|she|they)\s+deems\s+(fit|appropriate|necessary)\b', re.I),
            re.compile(r'\bat\s+the\s+(owner|landlord|licensor|company|client|employer)\'?s?\s+discretion\b', re.I),
            # Expanded phrasings
            re.compile(r'\bmay\s+determine\s+at\s+its\s+discretion\b', re.I),
            re.compile(r'\bas\s+it\s+sees\s+fit\b', re.I),
            re.compile(r'\bas\s+it\s+considers\s+necessary\b', re.I),
            re.compile(r'\bin\s+its\s+(sole\s+)?opinion\b', re.I),
            re.compile(r'\bhas\s+the\s+(sole\s+)?right\s+to\s+determine\b', re.I),
            re.compile(r'\bat\s+the\s+discretion\s+of\s+the\s+\w+\b', re.I),
            
            # New vocabulary additions (Phase 2)
            re.compile(r'\bsole\s+judgment\b', re.I),
            re.compile(r'\swithout\s+prior\s+notice\b', re.I),
        ],
        score=2.0,
        category="Power Imbalance",
        snippet_hint="reserves the right",
    ),
    RiskSignal(
        name="Forced Arbitration",
        patterns=[
            # Core forms
            re.compile(r'\bbinding\s+arbitration\b', re.I),
            re.compile(r'\bshall\s+be\s+resolved\s+by\s+arbitration\b', re.I),
            re.compile(r'\bsubmit\s+(all\s+)?disputes?\s+to\s+arbitration\b', re.I),
            # Expanded phrasings
            re.compile(r'\breferred?\s+to\s+arbitration\b', re.I),
            re.compile(r'\bdisputes?\s+shall\s+be\s+arbitrat\w+\b', re.I),
            re.compile(r'\bmatter\s+shall\s+be\s+(settled\s+by\s+)?arbitrat\w+\b', re.I),
            re.compile(r'\bsettled\s+by\s+arbitration\b', re.I),
        ],
        score=4.0,  # Raised from 2.0: binding arbitration forces Medium tier on its own
        category="Dispute Risk",
        snippet_hint="binding arbitration",
    ),
    RiskSignal(
        name="Biased Arbitration",
        patterns=[
            # Core forms
            re.compile(r'\barbitrat\w+\s+appointed\s+by\s+the\s+\w+\b', re.I),
            re.compile(r'\bsole\s+arbitrat\w+\b', re.I),
            re.compile(r'\barbitrat\w+\s+selected\s+by\s+(one|a\s+single)\s+party\b', re.I),
            # Expanded phrasings
            re.compile(r'\bappointed\s+exclusively\s+by\b', re.I),
            re.compile(r'\bsole\s+arbitrat\w+\s+appointed\s+by\b', re.I),
            re.compile(r'\bshall\s+nominate\s+the\s+arbitrat\w+\b', re.I),
            re.compile(r'\bshall\s+have\s+the\s+exclusive\s+right\s+to\s+appoint\b', re.I),
            re.compile(r'\bappointed\s+solely\s+by\b', re.I),
            re.compile(r'\barbitrat\w+\s+shall\s+be\s+nominated\s+by\s+(one\s+party|the\s+\w+)\b', re.I),
            re.compile(r'\bunilateral\w*\s+appoint\w+\s+of\s+(the\s+)?arbitrat\w+\b', re.I),
            # Additional: discretion-based arbitrator control
            re.compile(r'\bat\s+the\s+discretion\s+of\s+(the\s+)?(client|owner|company|landlord|licensor|employer)\b', re.I),
            re.compile(r'\bexclusive\s+(right|power)\s+to\s+appoint\s+(the\s+)?arbitrat\w+\b', re.I),
            re.compile(r'\barbitrat\w+\s+chosen\s+(exclusively\s+)?by\s+(the\s+)?(client|owner|company|landlord|licensor)\b', re.I),
            
            # New vocabulary additions (Phase 2)
            re.compile(r'\bappointed\s+exclusively\s+by\b', re.I), # Redundant but explicit
            re.compile(r'\bat\s+its\s+discretion\s+appoint\b', re.I),
        ],
        score=7.0,  # Raised: sole arbitrator appointment by one party is inherently High Risk
        category="Dispute Risk",
        snippet_hint="arbitrator appointed by one party",
    ),
    RiskSignal(
        name="Broad Indemnity",
        patterns=[
            re.compile(r'\bindemnif\w+\s+and\s+(hold\s+harmless|defend)\b', re.I),
            re.compile(r'\bhold\s+harmless\b', re.I),
            re.compile(r'\bindemnif\w+\s+(from|against|for)\s+(any|all|loss\w*|claim\w*)\b', re.I),
        ],
        score=3.0,
        category="Financial Exposure",
        snippet_hint="indemnify and hold harmless",
    ),
    RiskSignal(
        name="Financial Deposit Risk",
        patterns=[
            re.compile(r'\bsecurity\s+deposit\b', re.I),
            re.compile(r'\badvance\s+(deposit|payment)\b', re.I),
            re.compile(r'\binterest.{0,15}deposit\b', re.I),
            re.compile(r'\bdeposit.{0,20}(not|no)\s+(bear|earn)\s+interest\b', re.I),
        ],
        score=3.0,
        category="Financial Exposure",
        snippet_hint="security deposit",
    ),
    RiskSignal(
        name="Penalty Clause",
        patterns=[
            re.compile(r'\bpenalt\w*\b', re.I),
            re.compile(r'\bliquidated\s+damages\b', re.I),
            re.compile(r'\bcompensation\s+of\s+\w+\s+times\b', re.I),
            re.compile(r'\blow\s+shall\s+pay\b', re.I),
        ],
        score=2.0,
        category="Financial Exposure",
        snippet_hint="penalty clause",
    ),
]

# Boilerplate qualifiers that dampen total score
BOILERPLATE_PATTERNS = [
    re.compile(r'\bin\s+accordance\s+with\s+applicable\s+law\b', re.I),
    re.compile(r'\bsubject\s+to\s+(applicable\s+)?law\b', re.I),
    re.compile(r'\bas\s+per\s+statute\b', re.I),
    re.compile(r'\bto\s+the\s+extent\s+permitted\s+by\s+law\b', re.I),
    re.compile(r'\bunder\s+applicable\s+laws\b', re.I),
]

# ─────────────────────────────────────────────────────────────────────────────
# Directionality — simple Subject-Verb-Object extraction
# ─────────────────────────────────────────────────────────────────────────────

# Common party nouns in contracts
PARTY_TERMS = [
    'tenant', 'lessee', 'licensee', 'client', 'customer', 'buyer', 'vendor',
    'party a', 'party b', 'the resident', 'the hostel', 'licensor',
    'owner', 'landlord', 'lessor', 'company', 'service provider', 'contractor',
    'employer', 'employee', 'principal',
]

OBLIGATORY_VERBS = [
    'shall indemnify', 'shall pay', 'shall bear', 'shall forfeit',
    'shall be liable', 'shall compensate', 'must pay', 'is required to pay',
    'is obligated to', 'agrees to indemnify',
]


def _extract_exposed_party(text: str) -> str:
    """
    Simple SVO extraction: find [party] + [shall verb] patterns.
    Returns the party name if found, else "Unknown".
    """
    text_lower = text.lower()

    # Look for "[party] shall [verb indicating obligation]"
    for party in PARTY_TERMS:
        escaped = re.escape(party)
        for verb in OBLIGATORY_VERBS:
            verb_escaped = re.escape(verb)
            # Allow up to 60 chars between party and verb
            pattern = rf'\b{escaped}\b.{{0,60}}\b{verb_escaped}\b'
            if re.search(pattern, text_lower, re.DOTALL):
                return party.title()

    # Fallback: look for "the [Party]" near obligatory verbs
    for verb in OBLIGATORY_VERBS:
        verb_escaped = re.escape(verb)
        m = re.search(rf'(the\s+\w+)\s+{verb_escaped}', text_lower)
        if m:
            subject = m.group(1).strip().title()
            if len(subject.split()) <= 3:
                return subject

    return "Unknown"


def _extract_snippet(text: str, signal: RiskSignal) -> str:
    """
    Extract the exact triggering phrase from text for a given signal.
    Returns a 6-12 word snippet around the match.
    """
    for pattern in signal.patterns:
        m = pattern.search(text)
        if m:
            start = max(0, m.start() - 15)
            end = min(len(text), m.end() + 30)
            raw = text[start:end].strip()
            # Trim to 12 words
            words = raw.split()
            snippet = ' '.join(words[:12])
            return snippet.strip('.,;: ')

    return signal.snippet_hint


class RiskService:

    def analyze_risk(
        self,
        clause_text: str,
        clause_type: str,
        is_mutual: bool = False,
        skip_risk: bool = False,
    ) -> RiskAnalysisResult:
        """
        Compute deterministic risk score from legal signal engine.

        Args:
            clause_text: Full text of the clause
            clause_type: Classification result (e.g. "Termination")
            is_mutual:   True if mutual language detected by classifier
            skip_risk:   True for NON_RISK / Informational clauses

        Returns:
            RiskAnalysisResult with score, level, reasons, snippet, party, category
        """
        if skip_risk or clause_type in ("NON_RISK", "Informational"):
            return RiskAnalysisResult(
                risk_score=0.0,
                risk_level="Informational",
                risk_reasons=["Clause is informational and does not carry legal risk."],
                risky_snippet="",
                exposed_party="N/A",
                risk_category="Informational",
            )

        raw_score = 0.0
        reasons: list[str] = []
        triggered_signals: list[tuple[RiskSignal, str]] = []  # (signal, snippet)

        text_lower = clause_text.lower()

        # ── Fire each signal ──────────────────────────────────────────────────
        for signal in RISK_SIGNALS:
            for pattern in signal.patterns:
                if pattern.search(text_lower):
                    snippet = _extract_snippet(clause_text, signal)
                    triggered_signals.append((signal, snippet))
                    raw_score += signal.score
                    reasons.append(f"{signal.name}: \"{snippet}\"")
                    break  # only fire each signal once per clause

        # ── One-way indemnity bonus ───────────────────────────────────────────
        indemnity_signal = next(
            (s for s in triggered_signals if s[0].name == "Broad Indemnity"), None
        )
        if indemnity_signal and not is_mutual:
            raw_score += 2.0
            reasons.append("Indemnity appears one-directional (no mutual qualifier detected).")

        # ── Mutual dampening — divide signal score by 1.5 ─────────────────────
        if is_mutual and raw_score > 0:
            raw_score = raw_score / 1.5
            reasons.append("Risk dampened: mutual obligation language detected.")

        # ── Boilerplate dampening ─────────────────────────────────────────────
        boilerplate_hits = sum(1 for p in BOILERPLATE_PATTERNS if p.search(text_lower))
        if boilerplate_hits:
            raw_score = max(0.0, raw_score - boilerplate_hits * 0.5)
            reasons.append(f"Score reduced by {boilerplate_hits * 0.5:.1f} for standard legal qualifiers.")

        # ── Fallback: clause type carries base informational risk ─────────────
        if raw_score == 0.0 and clause_type not in ("Unknown", "NON_RISK", "Informational"):
            raw_score = 1.0
            reasons.append(f"Clause type '{clause_type}' carries low inherent exposure.")

        # ── Normalize ─────────────────────────────────────────────────────────
        final_score = round(min(10.0, max(0.0, raw_score)), 2)

        # ── Tiered level ──────────────────────────────────────────────────────
        if final_score >= 7.0:
            risk_level = "High"
        elif final_score >= 4.0:
            risk_level = "Medium"
        elif final_score > 0.0:
            risk_level = "Low"
        else:
            risk_level = "Informational"

        # ── Pick best snippet (highest-score signal) ──────────────────────────
        best_snippet = ""
        best_category = "General"
        if triggered_signals:
            # Sort by signal score descending
            triggered_signals.sort(key=lambda x: x[0].score, reverse=True)
            best_snippet = triggered_signals[0][1]
            best_category = triggered_signals[0][0].category

        # ── Directionality / exposed party ────────────────────────────────────
        exposed_party = _extract_exposed_party(clause_text) if triggered_signals else "N/A"

        return RiskAnalysisResult(
            risk_score=final_score,
            risk_level=risk_level,
            risk_reasons=reasons,
            risky_snippet=best_snippet,
            exposed_party=exposed_party,
            risk_category=best_category,
        )


risk_service = RiskService()
