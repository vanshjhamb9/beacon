"""Simulate the ecommerce leads list query."""
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    pass

class EcommerceLeadRow(Base):
    __tablename__ = "ecommerce_leads"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(512))
    domain: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(64))
    industry: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(128))
    country: Mapped[str] = mapped_column(String(128))
    city: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    product_count: Mapped[int] = mapped_column(Integer)
    estimated_size: Mapped[str] = mapped_column(String(64))
    social_links: Mapped[dict] = mapped_column(JSONB)
    instagram_url: Mapped[str] = mapped_column(String(512))
    facebook_url: Mapped[str] = mapped_column(String(512))
    linkedin_url: Mapped[str] = mapped_column(String(512))
    owner_name: Mapped[str] = mapped_column(String(255))
    founder_name: Mapped[str] = mapped_column(String(255))
    decision_maker_role: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(320))
    phone: Mapped[str] = mapped_column(String(64))
    contact_source: Mapped[str] = mapped_column(String(64))
    contact_confidence: Mapped[float] = mapped_column(Float)
    shopify_detected: Mapped[bool] = mapped_column(Boolean)
    woocommerce_detected: Mapped[bool] = mapped_column(Boolean)
    magento_detected: Mapped[bool] = mapped_column(Boolean)
    chatbot_detected: Mapped[bool] = mapped_column(Boolean)
    whatsapp_detected: Mapped[bool] = mapped_column(Boolean)
    crm_detected: Mapped[bool] = mapped_column(Boolean)
    comai_score: Mapped[float] = mapped_column(Float)
    lead_priority: Mapped[str] = mapped_column(String(32))
    sales_reason: Mapped[str] = mapped_column(Text)
    pain_points: Mapped[list] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(64))

async def main():
    e = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/beacon")
    async with e.begin() as c:
        # Simulate the exact query from the repository
        query = select(EcommerceLeadRow).where(EcommerceLeadRow.deleted_at.is_(None)).limit(3)
        try:
            r = await c.execute(query)
            rows = r.scalars().all()
            print(f"Got {len(rows)} rows")
            for row in rows:
                print(f"  {row.company_name} | {row.email} | {row.phone}")
        except Exception as ex:
            print(f"Error: {ex}")
    await e.dispose()

asyncio.run(main())
