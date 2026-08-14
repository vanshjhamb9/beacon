"""Generate outreach drafts for OUTREACH_READY companies only.

CTO Rules:
- Only generate for OUTREACH_READY queue
- Never use generic claims unless evidence supports
- Position as solution to requirement, not "we know you need"
- Hiring signal positioning: "Instead of waiting through hiring cycle..."
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

PROJECT_ROOT = Path(__file__).parent
EXPORTS_DIR = PROJECT_ROOT / "exports"


def load_sales_queue() -> list[dict[str, Any]]:
    """Load final sales queue."""
    input_file = EXPORTS_DIR / "final_sales_queue.json"
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_email_draft(company: dict) -> dict:
    """Generate email draft for OUTREACH_READY company."""
    company_name = company.get("company")
    requirement = company.get("requirement")
    decision_maker = company.get("decision_maker")
    service_match = company.get("service_match")
    pitch_angle = company.get("pitch_angle")
    why_now = company.get("why_now")

    # Extract key requirement details
    role = "AI Conversational Chatbot Developer"
    locations = "multiple cities"
    experience = "1-4 years"

    if "Chatbot Developer" in requirement:
        role = "AI Conversational Chatbot Developer"
    if "3 cities" in requirement:
        locations = "3 cities"
    if "1-4 Yrs" in requirement:
        experience = "1-4 years"

    subject = f"Engineering support for your chatbot hiring initiative"

    body = f"""Hi {decision_maker},

I noticed Benovymed is hiring an {role} across {locations} with {experience} experience in Python, deep learning, Rasa, and Dialogflow.

Instead of waiting through the hiring cycle for this specialized healthcare AI role, we could explore whether an external engineering team could support this requirement immediately.

We've built production-grade conversational AI for healthcare applications — including HIPAA-compliant chatbots, patient engagement systems, and clinical workflow automation.

Our healthcare AI team has delivered:
- Rasa-based symptom assessment chatbots
- Dialogflow-powered patient intake systems
- HIPAA-compliant conversational interfaces
- Integration with EHR/EMR systems

Would you be open to a 15-minute call to discuss whether this could accelerate your healthcare AI initiative?

Best regards,
Vansh Jamb
Inowix
vansh@inowix.in"""

    return {
        "company": company_name,
        "channel": "email",
        "to": company.get("email"),
        "to_status": company.get("email_status"),
        "subject": subject,
        "body": body,
        "generated_at": datetime.now().isoformat(),
        "requires_verification": company.get("email_status") != "VERIFIED",
    }


def generate_linkedin_draft(company: dict) -> dict:
    """Generate LinkedIn message draft."""
    company_name = company.get("company")
    decision_maker = company.get("decision_maker")
    decision_maker_linkedin = company.get("decision_maker_linkedin")

    message = f"""Hi {decision_maker},

I noticed Benovymed is hiring an AI Chatbot Developer across 3 cities. We specialize in healthcare conversational AI — Rasa, Dialogflow, HIPAA-compliant systems.

Instead of waiting through the hiring cycle for this specialized role, we could explore whether an external team could support this requirement immediately.

Would you be open to a brief conversation?

Best,
Vansh"""

    return {
        "company": company_name,
        "channel": "linkedin",
        "to": decision_maker,
        "to_linkedin": decision_maker_linkedin,
        "message": message,
        "generated_at": datetime.now().isoformat(),
        "connection_note": "Send connection request with personalized note first",
    }


def generate_whatsapp_draft(company: dict) -> dict:
    """Generate WhatsApp draft if appropriate contact exists."""
    company_name = company.get("company")
    decision_maker = company.get("decision_maker")

    message = f"""Hi {decision_maker}, this is Vansh from Inowix.

I noticed Benovymed is hiring an AI Chatbot Developer across 3 cities. We specialize in healthcare conversational AI.

Instead of waiting through the hiring cycle, we could explore whether an external team could support this requirement immediately.

Would you be open to a brief call?

Best,
Vansh"""

    return {
        "company": company_name,
        "channel": "whatsapp",
        "to": decision_maker,
        "phone": company.get("phone"),
        "phone_status": company.get("phone_status"),
        "message": message,
        "generated_at": datetime.now().isoformat(),
        "requires_verified_phone": company.get("phone_status") != "VERIFIED",
    }


def main():
    """Generate outreach drafts for OUTREACH_READY companies only."""
    print("Loading sales queue...")
    companies = load_sales_queue()

    # Filter for OUTREACH_READY only
    outreach_ready = [c for c in companies if c.get("queue") == "OUTREACH_READY"]
    print(f"Found {len(outreach_ready)} OUTREACH_READY companies")

    all_drafts = []

    for company in outreach_ready:
        company_name = company.get("company")
        print(f"\nGenerating drafts for {company_name}...")

        # Email draft
        email_draft = generate_email_draft(company)
        all_drafts.append(email_draft)
        print(f"  Email draft generated")

        # LinkedIn draft
        linkedin_draft = generate_linkedin_draft(company)
        all_drafts.append(linkedin_draft)
        print(f"  LinkedIn draft generated")

        # WhatsApp draft (if phone available)
        if company.get("phone"):
            whatsapp_draft = generate_whatsapp_draft(company)
            all_drafts.append(whatsapp_draft)
            print(f"  WhatsApp draft generated")

    # Save drafts
    output_file = EXPORTS_DIR / "final_outreach_drafts.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_drafts, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_drafts)} outreach drafts to {output_file}")

    # Print summary
    print(f"\n{'='*60}")
    print("OUTREACH DRAFTS SUMMARY")
    print(f"{'='*60}")
    for draft in all_drafts:
        print(f"  {draft['company']} - {draft['channel']}")


if __name__ == "__main__":
    main()
