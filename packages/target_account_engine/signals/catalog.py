from __future__ import annotations


INTENT_SIGNAL_WEIGHTS: dict[str, float] = {
    "hiring": 10.0,
    "funding": 12.0,
    "ai": 11.0,
    "automation": 11.0,
    "expansion": 9.0,
    "support growth": 10.0,
    "migration": 10.0,
    "digital transformation": 11.0,
    "customer complaints": 8.0,
    "scaling": 9.0,
    "product launch": 10.0,
    "whatsapp": 8.0,
    "shopify": 7.0,
    "crm": 6.0,
}

URGENCY_SIGNAL_WEIGHTS: dict[str, float] = {
    "recent funding": 14.0,
    "funding": 10.0,
    "hiring": 9.0,
    "migration": 12.0,
    "expansion": 9.0,
    "leadership change": 11.0,
    "support overload": 13.0,
    "website redesign": 10.0,
    "tech migration": 12.0,
    "ai adoption": 11.0,
    "product launch": 10.0,
    "hubspot": 8.0,
    "salesforce": 8.0,
}


def detect_signals(corpus: list[str], catalog: dict[str, float]) -> list[str]:
    text = " ".join((item or "").lower() for item in corpus)
    hits: list[str] = []
    for name in catalog:
        if name.lower() in text:
            hits.append(name)
    return hits
