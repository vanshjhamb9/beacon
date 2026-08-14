"""Security composition checks for Sprint 21."""

from pathlib import Path
from uuid import uuid4

from production_validation.audit.security import SecurityAuditEngine
from production_validation.models.types import HealthStatus, ProductionValidationInput


def test_security_audit_all_controls_pass() -> None:
    report = SecurityAuditEngine().audit(
        ProductionValidationInput(
            oauth_ok=True,
            security_flags={k: True for k in (
                "oauth_tokens", "secrets", "encryption", "webhook_signatures", "rbac",
                "audit_logs", "rate_limits", "csrf", "jwt", "api_keys",
            )},
        )
    )
    assert report.overall_status == HealthStatus.PASS
    assert report.score >= 90


def test_security_docs_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "security.md").exists() or (root / "docs" / "oauth.md").exists()


def test_webhook_crypto_module_present() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "packages" / "communication_gateway" / "security" / "crypto.py").exists()
