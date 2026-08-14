"""Audit engine — records every decision, every gate, every timestamp.

No NULLs. Every opportunity fully auditable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .v1_schemas import AuditEntry, OpportunityMetadata, ValidationOutcome


class AuditEngine:
    """Records every validation decision with full audit trail."""

    def __init__(self):
        self._entries: list[dict[str, Any]] = []
        self._gate_results: dict[str, list[dict[str, Any]]] = {}

    def record_gate(
        self,
        opportunity_id: str,
        gate: str,
        decision: str,
        reasons: list[str],
        evidence: dict[str, Any],
    ) -> AuditEntry:
        """Record a single gate result."""
        entry = AuditEntry(
            data={
                "opportunity_id": opportunity_id,
                "gate": gate,
                "decision": decision,
                "reasons": reasons,
                "evidence": evidence,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        self._entries.append(entry.to_dict())
        if opportunity_id not in self._gate_results:
            self._gate_results[opportunity_id] = []
        self._gate_results[opportunity_id].append(entry.to_dict())
        return entry

    def record_validation(
        self,
        metadata: OpportunityMetadata,
        outcome: ValidationOutcome,
    ) -> list[AuditEntry]:
        """Record full validation outcome as audit entries."""
        entries = []

        # Record each reason as separate audit entry
        for reason in outcome.reasons:
            entry = self.record_gate(
                opportunity_id=metadata.opportunity_id,
                gate="validation_reason",
                decision=outcome.decision,
                reasons=[reason],
                evidence=outcome.evidence,
            )
            entries.append(entry)

        # Record overall decision
        entry = self.record_gate(
            opportunity_id=metadata.opportunity_id,
            gate="final_decision",
            decision=outcome.decision,
            reasons=outcome.reasons,
            evidence=outcome.evidence,
        )
        entries.append(entry)

        return entries

    def get_audit_trail(self, opportunity_id: str) -> list[dict[str, Any]]:
        """Get full audit trail for opportunity."""
        return self._gate_results.get(opportunity_id, [])

    def get_all_entries(self) -> list[dict[str, Any]]:
        """Get all audit entries."""
        return list(self._entries)

    def get_entries_by_gate(self, gate: str) -> list[dict[str, Any]]:
        """Get all entries for a specific gate."""
        return [e for e in self._entries if e.get("gate") == gate]

    def get_entries_by_decision(self, decision: str) -> list[dict[str, Any]]:
        """Get all entries for a specific decision."""
        return [e for e in self._entries if e.get("decision") == decision]

    def get_statistics(self) -> dict[str, Any]:
        """Get audit statistics."""
        total = len(self._entries)
        gates = {}
        decisions = {}

        for entry in self._entries:
            gate = entry.get("gate", "unknown")
            decision = entry.get("decision", "unknown")
            gates[gate] = gates.get(gate, 0) + 1
            decisions[decision] = decisions.get(decision, 0) + 1

        return {
            "total_entries": total,
            "by_gate": gates,
            "by_decision": decisions,
            "unique_opportunities": len(self._gate_results),
        }

    def clear(self):
        """Clear all audit entries (for testing)."""
        self._entries.clear()
        self._gate_results.clear()
