"""Intent Detection Engine for Beacon.

Detects explicit buying requirements from public signals.
Priority: EXPLICIT REQUIREMENTS > ICP FIT > GENERIC SIGNALS.

Rules:
- "looking for developers" = HIGH INTENT
- "funded D2C brand" = LOW INTENT (discovery signal only)
- Never convert absence of intent into positive/negative claim
"""
