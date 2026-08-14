from __future__ import annotations

from typing import Any, Sequence

from runtime_ops.migrations.catalog import HEAD_REVISION, PENDING_CHAIN, REQUIRED_TABLES
from runtime_ops.models.types import MigrationValidationResult


class MigrationValidator:
    """Verify Alembic revision + required operational tables exist."""

    def __init__(
        self,
        *,
        head_revision: str = HEAD_REVISION,
        required_tables: Sequence[str] = REQUIRED_TABLES,
        pending_chain: Sequence[str] = PENDING_CHAIN,
    ) -> None:
        self.head_revision = head_revision
        self.required_tables = tuple(required_tables)
        self.pending_chain = tuple(pending_chain)

    def evaluate(
        self,
        *,
        current_revision: str | None,
        existing_tables: Sequence[str],
    ) -> MigrationValidationResult:
        tables = {t.lower() for t in existing_tables}
        present = [t for t in self.required_tables if t.lower() in tables]
        missing = [t for t in self.required_tables if t.lower() not in tables]

        pending: list[str] = []
        if current_revision != self.head_revision:
            if not current_revision:
                pending = list(self.pending_chain)
            else:
                try:
                    idx = self.pending_chain.index(current_revision)
                    pending = list(self.pending_chain[idx + 1 :])
                except ValueError:
                    # Current may be before chain start or already head with alias.
                    if current_revision != self.head_revision:
                        pending = list(self.pending_chain)

        ok = current_revision == self.head_revision and not missing
        evidence = [
            f"current:{current_revision or 'none'}",
            f"head:{self.head_revision}",
            f"present_tables:{len(present)}",
            f"missing_tables:{len(missing)}",
            f"pending:{len(pending)}",
        ]
        return MigrationValidationResult(
            ok=ok,
            current_revision=current_revision,
            head_revision=self.head_revision,
            pending_revisions=pending,
            missing_tables=missing,
            present_tables=present,
            evidence=evidence,
        )

    def evaluate_from_rows(self, *, current_revision: str | None, table_rows: Sequence[Any]) -> MigrationValidationResult:
        names = [str(row[0] if not isinstance(row, str) else row) for row in table_rows]
        return self.evaluate(current_revision=current_revision, existing_tables=names)
