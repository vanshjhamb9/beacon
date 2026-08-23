"""Verified SaaS / tech product companies for inowix live discovery.

Small/mid-size product companies that may need engineering capacity,
AI integration, or mobile development partners.
"""

from __future__ import annotations

from packages.ecommerce_leads.models import RawEcommerceLead


# Each entry: (company_name, website, industry, city)
SAAS_VERIFIED_BRANDS: list[tuple[str, str, str, str]] = [
    # YC SaaS companies (small teams, likely need capacity)
    ("Nessie Labs", "https://nessielabs.com", "saas", "San Francisco"),
    ("Juno", "https://junocompanion.com", "healthtech", "San Francisco"),
    ("Prematch", "https://prematchapp.de", "saas", "Cologne"),
    ("Hoplite", "https://hoplite.dev", "developer tools", "San Francisco"),
    ("CultOS", "https://cultos.com", "saas", "New York"),
    ("Verve", "https://verve.com", "fintech", "London"),
    ("Zepel", "https://zepel.io", "developer tools", "Bangalore"),
    ("Feather", "https://feather-insurance.com", "fintech", "Berlin"),
    ("Livspace", "https://livspace.com", "marketplace", "Bangalore"),
    ("Mews", "https://mews.com", "saas", "Amsterdam"),
    ("Spendesk", "https://spendesk.com", "fintech", "Paris"),
    ("PriceListo", "https://pricelisto.com", "saas", "Singapore"),
    ("Elenas", "https://elenas.co", "marketplace", "Bogota"),
    ("Dot", "https://dot.me", "saas", "Tel Aviv"),
    ("Elph", "https://elph.com", "fintech", "San Francisco"),
    ("Keel", "https://keel.com", "saas", "London"),
    ("Polywork", "https://polywork.com", "saas", "San Francisco"),
    ("Cron", "https://cron.com", "productivity", "Berlin"),
    ("Ribbon", "https://ribbon.co", "fintech", "New York"),
    ("Pilot", "https://pilot.com", "fintech", "San Francisco"),
    # Indian SaaS companies
    ("Postman", "https://postman.com", "developer tools", "Bangalore"),
    ("Razorpay", "https://razorpay.com", "fintech", "Bangalore"),
    ("Freshworks", "https://freshworks.com", "saas", "Chennai"),
    ("Zoho", "https://zoho.com", "saas", "Chennai"),
    ("InMobi", "https://inmobi.com", "saas", "Bangalore"),
    ("Druva", "https://druva.com", "saas", "Pune"),
    ("CleverTap", "https://clevertap.com", "saas", "Mumbai"),
    ("Whatfix", "https://whatfix.com", "saas", "Bangalore"),
    ("Vakilsearch", "https://vakilsearch.com", "saas", "Chennai"),
    ("NoPaperForms", "https://nopaperforms.com", "saas", "Bangalore"),
    ("Darwinbox", "https://darwinbox.com", "saas", "Hyderabad"),
    ("Hevo Data", "https://hevodata.com", "saas", "Bangalore"),
    ("Kissflow", "https://kissflow.com", "saas", "Chennai"),
    ("Qubole", "https://qubole.com", "saas", "Bangalore"),
    ("RateGain", "https://rategain.com", "saas", "Noida"),
    ("Instamojo", "https://instamojo.com", "saas", "Bangalore"),
    ("Uniphore", "https://uniphore.com", "saas", "Bangalore"),
    ("Yellow.ai", "https://yellow.ai", "saas", "Bangalore"),
    ("Skit.ai", "https://skit.ai", "saas", "Bangalore"),
    # Global SaaS (small teams)
    ("Linear", "https://linear.app", "developer tools", "San Francisco"),
    ("Notion", "https://notion.so", "productivity", "San Francisco"),
    ("Figma", "https://figma.com", "design tools", "San Francisco"),
    ("Vercel", "https://vercel.com", "developer tools", "San Francisco"),
    ("Supabase", "https://supabase.com", "developer tools", "San Francisco"),
    ("Railway", "https://railway.app", "developer tools", "San Francisco"),
    ("Render", "https://render.com", "developer tools", "San Francisco"),
    ("Fly.io", "https://fly.io", "developer tools", "San Francisco"),
    ("Loops", "https://loops.so", "saas", "San Francisco"),
    ("Resend", "https://resend.com", "developer tools", "San Francisco"),
    ("Cal.com", "https://cal.com", "saas", "San Francisco"),
    ("Tldv", "https://tldv.io", "saas", "Berlin"),
    ("Loom", "https://loom.com", "saas", "San Francisco"),
    ("Maze", "https://maze.co", "design tools", "New York"),
    ("Crowd", "https://crowd.dev", "saas", "Berlin"),
    ("Clerk", "https://clerk.com", "developer tools", "San Francisco"),
    ("WorkOS", "https://workos.com", "developer tools", "San Francisco"),
    ("Stytch", "https://stytch.com", "developer tools", "San Francisco"),
    ("Retool", "https://retool.com", "developer tools", "San Francisco"),
    ("Temporal", "https://temporal.io", "developer tools", "San Francisco"),
]


def get_saas_verified_leads() -> list[RawEcommerceLead]:
    """Return SaaS verified brands as RawEcommerceLead objects for live discovery."""
    leads: list[RawEcommerceLead] = []
    for company_name, website, industry, city in SAAS_VERIFIED_BRANDS:
        domain = website.replace("https://", "").replace("http://", "").rstrip("/")
        leads.append(
            RawEcommerceLead(
                company_name=company_name,
                domain=domain,
                industry=industry,
                city=city,
                website=website,
            )
        )
    return leads
