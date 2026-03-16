# =============================================================================
#  MODULE 5 — GATEWAY PIPELINE
#  User Input -> Injection Detection -> Presidio Analyzer -> Policy -> Output
# =============================================================================

import time

try:
    from presidio_analyzer import (AnalyzerEngine, PatternRecognizer,
                                    Pattern, RecognizerRegistry)
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

from pii_detector            import fallback_analyze
from injection_detector      import detect_injection
from presidio_customizations import context_aware_score, composite_boost, calibrate_confidence
from policy_engine           import policy_decision, anonymize_text

# ── Build Presidio Analyzer ───────────────────────────────────────────────────
def build_presidio():
    api_key_rec = PatternRecognizer(
        supported_entity="API_KEY",
        patterns=[
            Pattern("api_key_sk",  r"sk-[A-Za-z0-9]{6,}",                         0.90),
            Pattern("api_key_ctx", r"(?i)(api[_\s]?key|token)\s*[:=\s]\s*\S{6,}", 0.90),
            Pattern("api_key_gen", r"\b[A-Za-z0-9]{32,45}\b",                      0.70),
        ],
        context=["api", "key", "token", "secret", "bearer", "auth"]
    )
    emp_id_rec = PatternRecognizer(
        supported_entity="INTERNAL_ID",
        patterns=[
            Pattern("emp_prefix", r"\b(EMP|INT|ID|STAFF)-\d{3,6}\b", 0.88),
            Pattern("emp_plain",  r"\b\d{4,6}\b",                      0.60),
        ],
        context=["employee", "emp", "staff", "internal", "id", "identifier"]
    )
    cc_rec = PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[Pattern("cc", r"\b(\d{4}[\s\-]?){3}\d{4}\b", 0.85)],
        context=["card", "credit", "debit", "payment"]
    )
    try:
        nlp = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
        }).create_engine()
    except Exception:
        nlp = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
        }).create_engine()
    reg = RecognizerRegistry()
    reg.load_predefined_recognizers()
    for r in [api_key_rec, emp_id_rec, cc_rec]:
        reg.add_recognizer(r)
    return AnalyzerEngine(nlp_engine=nlp, registry=reg)

_analyzer = None

def init_presidio():
    global _analyzer
    if PRESIDIO_AVAILABLE and _analyzer is None:
        try:
            _analyzer = build_presidio()
        except Exception:
            pass

# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run_gateway(user_input):
    t0 = time.perf_counter()

    # Step 1 — Injection Detection
    is_inj, inj_score, inj_match, ctx_phrases = detect_injection(user_input)

    # Step 2 — PII Analysis (fallback regex always runs first)
    entities   = []
    seen_spans = set()

    for e in fallback_analyze(user_input):
        e["score"] = context_aware_score(e["entity"], e["score"], user_input, e["start"], e["end"])
        entities.append(e)
        seen_spans.add((e["start"], e["end"]))

    # Presidio adds PERSON / NLP-based detections on top
    if PRESIDIO_AVAILABLE and _analyzer:
        try:
            for r in _analyzer.analyze(text=user_input, language="en"):
                if (r.start, r.end) in seen_spans:
                    continue
                cal = calibrate_confidence(r.entity_type, r.score, user_input, r.start, r.end)
                if cal:
                    entities.append({
                        "entity": r.entity_type,
                        "start":  r.start,
                        "end":    r.end,
                        "match":  user_input[r.start:r.end],
                        "score":  cal,
                    })
                    seen_spans.add((r.start, r.end))
        except Exception:
            pass

    # Step 3 — Composite Detection
    comp = composite_boost({e["entity"] for e in entities})

    # Step 4 — Policy Decision
    action, risk, entity_types = policy_decision(inj_score, entities, comp)

    # Step 5 — Output
    if action == "BLOCK":
        output = "REQUEST BLOCKED: Prompt violates security policies."
    elif action == "ANONYMIZE":
        output = "[ANONYMIZED] " + anonymize_text(user_input, entities)
    else:
        output = "[ALLOWED] " + user_input

    return {
        "input":       user_input,
        "action":      action,
        "risk":        risk,
        "entities":    entity_types,
        "inj_score":   inj_score,
        "inj_match":   inj_match,
        "ctx_phrases": ctx_phrases,
        "comp_boost":  round(comp, 3),
        "output":      output,
        "latency_ms":  round((time.perf_counter() - t0) * 1000, 2),
    }
