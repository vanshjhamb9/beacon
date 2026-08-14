import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from packages.revenue_data_acquisition.contact_recovery.engine import ContactRecoveryEngine

async def test():
    engine = ContactRecoveryEngine()

    domains = [
        "partnac.com",
        "buildzoom.com",
        "coddykit.com",
        "tryharmony.ai",
        "databricks.com",
    ]

    for domain in domains:
        print(f"\n=== {domain} ===")
        try:
            result = engine.recover(f"https://{domain}")
            print(f"  Contacts found: {len(result)}")
            for contact in result[:5]:
                print(f"    {contact.value} (source: {contact.source}, conf: {contact.confidence})")
        except Exception as e:
            print(f"  Error: {e}")

asyncio.run(test())
