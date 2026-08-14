from __future__ import annotations

from production_validation.models.types import (
    EngineHealthReport,
    HealthStatus,
    ModuleReadiness,
    ProductionReadinessReport,
    RevenueHealthSnapshot,
    SecurityAuditReport,
)


MODULES = (
    "Infrastructure",
    "API",
    "Workers",
    "Queues",
    "Database",
    "Redis",
    "Email",
    "WhatsApp",
    "Campaigns",
    "Revenue Hunter",
    "Founder OS",
    "Sales Intelligence",
    "Dashboard",
    "Security",
    "Performance",
    "Monitoring",
    "Documentation",
    "Testing",
)


class ReadinessReportEngine:
    def build(
        self,
        *,
        health: EngineHealthReport,
        revenue: RevenueHealthSnapshot,
        security: SecurityAuditReport,
        docs_ok: bool = True,
        tests_ok: bool = True,
        performance_ok: bool = True,
    ) -> ProductionReadinessReport:
        by_name = {c.name: c for c in health.components}
        modules: list[ModuleReadiness] = []
        mapping = {
            "API": "api",
            "Workers": "workers",
            "Queues": "queues",
            "Database": "database",
            "Redis": "redis",
            "Email": "email",
            "WhatsApp": "whatsapp",
            "Campaigns": "campaigns",
            "Monitoring": "pipeline",
        }
        for module in MODULES:
            if module == "Security":
                status, score = security.overall_status, security.score
                rec = "Security controls healthy." if status == HealthStatus.PASS else "Fix FAIL security controls."
            elif module == "Documentation":
                status = HealthStatus.PASS if docs_ok else HealthStatus.WARNING
                score = 100.0 if docs_ok else 70.0
                rec = "Docs present." if docs_ok else "Update production runbooks."
            elif module == "Testing":
                status = HealthStatus.PASS if tests_ok else HealthStatus.FAIL
                score = 100.0 if tests_ok else 40.0
                rec = "Test suites green." if tests_ok else "Repair failing tests before merge."
            elif module == "Performance":
                status = HealthStatus.PASS if performance_ok else HealthStatus.WARNING
                score = 100.0 if performance_ok else 65.0
                rec = "Perf budgets met." if performance_ok else "Re-run load benchmarks."
            elif module in {"Revenue Hunter", "Founder OS", "Sales Intelligence", "Dashboard", "Infrastructure"}:
                # Compose from overall platform health + revenue observability
                status = health.overall_status
                score = health.overall_score
                rec = "Composable engines observable via Production Validation."
                if module == "Infrastructure" and health.overall_score < 85:
                    rec = "Stabilize FAIL/WARNING components first."
            else:
                key = mapping.get(module, module.lower())
                comp = by_name.get(key)
                if comp:
                    status, score = comp.status, self._score(comp.status)
                    rec = comp.recommendation or "Healthy."
                else:
                    status, score, rec = HealthStatus.WARNING, 70.0, "No direct probe; monitor via system-health."
            modules.append(
                ModuleReadiness(module=module, status=status, score=round(score, 4), recommendation=rec, evidence=[f"module:{module}"])
            )

        overall = sum(m.score for m in modules) / max(len(modules), 1)
        # Soft boost when revenue metrics are present (business observability)
        if revenue.pipeline_value or revenue.campaigns:
            overall = min(100.0, overall + 1.0)
        overall_status = (
            HealthStatus.PASS if overall >= 95 else HealthStatus.WARNING if overall >= 80 else HealthStatus.FAIL
        )
        blockers = [m.module for m in modules if m.status == HealthStatus.FAIL]
        warnings = [m.module for m in modules if m.status == HealthStatus.WARNING]
        return ProductionReadinessReport(
            overall_score=round(overall, 4),
            overall_status=overall_status,
            modules=modules,
            blockers=blockers,
            warnings=warnings,
            evidence=[f"modules:{len(modules)}", f"blockers:{len(blockers)}", f"score:{overall}"],
        )

    def _score(self, status: HealthStatus) -> float:
        return {HealthStatus.PASS: 100.0, HealthStatus.WARNING: 75.0, HealthStatus.FAIL: 40.0}.get(status, 50.0)
