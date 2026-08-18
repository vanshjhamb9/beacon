"""Competitors and pentest vendors that must never become cyber leads."""

from __future__ import annotations

CYBER_COMPETITORS: tuple[str, ...] = (
    "rapid7",
    "tenable",
    "qualys",
    "crowdstrike",
    "palo alto",
    "sentinelone",
    "hackerone",
    "bugcrowd",
    "intigriti",
    "yeswehack",
    "cobalt",
    "synack",
    "bishop fox",
    "ncc group",
    "mandiant",
    "offensive security",
    "portswigger",
    "detectify",
    "pentest-tools",
    "pentest tools",
    "trustedsec",
    "secureworks",
    "proofpoint",
    "zscaler",
    "checkmarx",
    "veracode",
    "snyk",
    "sonarqube",
    "hack the box",
    "tryhackme",
    "offsec",
    "netspi",
    "trail of bits",
    "cure53",
    "includesecurity",
    "include security",
    "praetorian",
    "atomics",
    "nowsecure",
    "data theorem",
)


def is_competitor(name_or_text: str) -> bool:
    blob = (name_or_text or "").lower()
    if not blob:
        return False
    return any(comp in blob for comp in CYBER_COMPETITORS)
