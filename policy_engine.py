# =============================================================================
#  MODULE 4 — POLICY DECISION ENGINE
#  Allow / Anonymize / Block
# =============================================================================

# Configurable thresholds
BLOCK_THRESHOLD     = 0.70
ANONYMIZE_THRESHOLD = 0.40

MASK_MAP = {
    "PHONE_NUMBER":  "<PHONE_REDACTED>",
    "EMAIL_ADDRESS": "<EMAIL_REDACTED>",
    "PERSON":        "<NAME_REDACTED>",
    "API_KEY":       "<API_KEY_REDACTED>",
    "CREDIT_CARD":   "<CC_REDACTED>",
    "PASSWORD":      "<PASSWORD_REDACTED>",
    "INTERNAL_ID":   "<ID_REDACTED>",
    "DEFAULT":       "<REDACTED>",
}

def policy_decision(inj_score, entities, comp):
    """
    Returns (action, risk_score, entity_types).
    - Any injection score > 0  -> BLOCK
    - Any PII detected         -> ANONYMIZE
    - Clean input              -> ALLOW
    """
    entity_types = list({e["entity"] for e in entities})
    if inj_score > 0:
        return "BLOCK", round(inj_score, 3), entity_types
    if entities:
        risk = round(min(max(e["score"] for e in entities) + comp, 1.0), 2)
        return "ANONYMIZE", risk, entity_types
    return "ALLOW", 0.0, []

def anonymize_text(text, entities):
    """Replace detected entities with masked placeholders."""
    for e in sorted(entities, key=lambda x: x["start"], reverse=True):
        text = text[:e["start"]] + MASK_MAP.get(e["entity"], "<REDACTED>") + text[e["end"]:]
    return text
