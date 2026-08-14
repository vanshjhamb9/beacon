"""Opportunity Connector Platform (OCP v1) — standardized evidence-only connectors."""

from opportunity_connector_platform.connector import Connector, ConnectorHealth
from opportunity_connector_platform.connector_capabilities import ConnectorCapability
from opportunity_connector_platform.connector_events import EvidenceEvent, RoutedEvidenceEvent

__all__ = [
    "Connector",
    "ConnectorHealth",
    "ConnectorCapability",
    "EvidenceEvent",
    "RoutedEvidenceEvent",
]
