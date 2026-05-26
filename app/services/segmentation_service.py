"""
Hierarchy-aware contract segmentation service.

Replaces NLTK sentence tokenizer with a regex-based parser that understands
legal document structure: Articles, numbered clauses, sub-clauses, and bullets.

Returns clause metadata including start/end positions, depth, parent clause,
and a SHA-256 hash for deduplication and auditing.
"""

import re
import hashlib
from app.core.logging import logger


# ─────────────────────────────────────────────────────────────────────────────
# Clause-number patterns ordered from most-specific to least-specific
# Each tuple: (regex, depth, label)
# ─────────────────────────────────────────────────────────────────────────────
ARTICLE_PATTERN = re.compile(
    r'^(?:ARTICLE|Article)\s*[\-\u2013\u2014]?\s*(\d+|[IVXLCDM]+)\b',
    re.MULTILINE
)

# Numbered sub-clauses: 3.1.2  / 12.4.1
DEEP_CLAUSE_PATTERN = re.compile(
    r'^\s*(\d{1,3}\.\d{1,3}\.\d{1,3})\s*(.*)',
    re.MULTILINE
)

# Standard clauses: 3.1  / 12.4
CLAUSE_PATTERN = re.compile(
    r'^\s*(\d{1,3}\.\d{1,3})\s*(.*)',
    re.MULTILINE
)

# Top-level numbered: 3.  / 12.
TOP_CLAUSE_PATTERN = re.compile(
    r'^\s*(\d{1,3})\.\s+(.*)',
    re.MULTILINE
)

# Alphabetic bullets: a)  / (b)
ALPHA_BULLET_PATTERN = re.compile(
    r'^\s*\(?([a-z])\)\s+(.*)',
    re.MULTILINE
)

# Roman numeral sub-items: (i) / (ii) / (iii)
ROMAN_BULLET_PATTERN = re.compile(
    r'^\s*\(([ivxlIVXL]+)\)\s+(.*)',
    re.MULTILINE
)

# Words considered "non-risk" short headings to skip
SHORT_HEADING_RE = re.compile(r'^[A-Z\s\-]{1,60}$')

# Blacklist clause types determined before risk engine
NON_RISK_HEADING_KEYWORDS = {
    'definitions', 'interpretation', 'signature', 'signatures',
    'witness', 'witnesses', 'execution', 'schedule', 'annexure',
    'exhibit', 'appendix', 'table of contents'
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()


def _word_count(text: str) -> int:
    return len(text.split())


def _is_pure_heading(text: str) -> bool:
    """True if text is all-caps and short — not a substantive clause."""
    stripped = text.strip()
    return bool(SHORT_HEADING_RE.match(stripped)) and _word_count(stripped) <= 6


def _heading_is_non_risk(heading: str) -> bool:
    if not heading:
        return False
    return any(kw in heading.lower() for kw in NON_RISK_HEADING_KEYWORDS)


class SegmentationService:
    """
    Segments a legal contract into atomic clause units with full metadata.
    """

    def segment_text(self, text: str) -> list[dict]:
        """
        Parse contract text into a list of clause dicts:

        {
            clause_index   : int,
            article_number : str | None,
            clause_number  : str | None,
            heading        : str | None,
            full_text      : str,
            depth          : int,          # 0=Article 1=Top 2=NN 3=NNN 4=Alpha 5=Roman
            parent_clause  : str | None,
            start_char     : int,
            end_char       : int,
            clause_hash    : str,
            skip_risk      : bool          # True → Informational, skip risk scoring
        }
        """
        clauses = []
        clause_index = 0

        # ── Build a flat list of (match_start, clause_number, depth, heading_text) ──
        anchors: list[dict] = []

        # Articles (depth 0)
        for m in ARTICLE_PATTERN.finditer(text):
            anchors.append({
                'start': m.start(),
                'clause_number': None,
                'article_number': m.group(1),
                'depth': 0,
                'heading_raw': m.group(0).strip(),
            })

        # Deep sub-clauses N.N.N (depth 3) — before N.N to avoid partial match
        for m in DEEP_CLAUSE_PATTERN.finditer(text):
            anchors.append({
                'start': m.start(),
                'clause_number': m.group(1),
                'article_number': None,
                'depth': 3,
                'heading_raw': m.group(2).strip(),
            })

        # Standard clauses N.N (depth 2)
        for m in CLAUSE_PATTERN.finditer(text):
            num = m.group(1)
            anchors.append({
                'start': m.start(),
                'clause_number': num,
                'article_number': None,
                'depth': 2,
                'heading_raw': m.group(2).strip(),
            })

        # Top-level clauses N. (depth 1)
        for m in TOP_CLAUSE_PATTERN.finditer(text):
            anchors.append({
                'start': m.start(),
                'clause_number': m.group(1) + '.',
                'article_number': None,
                'depth': 1,
                'heading_raw': m.group(2).strip(),
            })

        # Alpha bullets a) / (b) (depth 4)
        for m in ALPHA_BULLET_PATTERN.finditer(text):
            anchors.append({
                'start': m.start(),
                'clause_number': m.group(1) + ')',
                'article_number': None,
                'depth': 4,
                'heading_raw': m.group(2).strip(),
            })

        # Roman bullets (i) (depth 5)
        for m in ROMAN_BULLET_PATTERN.finditer(text):
            anchors.append({
                'start': m.start(),
                'clause_number': '(' + m.group(1) + ')',
                'article_number': None,
                'depth': 5,
                'heading_raw': m.group(2).strip(),
            })

        if not anchors:
            # Fallback: paragraph-based segmentation
            return self._fallback_paragraph_segment(text)

        # ── Sort by position, deduplicate overlapping anchors ──
        anchors.sort(key=lambda a: a['start'])
        anchors = self._dedup_anchors(anchors)

        # ── Slice text between anchors to get full_text for each clause ──
        current_article = None
        parent_stack: list[tuple[int, str]] = []  # stack of (depth, clause_number) for parent tracking

        for i, anchor in enumerate(anchors):
            start = anchor['start']
            end = anchors[i + 1]['start'] if i + 1 < len(anchors) else len(text)

            full_text = text[start:end].strip()

            # Update article tracker
            if anchor['depth'] == 0:
                current_article = anchor.get('article_number')

            # Determine parent
            depth = anchor['depth']
            clause_num = anchor.get('clause_number')

            # Trim parent stack: pop entries at same or deeper depth
            while parent_stack and parent_stack[-1][0] >= depth:
                parent_stack.pop()
            parent = parent_stack[-1][1] if parent_stack else None
            if clause_num is not None:
                parent_stack.append((depth, clause_num))

            heading = anchor['heading_raw'][:120] if anchor['heading_raw'] else None

            # ── Apply length guard ──
            word_count = _word_count(full_text)
            skip_risk = False

            if word_count < 5:
                skip_risk = True
            elif _is_pure_heading(full_text):
                skip_risk = True
            elif _heading_is_non_risk(heading):
                skip_risk = True

            clause_index += 1
            clauses.append({
                'clause_index': clause_index,
                'article_number': current_article,
                'clause_number': clause_num,
                'heading': heading,
                'full_text': full_text,
                'depth': depth,
                'parent_clause': parent,
                'start_char': start,
                'end_char': end,
                'clause_hash': _sha256(full_text),
                'skip_risk': skip_risk,
            })

        logger.info(f"Segmented {len(clauses)} clauses ({sum(1 for c in clauses if c['skip_risk'])} informational)")
        return clauses

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _dedup_anchors(self, anchors: list[dict]) -> list[dict]:
        """Remove anchors whose start position is within 5 chars of a more-specific match."""
        deduped = []
        seen_positions = set()
        for anchor in anchors:
            pos = anchor['start']
            # Check if any position within ±5 already claimed by a deeper-depth anchor
            conflict = any(abs(pos - s) <= 5 for s in seen_positions)
            if not conflict:
                deduped.append(anchor)
                seen_positions.add(pos)
        return deduped

    def _fallback_paragraph_segment(self, text: str) -> list[dict]:
        """
        When no structural anchors found, split by double newlines (paragraphs).
        Skips paragraphs < 20 words.
        """
        paragraphs = re.split(r'\n\s*\n', text)
        clauses = []
        pos = 0
        for i, para in enumerate(paragraphs):
            stripped = para.strip()
            start = text.find(stripped, pos)
            end = start + len(stripped)
            pos = end

            if _word_count(stripped) < 20:
                continue

            clauses.append({
                'clause_index': i + 1,
                'article_number': None,
                'clause_number': None,
                'heading': None,
                'full_text': stripped,
                'depth': 1,
                'parent_clause': None,
                'start_char': start,
                'end_char': end,
                'clause_hash': _sha256(stripped),
                'skip_risk': False,
            })

        logger.info(f"Fallback segmentation: {len(clauses)} paragraphs")
        return clauses


segmentation_service = SegmentationService()
