"""End-to-end test: Detection -> Enrichment -> Outreach Draft"""
import asyncio
import sys
sys.path.insert(0, "apps/api")
sys.path.insert(0, "apps/worker")
sys.path.insert(0, "packages")

from app.db.session import AsyncSessionLocal
from app.services.buying_events import BuyingEventDetector
from app.models.buying_event import BuyingEvent, BuyingEventStatus
from app.models.raw_event import RawEvent, RawEventStatus
from app.models.company_universe import CompanyUniverse
from revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine
from revenue_data_acquisition.dm_recovery.engine import DecisionMakerRecoveryEngine
from sqlalchemy import func, select

async def main():
    async with AsyncSessionLocal() as session:
        detector = BuyingEventDetector(session)
        
        # Reset processed events back to RECEIVED so detection can re-process
        from sqlalchemy import update
        await session.execute(
            update(RawEvent).where(RawEvent.status == "PROCESSED").values(status=RawEventStatus.RECEIVED)
        )
        # Delete old buying events
        await session.execute(
            BuyingEvent.__table__.delete()
        )
        # Reset company_universe buying event flags
        await session.execute(
            update(CompanyUniverse).where(CompanyUniverse.has_buying_event == True).values(has_buying_event=False, buying_event_id=None)
        )
        await session.commit()
        
        print("=" * 60)
        print("STEP 1: DETECT BUYING EVENTS")
        print("=" * 60)
        
        comai_events = await detector.detect_buying_events("COMAI", batch_size=5000)
        print(f"COMAI buying events detected: {len(comai_events)}")
        
        inowix_events = await detector.detect_buying_events("INOWIX", batch_size=5000)
        print(f"INOWIX buying events detected: {len(inowix_events)}")
        
        all_events = comai_events + inowix_events
        
        # Save verified events
        for event_data in all_events:
            buying_event = BuyingEvent(
                raw_event_id=event_data["raw_event_id"],
                department=event_data["department"],
                event_type=event_data["event_type"],
                confidence=event_data["confidence"],
                evidence=event_data["evidence"],
                company_name=event_data["company_name"],
                company_domain=event_data.get("company_domain"),
                contact_info=event_data.get("contact_info", {}),
                disqualifiers=event_data.get("disqualifiers", []),
                status=BuyingEventStatus.VERIFIED,
                verified_at=event_data.get("verified_at"),
            )
            session.add(buying_event)
            
            print(f"\n  Saved: {event_data['department']} - {event_data['event_type']}")
            print(f"    Company: {event_data['company_name']}")
            print(f"    Domain: {event_data.get('company_domain', 'N/A')}")
            print(f"    Confidence: {event_data['confidence']:.2f}")
            print(f"    Contact: {event_data.get('contact_info', {})}")
        
        # Mark processed raw events
        for event in all_events:
            raw_event = await session.get(RawEvent, event["raw_event_id"])
            if raw_event:
                raw_event.status = RawEventStatus.PROCESSED
        
        await session.commit()
        
        print(f"\n{'=' * 60}")
        print("STEP 2: ENRICH DATA (Emails, Decision Makers)")
        print("=" * 60)
        
        contact_engine = ContactRecoveryEngine()
        dm_engine = DecisionMakerRecoveryEngine()
        
        enriched_data = {}
        for event_data in all_events:
            domain = event_data.get("company_domain")
            if not domain:
                continue
            
            print(f"\n  Enriching: {domain}")
            
            # Recover emails
            emails = contact_engine.recover(domain)
            if emails:
                print(f"    Emails found: {len(emails)}")
                for e in emails[:3]:
                    print(f"      - {e.value} (confidence: {e.confidence}%)")
            else:
                print("    No emails found from website")
            
            # Recover decision makers
            dms = dm_engine.recover(domain)
            if dms:
                print(f"    Decision makers found: {len(dms)}")
                for dm in dms[:3]:
                    print(f"      - {dm['name']} ({dm['role']})")
            else:
                print("    No decision makers found from website")
            
            enriched_data[domain] = {
                "emails": emails,
                "dms": dms,
                "existing_email": event_data.get("contact_info", {}).get("email"),
                "existing_author": event_data.get("contact_info", {}).get("author"),
                "linkedin": event_data.get("contact_info", {}).get("linkedin"),
            }
        
        print(f"\n{'=' * 60}")
        print("STEP 3: GENERATE OUTREACH DRAFTS")
        print("=" * 60)
        
        for event_data in all_events:
            domain = event_data.get("company_domain")
            company_name = event_data.get("company_name")
            event_type = event_data.get("event_type")
            
            if not domain:
                continue
            
            enriched = enriched_data.get(domain, {})
            
            # Best email available
            email = None
            if enriched.get("emails"):
                email = enriched["emails"][0].value
            elif enriched.get("existing_email"):
                email = enriched["existing_email"]
            else:
                email = f"hello@{domain}"
            
            # Best contact name
            dm_name = "there"
            dm_role = "Team"
            if enriched.get("dms"):
                dm_name = enriched["dms"][0]["name"].split()[0]
                dm_role = enriched["dms"][0]["role"]
            elif enriched.get("existing_author"):
                dm_name = enriched["existing_author"]
            
            # Personalized outreach based on event type
            event_description = event_type.replace("_", " ")
            
            if event_type == "outsourcing_signal":
                hook = f"I saw you're hiring engineers for your AI manufacturing platform"
            elif event_type == "building_mvp":
                hook = f"I noticed you're building an MVP and might need technical execution support"
            elif event_type == "technical_blocked":
                hook = f"I saw you're facing technical challenges and might need extra development capacity"
            elif event_type == "explicit_need":
                hook = f"I saw your post looking for a development partner"
            else:
                hook = f"I came across {company_name} and thought we could help"
            
            outreach = f"""
{'='*50}
OUTREACH DRAFT: {company_name}
{'='*50}
To: {email}
Contact: {dm_name} ({dm_role})
LinkedIn: {enriched.get('linkedin', 'N/A')}
Source: {event_data.get('source', 'N/A')}
Event: {event_description} (confidence: {event_data['confidence']:.0%})

Subject: Quick question about {company_name}

Hi {dm_name},

{hook}.

At INOWIX, we help startups and growing companies:
- Build production-ready MVPs and scale products
- Provide dedicated development teams on demand
- Deliver complex technical projects on time and budget

I'd love to learn more about what you're building and see if there's a fit.

Would you be open to a 15-minute call this week?

Best,
[Your Name]
INOWIX | Software Development Partner
{'='*50}
"""
            print(outreach)
        
        print(f"\n{'=' * 60}")
        print("FINAL DATABASE STATE")
        print("=" * 60)
        
        buying_count = (await session.execute(select(func.count(BuyingEvent.id)))).scalar()
        company_count = (await session.execute(select(func.count(CompanyUniverse.id)))).scalar()
        companies_with_events = (await session.execute(
            select(func.count(CompanyUniverse.id)).where(CompanyUniverse.has_buying_event == True)
        )).scalar()
        raw_count = (await session.execute(select(func.count(RawEvent.id)))).scalar()
        
        print(f"  Raw Events: {raw_count}")
        print(f"  Buying Events: {buying_count}")
        print(f"  Companies in Universe: {company_count}")
        print(f"  Companies with Buying Events: {companies_with_events}")
        print(f"  Outreach Drafts Generated: {len(all_events)}")

asyncio.run(main())
