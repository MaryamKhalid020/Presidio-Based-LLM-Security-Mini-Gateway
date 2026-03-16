# =============================================================================
#  MODULE 3 — PRESIDIO CUSTOMIZATIONS
#  1. Context-Aware Scoring
#  2. Composite Entity Detection
#  3. Confidence Calibration
# =============================================================================

# ── Customization 1: Context-Aware Scoring ───────────────────────────────────
CONTEXT_BOOST = {
    "PHONE_NUMBER":  ["call", "mobile", "phone", "contact", "reach", "dial", "number"],
    "EMAIL_ADDRESS": ["email", "mail", "contact", "send", "inbox", "address", "is"],
    "API_KEY":       ["api", "token", "key", "secret", "bearer", "auth"],
    "INTERNAL_ID":   ["employee", "emp", "staff", "id", "internal", "account"],
    "CREDIT_CARD":   ["card", "credit", "debit", "payment", "pay"],
    "PASSWORD":      ["login", "password", "credential", "auth"],
}

def context_aware_score(entity_type, raw_score, text, start, end):
    """Boost score if context words appear within +-50 chars of entity."""
    window = text[max(0, start-50): min(len(text), end+50)].lower()
    boost  = sum(0.05 for w in CONTEXT_BOOST.get(entity_type, []) if w in window)
    return round(min(raw_score + boost, 1.0), 2)


# ── Customization 2: Composite Entity Detection ──────────────────────────────
COMPOSITE_RULES = [
    ({"PERSON", "EMAIL_ADDRESS"},                0.15),
    ({"PERSON", "PHONE_NUMBER"},                 0.15),
    ({"PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"},0.25),
    ({"API_KEY", "EMAIL_ADDRESS"},               0.20),
    ({"PASSWORD", "EMAIL_ADDRESS"},              0.25),
    ({"CREDIT_CARD", "PERSON"},                  0.20),
]

def composite_boost(detected_types):
    """Extra risk score when multiple sensitive entity types co-occur."""
    boost = sum(extra for rule, extra in COMPOSITE_RULES
                if rule.issubset(detected_types))
    return min(boost, 0.30)


# ── Customization 3: Confidence Calibration ──────────────────────────────────
CONFIDENCE_THRESHOLDS = {
    "API_KEY":       0.65,
    "PASSWORD":      0.65,
    "CREDIT_CARD":   0.60,
    "PHONE_NUMBER":  0.40,
    "EMAIL_ADDRESS": 0.40,
    "PERSON":        0.40,
    "INTERNAL_ID":   0.40,
    "DEFAULT":       0.40,
}

def calibrate_confidence(entity_type, score, text, start, end):
    """Apply context boost then filter by per-entity threshold."""
    cal       = context_aware_score(entity_type, score, text, start, end)
    threshold = CONFIDENCE_THRESHOLDS.get(entity_type, CONFIDENCE_THRESHOLDS["DEFAULT"])
    return cal if cal >= threshold else None
