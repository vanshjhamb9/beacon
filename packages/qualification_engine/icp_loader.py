"""Load ICP configurations from YAML files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ICPConfig:
    """ICP configuration for a business unit."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.business_unit: str = config["business_unit"]
        self.name: str = config["name"]
        self.description: str = config["description"]
        
        # Handle both B2C and B2B ICP formats
        self.is_b2b_partner: bool = "partner_types" in config
        
        if self.is_b2b_partner:
            # B2B Partner ICP format
            self.target_industries: list[str] = []
            partner_types = config.get("partner_types", {})
            for priority_data in partner_types.values():
                if isinstance(priority_data, dict) and "types" in priority_data:
                    self.target_industries.extend(priority_data["types"])
            
            # Size - B2B partners are agencies, not brands
            self.min_employees: int = config.get("partner_icp", {}).get("priority", {}).get("min_clients", 0)
            self.max_employees: int = 1000  # Agencies can be larger
            self.min_revenue: float = 0.0
            self.max_revenue: float = 1_000_000_000.0
            self.min_product_count: int = 0
            self.max_product_count: int = 100000
            
            # Geography
            target_countries = config.get("target_countries", {})
            if isinstance(target_countries, dict):
                self.target_countries: list[str] = target_countries.get("tier_1", [])
            else:
                self.target_countries = target_countries
            self.target_cities: list[str] = []  # B2B partners can be anywhere
            
            # Technology
            self.target_platforms: list[str] = []
            
            # Exclusions - B2B specific
            self.exclusion_rules: dict[str, list[str]] = {}
            
            # B2B specific fields
            self.partner_types: dict[str, Any] = partner_types
            self.high_value_signals: dict[str, int] = config.get("high_value_signals", {})
            self.high_intent_signals: list[str] = config.get("high_intent_signals", [])
            self.partner_icp: dict[str, Any] = config.get("partner_icp", {})
            self.partner_tiers: dict[str, Any] = config.get("partner_tiers", {})
            self.client_access_scoring: dict[str, Any] = config.get("client_access_scoring", {})
            self.comai_partner_fit_scoring: dict[str, Any] = config.get("comai_partner_fit_scoring", {})
            
            # Default values for B2C fields
            self.buyability_scoring: dict[str, int] = {}
            self.business_stages: dict[str, dict[str, Any]] = {}
            self.thresholds: dict[str, int] = config.get("thresholds", {})
            self.services: list[dict[str, Any]] = []
            self.follow_up_config: dict[str, str] = {}
        else:
            # B2C ICP format (existing)
            self.target_industries: list[str] = config.get("target_industries", [])
            
            # Size
            self.min_employees: int = config.get("min_employees", 0)
            self.max_employees: int = config.get("max_employees", 100000)
            self.min_revenue: float = config.get("min_revenue", 0.0)
            self.max_revenue: float = config.get("max_revenue", 1_000_000_000.0)
            self.min_product_count: int = config.get("min_product_count", 0)
            self.max_product_count: int = config.get("max_product_count", 100000)

            # Geography
            self.target_countries: list[str] = config.get("target_countries", [])
            self.target_cities: list[str] = config.get("target_cities", [])

            # Technology
            self.target_platforms: list[str] = config.get("target_platforms", [])

            # Exclusions
            self.exclusion_rules: dict[str, list[str]] = config.get("exclusion_rules", {})

            # Buyability scoring weights
            self.buyability_scoring: dict[str, int] = config.get("buyability_scoring", {})

            # High-value signal bonuses
            self.high_value_signals: dict[str, int] = config.get("high_value_signals", {})

            # Business stages
            self.business_stages: dict[str, dict[str, Any]] = config.get("business_stages", {})

            # Thresholds
            self.thresholds: dict[str, int] = config.get("thresholds", {})

            # Services
            self.services: list[dict[str, Any]] = config.get("services", [])

            # Follow-up
            self.follow_up_config: dict[str, str] = config.get("follow_up_config", {})

            # B2B specific fields (empty for B2C)
            self.partner_types: dict[str, Any] = {}
            self.high_intent_signals: list[str] = []
            self.partner_icp: dict[str, Any] = {}
            self.partner_tiers: dict[str, Any] = {}
            self.client_access_scoring: dict[str, Any] = {}
            self.comai_partner_fit_scoring: dict[str, Any] = {}

        # Decision maker
        self.decision_maker_roles: list[str] = config.get("decision_maker_roles", [])

        # Discovery sources
        self.discovery_sources: list[dict[str, Any]] = config.get("discovery_sources", [])

        # Output requirements
        self.output_requirements: dict[str, Any] = config.get("output_requirements", {})


def load_icp(business_unit: str) -> ICPConfig:
    """Load ICP configuration for a business unit."""
    config_path = (
        Path(__file__).parent.parent.parent / "config" / "icps" / f"{business_unit}.yaml"
    )
    if not config_path.exists():
        raise FileNotFoundError(f"ICP config not found: {config_path}")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    logger.info("Loaded ICP config for %s: %s", business_unit, config["name"])
    return ICPConfig(config)


def load_all_icps() -> dict[str, ICPConfig]:
    """Load all ICP configurations."""
    icp_dir = Path(__file__).parent.parent.parent / "config" / "icps"
    icps: dict[str, ICPConfig] = {}
    for yaml_file in icp_dir.glob("*.yaml"):
        business_unit = yaml_file.stem
        icps[business_unit] = load_icp(business_unit)
    return icps
