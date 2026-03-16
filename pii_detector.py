# =============================================================================
#  MODULE 1 — PII DETECTION
#  Fallback regex patterns + Presidio NLP
# =============================================================================

import re

# ── Fallback Regex Patterns ───────────────────────────────────────────────────
FALLBACK_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    "PHONE_NUMBER":  re.compile(r"\b0\d{10}\b|\b\+?\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{4}\b"),
    "API_KEY":       re.compile(r"sk-[A-Za-z0-9]{6,}|(?i)(?:api[_\s]?key|token)\s*[:=]\s*\S{4,}"),
    "INTERNAL_ID":   re.compile(r"\b(EMP|INT|ID|STAFF)-\d{3,6}\b|\bid\s+(is\s+)?\d{3,6}\b", re.IGNORECASE),
    "CREDIT_CARD":   re.compile(r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b"),
    "PASSWORD":      re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+"),
}

def fallback_analyze(text):
    results = []
    for entity, pat in FALLBACK_PATTERNS.items():
        for m in pat.finditer(text):
            results.append({
                "entity": entity,
                "start":  m.start(),
                "end":    m.end(),
                "match":  m.group(),
                "score":  0.85,
            })
    return results
