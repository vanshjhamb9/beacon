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
