from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EcommerceLeadResponse(BaseModel):
    id: UUID
    company_name: str
    website: str
    domain: str
    platform: str
    industry: str
    category: str
    country: str
    city: str
    state: str
    description: str
    product_count: int
    estimated_size: str
    social_links: dict[str, Any] = Field(default_factory=dict)
    instagram_url: str
    facebook_url: str
    linkedin_url: str
    owner_name: str
    founder_name: str
    decision_maker_role: str
    email: str
    phone: str
    contact_source: str
    contact_confidence: float
    shopify_detected: bool
    woocommerce_detected: bool
    magento_detected: bool
    chatbot_detected: bool
    whatsapp_detected: bool
    crm_detected: bool
    comai_score: float
    lead_priority: str
    sales_reason: str
    pain_points: list[str] = Field(default_factory=list)
    source: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class EcommerceLeadListResponse(BaseModel):
    leads: list[EcommerceLeadResponse]
    total: int
    page: int
    page_size: int


class EcommerceDiscoverRequest(BaseModel):
    limit: int = 500
    country: str = "India"


class EcommerceDiscoverResponse(BaseModel):
    status: str
    message: str
    task_id: str | None = None


class EcommerceExportResponse(BaseModel):
    download_url: str
    filename: str
    lead_count: int


class EcommerceStatsResponse(BaseModel):
    total_leads: int
    hot_leads: int
    warm_leads: int
    low_leads: int
    platforms: dict[str, int]
    categories: dict[str, int]
    avg_score: float
