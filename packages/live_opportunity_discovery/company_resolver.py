"""Deterministic company name normalization."""

from __future__ import annotations

import re


LEGAL_SUFFIXES = {
    "inc",
    "incorporated",
    "llc",
    "ltd",
    "limited",
    "corp",
    "corporation",
    "plc",
    "pvt",
    "gmbh",
}


class CompanyResolver:
    def normalize(self, name: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", name).lower()
        tokens = [token for token in cleaned.split() if token not in LEGAL_SUFFIXES]
        return "".join(tokens)

    def display_name(self, name: str) -> str:
        return " ".join(part.capitalize() for part in re.sub(r"\s+", " ", name.strip()).split(" "))
