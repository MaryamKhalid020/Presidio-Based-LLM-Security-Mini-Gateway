# =============================================================================
#  MODULE 2 — INJECTION & JAILBREAK DETECTION
#  Phrase-context aware scoring
# =============================================================================

import re

INJECTION_RULES = [
    (r"ignore\s+(all\s+)?(previous\s+)?instructions?",
     ["follow", "new", "instead", "below"],         0.95),
    (r"forget\s+(all\s+)?(your\s+)?(rules?|guidelines?|instructions?)",
     ["start", "fresh", "now", "instead"],           0.95),
    (r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions?|rules?)",
     ["show", "tell", "display", "print", "repeat"], 0.90),
    (r"repeat\s+(the\s+)?(hidden|system)\s+(message|prompt|instructions?)",
     ["word", "verbatim", "exactly", "copy"],         0.90),
    (r"bypass\s+(your\s+)?(safety|security|content)\s*(filter|policy|rules?)?",
     ["unrestricted", "disable", "skip", "override"],0.92),
    (r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(system|dan|evil|unrestricted)",
     ["no rules", "no restrictions", "bypass"],       0.88),
    (r"act\s+as\s+system",
     ["bypass", "safety", "ignore"],                  0.88),
    (r"jailbreak",
     ["mode", "enable", "activate"],                  0.95),
    (r"do\s+anything\s+now",
     ["dan", "enabled", "no restrictions"],           0.95),
    (r"(developer|sudo|unrestricted|god)\s+mode",
     ["enable", "activate", "enter", "switch"],       0.90),
    (r"override\s+(your\s+)?(instructions?|guidelines?|training)",
     ["new", "follow", "instead", "below"],           0.90),
    (r"pretend\s+(you\s+)?(have\s+no|don.t\s+have)\s+(rules?|restrictions?)",
     ["safety", "filter", "limit"],                   0.88),
    (r"disregard\s+(your\s+)?(previous\s+)?(training|instructions?|guidelines?)",
     ["new", "follow", "instead"],                    0.88),
    (r"show\s+(me\s+)?(your\s+)?(hidden|system|internal)\s+(prompt|rules?|instructions?)",
     ["display", "print", "repeat", "tell"],           0.90),
]

def detect_injection(text):
    """
    Returns (is_attack, score, matched_phrase, context_words_triggered).
    Checks pattern AND nearby phrases (+-60 chars) for context boost.
    """
    best_score, best_match, best_ctx = 0.0, "", []
    for pattern, ctx_words, base in INJECTION_RULES:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            window    = text[max(0, m.start()-60): min(len(text), m.end()+60)].lower()
            triggered = [w for w in ctx_words if w in window]
            score     = round(min(base + 0.02 * len(triggered), 1.0), 3)
            if score > best_score:
                best_score, best_match, best_ctx = score, m.group(), triggered
    return (best_score > 0, best_score, best_match, best_ctx)
