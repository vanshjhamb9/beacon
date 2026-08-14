"""Account Scheduler - Orchestrate SIDP processing."""

from __future__ import annotations

import logging

from packages.sales_intelligence_platform.engines.account_builder import build_account
from packages.sales_intelligence_platform.engines.account_dashboard import (
    generate_dashboard_data,
)
from packages.sales_intelligence_platform.engines.account_metrics import calculate_metrics
from packages.sales_intelligence_platform.engines.account_reports import (
    generate_account_report,
)
from packages.sales_intelligence_platform.models import Account

logger = logging.getLogger(__name__)


class AccountScheduler:
    """Orchestrate the SIDP processing pipeline."""

    def process_lead(self, lead_data: dict) -> Account:
        """Process a single ecommerce lead into a sales account."""
        return build_account(lead_data)

    def process_leads(self, leads: list[dict]) -> list[Account]:
        """Process multiple ecommerce leads into sales accounts."""
        accounts: list[Account] = []
        for lead in leads:
            try:
                account = self.process_lead(lead)
                accounts.append(account)
            except Exception as e:
                logger.warning("Failed to process lead %s: %s", lead.get("domain"), e)
        return accounts

    def get_dashboard(self, accounts: list[Account]) -> dict:
        """Generate dashboard data."""
        return generate_dashboard_data(accounts)

    def get_metrics(self, accounts: list[Account]) -> dict:
        """Calculate aggregate metrics."""
        return calculate_metrics(accounts)

    def get_account_report(self, account: Account) -> dict:
        """Generate detailed report for one account."""
        return generate_account_report(account)

    def filter_sales_ready(self, accounts: list[Account]) -> list[Account]:
        """Filter to only sales-ready accounts."""
        return [a for a in accounts if a.status == "SALES_READY"]

    def filter_needs_enrichment(self, accounts: list[Account]) -> list[Account]:
        """Filter to accounts needing enrichment."""
        return [a for a in accounts if a.status == "NEEDS_ENRICHMENT"]

    def filter_manual_review(self, accounts: list[Account]) -> list[Account]:
        """Filter to accounts needing manual review."""
        return [a for a in accounts if a.status == "MANUAL_REVIEW"]
