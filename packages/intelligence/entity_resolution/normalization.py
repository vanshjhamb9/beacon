import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

LEGAL_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "gmbh",
    "inc",
    "incorporated",
    "ltd",
    "llc",
    "limited",
    "plc",
}


def normalize_company_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", name).lower()
    tokens = [token for token in cleaned.split() if token not in LEGAL_SUFFIXES]
    return " ".join(tokens)


def normalize_domain(value: str) -> str | None:
    candidate = value.strip().lower()
    if not candidate:
        return None
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    host = parsed.netloc or parsed.path
    host = host.removeprefix("www.")
    if "." not in host:
        return None
    return host.split("/")[0]


def fuzzy_similarity(left: str, right: str) -> float:
    normalized_left = normalize_company_name(left)
    normalized_right = normalize_company_name(right)
    if not normalized_left or not normalized_right:
        return 0.0
    return round(SequenceMatcher(None, normalized_left, normalized_right).ratio(), 4)
